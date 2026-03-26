"use client";

import { useState, useRef, useTransition, useCallback } from "react";
import { search, parsePriceConstraints, type SearchResult } from "@/lib/api";

const EXAMPLES = [
  "jean slim moins de 80$",
  "robe d'été",
  "chaussures de running",
  "sac en cuir",
];

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
          (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-subtle)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLTableRowElement).style.background = "";
        }}
      >
        <td className="mono tabnum py-3 pr-4" style={{ fontSize: 11, color: "var(--text-faint)" }}>
          {String(index + 1).padStart(2, "0")}
        </td>
        <td className="py-3 pr-6 hidden sm:table-cell" style={{ fontSize: 13, color: "var(--text-muted)", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {tc(item.brand)}
        </td>
        <td className="py-3 pr-6" style={{ fontSize: 13 }}>
          {tc(item.name)}
          <span className="sm:hidden" style={{ display: "block", fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
            {tc(item.brand)}
          </span>
        </td>
        <td className="py-3 pr-6 label-caps hidden md:table-cell" style={{ color: "var(--text-faint)", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {item.category}
        </td>
        <td className="py-3 tabnum text-right mono" style={{ color: "var(--accent)", fontSize: 13, whiteSpace: "nowrap" }}>
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
      <col style={{ width: 130 }} className="hidden sm:table-column" />
      <col />
      <col style={{ width: 120 }} className="hidden md:table-column" />
      <col style={{ width: 80 }} />
      <col style={{ width: 20 }} className="hidden sm:table-column" />
    </colgroup>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(20);
  const [isPending, startTransition] = useTransition();
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastQuery = useRef("");

  const run = useCallback((q: string, k = 20) => {
    if (!q.trim()) return;
    setError(null);
    lastQuery.current = q.trim();
    startTransition(async () => {
      try {
        const data = await search(q.trim(), k);
        setResults(data);
        setTopK(k);
      } catch (e) {
        setError((e as Error).message);
        setResults(null);
      }
    });
  }, []);

  const loadMore = useCallback(async () => {
    if (!lastQuery.current) return;
    setIsLoadingMore(true);
    try {
      const newK = topK + 20;
      const data = await search(lastQuery.current, newK);
      setResults(data);
      setTopK(newK);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setIsLoadingMore(false);
    }
  }, [topK]);

  return (
    <div className="max-w-7xl mx-auto px-6">
      {/* ── Hero ──────────────────────────────────────────────────── */}
      <div className="py-16 md:py-20">
        <h1
          className="display heading-tight"
          style={{ fontSize: "clamp(36px, 5vw, 56px)", lineHeight: 1.1 }}
        >
          Catalogue Intelligent
        </h1>
        <p className="mono mt-2" style={{ fontSize: 12, color: "var(--text-muted)" }}>
          29 118 articles · recherche par description · 603 familles de produits
        </p>

        <div className="search-wrap mt-8 max-w-xl">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run(query)}
            placeholder="Décrivez ce que vous cherchez…"
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

        <div className="mt-3 flex items-center gap-3 flex-wrap">
          <p className="label-caps" style={{ color: "var(--text-faint)" }}>
            {isPending ? "Recherche en cours…" : "Exemples :"}
          </p>
          {!isPending && EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => { setQuery(ex); run(ex); }}
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                background: "none",
                border: "1px solid var(--border)",
                borderRadius: 4,
                padding: "3px 10px",
                cursor: "pointer",
                transition: "border-color 120ms",
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-strong)")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)")}
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="mb-6 mono" style={{ fontSize: 12, color: "var(--red)" }}>{error}</p>
      )}

      {results !== null && (
        <section className="mb-16">
          {results.length === 0 ? (
            <p className="py-12 mono text-center" style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Aucun résultat pour &ldquo;{query}&rdquo;
            </p>
          ) : (
            <>
              <div className="flex items-center gap-4 mb-3 flex-wrap">
                <p className="label-caps" style={{ color: "var(--text-faint)" }}>
                  {results.length} résultat{results.length > 1 ? "s" : ""}
                </p>
                {(() => {
                  const { max_price, min_price } = parsePriceConstraints(lastQuery.current);
                  if (max_price === undefined && min_price === undefined) return null;
                  const label = max_price !== undefined && min_price !== undefined
                    ? `${min_price}$ – ${max_price}$`
                    : max_price !== undefined
                    ? `max ${max_price}$`
                    : `min ${min_price}$`;
                  return (
                    <span className="label-caps" style={{ color: "var(--accent)", border: "1px solid var(--accent)", borderRadius: 4, padding: "2px 8px" }}>
                      filtre prix : {label}
                    </span>
                  );
                })()}
              </div>
              <div className="table-scroll">
                <table className="w-full table-fixed" style={{ minWidth: 400 }}>
                  <Cols />
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-strong)" }}>
                      {(
                        [
                          ["#", ""],
                          ["Marque", "hidden sm:table-cell"],
                          ["Article", ""],
                          ["Catégorie", "hidden md:table-cell"],
                          ["Prix", "text-right"],
                          ["", "hidden sm:table-cell"],
                        ] as [string, string][]
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
              </div>

              {/* Voir plus */}
              {results.length === topK && topK < 60 && (
                <div className="mt-6 flex justify-center">
                  <button
                    onClick={loadMore}
                    disabled={isLoadingMore}
                    style={{
                      background: "none",
                      border: "1px solid var(--border-strong)",
                      color: isLoadingMore ? "var(--text-faint)" : "var(--text)",
                      cursor: isLoadingMore ? "default" : "pointer",
                      padding: "10px 24px",
                      fontSize: 12,
                      letterSpacing: "0.08em",
                      fontFamily: "var(--font-ui)",
                      transition: "border-color 120ms",
                    }}
                  >
                    {isLoadingMore ? "Chargement…" : "Voir plus de résultats"}
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      )}

      {results === null && !isPending && (
        <div className="py-20" style={{ borderTop: "1px solid var(--border)" }} />
      )}
    </div>
  );
}
