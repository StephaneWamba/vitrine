"use client";

import { useState, useRef, useTransition, useCallback } from "react";
import { search, type SearchResult } from "@/lib/api";

function tc(s: string) {
  return s.toLowerCase().replace(/(?:^|\s)\S/g, (c) => c.toUpperCase());
}

function fmt(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function ResultRow({ item, index }: { item: SearchResult; index: number }) {
  const [open, setOpen] = useState(false);
  const hasDesc = Boolean(item.description_enriched);

  return (
    <>
      <tr
        className="row-enter"
        style={{
          animationDelay: `${index * 30}ms`,
          borderTop: "1px solid var(--border)",
          cursor: hasDesc ? "pointer" : "default",
          transition: "background 120ms",
        }}
        onClick={() => hasDesc && setOpen((v) => !v)}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLTableRowElement).style.background =
            "var(--bg-subtle)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLTableRowElement).style.background = "";
        }}
      >
        <td className="mono tabnum py-3 pr-4" style={{ fontSize: 11, color: "var(--text-faint)" }}>
          {String(index + 1).padStart(2, "0")}
        </td>
        <td className="py-3 pr-6" style={{ fontSize: 13, color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {tc(item.brand)}
        </td>
        <td className="py-3 pr-6" style={{ fontSize: 13 }}>
          {tc(item.name)}
        </td>
        <td className="py-3 pr-6 label-caps hidden md:table-cell" style={{ color: "var(--text-faint)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {item.category}
        </td>
        <td className="py-3 tabnum text-right mono" style={{ color: "var(--accent)", fontSize: 13 }}>
          {fmt(item.retail_price)}
        </td>
        <td className="py-3 pl-3 text-right hidden sm:table-cell" style={{ color: "var(--text-faint)", fontSize: 11 }}>
          {hasDesc ? (open ? "−" : "+") : ""}
        </td>
      </tr>
      {open && item.description_enriched && (
        <tr>
          <td colSpan={6} className="pb-3 pt-0" style={{ background: "var(--bg-subtle)" }}>
            <p style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6, paddingLeft: 32, paddingRight: 80 }}>
              {item.description_enriched}
            </p>
          </td>
        </tr>
      )}
    </>
  );
}

function Cols() {
  return (
    <colgroup>
      <col style={{ width: 32 }} />
      <col style={{ width: 130 }} />
      <col />
      <col style={{ width: 120 }} className="hidden md:table-column" />
      <col style={{ width: 70 }} />
      <col style={{ width: 20 }} className="hidden sm:table-column" />
    </colgroup>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const inputRef = useRef<HTMLInputElement>(null);

  const run = useCallback((q: string) => {
    if (!q.trim()) return;
    setError(null);
    startTransition(async () => {
      try {
        const data = await search(q.trim());
        setResults(data);
      } catch (e) {
        setError((e as Error).message);
        setResults(null);
      }
    });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6">
      {/* ── Hero ──────────────────────────────────────────────────── */}
      <div className="py-16 md:py-20">
        <h1
          className="display heading-tight"
          style={{ fontSize: "clamp(36px, 5vw, 56px)", lineHeight: 1.1 }}
        >
          Product Intelligence
        </h1>
        <p className="mono mt-2" style={{ fontSize: 12, color: "var(--text-muted)" }}>
          29,118 products · semantic search · 603 semantic clusters
        </p>

        <div className="search-wrap mt-8 max-w-xl">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run(query)}
            placeholder="slim jeans under $80, summer dress, running shoes…"
            autoComplete="off"
            spellCheck={false}
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              outline: "none",
              fontSize: 15,
              color: "var(--text)",
              paddingBottom: 6,
            }}
          />
          <div className="search-line" />
        </div>

        <p className="mt-2 label-caps" style={{ color: "var(--text-faint)" }}>
          Press Enter to search
          {isPending && (
            <span style={{ marginLeft: 12, color: "var(--text-muted)" }}>Searching…</span>
          )}
        </p>
      </div>

      {error && (
        <p className="mb-6 mono" style={{ fontSize: 12, color: "var(--red)" }}>{error}</p>
      )}

      {results !== null && (
        <section className="mb-16">
          {results.length === 0 ? (
            <p className="py-12 mono text-center" style={{ fontSize: 12, color: "var(--text-muted)" }}>
              No results for &ldquo;{query}&rdquo;
            </p>
          ) : (
            <table className="w-full table-fixed">
              <Cols />
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-strong)" }}>
                  {(
                    [["#", ""], ["Brand", ""], ["Product", ""], ["Category", "hidden md:table-cell"], ["Price", "text-right"], ["", "hidden sm:table-cell"]] as [string, string][]
                  ).map(([label, cls]) => (
                    <th key={label} className={`label-caps text-left pb-3 ${cls}`} style={{ color: "var(--text-faint)", fontWeight: 400 }}>
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((item, i) => (
                  <ResultRow key={item.product_id} item={item} index={i} />
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {results === null && !isPending && (
        <div className="py-20" style={{ borderTop: "1px solid var(--border)" }} />
      )}
    </div>
  );
}
