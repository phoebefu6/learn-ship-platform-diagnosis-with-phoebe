"""Synthetic five-year dataset for the Printwell platform diagnosis course.

Printwell is a fictional B2B e-commerce platform: it hosts merchants on ten servers,
merchants open stores and onboard their own customers, and customers buy either the
platform's standard goods (t-shirts, mugs, notebooks ...) or the merchant's customised
versions of the same product lines.

Everything is seeded (SEED = 42). Rerunning this file reproduces every CSV byte for byte.

Planted ground truth the course recovers (do not read before session a2 if you want the
detective experience):
  * 2024-03: a fulfilment/direction shift on servers S07 and S08 raises unit cost ~22 percent
    with prices and volumes unchanged -> revenue flat, profit and margin drop.
  * 2024-09: repeat-purchase propensity on S07/S08 falls ~38 percent (retention lag).
  * 2024-06: merchant churn hazard on S07/S08 rises 2.5x; acquisition slows.
  * Customised (merchant) SKUs carry higher margin AND customers of high-customisation
    merchants repeat ~1.4x more often.
  * Category mix: drinkware/home spike in 2020, stationery declining since 2023, bags rising.
  * Baskets: mug + t-shirt, poster + cushion, notebook + sticker + pen co-occur far above chance.
  * Promo-acquired customers buy bigger first baskets but repeat less.
  * Data quality: S02 duplicated ~3 percent of rows in 2021-H1 (migration); guest checkout
    leaves customer_id empty (5 -> 12 percent, rising with time).
  * Availability gaps: logins exist only for 2026-07-01 .. 2026-09-07; the promotions table
    starts 2025-01 although promo_id is stamped on transactions since 2020 (orphans).
"""
from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT = Path(__file__).resolve().parent
START = pd.Timestamp("2020-01-01")
END = pd.Timestamp("2026-09-07")
MONTHS = pd.period_range(START, END, freq="M")
N_M = len(MONTHS)  # 81 months
rng = np.random.default_rng(SEED)


def midx(ts: str) -> int:
    return MONTHS.get_loc(pd.Period(ts, freq="M"))


SHIFT_COST = midx("2024-03")      # cost shock month on S07/S08
SHIFT_RET = midx("2024-09")       # repeat-propensity drop on S07/S08
SHIFT_CHURN = midx("2024-06")     # merchant churn hazard rise on S07/S08
KEY_SERVERS = {"S07", "S08"}

# ----------------------------------------------------------------------------- servers
servers = pd.DataFrame({
    "server_id": [f"S{i:02d}" for i in range(1, 11)],
    "region": ["SG", "SG", "MY", "MY", "ID", "TH", "VN", "VN", "PH", "AU"],
    "launch_month": ["2020-01", "2020-01", "2020-01", "2020-01", "2020-09", "2020-09",
                     "2021-03", "2021-03", "2022-06", "2024-01"],
    "tier": ["core", "core", "core", "core", "growth", "growth", "key", "key", "growth", "new"],
})

# ----------------------------------------------------------------------------- products
LINES = {  # category -> line -> (n_platform_skus, base_price, base_margin)
    "Apparel":    {"T-shirt": (12, 24.0, 0.40), "Hoodie": (8, 52.0, 0.38), "Cap": (6, 18.0, 0.42)},
    "Drinkware":  {"Mug": (10, 15.0, 0.45), "Tumbler": (6, 28.0, 0.40), "Bottle": (6, 22.0, 0.41)},
    "Stationery": {"Notebook": (8, 12.0, 0.44), "Sticker pack": (6, 6.0, 0.55), "Pen set": (4, 9.0, 0.48)},
    "Home":       {"Cushion": (5, 30.0, 0.37), "Poster": (8, 20.0, 0.50), "Blanket": (4, 58.0, 0.35)},
    "Bags":       {"Tote": (6, 19.0, 0.43), "Backpack": (4, 62.0, 0.36), "Pouch": (5, 11.0, 0.47)},
}
rows = []
for cat, lines in LINES.items():
    for line, (n, price, margin) in lines.items():
        for k in range(n):
            p = round(price * rng.uniform(0.85, 1.25), 2)
            rows.append({"sku_id": f"P-{line[:3].upper()}-{k+1:03d}", "owner": "platform",
                         "merchant_id": "", "category": cat, "product_line": line,
                         "list_price": p, "unit_cost": round(p * (1 - margin * rng.uniform(0.9, 1.1)), 2)})
platform_skus = pd.DataFrame(rows)

# ----------------------------------------------------------------------------- merchants
onboard_plan = {2020: 22, 2021: 34, 2022: 38, 2023: 24, 2024: 12, 2025: 8, 2026: 2}
server_weights = {
    2020: [.2, .2, .2, .2, .1, .1, 0, 0, 0, 0],
    2021: [.08, .08, .08, .08, .08, .08, .26, .26, 0, 0],
    2022: [.06, .06, .06, .06, .07, .07, .22, .22, .18, 0],
    2023: [.08, .08, .08, .08, .08, .08, .16, .16, .20, 0],
    2024: [.1, .1, .1, .1, .1, .1, .05, .05, .1, .2],
    2025: [.1, .1, .1, .1, .1, .1, .04, .04, .12, .2],
    2026: [.1, .1, .1, .1, .1, .1, .05, .05, .1, .2],
}
merch = []
mid = 0
launch_idx = {s: midx(m) for s, m in zip(servers.server_id, servers.launch_month)}
for year, n in onboard_plan.items():
    for _ in range(n):
        mid += 1
        sid = rng.choice(servers.server_id, p=server_weights[year])
        first = max(midx(f"{year}-01"), launch_idx[sid])
        last = N_M - 1 if year == 2026 else midx(f"{year}-12")
        m0 = int(rng.integers(first, last + 1))
        seg = rng.choice(["SMB", "Mid", "Enterprise"], p=[.6, .3, .1])
        custom_share = float(np.clip(rng.beta(2, 3), 0.02, 0.9))  # share of sales on own SKUs
        merch.append({"merchant_id": f"M{mid:03d}", "server_id": sid, "segment": seg,
                      "onboard_month": str(MONTHS[m0]), "m0i": m0, "custom_share": round(custom_share, 3),
                      "vertical": rng.choice(["creator", "school", "corporate gifting", "cafe", "sports club", "nonprofit"],
                                             p=[.3, .15, .2, .15, .1, .1])})
merchants = pd.DataFrame(merch)

# merchant churn: monthly hazard, higher for SMB, x2.5 on key servers after SHIFT_CHURN
churn_month = []
for r in merchants.itertuples():
    base = {"SMB": 0.014, "Mid": 0.008, "Enterprise": 0.004}[r.segment]
    cm = None
    for m in range(r.m0i + 3, N_M):
        h = base * (2.5 if (r.server_id in KEY_SERVERS and m >= SHIFT_CHURN) else 1.0)
        if rng.random() < h:
            cm = m
            break
    churn_month.append(cm)
merchants["mci"] = churn_month
merchants["churn_month"] = [str(MONTHS[c]) if c is not None else "" for c in churn_month]

# merchant custom SKUs (customised versions of platform lines, priced up, higher margin)
crow = []
for r in merchants.itertuples():
    n_custom = int(np.clip(rng.poisson(3 + 12 * r.custom_share), 1, 15))
    lines_pool = [(cat, ln, v) for cat, d in LINES.items() for ln, v in d.items()]
    for k in range(n_custom):
        cat, ln, (n, price, margin) = lines_pool[int(rng.integers(len(lines_pool)))]
        p = round(price * rng.uniform(1.15, 1.6), 2)
        crow.append({"sku_id": f"{r.merchant_id}-{ln[:3].upper()}-{k+1:02d}", "owner": "merchant",
                     "merchant_id": r.merchant_id, "category": cat, "product_line": ln,
                     "list_price": p, "unit_cost": round(p * (1 - (margin + 0.08) * rng.uniform(0.92, 1.08)), 2)})
products = pd.concat([platform_skus, pd.DataFrame(crow)], ignore_index=True)

# ----------------------------------------------------------------------------- stores
st = []
sid_n = 0
for r in merchants.itertuples():
    n_st = {"SMB": 1, "Mid": int(rng.integers(2, 5)), "Enterprise": int(rng.integers(4, 9))}[r.segment]
    for k in range(n_st):
        sid_n += 1
        open_m = r.m0i if k == 0 else int(min(N_M - 1, r.m0i + rng.integers(0, 18)))
        close_m = None if pd.isna(r.mci) else int(r.mci)
        if close_m is None and rng.random() < 0.12:  # store closed while merchant stays
            close_m = int(min(N_M - 1, open_m + rng.integers(6, 40)))
        if close_m is not None and close_m < open_m:
            continue
        st.append({"store_id": f"{r.merchant_id}-ST{k+1}", "merchant_id": r.merchant_id, "server_id": r.server_id,
                   "store_type": rng.choice(["web", "pop-up", "campus", "corporate"], p=[.55, .15, .15, .15]),
                   "open_month": str(MONTHS[open_m]), "oi_": open_m,
                   "close_month": str(MONTHS[close_m]) if close_m is not None else "", "ci_": close_m})
stores = pd.DataFrame(st)
# real dimension tables rarely get closed: ~65% of dead stores keep a blank close_month
never_closed = (stores.close_month != "") & (rng.random(len(stores)) < 0.65)
stores.loc[never_closed, "close_month"] = ""

# ----------------------------------------------------------------------------- customers
season = np.array([0.82, 0.74, 0.9, 0.95, 1.0, 0.98, 1.0, 1.02, 1.05, 1.15, 1.45, 1.6])
covid = np.ones(N_M)
covid[midx("2020-04"):midx("2020-12") + 1] = 1.35  # lockdown online surge
cust = []
merch_by_id = merchants.set_index("merchant_id")
for s in stores.itertuples():
    seg = merch_by_id.loc[s.merchant_id, "segment"]
    lam = {"SMB": 2.6, "Mid": 4.5, "Enterprise": 8.0}[seg]
    last = N_M - 1 if pd.isna(s.ci_) else int(s.ci_)
    will_churn = merch_by_id.loc[s.merchant_id, "mci"] is not None and not pd.isna(merch_by_id.loc[s.merchant_id, "mci"])
    lag = int(rng.integers(0, 3)) + (int(rng.integers(1, 4)) if will_churn else 0)  # months before the first sale; slower starters churn more
    slow = 0.6 if will_churn else 1.0
    for m in range(s.oi_ + lag, last + 1):
        age = m - s.oi_ - lag
        ramp = min(1.0, (0.35 + age / 8) * (slow if age < 6 else 1.0))
        grow = 1.0
        if s.server_id in KEY_SERVERS:  # fast ramp, plateau, then the post-shift slowdown
            grow = 1.7 if m < midx("2022-07") else (0.6 if m >= SHIFT_CHURN else 0.85)
        n = rng.poisson(lam * ramp * grow * season[MONTHS[m].month - 1] * covid[m])
        for _ in range(n):
            cust.append((s.store_id, s.merchant_id, s.server_id, m))
customers = pd.DataFrame(cust, columns=["store_id", "merchant_id", "server_id", "m0i"])
customers["customer_id"] = [f"C{i:06d}" for i in range(1, len(customers) + 1)]
customers["acq_channel"] = rng.choice(["organic", "merchant-referral", "promo", "paid-social"],
                                      size=len(customers), p=[.42, .25, .18, .15])
customers["signup_month"] = [str(MONTHS[m]) for m in customers.m0i]
customers["country"] = customers.server_id.map(servers.set_index("server_id").region)

# ----------------------------------------------------------------------------- purchase process
cs = customers.merge(merchants[["merchant_id", "custom_share"]], on="merchant_id")
base_p = rng.beta(1.4, 10, size=len(cs)) * (1 + 0.6 * cs.custom_share.values)  # ~0.12 mean monthly repeat, higher for custom
base_p = np.where(cs.acq_channel.values == "promo", base_p * 0.72, base_p)
m0 = cs.m0i.values
is_key = cs.server_id.isin(KEY_SERVERS).values
months = np.arange(N_M)
k = months[None, :] - m0[:, None]  # months since signup
alive = k > 0
decay = 0.94 ** np.clip(k, 0, None)
seas = season[[p.month - 1 for p in MONTHS]][None, :]
shift = np.where(is_key[:, None] & (months[None, :] >= SHIFT_RET), 0.62, 1.0)
prob = base_p[:, None] * decay * seas * shift * covid[None, :]
buy = alive & (rng.random(prob.shape) < prob)
buy[np.arange(len(cs)), m0] = True  # first purchase in signup month
ci, mi = np.nonzero(buy)
orders = pd.DataFrame({"cix": ci, "mi_": mi})
orders["customer_id"] = cs.customer_id.values[ci]
orders["store_id"] = cs.store_id.values[ci]
orders["merchant_id"] = cs.merchant_id.values[ci]
orders["server_id"] = cs.server_id.values[ci]
orders["custom_share"] = cs.custom_share.values[ci]
orders["is_first"] = orders.mi_ == m0[ci]
orders["acq_channel"] = cs.acq_channel.values[ci]
# timestamp within the month
per = MONTHS[orders.mi_.values]
days_in = np.array([p.days_in_month for p in per])
day = rng.integers(0, days_in)
orders["ts"] = pd.to_datetime([p.start_time for p in per]) + pd.to_timedelta(day, "D") \
    + pd.to_timedelta(rng.integers(8 * 3600, 23 * 3600, len(orders)), "s")
orders = orders[orders.ts <= END].reset_index(drop=True)
orders["txn_id"] = [f"T{i:07d}" for i in range(1, len(orders) + 1)]

# ----------------------------------------------------------------------------- basket lines
cat_trend = {  # multiplier by year for category share
    "Apparel":    {2020: 1.0, 2021: 1.05, 2022: 1.1, 2023: 1.1, 2024: 1.1, 2025: 1.1, 2026: 1.1},
    "Drinkware":  {2020: 1.6, 2021: 1.2, 2022: 1.0, 2023: 1.0, 2024: 1.0, 2025: 1.0, 2026: 1.0},
    "Stationery": {2020: 1.0, 2021: 1.0, 2022: 0.95, 2023: 0.8, 2024: 0.65, 2025: 0.55, 2026: 0.5},
    "Home":       {2020: 1.5, 2021: 1.1, 2022: 0.9, 2023: 0.9, 2024: 0.9, 2025: 0.9, 2026: 0.9},
    "Bags":       {2020: 0.6, 2021: 0.7, 2022: 0.85, 2023: 1.0, 2024: 1.2, 2025: 1.4, 2026: 1.5},
}
BUNDLES = [("Mug", "T-shirt", 0.35), ("Poster", "Cushion", 0.30), ("Notebook", "Sticker pack", 0.40),
           ("Sticker pack", "Pen set", 0.30), ("Tote", "T-shirt", 0.2)]
line_of = {ln: cat for cat, d in LINES.items() for ln in d}
line_list = list(line_of)
prod_by_line_platform = {ln: platform_skus[platform_skus.product_line == ln].sku_id.values for ln in line_list}
prod_by_merchant = {mid_: g for mid_, g in products[products.owner == "merchant"].groupby("merchant_id")}
PRICE = dict(zip(products.sku_id, products.list_price))
COST = dict(zip(products.sku_id, products.unit_cost))
BUNDLE_NEXT = {a: (b, pr) for a, b, pr in BUNDLES}
CATS = list(LINES)
LINES_OF = {c: list(d) for c, d in LINES.items()}

# promotions: platform + merchant campaigns, quarterly-ish, 2020..2026; the TABLE later keeps only 2025+
promo_rows = []
pid = 0
for m in range(N_M):
    per_m = MONTHS[m]
    n_p = 2 if per_m.month in (11, 12) else (1 if per_m.month in (3, 6, 9) else 0)
    for _ in range(n_p):
        pid += 1
        promo_rows.append({"promo_id": f"PR{pid:04d}", "scope": "platform", "merchant_id": "",
                           "promo_type": rng.choice(["percent-off", "bundle", "free-shipping", "flash"]),
                           "discount_pct": int(rng.choice([10, 15, 20, 25, 30])),
                           "start_date": str(per_m.start_time.date()), "end_date": str(per_m.end_time.date()), "mi_": m})
    for mr in merchants[(merchants.m0i <= m) & ((merchants.mci.isna()) | (merchants.mci > m))].itertuples():
        if rng.random() < 0.06:
            pid += 1
            promo_rows.append({"promo_id": f"PR{pid:04d}", "scope": "merchant", "merchant_id": mr.merchant_id,
                               "promo_type": rng.choice(["percent-off", "bundle", "flash"]),
                               "discount_pct": int(rng.choice([10, 15, 20])),
                               "start_date": str(per_m.start_time.date()), "end_date": str(per_m.end_time.date()), "mi_": m})
promos = pd.DataFrame(promo_rows)
promo_by_m = {m: g for m, g in promos.groupby("mi_")}

lines_out = []
n_lines = np.clip(rng.geometric(0.55, size=len(orders)), 1, 4)
years = orders.ts.dt.year.values
for i, o in enumerate(orders.itertuples()):
    yr = int(years[i])
    cat_w = np.array([cat_trend[c][yr] for c in LINES])
    cat_w = cat_w / cat_w.sum()
    chosen: list[str] = []
    for _ in range(int(n_lines[i])):
        nxt = BUNDLE_NEXT.get(chosen[-1]) if chosen else None
        if nxt and rng.random() < nxt[1]:
            chosen.append(nxt[0])
        else:
            cat = CATS[int(rng.choice(len(CATS), p=cat_w))]
            chosen.append(LINES_OF[cat][int(rng.integers(len(LINES_OF[cat])))])
    # promo assignment
    promo_id = ""
    if o.mi_ in promo_by_m:
        g = promo_by_m[o.mi_]
        elig = g[(g.scope == "platform") | (g.merchant_id == o.merchant_id)]
        if len(elig) and (rng.random() < (0.55 if o.acq_channel == "promo" and o.is_first else 0.18)):
            promo_id = elig.promo_id.iloc[int(rng.integers(len(elig)))]
    seen: set[str] = set()
    for ln in chosen:
        use_custom = (o.merchant_id in prod_by_merchant) and (rng.random() < o.custom_share)
        if use_custom:
            g = prod_by_merchant[o.merchant_id]
            g2 = g[g.product_line == ln]
            sku = (g2 if len(g2) else g).sku_id.values
            sku = sku[int(rng.integers(len(sku)))]
        else:
            pool = prod_by_line_platform[ln]
            sku = pool[int(rng.integers(len(pool)))]
        if sku in seen:  # one row per SKU per order; a repeated pick just means a bigger basket
            continue
        seen.add(sku)
        qty = int(np.clip(rng.geometric(0.6), 1, 6))
        price = PRICE[sku]
        cost = COST[sku]
        if o.server_id in KEY_SERVERS and o.mi_ >= SHIFT_COST:
            cost *= 1.22  # the planted direction shift: premium fulfilment absorbed, price untouched
        if promo_id:
            price *= 1 - 0.17
            qty = int(qty * 1.3) + (1 if o.is_first else 0)
        lines_out.append((o.txn_id, sku, qty, round(price, 2), round(cost, 2), promo_id))
lines_df = pd.DataFrame(lines_out, columns=["txn_id", "sku_id", "qty", "unit_price", "unit_cost", "promo_id"])
tx = orders[["txn_id", "ts", "server_id", "merchant_id", "store_id", "customer_id"]].merge(lines_df, on="txn_id")
tx = tx.merge(products[["sku_id", "owner", "category", "product_line"]], on="sku_id")
tx["revenue"] = (tx.qty * tx.unit_price).round(2)
tx["cost"] = (tx.qty * tx.unit_cost).round(2)
tx["profit"] = (tx.revenue - tx.cost).round(2)
tx["channel"] = rng.choice(["web", "app", "pos"], size=len(tx), p=[.6, .3, .1])

# ---- data-quality plants
# guest checkout: customer_id blank, share rising with time (5% 2020 -> 12% 2026)
frac = 0.05 + 0.07 * (tx.ts - START).dt.days / (END - START).days
guest = rng.random(len(tx)) < frac.values
tx.loc[guest, "customer_id"] = ""
# S02 migration duplicates in 2021-H1
dup_mask = (tx.server_id == "S02") & (tx.ts >= "2021-01-01") & (tx.ts < "2021-07-01")
dups = tx[dup_mask].sample(frac=0.03, random_state=SEED)
tx = pd.concat([tx, dups], ignore_index=True)
tx = tx.sort_values(["ts", "txn_id"]).reset_index(drop=True)
tx["ts"] = tx.ts.dt.strftime("%Y-%m-%d %H:%M:%S")

# ----------------------------------------------------------------------------- logins (only last ~2 months exist)
LOGIN_START = pd.Timestamp("2026-07-01")
active_recent = orders[orders.ts >= "2025-06-01"].customer_id.unique()
lg = []
for cid in active_recent:
    n = rng.poisson(3.2)
    for _ in range(n):
        t = LOGIN_START + pd.to_timedelta(rng.integers(0, (END - LOGIN_START).days + 1), "D") \
            + pd.to_timedelta(rng.integers(6 * 3600, 24 * 3600), "s")
        lg.append((cid, t))
logins = pd.DataFrame(lg, columns=["customer_id", "login_ts"]).merge(
    customers[["customer_id", "server_id", "merchant_id"]], on="customer_id")
conv_p = np.where(logins.server_id.isin(KEY_SERVERS), 0.17, 0.27)
logins["device"] = rng.choice(["ios", "android", "web"], size=len(logins), p=[.4, .35, .25])
logins["session_seconds"] = rng.lognormal(5.2, 0.7, len(logins)).astype(int)
logins["viewed_products"] = rng.poisson(4.5, len(logins))
logins["added_to_cart"] = (rng.random(len(logins)) < 0.45).astype(int)
logins["purchased"] = ((logins.added_to_cart == 1) & (rng.random(len(logins)) < conv_p / 0.45)).astype(int)
logins["login_ts"] = logins.login_ts.dt.strftime("%Y-%m-%d %H:%M:%S")
logins = logins.sort_values("login_ts").reset_index(drop=True)

# ----------------------------------------------------------------------------- known events (what the team remembers)
known_events = pd.DataFrame([
    ("2020-04-01", "business", "Lockdown demand surge; drinkware and home goods sell out", "platform"),
    ("2021-03-15", "tech", "Servers S07 and S08 launched for VN expansion", "S07,S08"),
    ("2021-02-01", "tech", "Order database migration on S02 (duplicate writes suspected)", "S02"),
    ("2022-06-20", "tech", "New checkout flow rolled out to all servers", "platform"),
    ("2023-11-01", "business", "Merchant plan pricing revised; SMB tier fee reduced", "platform"),
    ("2024-03-01", "business", "Strategic shift on S07/S08: premium fulfilment partner, free shipping absorbed by platform", "S07,S08"),
    ("2024-06-10", "business", "Merchant success team for VN region reduced", "S07,S08"),
    ("2025-01-01", "data", "Promotion management module launched; promo table starts here", "platform"),
    ("2026-07-01", "data", "Login analytics enabled; login table starts here", "platform"),
], columns=["event_date", "event_type", "description", "scope"])

# ----------------------------------------------------------------------------- write
servers.to_csv(OUT / "dim_server.csv", index=False)
merchants.drop(columns=["m0i", "mci"]).to_csv(OUT / "dim_merchant.csv", index=False)
stores.drop(columns=["oi_", "ci_"]).to_csv(OUT / "dim_store.csv", index=False)
customers.drop(columns=["m0i"]).to_csv(OUT / "dim_customer.csv", index=False)
products.to_csv(OUT / "dim_product.csv", index=False)
promos[promos.mi_ >= midx("2025-01")].drop(columns=["mi_"]).to_csv(OUT / "dim_promotion.csv", index=False)
known_events.to_csv(OUT / "known_events.csv", index=False)
with gzip.open(OUT / "fact_transaction.csv.gz", "wt", newline="") as f:
    tx.to_csv(f, index=False)
with gzip.open(OUT / "fact_login.csv.gz", "wt", newline="") as f:
    logins.to_csv(f, index=False)

print(f"servers {len(servers)} | merchants {len(merchants)} ({merchants.churn_month.ne('').sum()} churned) | "
      f"stores {len(stores)} | customers {len(customers):,} | products {len(products)} "
      f"({(products.owner=='merchant').sum()} merchant) | promos kept {int((promos.mi_ >= midx('2025-01')).sum())} of {len(promos)}")
print(f"transactions {len(tx):,} lines / {tx.txn_id.nunique():,} orders | logins {len(logins):,}")
kk = tx[tx.server_id.isin(KEY_SERVERS)].copy()
kk["yr"] = kk.ts.str[:4]
print((kk.groupby("yr")[["revenue", "profit"]].sum().assign(margin=lambda d: d.profit / d.revenue)).round(3))
