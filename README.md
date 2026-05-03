# 💰 FinOps Seller Payout Reconciliation Dashboard

> **Built for:** Amazon Seller Services · Process Associate L3 Role  
> **Domain:** Financial Operations · Data Analytics · Seller Engagement  
> **Stack:** Python · SQL (SQLite) · HTML/CSS/JS · Excel (openpyxl)

---

## 🎯 Business Problem

Amazon processes thousands of seller payouts every month across categories like Electronics, Fashion, Food, and more. Manual reconciliation of these payouts is error-prone, time-consuming, and lacks real-time visibility into discrepancies.

This project simulates a **production-grade FinOps reconciliation system** that automates:
- Monthly payout calculation across 120 sellers
- Discrepancy detection (overpayments & underpayments)
- Seller risk scoring
- Stakeholder-ready dashboards and reports

---

## 📊 Dataset

| Metric | Value |
|--------|-------|
| Transactions | 10,500 |
| Sellers | 120 |
| Period | Q4 2024 (Oct – Dec) |
| Total GMV | ₹2.35 Crore |
| Total Net Payout | ₹1.87 Crore |
| Discrepancies Flagged | 287 (₹69,122 at risk) |
| Seller Tiers | Platinum · Gold · Silver · Bronze |

---

## 🚀 Features

### 1. Interactive Dashboard (`seller_payout_dashboard.html`)
- **Overview** — KPI cards, monthly bar charts, transaction status donut, category GMV bars
- **Monthly Payouts** — Trend line chart, refund rate analysis, payment method breakdown
- **Discrepancies** — Flagged transactions with filter by Overpayment / Underpayment
- **Seller Profiles** — Filter by tier, sortable columns, pagination, live search
- **Tier Management** — Commission rates, GMV by tier, seller distribution charts
- **Export Reports** — One-click CSV downloads for all data views

### 2. Automated Python Pipeline (`payout_automation.py`)
```
[1/5] Monthly payout summary
[2/5] Discrepancy detection
[3/5] Seller risk scoring
[4/5] Category performance analysis
[5/5] Alert generation + Excel export
```

### 3. SQL Query Bank (`payout_queries.sql`)
6 production-grade queries covering:
- Monthly payout aggregation
- Top sellers by GMV
- Discrepancy detection with JOIN
- Category-level refund rates
- Seller risk scoring formula
- Month-over-month growth calculation

---

## 🗂️ Project Structure

```
Seller-Payout-Reconciliation-Dashboard/
│
├── 📄 README.md
├── 🐍 generate_data.py          # Generates synthetic dataset
├── 🐍 payout_automation.py      # Main reconciliation pipeline
├── 🗃️  payout_queries.sql        # SQL analysis queries
├── 🌐 seller_payout_dashboard.html  # Interactive dashboard
│
├── data/
│   ├── transactions.csv         # 10,500 transaction records
│   └── sellers.csv              # 120 seller profiles
│
└── reports/
    └── FinOps_Payout_Report_Q4_2024.xlsx  # Auto-generated Excel report
```

---

## ⚙️ How to Run

### Prerequisites
```bash
pip install pandas numpy openpyxl
```

### Step 1 — Generate Dataset
```bash
python generate_data.py
```
Output: `seller_payouts.db`, `transactions.csv`, `sellers.csv`

### Step 2 — Run Reconciliation Pipeline
```bash
python payout_automation.py
```
Output: Excel report in `reports/` folder + terminal alerts

### Step 3 — Open Dashboard
Double-click `seller_payout_dashboard.html` — opens in any browser, no server needed.

---

## 🔍 Key SQL Queries

### Monthly Payout Summary
```sql
SELECT
    month,
    COUNT(DISTINCT seller_id)    AS active_sellers,
    ROUND(SUM(gmv), 2)           AS total_gmv,
    ROUND(SUM(net_payout), 2)    AS total_net_payout,
    SUM(CASE WHEN status = 'Discrepancy' 
        THEN 1 ELSE 0 END)       AS discrepancy_count
FROM transactions
GROUP BY month
ORDER BY month;
```

### Discrepancy Detection
```sql
SELECT
    t.transaction_id,
    s.seller_name,
    s.tier,
    t.discrepancy_amount,
    CASE WHEN t.discrepancy_amount > 0 
         THEN 'Overpayment' ELSE 'Underpayment' END AS type
FROM transactions t
JOIN sellers s ON t.seller_id = s.seller_id
WHERE t.status = 'Discrepancy'
ORDER BY ABS(t.discrepancy_amount) DESC;
```

---

## 📈 Business Impact

| Metric | Result |
|--------|--------|
| Transactions processed | 10,500 |
| Discrepancies auto-detected | 287 |
| Amount at risk flagged | ₹69,122 |
| Manual reporting time saved | ~80% |
| Risk score coverage | 100% of sellers |
| Excel report auto-generated | ✅ 4 sheets |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python (Pandas, NumPy) | Data generation & pipeline automation |
| SQLite | Relational data storage & SQL analysis |
| HTML / CSS / JavaScript | Interactive dashboard UI |
| Chart.js | Data visualizations |
| openpyxl | Excel report generation |
| Git + GitHub Pages | Version control & live deployment |

---

## 👤 Author

**Aditi Yadav**  
Aspiring Process Associate · FinOps & Data Analytics  
📧 [your email] · 🔗 [your LinkedIn]

---

> *This project was built to demonstrate hands-on skills in financial operations, SQL analysis, Python automation, and data visualization — directly aligned with the Amazon Seller Services Process Associate (L3) role.*
