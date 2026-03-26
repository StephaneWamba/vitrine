"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const LINKS = [
  { href: "/", label: "Search" },
  { href: "/clusters", label: "Clusters" },
  { href: "/intent", label: "Intent" },
  { href: "/analytics", label: "Analytics" },
  { href: "/quality", label: "Quality" },
];

const LOOKER_URL =
  "https://lookerstudio.google.com/reporting/1bc6db02-16eb-468b-a6df-57928fddcaba";

export default function Nav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <nav
      style={{ borderBottom: "1px solid var(--border)", background: "var(--bg)" }}
      className="sticky top-0 z-50"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-6 h-12 flex items-center justify-between">
        {/* Brand */}
        <Link
          href="/"
          className="label-caps"
          style={{ color: "var(--text)", letterSpacing: "0.2em" }}
          onClick={() => setOpen(false)}
        >
          Vitrine
        </Link>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-8 list-none">
          {LINKS.map(({ href, label }) => {
            const active = href === "/" ? path === "/" : path.startsWith(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className="label-caps transition-colors"
                  style={{ color: active ? "var(--text)" : "var(--text-muted)" }}
                >
                  {label}
                </Link>
              </li>
            );
          })}
          <li>
            <a
              href={LOOKER_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="label-caps transition-colors"
              style={{ color: "var(--text-muted)" }}
            >
              Looker ↗
            </a>
          </li>
        </ul>

        {/* Mobile hamburger */}
        <button
          className="md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 4,
            color: "var(--text)",
            display: "flex",
            flexDirection: "column",
            gap: 5,
          }}
        >
          <span
            style={{
              display: "block",
              width: 22,
              height: 1,
              background: "currentColor",
              transition: "transform 200ms, opacity 200ms",
              transformOrigin: "center",
              transform: open ? "translateY(6px) rotate(45deg)" : "none",
            }}
          />
          <span
            style={{
              display: "block",
              width: 22,
              height: 1,
              background: "currentColor",
              transition: "opacity 200ms",
              opacity: open ? 0 : 1,
            }}
          />
          <span
            style={{
              display: "block",
              width: 22,
              height: 1,
              background: "currentColor",
              transition: "transform 200ms, opacity 200ms",
              transformOrigin: "center",
              transform: open ? "translateY(-6px) rotate(-45deg)" : "none",
            }}
          />
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div
          style={{
            background: "var(--bg)",
            borderBottom: "1px solid var(--border)",
            padding: "16px 24px 20px",
          }}
          className="md:hidden"
        >
          <ul className="flex flex-col gap-5 list-none">
            {LINKS.map(({ href, label }) => {
              const active = href === "/" ? path === "/" : path.startsWith(href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    className="label-caps"
                    style={{
                      color: active ? "var(--text)" : "var(--text-muted)",
                      fontSize: 12,
                    }}
                    onClick={() => setOpen(false)}
                  >
                    {label}
                  </Link>
                </li>
              );
            })}
            <li>
              <a
                href={LOOKER_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="label-caps"
                style={{ color: "var(--text-muted)", fontSize: 12 }}
                onClick={() => setOpen(false)}
              >
                Looker ↗
              </a>
            </li>
          </ul>
        </div>
      )}
    </nav>
  );
}
