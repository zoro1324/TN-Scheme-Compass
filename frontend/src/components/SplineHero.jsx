export default function SplineHero({ text }) {
  const heroText = text || {
    kicker: "TN Scheme Compass",
    title: "AI Welfare Scheme Assistant",
    subtitle: "Ask naturally. Get clear eligibility, benefits, and application guidance in one place.",
  };

  return (
    <section className="hero-shell" aria-label="TN Scheme Compass hero">
      <div className="hero-avatar" aria-hidden="true">
        <span className="hero-avatar__emoji">👻</span>
      </div>
      <div className="hero-content">
        <p className="hero-kicker">{heroText.kicker}</p>
        <h1 className="hero-title">{heroText.title}</h1>
        <p className="hero-subtitle">{heroText.subtitle}</p>
      </div>
    </section>
  );
}
