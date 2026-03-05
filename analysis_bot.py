"""
Analyze lead data and generate cleaning/classification reports.
"""

import logging
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# -------------------------
# Logging configuration
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -------------------------
# Configuration
# -------------------------
INPUT_FILE = "leads.csv"
CLEAN_OUTPUT_FILE = "clean_leads.csv"
BEST_LEADS_FILE = "best_leads.csv"
CHART_FILE = "charts.png"
REPORT_FILE = "report.txt"

PHONE_PATTERN = r"^[6-9]\d{9}$"
EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

REQUIRED_COLUMNS = ["phone", "email", "lead_score", "call_attempt"]


# -------------------------
# Load data
# -------------------------
def load_data(filepath: str) -> pd.DataFrame:

    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(filepath)

    # Validate columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} records")
    return df


# -------------------------
# Clean data
# -------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    df_clean = df.copy()

    df_clean["phone"] = df_clean["phone"].astype(str).str.replace(r"\D", "", regex=True)

    before = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=["phone", "email"])
    removed = before - len(df_clean)

    logger.info(f"Removed {removed} duplicates")

    return df_clean


# -------------------------
# Validate phone & email
# -------------------------
def validate_data(df: pd.DataFrame) -> pd.DataFrame:

    df_valid = df.copy()

    df_valid["phone_valid"] = df_valid["phone"].str.match(PHONE_PATTERN)
    df_valid["email_valid"] = df_valid["email"].str.match(EMAIL_PATTERN)

    valid_count = (df_valid["phone_valid"] & df_valid["email_valid"]).sum()

    logger.info(f"Valid leads found: {valid_count}")

    return df_valid


# -------------------------
# Lead classification
# -------------------------
def classify_leads(df: pd.DataFrame) -> pd.DataFrame:

    df_classified = df.copy()

    conditions = [
        (df_classified["lead_score"] >= 80) & (df_classified["call_attempt"] <= 2),
        df_classified["lead_score"].between(50, 79),
        df_classified["lead_score"] < 50
    ]

    choices = ["HOT_LEAD", "WARM_LEAD", "COLD_LEAD"]

    df_classified["lead_category"] = np.select(conditions, choices, default="LOW")

    for c in choices:
        count = (df_classified["lead_category"] == c).sum()
        logger.info(f"{c}: {count}")

    return df_classified


# -------------------------
# Save outputs
# -------------------------
def save_outputs(valid_df: pd.DataFrame, best_df: pd.DataFrame):

    valid_df.to_csv(CLEAN_OUTPUT_FILE, index=False)
    best_df.to_csv(BEST_LEADS_FILE, index=False)

    logger.info(f"Saved clean leads -> {CLEAN_OUTPUT_FILE}")
    logger.info(f"Saved best leads -> {BEST_LEADS_FILE}")


# -------------------------
# Generate chart
# -------------------------
def generate_chart(valid_df: pd.DataFrame):

    labels = ["HOT", "WARM", "COLD"]

    values = [
        (valid_df["lead_category"] == "HOT_LEAD").sum(),
        (valid_df["lead_category"] == "WARM_LEAD").sum(),
        (valid_df["lead_category"] == "COLD_LEAD").sum()
    ]

    plt.figure(figsize=(8,6))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title("Lead Quality Distribution")
    plt.tight_layout()
    plt.savefig(CHART_FILE, dpi=300)
    plt.close()

    logger.info(f"Chart saved -> {CHART_FILE}")


# -------------------------
# Generate report
# -------------------------
def generate_report(df, valid_df, best_df, processing_time):

    total = len(df)
    valid = len(valid_df)
    best = len(best_df)
    removed = total - valid

    percent = (valid / total * 100) if total else 0
    speed = (total / processing_time) if processing_time else 0

    report = f"""
==================================================
AI LEAD ANALYSIS REPORT
==================================================

DATA SUMMARY
--------------------------------------------------
Total Leads Processed:     {total:,}
Valid Leads:               {valid:,} ({percent:.1f}%)
Invalid Leads Removed:     {removed:,}

LEAD CLASSIFICATION
--------------------------------------------------
HOT Leads (Best):          {best:,}
HOT Leads:                 {(valid_df['lead_category']=='HOT_LEAD').sum():,}
WARM Leads:                {(valid_df['lead_category']=='WARM_LEAD').sum():,}
COLD Leads:                {(valid_df['lead_category']=='COLD_LEAD').sum():,}

OUTPUT FILES
--------------------------------------------------
clean_leads.csv
best_leads.csv
charts.png

AI RECOMMENDATION
--------------------------------------------------
Focus telecalling on HOT leads first.
WARM leads should be nurtured through follow-ups.
COLD leads require additional engagement strategy.

PERFORMANCE
--------------------------------------------------
Processing Time:           {processing_time:.2f} sec
Records / Second:          {speed:.0f}

==================================================
"""

    return report


# -------------------------
# Main pipeline
# -------------------------
def main():

    start = time.time()

    try:

        logger.info("Starting lead analysis pipeline...")

        df = load_data(INPUT_FILE)

        df_clean = clean_data(df)

        df_validated = validate_data(df_clean)

        valid_df = df_validated[
            (df_validated["phone_valid"]) &
            (df_validated["email_valid"])
        ].copy()

        valid_df = classify_leads(valid_df)

        best_df = valid_df[valid_df["lead_category"] == "HOT_LEAD"]

        save_outputs(valid_df, best_df)

        generate_chart(valid_df)

        processing_time = time.time() - start

        report = generate_report(df, valid_df, best_df, processing_time)

        # IMPORTANT FIX → UTF-8 encoding
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Report saved -> {REPORT_FILE}")

        print("\n" + report)
        print("[SUCCESS] Lead analysis completed\n")

    except Exception as e:

        logger.error(f"Pipeline failed: {e}")
        print(f"\nERROR: {e}\n")
        raise


# -------------------------
# Entry point
# -------------------------
if __name__ == "__main__":
    main()
