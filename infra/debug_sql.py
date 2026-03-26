"""Debug: print what's being extracted from 02_transform.sql."""
from pathlib import Path

path = Path("sql/02_transform.sql")
raw = path.read_text(encoding="utf-8")
statements = [s.strip() for s in raw.split(";") if s.strip()]
print(f"Number of statements: {len(statements)}")
first = statements[0]
lines = first.split("\n")
print(f"First statement lines: {len(lines)}")
print("--- Lines 48-56 of extracted statement ---")
for i, line in enumerate(lines[47:57], start=48):
    print(f"{i:3}: {line}")
