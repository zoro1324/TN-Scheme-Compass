export default function SchemeCard({ scheme }) {
  return (
    <article className="scheme-card">
      <div className="scheme-card__header">
        <h4>{scheme.scheme_name}</h4>
        <span className="scheme-card__badge">
          {scheme.scheme_level || "N/A"}
        </span>
      </div>

      <p className="scheme-card__reason">{scheme.match_reason}</p>

      <ul className="scheme-card__meta">
        <li><strong>Benefit:</strong> {scheme.benefit_description || "N/A"}</li>
        <li><strong>Amount:</strong> {scheme.benefit_amount || "N/A"}</li>
        <li><strong>Eligibility:</strong> {scheme.eligibility_criteria || "N/A"}</li>
        <li><strong>Documents:</strong> {scheme.required_documents || "N/A"}</li>
        <li><strong>Apply:</strong> {scheme.application_process || "N/A"}</li>
      </ul>

      {scheme.application_url && (
        <a
          className="scheme-card__link"
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
