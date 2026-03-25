import Link from "next/link";
import { getClusters, type Cluster } from "@/lib/api";

export const dynamic = "force-dynamic";

function fmt(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function ClusterRow({ cluster, index }: { cluster: Cluster; index: number }) {
  return (
    <Link
      href={`/clusters/${cluster.cluster_id}`}
      className="block row-enter cluster-row"
      style={{
        animationDelay: `${index * 25}ms`,
        borderTop: "1px solid var(--border)",
        textDecoration: "none",
      }}
    >
      <div
        className="py-4 grid items-center gap-4"
        style={{ gridTemplateColumns: "32px 1fr 90px 70px" }}
      >
        <span className="mono tabnum" style={{ fontSize: 11, color: "var(--text-faint)" }}>
          {String(cluster.cluster_id).padStart(2, "0")}
        </span>

        <p style={{ fontSize: 14, color: "var(--text)" }}>
          {cluster.cluster_label}
        </p>

        <p className="tabnum mono text-right" style={{ fontSize: 13, color: "var(--accent)" }}>
          {fmt(cluster.avg_price)}
        </p>

        <p className="tabnum text-right label-caps" style={{ color: "var(--text-muted)" }}>
          {cluster.product_count.toLocaleString()}
        </p>
      </div>
    </Link>
  );
}

export default async function ClustersPage() {
  let clusters: Cluster[] = [];
  let error: string | null = null;

  try {
    clusters = await getClusters();
  } catch (e) {
    error = (e as Error).message;
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="mb-10">
        <p className="label-caps" style={{ color: "var(--text-muted)" }}>/ clusters</p>
        <h1 className="display heading-tight mt-1" style={{ fontSize: "clamp(28px, 4vw, 44px)" }}>
          Product Clusters
        </h1>
        {clusters.length > 0 && (
          <p className="mono mt-1" style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {clusters.length} semantic groups
          </p>
        )}
      </div>

      {error ? (
        <p className="mono" style={{ fontSize: 12, color: "var(--red)" }}>{error}</p>
      ) : clusters.length === 0 ? (
        <p className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
          No clusters yet — run the pipeline first.
        </p>
      ) : (
        <>
          <div
            className="grid gap-4 pb-2"
            style={{
              gridTemplateColumns: "32px 1fr 90px 70px",
              borderBottom: "1px solid var(--border-strong)",
            }}
          >
            <span className="label-caps" style={{ color: "var(--text-faint)" }}>#</span>
            <span className="label-caps" style={{ color: "var(--text-faint)" }}>Cluster</span>
            <span className="label-caps text-right" style={{ color: "var(--text-faint)" }}>Avg price</span>
            <span className="label-caps text-right" style={{ color: "var(--text-faint)" }}>Items</span>
          </div>

          <div className="mb-16">
            {clusters
              .slice()
              .sort((a, b) => b.product_count - a.product_count)
              .map((c, i) => (
                <ClusterRow key={c.cluster_id} cluster={c} index={i} />
              ))}
          </div>
        </>
      )}
    </div>
  );
}
