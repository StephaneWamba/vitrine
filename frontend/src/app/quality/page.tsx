import { getQuality, type QualityReport } from "@/lib/api";

export const dynamic = "force-dynamic";

function fmt(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function KPI({ value, label, accent = false }: { value: string; label: string; accent?: boolean }) {
  return (
    <div>
      <p
        className="display heading-tight tabnum count-target"
        style={{
          fontSize: "clamp(40px, 5vw, 72px)",
          lineHeight: 1,
          color: accent ? "var(--accent)" : "var(--text)",
        }}
      >
        {value}
      </p>
      <p className="label-caps mt-2" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
    </div>
  );
}

function StatRow({ label, value, bar }: { label: string; value: string; bar?: number }) {
  return (
    <div className="py-3 flex items-center gap-4" style={{ borderTop: "1px solid var(--border)" }}>
      <span style={{ fontSize: 13, flex: 1, color: "var(--text-muted)" }}>{label}</span>
      {bar !== undefined && (
        <div className="relative" style={{ width: 80, height: 3, background: "var(--border)" }}>
          <div
            className="bar-fill absolute left-0 top-0 h-full"
            style={{
              width: `${bar}%`,
              background: bar >= 80 ? "var(--green)" : bar >= 50 ? "var(--accent)" : "var(--red)",
            }}
          />
        </div>
      )}
      <span className="mono tabnum" style={{ fontSize: 13, color: "var(--text)", minWidth: 60, textAlign: "right" }}>
        {value}
      </span>
    </div>
  );
}

function pct(count: number | null, total: number): number | null {
  if (count === null || total === 0) return null;
  return Math.round((count / total) * 100);
}

export default async function QualityPage() {
  let report: QualityReport | null = null;
  let error: string | null = null;

  try {
    report = await getQuality();
  } catch (e) {
    const msg = (e as Error).message;
    // 404 = no report yet, not an error
    if (!msg.startsWith("404")) error = msg;
  }

  return (
    <div>
      {/* ── Hero with grid texture ─────────────────────────────────── */}
      <div className="grid-texture" style={{ borderBottom: "1px solid var(--border)" }}>
        <div className="max-w-7xl mx-auto px-6 py-16">
          <p className="label-caps" style={{ color: "var(--text-muted)" }}>/ quality</p>
          <h1 className="display heading-tight mt-1" style={{ fontSize: "clamp(28px, 4vw, 44px)" }}>
            Data Quality Report
          </h1>
          {report && (
            <p className="mono mt-1" style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {new Date(report.report_timestamp).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-14">
        {error ? (
          <p className="mono" style={{ fontSize: 12, color: "var(--red)" }}>{error}</p>
        ) : !report ? (
          <p className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
            No quality report yet — run the pipeline first.
          </p>
        ) : (
          <>
            {/* ── KPIs ──────────────────────────────────────────────── */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-10 mb-16">
              <KPI value={report.total_records.toLocaleString()} label="Total records" />
              <KPI value={report.valid_records.toLocaleString()} label="Valid records" />
              <KPI
                value={`${report.completeness_pct.toFixed(1)}%`}
                label="Completeness"
                accent
              />
              {report.price_mean !== null && (
                <KPI value={fmt(report.price_mean)} label="Avg price" accent />
              )}
            </div>

            {/* ── Field coverage ────────────────────────────────────── */}
            <div className="grid md:grid-cols-2 gap-x-16 mb-16">
              <div>
                <h2 className="display heading-tight mb-4" style={{ fontSize: 20 }}>
                  Field Coverage
                </h2>
                {report.field_name_completeness !== null && (() => { const p = pct(report.field_name_completeness, report.total_records)!; return <StatRow label="Name" value={`${p}%`} bar={p} />; })()}
                {report.field_brand_completeness !== null && (() => { const p = pct(report.field_brand_completeness, report.total_records)!; return <StatRow label="Brand" value={`${p}%`} bar={p} />; })()}
                {report.field_cat_completeness !== null && (() => { const p = pct(report.field_cat_completeness, report.total_records)!; return <StatRow label="Category" value={`${p}%`} bar={p} />; })()}
                {report.field_price_completeness !== null && (() => { const p = pct(report.field_price_completeness, report.total_records)!; return <StatRow label="Price" value={`${p}%`} bar={p} />; })()}
              </div>

              {/* ── Price range ───────────────────────────────────────── */}
              {report.price_min !== null && (
                <div>
                  <h2 className="display heading-tight mb-4" style={{ fontSize: 20 }}>
                    Price Range
                  </h2>
                  <StatRow label="Min" value={fmt(report.price_min)} />
                  {report.price_mean !== null && (
                    <StatRow label="Mean" value={fmt(report.price_mean)} />
                  )}
                  {report.price_max !== null && (
                    <StatRow label="Max" value={fmt(report.price_max)} />
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
