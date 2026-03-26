import Link from "next/link";
import { getClusterProducts, type ClusterProduct } from "@/lib/api";
import { notFound } from "next/navigation";

function tc(s: string) {
  return s.toLowerCase().replace(/(?:^|\s)\S/g, (c) => c.toUpperCase());
}

function fmt(n: number) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function Cols() {
  return (
    <colgroup>
      <col style={{ width: 32 }} />
      <col style={{ width: 130 }} />
      <col />
      <col style={{ width: 70 }} />
    </colgroup>
  );
}

function ProductRow({ product, index }: { product: ClusterProduct; index: number }) {
  return (
    <tr
      className="row-enter"
      style={{ animationDelay: `${index * 20}ms`, borderTop: "1px solid var(--border)" }}
    >
      <td className="mono tabnum py-3 pr-4" style={{ fontSize: 11, color: "var(--text-faint)" }}>
        {String(index + 1).padStart(2, "0")}
      </td>
      <td className="py-3 pr-6" style={{ fontSize: 13, color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {tc(product.brand)}
      </td>
      <td className="py-3 pr-4" style={{ fontSize: 13 }}>
        <div>{tc(product.name)}</div>
        {product.description_enriched && (
          <div
            className="mt-0.5"
            style={{
              fontSize: 11,
              color: "var(--text-muted)",
              lineHeight: 1.5,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {product.description_enriched}
          </div>
        )}
      </td>
      <td className="py-3 tabnum mono text-right" style={{ color: "var(--accent)", fontSize: 13 }}>
        {fmt(product.retail_price)}
      </td>
    </tr>
  );
}

export default async function ClusterDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const clusterId = parseInt(id, 10);
  if (isNaN(clusterId)) notFound();

  let data: { cluster_id: number; cluster_label: string; products: ClusterProduct[] } | null = null;
  let error: string | null = null;

  try {
    data = await getClusterProducts(clusterId);
  } catch (e) {
    const msg = (e as Error).message;
    if (msg.startsWith("404")) notFound();
    error = msg;
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      {/* Fil d'Ariane */}
      <p className="label-caps" style={{ color: "var(--text-muted)" }}>
        <Link href="/clusters" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
          / collections
        </Link>
        {data && (
          <span style={{ color: "var(--text-faint)" }}> / {data.cluster_id}</span>
        )}
      </p>

      {/* En-tête */}
      {data && (
        <div className="mt-2 mb-10">
          <div className="flex items-baseline gap-4 flex-wrap">
            <span
              className="display heading-tight"
              style={{ fontSize: "clamp(48px, 7vw, 80px)", color: "var(--border-strong)", lineHeight: 1 }}
            >
              {String(data.cluster_id).padStart(2, "0")}
            </span>
            <h1
              className="display heading-tight"
              style={{ fontSize: "clamp(24px, 3.5vw, 40px)", lineHeight: 1.1 }}
            >
              {data.cluster_label}
            </h1>
          </div>

          <div className="flex gap-8 mt-4">
            <div>
              <p className="label-caps" style={{ color: "var(--text-faint)" }}>Articles</p>
              <p className="tabnum mono" style={{ fontSize: 20 }}>
                {data.products.length.toLocaleString("fr-FR")}
              </p>
            </div>
            {data.products.length > 0 && (
              <div>
                <p className="label-caps" style={{ color: "var(--text-faint)" }}>Prix moyen</p>
                <p className="tabnum mono" style={{ fontSize: 20, color: "var(--accent)" }}>
                  {fmt(
                    data.products.reduce((s, p) => s + p.retail_price, 0) /
                      data.products.length
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {error ? (
        <p className="mono" style={{ fontSize: 12, color: "var(--red)" }}>{error}</p>
      ) : data && (
        <table className="w-full table-fixed mb-16">
          <Cols />
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-strong)" }}>
              <th className="label-caps text-left pb-3" style={{ color: "var(--text-faint)", fontWeight: 400 }}>#</th>
              <th className="label-caps text-left pb-3" style={{ color: "var(--text-faint)", fontWeight: 400 }}>Marque</th>
              <th className="label-caps text-left pb-3" style={{ color: "var(--text-faint)", fontWeight: 400 }}>Article</th>
              <th className="label-caps text-right pb-3" style={{ color: "var(--text-faint)", fontWeight: 400 }}>Prix</th>
            </tr>
          </thead>
          <tbody>
            {data.products.map((p, i) => (
              <ProductRow key={p.product_id} product={p} index={i} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
