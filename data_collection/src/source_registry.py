from __future__ import annotations

from urllib.parse import urlparse

OFFICIAL_DOMAINS = {
    "tnsocialwelfare.tn.gov.in",
    "tn.gov.in",
    "cms.tn.gov.in",
    "www.tn.gov.in",
    "myscheme.gov.in",
    "www.myscheme.gov.in",
    "data.gov.in",
    "www.data.gov.in",
    "india.gov.in",
    "www.india.gov.in",
    "pmjdy.gov.in",
    "www.pmjdy.gov.in",
    "nrega.nic.in",
    "www.nrega.nic.in",
    "pmkisan.gov.in",
    "www.pmkisan.gov.in",
    "nsap.nic.in",
    "www.nsap.nic.in",
    "socialjustice.gov.in",
    "www.socialjustice.gov.in",
    "rural.nic.in",
    "www.rural.nic.in",
    "pib.gov.in",
    "www.pib.gov.in",
}

_DISCOVERY_QUERIES = [
    "Tamil Nadu welfare schemes official",
    "Tamil Nadu government social welfare schemes women children senior citizens",
    "Tamil Nadu schemes for women official website",
    "Tamil Nadu schemes for children official website",
    "Tamil Nadu senior citizen welfare schemes official",
    "Tamil Nadu transgender welfare schemes official",
    "Tamil Nadu disability welfare schemes official",
    "Tamil Nadu low income family welfare schemes official",
    "Indian central government welfare schemes applicable in Tamil Nadu",
    "central schemes for poor families India official",
    "social welfare and empowerment schemes India official",
    "financial inclusion schemes India official",
    "health and insurance schemes India official",
    "education scholarships schemes India official",
    "employment guarantee and livelihood schemes India official",
    "housing and social security schemes India official",
    "women and child development schemes India official",
]

_SEED_URLS = [
    "https://www.tnsocialwelfare.tn.gov.in/en/schemes",
    "https://www.tnsocialwelfare.tn.gov.in/en/specilisations",
    "https://www.tnsocialwelfare.tn.gov.in/en/specilisations/child-welfare",
    "https://www.tnsocialwelfare.tn.gov.in/en/specilisations/women-welfare",
    "https://www.tnsocialwelfare.tn.gov.in/en/specilisations/senior-citizen-welfare",
    "https://www.tnsocialwelfare.tn.gov.in/en/specilisations/transgenders-welfare",
    "https://www.tnsocialwelfare.tn.gov.in/en/state-resource-centre-for-women",
    "https://www.tnsocialwelfare.tn.gov.in/en/sitemap",
    "https://www.myscheme.gov.in/",
    "https://www.data.gov.in/",
    "https://www.pmjdy.gov.in/scheme",
    "https://www.india.gov.in/topics/benefits",
]


def _normalize_domain(domain: str) -> str:
    value = domain.strip().lower()
    if value.startswith("www."):
        return value[4:]
    return value


OFFICIAL_DOMAINS_NORMALIZED = {_normalize_domain(d) for d in OFFICIAL_DOMAINS}


def domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    return _normalize_domain(parsed.netloc)


def is_official_url(url: str) -> bool:
    domain = domain_from_url(url)
    if not domain:
        return False

    if domain in OFFICIAL_DOMAINS_NORMALIZED:
        return True

    for base_domain in OFFICIAL_DOMAINS_NORMALIZED:
        if domain.endswith("." + base_domain):
            return True

    return False


def discovery_queries() -> list[str]:
    return list(_DISCOVERY_QUERIES)


def seed_urls() -> list[str]:
    return list(dict.fromkeys(_SEED_URLS))


def include_domains_for_tavily() -> list[str]:
    return sorted(OFFICIAL_DOMAINS_NORMALIZED)
