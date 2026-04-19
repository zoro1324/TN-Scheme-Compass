from __future__ import annotations

import argparse
from datetime import datetime, timezone
import time
from typing import Any

from src.clients.groq_client import GroqClient
from src.clients.ollama_client import OllamaClient
from src.clients.tavily_client import TavilyClient
from src.config import load_settings
from src.fetcher import fetch_page_content
from src.models import ReviewRow, SchemeRecord, build_review_row, model_excerpt
from src.normalizer import deduplicate_records, normalize_scheme_record
from src.source_registry import (
    discovery_queries,
    domain_from_url,
    include_domains_for_tavily,
    is_official_url,
    seed_urls,
)
from src.validator import is_scheme_output, validate_scheme_record
from src.writer import (
    append_accepted_row,
    append_review_row,
    init_accepted_csv,
    init_review_csv,
    write_accepted_csv,
    write_metadata,
    write_review_csv,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Tamil Nadu welfare schemes CSV using official sources, Tavily discovery, and Groq extraction."
    )
    parser.add_argument(
        "--output-file",
        default="outputs/welfare_schemes_tamil_nadu.csv",
        help="Accepted records CSV path",
    )
    parser.add_argument(
        "--review-file",
        default="outputs/review_queue.csv",
        help="Rejected/needs-review CSV path",
    )
    parser.add_argument(
        "--metadata-file",
        default="outputs/run_metadata.json",
        help="Run metadata JSON path",
    )
    parser.add_argument(
        "--max-results-per-query",
        type=int,
        default=None,
        help="Override Tavily max results per query",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Override maximum number of candidate pages to process",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=None,
        help="Override minimum confidence threshold for accepted rows",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run fetch-only checks from seeded URLs without Tavily/Groq calls",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=10,
        help="Print extraction progress every N pages",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Write partial CSV outputs every N processed pages",
    )
    parser.add_argument(
        "--llm-delay-seconds",
        type=float,
        default=1.5,
        help="Delay between page-level LLM calls to reduce provider rate-limit errors",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["groq", "ollama"],
        default=None,
        help="LLM provider for extraction",
    )
    parser.add_argument(
        "--ollama-model",
        default=None,
        help="Ollama model name, for example llama3:8b",
    )
    parser.add_argument(
        "--ollama-base-url",
        default=None,
        help="Ollama server URL, for example http://localhost:11434",
    )
    parser.add_argument(
        "--groq-max-retries",
        type=int,
        default=None,
        help="Max retry attempts for Groq transient failures",
    )
    parser.add_argument(
        "--groq-backoff-seconds",
        type=float,
        default=None,
        help="Base exponential backoff seconds for Groq retries",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    started_at = datetime.now(timezone.utc)

    settings = load_settings()

    llm_provider = (
        args.llm_provider.strip().lower()
        if isinstance(args.llm_provider, str)
        else settings.llm_provider
    )
    if llm_provider not in {"groq", "ollama"}:
        raise ValueError("LLM provider must be one of: groq, ollama")

    ollama_model = (
        args.ollama_model.strip()
        if isinstance(args.ollama_model, str) and args.ollama_model.strip()
        else settings.ollama_model
    )
    ollama_base_url = (
        args.ollama_base_url.strip()
        if isinstance(args.ollama_base_url, str) and args.ollama_base_url.strip()
        else settings.ollama_base_url
    )
    groq_max_retries = (
        args.groq_max_retries
        if args.groq_max_retries is not None
        else settings.groq_max_retries
    )
    groq_backoff_seconds = (
        args.groq_backoff_seconds
        if args.groq_backoff_seconds is not None
        else settings.groq_backoff_seconds
    )

    if not args.dry_run and not settings.tavily_api_key:
        raise ValueError("Missing TAVILY_API_KEY in .env for discovery stage.")
    if not args.dry_run and llm_provider == "groq" and not settings.groq_api_key:
        raise ValueError("Missing GROQ_API_KEY in .env for Groq provider.")

    max_results_per_query = (
        args.max_results_per_query
        if args.max_results_per_query is not None
        else settings.max_results_per_query
    )
    max_pages = args.max_pages if args.max_pages is not None else settings.max_pages
    min_confidence = (
        args.min_confidence
        if args.min_confidence is not None
        else settings.min_confidence
    )
    log_every = max(1, args.log_every)
    checkpoint_every = max(1, args.checkpoint_every)
    llm_delay_seconds = max(0.0, args.llm_delay_seconds)

    print(
        f"[start] dry_run={args.dry_run} llm_provider={llm_provider} max_pages={max_pages} max_results_per_query={max_results_per_query} min_confidence={min_confidence} llm_delay_seconds={llm_delay_seconds}",
        flush=True,
    )

    include_domains = include_domains_for_tavily()
    queries = discovery_queries()

    candidate_urls: dict[str, str] = {}
    for url in seed_urls():
        if is_official_url(url):
            candidate_urls[url] = "seed"

    tavily_calls = 0
    tavily_errors = 0
    if not args.dry_run:
        tavily = TavilyClient(
            api_key=settings.tavily_api_key,
            timeout_seconds=settings.request_timeout_seconds,
        )

        for query_index, query in enumerate(queries, start=1):
            print(f"[discover] query {query_index}/{len(queries)}: {query}", flush=True)
            before_count = len(candidate_urls)
            try:
                hits = tavily.search(
                    query=query,
                    include_domains=include_domains,
                    max_results=max_results_per_query,
                )
                tavily_calls += 1
            except Exception as exc:
                tavily_errors += 1
                print(
                    f"[discover] query failed: {query} error={exc}",
                    flush=True,
                )
                continue

            for hit in hits:
                if not is_official_url(hit.url):
                    continue
                if hit.url not in candidate_urls:
                    candidate_urls[hit.url] = f"tavily:{query}"

            added = len(candidate_urls) - before_count
            print(
                f"[discover] query {query_index}/{len(queries)} added={added} total_candidates={len(candidate_urls)}",
                flush=True,
            )

    print(f"[discover] total official candidate URLs={len(candidate_urls)}", flush=True)

    ranked_candidates = sorted(
        candidate_urls.items(),
        key=lambda item: (_candidate_priority(item[0], item[1]), item[0]),
    )
    urls_to_process = [url for url, _ in ranked_candidates][: max(1, max_pages)]
    print(f"[extract] selected URLs to process={len(urls_to_process)}", flush=True)

    llm_client: Any = None
    if not args.dry_run:
        if llm_provider == "groq":
            llm_client = GroqClient(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                timeout_seconds=settings.request_timeout_seconds,
                max_retries=groq_max_retries,
                base_backoff_seconds=groq_backoff_seconds,
            )
        else:
            llm_client = OllamaClient(
                model=ollama_model,
                base_url=ollama_base_url,
                timeout_seconds=max(60, settings.request_timeout_seconds),
            )

    accepted_rows: list[SchemeRecord] = []
    review_rows: list[ReviewRow] = []

    init_accepted_csv(args.output_file)
    init_review_csv(args.review_file)
    print("[start] initialized output csv files", flush=True)

    def record_review(row: ReviewRow) -> None:
        review_rows.append(row)
        append_review_row(args.review_file, row)

    def record_accepted(row: SchemeRecord) -> None:
        accepted_rows.append(row)
        append_accepted_row(args.output_file, row)

    def maybe_checkpoint(processed_pages: int) -> None:
        if processed_pages % checkpoint_every != 0:
            return

        checkpoint_accepted = deduplicate_records(accepted_rows)
        write_accepted_csv(args.output_file, checkpoint_accepted)
        write_review_csv(args.review_file, review_rows)
        print(
            f"[checkpoint] processed={processed_pages}/{len(urls_to_process)} accepted={len(checkpoint_accepted)} review={len(review_rows)}",
            flush=True,
        )

    for index, url in enumerate(urls_to_process, start=1):
        if index == 1 or index % log_every == 0 or index == len(urls_to_process):
            print(f"[extract] page {index}/{len(urls_to_process)}: {url}", flush=True)

        fetch_started = time.perf_counter()
        page = fetch_page_content(
            url=url,
            timeout_seconds=settings.request_timeout_seconds,
            user_agent=settings.user_agent,
        )
        fetch_elapsed = time.perf_counter() - fetch_started
        print(
            f"[fetch] page {index}/{len(urls_to_process)} elapsed={fetch_elapsed:.2f}s status={page.status_code if page.status_code is not None else 'NA'} text_len={len(page.text)}",
            flush=True,
        )
        page_title = page.title
        source_domain = domain_from_url(url)

        if page.error:
            record_review(
                build_review_row(
                    source_url=url,
                    source_domain=source_domain,
                    page_title=page_title,
                    reason=f"fetch-error: {page.error}",
                )
            )
            maybe_checkpoint(index)
            continue

        if not page.text:
            record_review(
                build_review_row(
                    source_url=url,
                    source_domain=source_domain,
                    page_title=page_title,
                    reason="empty-page-text",
                )
            )
            maybe_checkpoint(index)
            continue

        if args.dry_run or llm_client is None:
            record_review(
                build_review_row(
                    source_url=url,
                    source_domain=source_domain,
                    page_title=page_title,
                    reason="dry-run-no-llm",
                )
            )
            maybe_checkpoint(index)
            continue

        print(
            f"[llm] page {index}/{len(urls_to_process)} provider={llm_provider} model={settings.groq_model if llm_provider == 'groq' else ollama_model} start",
            flush=True,
        )
        llm_started = time.perf_counter()
        raw = llm_client.extract_scheme(
            page_url=url,
            page_title=page_title,
            page_text=page.text,
        )
        llm_elapsed = time.perf_counter() - llm_started
        print(
            f"[llm] page {index}/{len(urls_to_process)} elapsed={llm_elapsed:.2f}s is_scheme={is_scheme_output(raw)} confidence={_as_float(raw.get('confidence', 0.0))}",
            flush=True,
        )

        if llm_delay_seconds > 0 and index < len(urls_to_process):
            time.sleep(llm_delay_seconds)

        confidence = _as_float(raw.get("confidence", 0.0))

        if not is_scheme_output(raw):
            record_review(
                build_review_row(
                    source_url=url,
                    source_domain=source_domain,
                    page_title=page_title,
                    reason="not-a-scheme-page",
                    confidence=confidence,
                    model_output_excerpt=model_excerpt(raw),
                )
            )
            maybe_checkpoint(index)
            continue

        record = normalize_scheme_record(
            raw=raw,
            fallback_source_url=url,
            extraction_method=f"{llm_provider}_llm+official_source",
        )

        reasons = validate_scheme_record(
            record=record,
            min_confidence=min_confidence,
            official_url_check=is_official_url,
        )
        if reasons:
            record_review(
                build_review_row(
                    source_url=url,
                    source_domain=source_domain,
                    page_title=page_title,
                    reason="; ".join(reasons),
                    confidence=record.confidence,
                    model_output_excerpt=model_excerpt(raw),
                )
            )
            maybe_checkpoint(index)
            continue

        record_accepted(record)
        maybe_checkpoint(index)

    accepted_before_dedupe = len(accepted_rows)
    accepted_rows = deduplicate_records(accepted_rows)

    write_accepted_csv(args.output_file, accepted_rows)
    write_review_csv(args.review_file, review_rows)

    ended_at = datetime.now(timezone.utc)
    metadata = {
        "started_at_utc": started_at.isoformat(),
        "ended_at_utc": ended_at.isoformat(),
        "dry_run": args.dry_run,
        "settings": {
            "llm_provider": llm_provider,
            "groq_model": settings.groq_model,
            "ollama_model": ollama_model,
            "ollama_base_url": ollama_base_url,
            "groq_max_retries": groq_max_retries,
            "groq_backoff_seconds": groq_backoff_seconds,
            "max_results_per_query": max_results_per_query,
            "max_pages": max_pages,
            "min_confidence": min_confidence,
            "llm_delay_seconds": llm_delay_seconds,
        },
        "discovery": {
            "seed_count": len(seed_urls()),
            "query_count": len(queries),
            "tavily_calls": tavily_calls,
            "tavily_errors": tavily_errors,
            "candidate_url_count": len(candidate_urls),
            "processed_url_count": len(urls_to_process),
        },
        "results": {
            "accepted_count": len(accepted_rows),
            "accepted_before_deduplication": accepted_before_dedupe,
            "review_count": len(review_rows),
        },
    }
    write_metadata(args.metadata_file, metadata)

    print(f"Processed URLs: {len(urls_to_process)}", flush=True)
    print(f"Accepted rows: {len(accepted_rows)}", flush=True)
    print(f"Review rows: {len(review_rows)}", flush=True)
    print(f"Output CSV: {args.output_file}", flush=True)
    print(f"Review CSV: {args.review_file}", flush=True)
    print(f"Metadata: {args.metadata_file}", flush=True)

    return 0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _candidate_priority(url: str, source_tag: str) -> int:
    path = url.lower()
    score = 0

    if source_tag.startswith("tavily:"):
        score -= 3

    if any(
        token in path
        for token in [
            "/scheme",
            "/schemes/",
            "pension",
            "assistance",
            "welfare-board",
            "programme",
            "benefit",
        ]
    ):
        score -= 2

    if path.endswith("/schemes") or path.endswith("/specilisations"):
        score += 3

    return score


if __name__ == "__main__":
    raise SystemExit(main())
