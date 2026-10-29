"""
09_run_pipeline.py
==================
Weekly automation pipeline for new customer files.

For every file in data/raw/weekly_drops/ that hasn't been processed yet:
    validate -> clean -> upsert into MySQL -> record it as processed
Then, if anything changed, rescore all customers (07_score_customers.py).

Run from the project root:
    python src/09_run_pipeline.py --test    # safe dry run into a TEST table, then checks the result
    python src/09_run_pipeline.py           # real run into the customers table

Key ideas:
  - Same rules every week: cleaning lives in cleaning.py, and missing values
    are filled with fixed medians from config/reference_values.json.
  - Idempotent: processed files are recorded in the pipeline_runs table and
    skipped next time. Loading uses an upsert, so even a re-run can't
    create duplicate customers.
  - Cross-week duplicates: if a customer already in the database shows up
    again, the incoming record only replaces it if it has no more missing
    values than the stored one (the same "keep the cleanest row" rule as
    02_clean.py).
  - Bad rows are not loaded. They are saved to logs/rejected/ with a reason.
"""

import argparse
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from config.db_config import LOG_DIR, PROCESSED_DIR, PROJECT_ROOT, RAW_DIR, get_engine
from cleaning import CUSTOMER_COLUMNS, clean_customers, load_reference_values

WEEKLY_DIR = RAW_DIR / "weekly_drops"
REJECT_DIR = LOG_DIR / "rejected"
STAGING_TABLE = "customers_staging"
TEST_TABLE = "customers_pipeline_test"

RAW_COLUMNS = [c for c in CUSTOMER_COLUMNS if not c.endswith("_was_missing")]
FLAGS = ["age_was_missing", "credit_score_was_missing", "estimated_salary_was_missing"]


# ============================================================
# LOGGING: everything goes to the screen AND logs/pipeline.log
# ============================================================
LOG_DIR.mkdir(exist_ok=True)
REJECT_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
              logging.StreamHandler()],
)
log = logging.getLogger("pipeline")


# ============================================================
# 1. SETUP
# ============================================================
def setup_tables(engine, target, test_mode):
    with engine.begin() as conn:
        # Remembers which files have been loaded into which table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                file_name     VARCHAR(100),
                target_table  VARCHAR(64),
                processed_at  DATETIME,
                rows_in       INT,
                rows_rejected INT,
                rows_loaded   INT,
                PRIMARY KEY (file_name, target_table)
            )"""))

        if test_mode:
            # Fresh, empty copy of the customers table for every test run
            conn.execute(text(f"DROP TABLE IF EXISTS {TEST_TABLE}"))
            conn.execute(text(f"CREATE TABLE {TEST_TABLE} LIKE customers"))
            conn.execute(text("DELETE FROM pipeline_runs WHERE target_table = :t"),
                         {"t": TEST_TABLE})
            log.info("Test mode: created empty table %s", TEST_TABLE)


def already_processed(engine, target):
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT file_name FROM pipeline_runs WHERE target_table = :t"), {"t": target})
        return {r[0] for r in rows}


# ============================================================
# 2. VALIDATE
# ============================================================
def validate(df, file_name, valid_branches):
    """Return (good_rows, number_rejected). Raises if the file itself is broken."""
    missing_cols = set(RAW_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"missing columns {sorted(missing_cols)}")
    if df.empty:
        raise ValueError("file has no rows")

    reasons = pd.Series("", index=df.index)
    reasons[df["customer_id"].isna()] += "missing customer_id; "
    reasons[~df["branch_id"].isin(valid_branches)] += "unknown branch_id; "
    reasons[pd.to_datetime(df["join_date"], errors="coerce").isna()] += "bad join_date; "
    reasons[~df["exited"].isin([0, 1])] += "exited not 0/1; "

    bad = reasons != ""
    if bad.any():
        rejected = df[bad].assign(reject_reason=reasons[bad])
        out = REJECT_DIR / f"{Path(file_name).stem}_rejected.csv"
        rejected.to_csv(out, index=False)
        log.warning("  %s rows rejected -> %s", bad.sum(), out.relative_to(PROJECT_ROOT))

    return df[~bad], int(bad.sum())


# ============================================================
# 3. LOAD (upsert)
# ============================================================
def upsert(engine, clean, target, file_name, rows_in, rows_rejected):
    """Load one cleaned file. All-or-nothing: the data AND the pipeline_runs
    record are written in one transaction, so a crash can't leave a file
    half-loaded or loaded-but-not-recorded."""
    cols = ", ".join(CUSTOMER_COLUMNS)
    updates = ", ".join(f"{c} = s.{c}" for c in CUSTOMER_COLUMNS if c != "customer_id")
    s_missing = " + ".join(f"s.{f}" for f in FLAGS)
    t_missing = " + ".join(f"t.{f}" for f in FLAGS)

    # Staging table is created OUTSIDE the transaction: in MySQL, CREATE/DROP
    # TABLE auto-commits, which would break the all-or-nothing guarantee.
    clean.to_sql(STAGING_TABLE, engine, if_exists="replace", index=False)

    with engine.begin() as conn:
        # Cross-week duplicates: drop incoming rows that are LESS clean
        # than the record already stored for that customer
        skipped = conn.execute(text(f"""
            DELETE s FROM {STAGING_TABLE} s
            JOIN {target} t ON t.customer_id = s.customer_id
            WHERE ({s_missing}) > ({t_missing})""")).rowcount
        if skipped:
            log.info("  %s rows kept the existing, cleaner record", skipped)

        # Upsert: insert new customers, update existing ones
        conn.execute(text(f"""
            INSERT INTO {target} ({cols})
            SELECT {cols} FROM {STAGING_TABLE} s
            ON DUPLICATE KEY UPDATE {updates}"""))

        loaded = len(clean) - skipped
        conn.execute(text("""
            INSERT INTO pipeline_runs VALUES (:f, :t, :at, :rin, :rrej, :rload)"""),
            {"f": file_name, "t": target, "at": datetime.now(),
             "rin": rows_in, "rrej": rows_rejected, "rload": loaded})

    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {STAGING_TABLE}"))
    return loaded


# ============================================================
# 4. CHECKS AND RESCORING
# ============================================================
def summary(engine, target):
    with engine.connect() as conn:
        n, rate = conn.execute(text(
            f"SELECT COUNT(*), AVG(exited) FROM {target}")).one()
    log.info("%s now has %s customers, churn rate %.4f", target, f"{n:,}", float(rate or 0))
    return n, float(rate or 0)


def compare_with_clean_csv(engine):
    """Test mode only: the 8 weekly files together are the same customers as
    customers_raw.csv, so the result must equal 02_clean.py's output."""
    db = pd.read_sql(f"SELECT * FROM {TEST_TABLE}", engine)
    csv = pd.read_csv(PROCESSED_DIR / "customers_clean.csv")
    db, csv = (d[CUSTOMER_COLUMNS].sort_values("customer_id").reset_index(drop=True)
               for d in (db, csv))
    # Compare dates as text (YYYY-MM-DD): MySQL and CSV store them differently
    for d in (db, csv):
        for col in ["join_date", "churn_date"]:
            d[col] = pd.to_datetime(d[col]).dt.strftime("%Y-%m-%d")
    try:
        pd.testing.assert_frame_equal(db, csv, check_dtype=False, atol=0.01)
        log.info("TEST PASSED: pipeline result matches customers_clean.csv row for row")
        return True
    except AssertionError as e:
        log.error("TEST FAILED: %s", str(e).splitlines()[0:6])
        return False


def rescore(engine):
    """07_score_customers.py reads customers_clean.csv, so refresh that file
    from the database first, then rerun scoring."""
    current = pd.read_sql("SELECT * FROM customers ORDER BY customer_id", engine)
    current.to_csv(PROCESSED_DIR / "customers_clean.csv", index=False)
    log.info("Refreshed customers_clean.csv from MySQL (%s rows)", f"{len(current):,}")

    log.info("Rescoring customers (07_score_customers.py)... takes a few minutes")
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "src" / "07_score_customers.py")],
                            cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("Rescoring failed:\n%s", result.stderr[-2000:])
    else:
        log.info("Rescoring done. Refresh Power BI to see the new scores.")


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true",
                        help="load into an empty test table instead of customers")
    args = parser.parse_args()
    target = TEST_TABLE if args.test else "customers"

    log.info("=" * 60)
    log.info("Pipeline started (target table: %s)", target)

    engine = get_engine()
    ref = load_reference_values()
    setup_tables(engine, target, args.test)

    valid_branches = set(pd.read_sql("SELECT branch_id FROM branches", engine)["branch_id"])
    done = already_processed(engine, target)
    files = sorted(WEEKLY_DIR.glob("customers_week_*.csv"))
    todo = [f for f in files if f.name not in done]
    log.info("%s weekly files found, %s already processed, %s to do",
             len(files), len(files) - len(todo), len(todo))

    total_loaded = 0
    for f in todo:
        log.info("Processing %s", f.name)
        try:
            raw = pd.read_csv(f)
            good, n_rejected = validate(raw, f.name, valid_branches)
            clean = clean_customers(good, ref)
            loaded = upsert(engine, clean, target, f.name, len(raw), n_rejected)
            total_loaded += loaded
            log.info("  rows in: %s | rejected: %s | after in-file dedup: %s | loaded: %s",
                     len(raw), n_rejected, len(clean), loaded)
        except Exception as e:
            # One bad file must not stop the others. It is NOT recorded as
            # processed, so it will be retried on the next run.
            log.error("  FAILED, file skipped and will be retried next run: %s", e)

    if not todo:
        log.info("Nothing new to process.")

    summary(engine, target)

    if args.test:
        compare_with_clean_csv(engine)
    elif total_loaded > 0:
        rescore(engine)

    log.info("Pipeline finished")


if __name__ == "__main__":
    main()