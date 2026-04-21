export default function SchemeCard({ scheme, labels }) {
  const text = labels || {
    benefit: "Benefit",
    amount: "Amount",
    eligibility: "Eligibility",
    documents: "Documents",
    apply: "Apply",
    openApplication: "Open Application Link",
    na: "N/A",
  };

  return (
    <article className="scheme-card">
      <div className="scheme-card__header">
        <h4>{scheme.scheme_name}</h4>
        <span className="scheme-card__badge">
          {scheme.scheme_level || text.na}
        </span>
      </div>

      <p className="scheme-card__reason">{scheme.match_reason}</p>

      <ul className="scheme-card__meta">
        <li><strong>{text.benefit}:</strong> {scheme.benefit_description || text.na}</li>
        <li><strong>{text.amount}:</strong> {scheme.benefit_amount || text.na}</li>
        <li><strong>{text.eligibility}:</strong> {scheme.eligibility_criteria || text.na}</li>
        <li><strong>{text.documents}:</strong> {scheme.required_documents || text.na}</li>
        <li><strong>{text.apply}:</strong> {scheme.application_process || text.na}</li>
      </ul>

      {scheme.application_url && (
        <a
          className="scheme-card__link"
          href={scheme.application_url}
          target="_blank"
          rel="noreferrer"
        >
          {text.openApplication}
        </a>
      )}
    </article>
  );
}
