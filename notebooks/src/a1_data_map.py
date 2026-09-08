# %% [markdown]
# # a1 - Map the data before you read it
# learn-ship-platform-diagnosis-with-phoebe - by Phoebe Fu
#
# Before a single trend chart: what tables exist, at what grain, for which months, joined how,
# and where they lie. This notebook produces the data-availability heatmap, the key-integrity
# report and the defect scan that the whole diagnosis stands on.

# %%
import sys
sys.path.insert(0, "../analysis")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import lib
lib.style()
tx = lib.load_transactions()          # raw: no dedupe yet, we want to SEE the defect first
lg = lib.load_logins()
dims = lib.load_dims()
events = lib.load_known_events()
print(f"transaction lines {len(tx):,} | orders {tx.txn_id.nunique():,} | span {tx.ts.min().date()} .. {tx.ts.max().date()}")
print(f"logins {len(lg):,} | span {lg.login_ts.min().date()} .. {lg.login_ts.max().date()}")
for k, v in dims.items():
    print(f"dim_{k:<10} {len(v):>7,} rows")

# %% [markdown]
# ## 1. Grain and hierarchy
# One row of `fact_transaction` is an order LINE (one SKU inside one order). Revenue and cost are
# additive at the line; orders are `txn_id` distinct counts; customers are `customer_id` distinct
# counts with blanks excluded. The hierarchy is platform > server > merchant > store > customer and
# category > product line > SKU, with an owner axis (platform SKU vs merchant SKU).

# %%
grain = pd.DataFrame({
    "table": ["fact_transaction", "fact_login", "dim_promotion", "dim_customer", "dim_store", "dim_merchant", "dim_product", "dim_server", "known_events"],
    "grain": ["order line", "login session", "campaign", "customer", "store", "merchant", "SKU", "server", "remembered event"],
    "date column": ["ts", "login_ts", "start_date", "signup_month", "open_month", "onboard_month", "-", "launch_month", "event_date"],
    "keys out": ["server, merchant, store, customer, sku, promo", "customer, server, merchant", "merchant (optional)", "store, merchant, server", "merchant, server", "server", "merchant (if owner=merchant)", "-", "scope"],
})
grain

# %% [markdown]
# ## 2. Coverage: which table covers which month
# The single most important chart before any analysis. Rows per table per month, shown as a
# presence heatmap. A five-year question can only be answered by a table with five years.

# %%
frames = {
    "fact_transaction": tx.assign(d=tx.ts),
    "fact_login": lg.assign(d=lg.login_ts),
    "dim_promotion": dims["promotion"].assign(d=pd.to_datetime(dims["promotion"].start_date)),
    "dim_customer (signups)": dims["customer"].assign(d=pd.to_datetime(dims["customer"].signup_month)),
    "dim_merchant (onboardings)": dims["merchant"].assign(d=pd.to_datetime(dims["merchant"].onboard_month)),
    "dim_store (openings)": dims["store"].assign(d=pd.to_datetime(dims["store"].open_month)),
    "known_events": events.assign(d=events.event_date),
}
cov = lib.coverage(frames, {k: "d" for k in frames})
cov.to_csv(lib.REPORTS / "a1_coverage_by_month.csv")
span = pd.DataFrame({"first month": cov.apply(lambda s: s[s > 0].index.min()), "last month": cov.apply(lambda s: s[s > 0].index.max()),
                     "months with data": (cov > 0).sum(), "months in business": len(cov)})
span["coverage"] = (span["months with data"] / span["months in business"]).round(2)
span

# %%
fig, ax = plt.subplots(figsize=(13, 3.8))
present = (cov > 0).T.astype(int)
ax.imshow(present.values, aspect="auto", cmap=plt.matplotlib.colors.ListedColormap([lib.HAIRLINE, lib.NAVY]), interpolation="nearest")
ax.set_yticks(range(len(present.index))); ax.set_yticklabels(present.index, fontsize=9)
xt = [i for i, p in enumerate(cov.index) if p.month == 1]
ax.set_xticks(xt); ax.set_xticklabels([str(cov.index[i].year) for i in xt])
ax.grid(False)
lib.finish(ax, "Two of seven tables cannot carry a five-year question", "rows present per table per month, 2020-01 to 2026-09 - navy = the table has rows that month")
for i, name in enumerate(present.index):
    s = present.loc[name]; got = s[s == 1]
    if len(got) and len(got) < len(s):
        ax.text(len(s) + 0.5, i, f"{len(got)} of {len(s)} months", va="center", fontsize=8, color=lib.MUTED)
ax.set_xlim(-0.5, len(cov) + 9)
lib.save(fig, "a1_coverage_heatmap")
plt.show()

# %% [markdown]
# Two tables cannot carry five-year questions: **fact_login** has about two months (login analytics
# was switched on 2026-07-01) and **dim_promotion** starts 2025-01 even though orders have carried a
# `promo_id` since 2020. Both are filed as data-collection recommendations, not dropped.

# %% [markdown]
# ## 3. Key integrity: do the joins hold?

# %%
def resolvable(col: str, dim: pd.DataFrame, key: str) -> pd.Series:
    ok = tx[col].isin(set(dim[key]))
    return tx.assign(ok=ok).groupby("year").ok.mean()

integrity = pd.DataFrame({
    "merchant_id -> dim_merchant": resolvable("merchant_id", dims["merchant"], "merchant_id"),
    "store_id -> dim_store": resolvable("store_id", dims["store"], "store_id"),
    "sku_id -> dim_product": resolvable("sku_id", dims["product"], "sku_id"),
    "customer_id present (not guest)": tx.assign(ok=tx.customer_id != "").groupby("year").ok.mean(),
    "promo_id resolvable (of lines with a promo)": tx[tx.promo_id != ""].assign(ok=lambda d: d.promo_id.isin(set(dims["promotion"].promo_id))).groupby("year").ok.mean(),
}).round(3)
integrity.to_csv(lib.REPORTS / "a1_key_integrity_by_year.csv")
integrity

# %%
fig, ax = plt.subplots(figsize=(10, 4))
guest = (1 - integrity["customer_id present (not guest)"]) * 100
orphan = (1 - integrity["promo_id resolvable (of lines with a promo)"]) * 100
ax.bar(integrity.index - 0.2, guest, width=0.4, color=lib.NAVY, label="guest checkout - blank customer_id (%)")
ax.bar(integrity.index + 0.2, orphan, width=0.4, color=lib.AMBER, label="promo_id with no promotion row (%)")
for x, v in zip(integrity.index, guest): ax.text(x - 0.2, v + 1, f"{v:.0f}%", ha="center", fontsize=8)
for x, v in zip(integrity.index, orphan): ax.text(x + 0.2, v + 1, f"{v:.0f}%", ha="center", fontsize=8)
lib.finish(ax, "Guest checkout doubles to 12 percent; promotion ids resolve only from 2025", "share of order lines per year with no customer id, and promo-tagged lines whose promo_id has no promotion row")
ax.set_ylim(0, 112); lib.kfmt(ax, pct=True); ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=9, frameon=False)
lib.save(fig, "a1_identity_gaps")
plt.show()

# %% [markdown]
# Guest checkout is rising every year: those orders have revenue but no customer, so any retention
# number silently excludes a growing slice. Promotion ids before 2025 point at nothing.

# %% [markdown]
# ## 4. Defect scan: exact duplicates
# An exact duplicate line (same order, SKU, quantity, price, cost) is a load defect, not two sales.
# Scan per server per half-year and the defect names itself.

# %%
key = ["txn_id", "sku_id", "qty", "unit_price", "unit_cost"]
tx["dup"] = tx.duplicated(subset=key, keep="first")
tx["half"] = tx.ts.dt.year.astype(str) + "-H" + ((tx.ts.dt.month > 6) + 1).astype(str)
dup = tx.groupby(["server_id", "half"]).dup.mean().unstack(fill_value=0) * 100
dup.round(2).to_csv(lib.REPORTS / "a1_duplicate_rate_pct.csv")
fig, ax = plt.subplots(figsize=(13, 4))
im = ax.imshow(dup.values, aspect="auto", cmap=lib.CM_AMBER, vmin=0, vmax=max(3.5, dup.values.max()))
ax.set_yticks(range(len(dup.index))); ax.set_yticklabels(dup.index)
ax.set_xticks(range(len(dup.columns))); ax.set_xticklabels(dup.columns, rotation=60, fontsize=8)
ax.grid(False); lib.finish(ax, "One hot cell: S02 duplicated 3.4 percent of its lines in 2021-H1, the migration window", "exact-duplicate order lines as percent of lines, server x half-year")
hot = np.argwhere(dup.values > 0.5)
for r, c in hot: ax.text(c, r, f"{dup.values[r, c]:.1f}%", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
lib.save(fig, "a1_duplicates_heatmap")
plt.show()
print("hot cells:", [(dup.index[r], dup.columns[c], round(dup.values[r, c], 2)) for r, c in hot])

# %% [markdown]
# S02 in 2021-H1 carries about 3 percent duplicated lines - exactly the window of the order
# database migration in `known_events`. Every later notebook loads with `dedupe=True`; the raw
# number would overstate S02 revenue for that half-year.

# %% [markdown]
# ## 5. Which questions can this data answer, and until when?

# %%
answerable = pd.DataFrame([
    ("Revenue, cost, profit, margin trend by server / merchant / product", "fact_transaction", "2020-01 .. 2026-09", "yes, full history"),
    ("Order count, AOV, units trend", "fact_transaction", "2020-01 .. 2026-09", "yes, full history"),
    ("Customer cohort retention (repeat purchase)", "fact_transaction (customer_id)", "2020-01 .. 2026-09 minus guests", "yes, with a growing guest blind spot"),
    ("Login-to-purchase funnel, device, session depth", "fact_login", "2026-07 .. 2026-09", "two months only - no trend, no seasonality"),
    ("Did a promotion type lift baskets or retention?", "fact_transaction x dim_promotion", "2025-01 .. 2026-09", "20 months; earlier promo ids unresolvable"),
    ("Merchant / store acquisition and survival", "dim_merchant, dim_store, fact_transaction", "2020-01 .. 2026-09", "yes, full history"),
    ("Basket co-purchase, bundles, cross-sell", "fact_transaction", "2020-01 .. 2026-09", "yes, full history"),
    ("What changed on the product / infra when the numbers moved?", "known_events (9 rows from memory)", "sparse", "NO - there is no event log; this is the gap"),
    ("Fulfilment cost per order (shipping, supplier, returns)", "-", "-", "NO - cost is a unit constant per SKU"),
    ("Product views, cart adds before 2026-07", "-", "-", "NO"),
], columns=["question", "needs", "answerable span", "verdict"])
answerable.to_csv(lib.REPORTS / "a1_question_availability.csv", index=False)
answerable

# %% [markdown]
# ## What a1 hands to the rest of the track
# - load with `lib.load_transactions(dedupe=True)`
# - exclude blank `customer_id` from any customer count and say so on the chart
# - treat `fact_login` and `dim_promotion` as short windows with an explicit caveat
# - overlay `known_events` on every long series, and file the missing event log as a recommendation
