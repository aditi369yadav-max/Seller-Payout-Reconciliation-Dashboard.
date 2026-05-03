import pandas as pd
import numpy as np
import sqlite3
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# Sellers
n_sellers = 120
seller_ids = [f"SLR{str(i).zfill(5)}" for i in range(1, n_sellers+1)]
seller_names = [
    "TechGadgets India", "FashionHub", "HomeDecor Plus", "ElectroZone", "BookWorld",
    "SportsPro", "KitchenKing", "BeautyBliss", "AutoParts Express", "ToysGalore",
    "OrganicFoods", "FurnitureMart", "JewelryBox", "PetCare Plus", "GardenGreen",
    "OfficeSupplies", "MusicStore", "ArtsCrafts", "HealthPlus", "TravelGear"
]
seller_categories = ["Electronics", "Fashion", "Home & Kitchen", "Books", "Sports", "Beauty", "Automotive", "Toys", "Food", "Furniture"]

sellers_df = pd.DataFrame({
    "seller_id": seller_ids,
    "seller_name": [random.choice(seller_names) + f" {i}" for i in range(1, n_sellers+1)],
    "category": [random.choice(seller_categories) for _ in range(n_sellers)],
    "tier": np.random.choice(["Gold", "Silver", "Bronze", "Platinum"], n_sellers, p=[0.1, 0.3, 0.45, 0.15]),
    "region": np.random.choice(["North", "South", "East", "West", "Central"], n_sellers),
    "onboarding_date": [datetime(2021, 1, 1) + timedelta(days=random.randint(0, 700)) for _ in range(n_sellers)]
})

# Transactions
n_txns = 10500
start_date = datetime(2024, 10, 1)

txn_dates = [start_date + timedelta(days=random.randint(0, 91)) for _ in range(n_txns)]
txn_seller_ids = np.random.choice(seller_ids, n_txns)

gmv = np.random.lognormal(mean=7, sigma=1.2, size=n_txns).round(2)
commission_rate = np.where(
    np.isin(txn_seller_ids, sellers_df[sellers_df.tier=="Platinum"].seller_id), 0.08,
    np.where(np.isin(txn_seller_ids, sellers_df[sellers_df.tier=="Gold"].seller_id), 0.10,
    np.where(np.isin(txn_seller_ids, sellers_df[sellers_df.tier=="Silver"].seller_id), 0.12, 0.15))
)
commission = (gmv * commission_rate).round(2)
shipping_fee = np.random.choice([0, 40, 60, 80, 100], n_txns, p=[0.3, 0.2, 0.25, 0.15, 0.1])
refund_amount = np.where(np.random.random(n_txns) < 0.08, gmv * np.random.uniform(0.5, 1.0, n_txns), 0).round(2)

discrepancy_flags = np.random.random(n_txns) < 0.03
discrepancy_amount = np.where(discrepancy_flags, np.random.uniform(-500, 500, n_txns).round(2), 0)

net_payout = (gmv - commission - shipping_fee - refund_amount + discrepancy_amount).round(2)

status = np.where(net_payout < 0, "On Hold",
         np.where(discrepancy_flags, "Discrepancy",
         np.where(np.random.random(n_txns) < 0.05, "Pending", "Processed")))

txns_df = pd.DataFrame({
    "transaction_id": [f"TXN{str(i).zfill(7)}" for i in range(1, n_txns+1)],
    "seller_id": txn_seller_ids,
    "transaction_date": txn_dates,
    "month": [d.strftime("%Y-%m") for d in txn_dates],
    "gmv": gmv,
    "commission_rate": commission_rate,
    "commission_amount": commission,
    "shipping_fee": shipping_fee,
    "refund_amount": refund_amount,
    "discrepancy_amount": discrepancy_amount,
    "net_payout": net_payout,
    "status": status,
    "payment_method": np.random.choice(["NEFT", "IMPS", "UPI", "RTGS"], n_txns, p=[0.4, 0.3, 0.2, 0.1])
})

# Save to SQLite
conn = sqlite3.connect("seller_payouts.db")
sellers_df.to_sql("sellers", conn, if_exists="replace", index=False)
txns_df.to_sql("transactions", conn, if_exists="replace", index=False)
conn.close()

# Save CSVs
txns_df.to_csv("transactions.csv", index=False)
sellers_df.to_csv("sellers.csv", index=False)

print(f"Dataset created: {len(txns_df)} transactions, {len(sellers_df)} sellers")
print(f"Discrepancies: {discrepancy_flags.sum()} rows ({discrepancy_flags.mean()*100:.1f}%)")
print(f"Total GMV: Rs.{txns_df.gmv.sum():,.0f}")
print(f"Total Net Payout: Rs.{txns_df.net_payout.sum():,.0f}")
print("Done! Files created: seller_payouts.db, transactions.csv, sellers.csv")