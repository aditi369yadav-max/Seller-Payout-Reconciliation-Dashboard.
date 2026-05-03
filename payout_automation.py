"""
============================================================
  Amazon Seller Services — FinOps Payout Reconciliation
  Automation Script v1.0
  Author: [Your Name] | Role: Process Associate L3
  Dataset: Q4 2024 | 10,500 transactions | 120 sellers
============================================================
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

DB_PATH = "seller_payouts.db"
OUTPUT_DIR = "reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. Connect ───────────────────────────────────────────
def get_connection():
    return sqlite3.connect(DB_PATH)

# ── 2. Monthly Payout Summary ────────────────────────────
def monthly_payout_summary(conn):
    df = pd.read_sql("""
        SELECT
            month,
            COUNT(DISTINCT seller_id)                               AS active_sellers,
            COUNT(*)                                                AS total_transactions,
            ROUND(SUM(gmv), 2)                                      AS total_gmv,
            ROUND(SUM(commission_amount), 2)                        AS total_commission,
            ROUND(SUM(refund_amount), 2)                            AS total_refunds,
            ROUND(SUM(net_payout), 2)                               AS total_net_payout,
            ROUND(SUM(net_payout) / SUM(gmv) * 100, 2)             AS payout_ratio_pct,
            SUM(CASE WHEN status = 'Discrepancy' THEN 1 ELSE 0 END) AS discrepancy_count,
            ROUND(SUM(CASE WHEN status = 'Discrepancy'
                     THEN ABS(discrepancy_amount) ELSE 0 END), 2)  AS discrepancy_value
        FROM transactions
        GROUP BY month
        ORDER BY month
    """, conn)
    return df

# ── 3. Discrepancy Detection ─────────────────────────────
def detect_discrepancies(conn, threshold: float = 0.0):
    """
    Flags transactions where |discrepancy_amount| > threshold.
    Enriches with seller metadata and classifies Over/Under payment.
    """
    df = pd.read_sql(f"""
        SELECT
            t.transaction_id,
            t.seller_id,
            s.seller_name,
            s.tier,
            s.category,
            s.region,
            t.month,
            t.transaction_date,
            t.gmv,
            t.commission_amount,
            t.refund_amount,
            t.net_payout,
            t.discrepancy_amount,
            CASE
                WHEN t.discrepancy_amount > 0 THEN 'Overpayment'
                ELSE 'Underpayment'
            END AS discrepancy_type,
            ABS(t.discrepancy_amount) AS abs_discrepancy
        FROM transactions t
        JOIN sellers s ON t.seller_id = s.seller_id
        WHERE t.status = 'Discrepancy'
          AND ABS(t.discrepancy_amount) > {threshold}
        ORDER BY ABS(t.discrepancy_amount) DESC
    """, conn)
    return df

# ── 4. Seller-Level Reconciliation ───────────────────────
def seller_reconciliation(conn):
    df = pd.read_sql("""
        SELECT
            t.seller_id,
            s.seller_name,
            s.tier,
            s.category,
            s.region,
            COUNT(*)                                                AS total_txns,
            ROUND(SUM(t.gmv), 2)                                    AS total_gmv,
            ROUND(SUM(t.net_payout), 2)                             AS total_payout,
            ROUND(AVG(t.commission_rate) * 100, 2)                  AS avg_commission_pct,
            ROUND(SUM(t.refund_amount) / SUM(t.gmv) * 100, 2)      AS refund_rate_pct,
            SUM(CASE WHEN t.status='Discrepancy' THEN 1 ELSE 0 END) AS discrepancies,
            ROUND(SUM(CASE WHEN t.status='Discrepancy'
                     THEN ABS(t.discrepancy_amount) ELSE 0 END), 2) AS discrepancy_value,
            SUM(CASE WHEN t.status='On Hold'  THEN 1 ELSE 0 END)    AS on_hold_txns,
            SUM(CASE WHEN t.status='Pending'  THEN 1 ELSE 0 END)    AS pending_txns
        FROM transactions t
        JOIN sellers s ON t.seller_id = s.seller_id
        GROUP BY t.seller_id, s.seller_name, s.tier, s.category, s.region
        ORDER BY total_gmv DESC
    """, conn)

    # Risk score: weighted formula
    df['risk_score'] = (
        df['discrepancies'] * 3 +
        df['on_hold_txns'] * 2 +
        df['pending_txns'] * 1 +
        (df['refund_rate_pct'] > 8).astype(int) * 5
    )
    df['risk_tier'] = pd.cut(df['risk_score'],
        bins=[-1, 3, 8, 15, 999],
        labels=['Low', 'Medium', 'High', 'Critical'])
    return df

# ── 5. Category Performance ───────────────────────────────
def category_performance(conn):
    return pd.read_sql("""
        SELECT
            s.category,
            COUNT(DISTINCT t.seller_id)                             AS sellers,
            COUNT(*)                                                AS transactions,
            ROUND(SUM(t.gmv), 2)                                    AS total_gmv,
            ROUND(SUM(t.net_payout), 2)                             AS total_payout,
            ROUND(AVG(t.commission_rate) * 100, 2)                  AS avg_commission_pct,
            ROUND(SUM(t.refund_amount) / SUM(t.gmv) * 100, 2)      AS refund_rate_pct,
            SUM(CASE WHEN t.status='Discrepancy' THEN 1 ELSE 0 END) AS discrepancy_count
        FROM transactions t
        JOIN sellers s ON t.seller_id = s.seller_id
        GROUP BY s.category
        ORDER BY total_gmv DESC
    """, conn)

# ── 6. Export to Excel with formatting ───────────────────
def export_report(monthly, discrepancies, reconciliation, categories):
    path = f"{OUTPUT_DIR}/FinOps_Payout_Report_Q4_2024.xlsx"
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        monthly.to_excel(writer, sheet_name='Monthly Summary', index=False)
        discrepancies.to_excel(writer, sheet_name='Discrepancies', index=False)
        reconciliation.to_excel(writer, sheet_name='Seller Reconciliation', index=False)
        categories.to_excel(writer, sheet_name='Category Performance', index=False)
    print(f"  ✓ Excel report saved → {path}")
    return path

# ── 7. Automated Alert Generator ─────────────────────────
def generate_alerts(discrepancies_df, reconciliation_df):
    alerts = []
    high_disc = discrepancies_df[discrepancies_df['abs_discrepancy'] > 400]
    if not high_disc.empty:
        alerts.append({
            'severity': 'HIGH',
            'type': 'Large Discrepancy',
            'message': f"{len(high_disc)} transactions with discrepancy > ₹400",
            'action': 'Immediate review required'
        })
    critical_sellers = reconciliation_df[reconciliation_df['risk_tier'] == 'Critical']
    if not critical_sellers.empty:
        alerts.append({
            'severity': 'CRITICAL',
            'type': 'Seller Risk',
            'message': f"{len(critical_sellers)} sellers flagged as Critical risk",
            'action': 'Escalate to Channel Lead'
        })
    high_refund = reconciliation_df[reconciliation_df['refund_rate_pct'] > 8]
    if not high_refund.empty:
        alerts.append({
            'severity': 'MEDIUM',
            'type': 'High Refund Rate',
            'message': f"{len(high_refund)} sellers with refund rate > 8%",
            'action': 'Review return policies'
        })
    return pd.DataFrame(alerts)

# ── MAIN ─────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  FinOps Payout Reconciliation Engine  |  Q4 2024")
    print("="*55)
    print(f"  Run time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Database : {DB_PATH}\n")

    conn = get_connection()

    print("[1/5] Computing monthly payout summary...")
    monthly = monthly_payout_summary(conn)
    print(monthly.to_string(index=False))

    print("\n[2/5] Detecting discrepancies...")
    disc = detect_discrepancies(conn, threshold=0)
    print(f"  → {len(disc)} discrepancies found | Total at risk: ₹{disc['abs_discrepancy'].sum():,.2f}")

    print("\n[3/5] Running seller reconciliation...")
    recon = seller_reconciliation(conn)
    risk_summary = recon['risk_tier'].value_counts()
    print(f"  → Risk breakdown:\n{risk_summary.to_string()}")

    print("\n[4/5] Analyzing category performance...")
    cats = category_performance(conn)
    print(cats[['category','total_gmv','refund_rate_pct','discrepancy_count']].to_string(index=False))

    print("\n[5/5] Generating alerts & exporting report...")
    alerts = generate_alerts(disc, recon)
    print(f"  → {len(alerts)} alerts generated:")
    for _, a in alerts.iterrows():
        print(f"     [{a['severity']}] {a['type']}: {a['message']}")

    export_report(monthly, disc, recon, cats)

    conn.close()
    print("\n✓ Pipeline complete.\n")

if __name__ == "__main__":
    main()
