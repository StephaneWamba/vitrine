export default function Footer() {
  return (
    <footer style={{ borderTop: "1px solid var(--border)", background: "var(--bg)" }}>
      <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="label-caps" style={{ color: "var(--text-faint)", letterSpacing: "0.2em" }}>
            Vitrine
          </p>
          <p className="mono mt-1" style={{ fontSize: 11, color: "var(--text-faint)" }}>
            29 000 articles · recherche par description · 603 familles produits
          </p>
        </div>

        <div className="flex flex-col sm:items-end gap-1">
          <p className="mono" style={{ fontSize: 11, color: "var(--text-faint)" }}>
            Next.js · FastAPI · BigQuery · OpenAI
          </p>
          <p className="mono" style={{ fontSize: 11, color: "var(--text-faint)" }}>
            Vercel · Cloud Run · Artifact Registry
          </p>
        </div>
      </div>
    </footer>
  );
}
