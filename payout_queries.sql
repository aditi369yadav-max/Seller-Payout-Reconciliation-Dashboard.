-- ============================================================
--  Amazon FinOps — Seller Payout SQL Query Bank
--  Author: [Your Name] | Process Associate L3
--  DB: seller_payouts.db | Q4 2024
-- ============================================================

-- 1. Monthly Payout Summary with Discrepancy Tracking
SELECT
    month,
    COUNT(DISTINCT seller_id)                                AS active_sellers,
    COUNT(*)                                                 AS total_transactions,
    ROUND(SUM(gmv), 2)                                       AS total_gmv,
    ROUND(SUM(commission_amount), 2)                         AS total_commission,
    ROUND(SUM(net_payout), 2)                                AS total_net_payout,
    ROUND(SUM(net_payout) / SUM(gmv) * 100, 2)              AS payout_ratio_pct,
    SUM(CASE WHEN status='Discrepancy' THEN 1 ELSE 0 END)    AS discrepancy_count,
    ROUND(SUM(CASE WHEN status='Discrepancy'
         THEN ABS(discrepancy_amount) ELSE 0 END), 2)        AS discrepancy_value
FROM transactions
GROUP BY month
ORDER BY month;

-- 2. Top 10 Sellers by GMV with Risk Flags
SELECT
    t.seller_id,
    s.seller_name,
    s.tier,
    s.category,
    COUNT(*)                                                 AS txns,
    ROUND(SUM(t.gmv), 2)                                     AS total_gmv,
    ROUND(SUM(t.net_payout), 2)                              AS net_payout,
    SUM(CASE WHEN t.status='Discrepancy' THEN 1 ELSE 0 END)  AS disc_count,
    ROUND(SUM(t.refund_amount)/SUM(t.gmv)*100, 2)            AS refund_rate_pct
FROM transactions t
JOIN sellers s ON t.seller_id = s.seller_id
GROUP BY t.seller_id, s.seller_name, s.tier, s.category
ORDER BY total_gmv DESC
LIMIT 10;

-- 3. Discrepancy Alert — Transactions Requiring Review
SELECT
    t.transaction_id,
    t.seller_id,
    s.seller_name,
    s.tier,
    t.month,
    t.gmv,
    t.net_payout,
    t.discrepancy_amount,
    CASE
        WHEN t.discrepancy_amount > 0 THEN 'Overpayment'
        ELSE 'Underpayment'
    END AS discrepancy_type,
    ABS(t.discrepancy_amount) AS abs_impact
FROM transactions t
JOIN sellers s ON t.seller_id = s.seller_id
WHERE t.status = 'Discrepancy'
ORDER BY ABS(t.discrepancy_amount) DESC;

-- 4. Category-Level Refund & Discrepancy Rates
SELECT
    s.category,
    COUNT(DISTINCT t.seller_id)                              AS seller_count,
    ROUND(SUM(t.gmv), 2)                                     AS total_gmv,
    ROUND(SUM(t.refund_amount)/SUM(t.gmv)*100, 2)           AS refund_rate_pct,
    SUM(CASE WHEN t.status='Discrepancy' THEN 1 ELSE 0 END)  AS discrepancy_count,
    ROUND(AVG(t.commission_rate)*100, 2)                     AS avg_commission_pct
FROM transactions t
JOIN sellers s ON t.seller_id = s.seller_id
GROUP BY s.category
ORDER BY discrepancy_count DESC;

-- 5. Seller Risk Scoring (Adhoc Calculation)
SELECT
    t.seller_id,
    s.seller_name,
    s.tier,
    SUM(CASE WHEN t.status='Discrepancy' THEN 3 ELSE 0 END) +
    SUM(CASE WHEN t.status='On Hold'     THEN 2 ELSE 0 END) +
    SUM(CASE WHEN t.status='Pending'     THEN 1 ELSE 0 END) AS risk_score,
    COUNT(*)                                                  AS total_txns
FROM transactions t
JOIN sellers s ON t.seller_id = s.seller_id
GROUP BY t.seller_id, s.seller_name, s.tier
HAVING risk_score > 10
ORDER BY risk_score DESC;

-- 6. Month-over-Month Payout Growth
SELECT
    a.month,
    a.total_payout,
    b.total_payout AS prev_payout,
    ROUND((a.total_payout - b.total_payout) / b.total_payout * 100, 2) AS mom_growth_pct
FROM (SELECT month, ROUND(SUM(net_payout),2) AS total_payout FROM transactions GROUP BY month) a
LEFT JOIN (SELECT month, ROUND(SUM(net_payout),2) AS total_payout FROM transactions GROUP BY month) b
    ON a.month > b.month
ORDER BY a.month;
