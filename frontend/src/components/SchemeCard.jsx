export default function SchemeCard({ scheme }) {
  return (
    <article className="rounded-2xl border border-brand-200/70 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lift">
      <div className="mb-2 flex items-start justify-between gap-3">
        <h4 className="font-heading text-base font-semibold text-ink">{scheme.scheme_name}</h4>
        <span className="rounded-full bg-brand-100 px-2 py-1 text-xs font-medium text-brand-800">
          {scheme.scheme_level || "N/A"}
        </span>
      </div>

      <p className="mb-3 text-sm text-slate-700">{scheme.match_reason}</p>

      <ul className="space-y-1 text-sm text-slate-700">
        <li><strong>Benefit:</strong> {scheme.benefit_description || "N/A"}</li>
        <li><strong>Amount:</strong> {scheme.benefit_amount || "N/A"}</li>
        <li><strong>Eligibility:</strong> {scheme.eligibility_criteria || "N/A"}</li>
        <li><strong>Documents:</strong> {scheme.required_documents || "N/A"}</li>
        <li><strong>Apply:</strong> {scheme.application_process || "N/A"}</li>
      </ul>

      {scheme.application_url && (
        <a
          className="mt-3 inline-block text-sm font-semibold text-brand-700 hover:text-brand-900"
          href={scheme.application_url}
          target="_blank"
          rel="noreferrer"
        >
          Open Application Link
        </a>
      )}
    </article>
  );
}
