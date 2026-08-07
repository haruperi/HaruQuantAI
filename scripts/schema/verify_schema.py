"""Editorial and syntactic verification of the authoritative schema model.

Run from anywhere: ``python scripts/schema/verify_schema.py``.
Exits non-zero on any failed check.
"""

import collections
import pathlib
import re
import sqlite3
import sys

DOCS = pathlib.Path(__file__).resolve().parents[2]
SPEC_FILES = [
    "app/utils/README.md",
    "app/services/brokers/README.md",
    "app/services/data/README.md",
    "app/services/strategy/README.md",
    "app/services/risk/README.md",
    "app/services/trading/README.md",
    "app/services/simulator/README.md",
    "app/services/optimization/README.md",
    "app/services/research/README.md",
    "app/services/portfolio/README.md",
    "app/agentic/README.md",
    "app/services/api/README.md",
]
PERF_FILE = "docs/ARCHITECTURE.md"

# created_at deliberately omitted. Both are code-authoritative tables transcribed
# verbatim from live migrations and stamp epoch nanoseconds instead. Documented in
# 00_domain_relationship_map.md section 8.
# Shipped tables that carry no `created_at`. All are applied and therefore immutable
# without a baseline reset, and each already records time in a domain-specific way.
# They are recorded here rather than "corrected" in the model, because the model must
# describe what these tables are, not what a convention would have preferred.
NO_CREATED_AT_ALLOWED = {
    "data_migration_ledger",  # applied_at_ns
    "data_write_locks",  # acquired_at_ns / expires_at_ns
    "data_source_state",  # updated_at_ns
    "data_source_attempts",  # timestamp_ns
    "data_audit_events",  # timestamp
    "data_economic_events",  # scheduled_at / updated_at
    "data_economic_calendar_coverage",  # synchronized_at
    "api_auth_failures",  # window_started_at
    "strategy_mutations",  # command-scoped; no time column by design
}

# Append-only tables whose `state` column records an observed state rather than a
# mutable lifecycle. A row is written once, so `updated_at` would be meaningless
# and its presence would wrongly imply the row can be revised.
APPEND_ONLY = {
    "agentic_workflow_checkpoints",
    "agentic_lifecycle_transitions",
}

# Shipped, applied tables with a mutable `state` but no `updated_at`. They track
# progress through purpose-specific columns instead and cannot be altered without a
# baseline reset.
NO_UPDATED_AT_ALLOWED = {
    "data_update_jobs",  # next_run_at / last_run_status / lease_expires_at
}


def statements(fname: str) -> list[tuple[str, str]]:
    """Extract executable SQL statements from one schema document.

    Args:
        fname: Repository-relative path to an owning specification.

    Returns:
        Pairs containing the source path and one extracted SQL statement.
    """
    text = (DOCS / fname).read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"```sql\n(.*?)```", text, re.DOTALL):
        lines = []
        for source_line in m.group(1).splitlines():
            # strip inline -- comments (may legitimately contain ';')
            cleaned_line = source_line.split("--", 1)[0]
            lines.append(cleaned_line)
        for raw in "\n".join(lines).split(";"):
            s = raw.strip()
            if s:
                out.append((fname, s))
    return out


def verdict(failures: object) -> str:
    """Format one validation outcome.

    Args:
        failures: Empty or populated failure evidence.

    Returns:
        A compact pass or failure label.
    """
    return "PASS" if not failures else f"FAIL {failures}"


stmts = [s for f in SPEC_FILES for s in statements(f)]
perf_stmts = statements(PERF_FILE)

creates = [(f, s) for f, s in stmts if re.match(r"CREATE TABLE", s, re.IGNORECASE)]
indexes = [
    (f, s) for f, s in stmts if re.match(r"CREATE (UNIQUE )?INDEX", s, re.IGNORECASE)
]
perf_idx = [
    (f, s)
    for f, s in perf_stmts
    if re.match(r"CREATE (UNIQUE )?INDEX", s, re.IGNORECASE)
]

print(f"sandbox sqlite_version = {sqlite3.sqlite_version}")
print(
    f"CREATE TABLE: {len(creates)} | CREATE INDEX (specs): {len(indexes)} | "
    f"(perf doc): {len(perf_idx)}"
)

con = sqlite3.connect(":memory:")
con.execute("PRAGMA foreign_keys=OFF")
errors, made_t, made_i, dup_i = [], [], [], []


def name_of(s: str, kind: str) -> str:
    """Return a table or index identifier from one DDL statement."""
    # `IF NOT EXISTS` must be consumed explicitly. Without it the first \w+ after
    # the keyword is "IF", so every guarded index reports its name as "IF".
    m = re.search(rf"{kind}\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", s, re.IGNORECASE)
    return m.group(1) if m else "?"


for f, s in creates:
    try:
        con.execute(s)
        made_t.append(name_of(s, "CREATE TABLE"))
    except sqlite3.Error as e:
        errors.append((f, name_of(s, "CREATE TABLE"), str(e)))
for f, s in indexes:
    try:
        con.execute(s)
        made_i.append(name_of(s, "INDEX"))
    except sqlite3.Error as e:
        errors.append((f, name_of(s, "INDEX"), str(e)))
# perf doc repeats some spec indexes as illustrations; duplicates are expected
for f, s in perf_idx:
    try:
        con.execute(s)
        made_i.append(name_of(s, "INDEX"))
    except sqlite3.Error as error:
        if "already exists" in str(error):
            dup_i.append(name_of(s, "INDEX"))
        else:
            errors.append((f, name_of(s, "INDEX"), str(error)))

print("\n=== 1: DDL executes ===")
print(
    f"tables {len(made_t)} | indexes {len(made_i)} | "
    f"illustrative repeats in performance docs: {len(dup_i)}"
)
if errors:
    print(f"FAILURES {len(errors)}:")
    for failure in errors:
        print("   ", failure)
else:
    print("PASS")

tset = set(made_t)
fk_bad = [
    (name_of(s, "CREATE TABLE"), r.group(1))
    for f, s in creates
    for r in re.finditer(r"REFERENCES\s+(\w+)\s*\(", s, re.IGNORECASE)
    if r.group(1) not in tset
]
print(f"\n=== 2: FK targets resolve ===\n{verdict(fk_bad)}")

idx_bad = [
    (name_of(s, "INDEX"), m.group(1))
    for f, s in indexes + perf_idx
    if (m := re.search(r"ON\s+(\w+)\s*\(", s, re.IGNORECASE)) and m.group(1) not in tset
]
print(f"\n=== 3: index targets resolve ===\n{verdict(idx_bad)}")

miss_c = [
    t
    for t in made_t
    if t not in NO_CREATED_AT_ALLOWED
    and "created_at" not in [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
]
print(
    "\n=== 4: created_at "
    f"(allowlist of {len(NO_CREATED_AT_ALLOWED)} documented exceptions) ==="
)
print("PASS" if not miss_c else f"FAIL {miss_c}")

real = [
    (t, r[1], r[2])
    for t in made_t
    for r in con.execute(f"PRAGMA table_info({t})")
    if r[2].upper() in ("REAL", "FLOAT", "DOUBLE")
]
print("\n=== 5: no REAL/FLOAT (money must be TEXT Decimal) ===")
print(verdict(real))

PREFIXES = [
    "util_",
    "broker_",
    "data_",
    "indicator_",
    "strategy_",
    "risk_",
    "trading_",
    "sim_",
    "analytics_",
    "optimization_",
    "research_",
    "portfolio_",
    "agentic_",
    "api_",
]
counts: collections.Counter[str] = collections.Counter()
unpre: list[str] = []
for t in made_t:
    matching_prefixes = [p for p in PREFIXES if t.startswith(p)]
    if matching_prefixes:
        counts[max(matching_prefixes, key=len)] += 1
    else:
        unpre.append(t)
print("\n=== 6: prefix ownership ===")
print("  " + " | ".join(f"{p.rstrip('_')}={counts[p]}" for p in PREFIXES))
print(f"  TOTAL {sum(counts.values())}")
# Utils owns no tables, Indicators is persistence-free, and Analytics retired its
# derived store. Their reserved prefixes are therefore valid while empty.
_reserved_empty = {"util_", "indicator_", "analytics_"}
_expected_in_use = {p for p in PREFIXES if p not in _reserved_empty}
_in_use = {p for p in PREFIXES if counts[p]}
print(
    "PASS"
    if not unpre and _in_use == _expected_in_use
    else f"FAIL unprefixed={unpre} missing={sorted(_expected_in_use - _in_use)}"
)

non_strict = [
    name_of(s, "CREATE TABLE") for f, s in creates if "STRICT" not in s.upper()
]
print(f"\n=== 7: STRICT mode ===\n{verdict(non_strict)}")

bad_upd = [
    t
    for t in made_t
    if t not in APPEND_ONLY
    and t not in NO_UPDATED_AT_ALLOWED
    and "state" in (c := [r[1] for r in con.execute(f"PRAGMA table_info({t})")])
    and "updated_at" not in c
]
print("\n=== 8: updated_at where mutable state exists ===")
print(verdict(bad_upd))

uniq_partial = [
    name_of(s, "INDEX")
    for f, s in indexes
    if re.match(r"CREATE UNIQUE INDEX", s, re.IGNORECASE) and "WHERE" in s.upper()
]
print("\n=== 9: unique partial indexes enforcing invariants ===")
print(f"  {len(uniq_partial)}: {', '.join(uniq_partial)}")


ok = not (
    errors or fk_bad or idx_bad or miss_c or real or unpre or non_strict or bad_upd
)

# ---- 10: every table declares a PRIMARY KEY ----
# SQLite happily accepts a PK-less table, so a dropped primary key is otherwise silent.
no_pk = [
    t_
    for t_ in made_t
    if not any(r[5] for r in con.execute(f"PRAGMA table_info({t_})"))
]
print(f"\n=== 10: PRIMARY KEY declared ===\n{verdict(no_pk)}")

# ---- 11: no synonym pairs coexisting in one table ----
SYNONYMS = [
    ("user_id", "account_id"),
    ("session_digest", "session_token_hash"),
    ("search_id", "job_id"),
    ("record_id", "memory_id"),
    ("allocation_id", "allocation_version_id"),
    ("sha256", "content_hash"),
    ("checksum", "snapshot_hash"),
    ("lifecycle_status", "state"),
]
clash = []
for t_ in made_t:
    cols = {r[1] for r in con.execute(f"PRAGMA table_info({t_})")}
    for a, b in SYNONYMS:
        if a in cols and b in cols:
            clash.append((t_, a, b))
print(f"\n=== 11: no rename collisions ===\n{verdict(clash)}")

# ---- 12: ratified table count matches parsed domain README model ----
stated = [("domain README executable target model", 94)]
drift = [(name, count) for name, count in stated if count != len(made_t)]
print(f"\n=== 12: doc counts match parsed ({len(made_t)}) ===")
print("PASS" if not drift and stated else f"FAIL stated={stated} parsed={len(made_t)}")

ok = ok and not no_pk and not clash and not drift

print("\n" + "=" * 52)
print("ALL CHECKS PASSED" if ok else "FAIL")

con.close()
sys.exit(0 if ok else 1)
