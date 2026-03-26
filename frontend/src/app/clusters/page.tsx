"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { getClusters, type Cluster } from "@/lib/api";

const PAGE_SIZE = 30;

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
        animationDelay: `${index * 20}ms`,
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

export default function ClustersPage() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getClusters()
      .then((data) => {
        setClusters(data.sort((a, b) => b.product_count - a.product_count));
      })
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = search.trim()
    ? clusters.filter((c) =>
        c.cluster_label.toLowerCase().includes(search.toLowerCase())
      )
    : clusters;

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // Reset page when search changes
  const handleSearch = (v: string) => {
    setSearch(v);
    setPage(0);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="mb-8">
        <p className="label-caps" style={{ color: "var(--text-muted)" }}>/ clusters</p>
        <h1 className="display heading-tight mt-1" style={{ fontSize: "clamp(28px, 4vw, 44px)" }}>
          Product Clusters
        </h1>
        {clusters.length > 0 && (
          <p className="mono mt-1" style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {clusters.length} semantic groups · HDBSCAN
          </p>
        )}
      </div>

      {/* Search filter */}
      {clusters.length > 0 && (
        <div className="mb-6 max-w-sm">
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Filter clusters…"
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              borderBottom: "1px solid var(--border-strong)",
              outline: "none",
              fontSize: 14,
              color: "var(--text)",
              paddingBottom: 6,
            }}
          />
        </div>
      )}

      {error ? (
        <p className="mono" style={{ fontSize: 12, color: "var(--red)" }}>{error}</p>
      ) : loading ? (
        <div className="py-20 flex items-center justify-center">
          <p className="mono" style={{ fontSize: 12, color: "var(--text-faint)" }}>Loading clusters…</p>
        </div>
      ) : filtered.length === 0 ? (
        <p className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
          {search ? `No clusters matching "${search}"` : "No clusters yet — run the pipeline first."}
        </p>
      ) : (
        <>
          {/* Header row */}
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

          <div>
            {paged.map((c, i) => (
              <ClusterRow key={c.cluster_id} cluster={c} index={i} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 mb-16 flex items-center justify-between">
              <p className="mono" style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { setPage((p) => Math.max(0, p - 1)); window.scrollTo(0, 0); }}
                  disabled={page === 0}
                  className="label-caps"
                  style={{
                    padding: "6px 14px",
                    background: "none",
                    border: "1px solid var(--border-strong)",
                    cursor: page === 0 ? "default" : "pointer",
                    color: page === 0 ? "var(--text-faint)" : "var(--text)",
                    fontSize: 11,
                    letterSpacing: "0.1em",
                  }}
                >
                  ← Prev
                </button>

                {/* Page numbers (show max 5 around current) */}
                {Array.from({ length: totalPages }, (_, i) => i)
                  .filter((i) => Math.abs(i - page) <= 2)
                  .map((i) => (
                    <button
                      key={i}
                      onClick={() => { setPage(i); window.scrollTo(0, 0); }}
                      className="mono tabnum"
                      style={{
                        width: 32,
                        height: 32,
                        border: i === page ? "1px solid var(--text)" : "1px solid var(--border)",
                        background: i === page ? "var(--text)" : "none",
                        color: i === page ? "var(--bg-surface)" : "var(--text-muted)",
                        cursor: "pointer",
                        fontSize: 12,
                      }}
                    >
                      {i + 1}
                    </button>
                  ))}

                <button
                  onClick={() => { setPage((p) => Math.min(totalPages - 1, p + 1)); window.scrollTo(0, 0); }}
                  disabled={page === totalPages - 1}
                  className="label-caps"
                  style={{
                    padding: "6px 14px",
                    background: "none",
                    border: "1px solid var(--border-strong)",
                    cursor: page === totalPages - 1 ? "default" : "pointer",
                    color: page === totalPages - 1 ? "var(--text-faint)" : "var(--text)",
                    fontSize: 11,
                    letterSpacing: "0.1em",
                  }}
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
