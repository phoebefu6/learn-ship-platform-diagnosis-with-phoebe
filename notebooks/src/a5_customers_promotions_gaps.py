# %% [markdown]
# # a5 - Customers, promotions and the gaps
# learn-ship-platform-diagnosis-with-phoebe - by Phoebe Fu
#
# Customer retention with frozen history, the lag between the 2024 cost decision and the customers
# leaving, what customisation does to repeat rates, the double edge of promotions, and the
# login-to-purchase funnel on the only two months that have logins. Ends with the canon numbers the
# chairman pages quote.

# %%
import sys, json
sys.path.insert(0, "../analysis")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import lib
lib.style()
tx = lib.load_transactions(dedupe=True)
dims = lib.load_dims(); lg = lib.load_logins()
txc = tx[tx.month < pd.Period(lib.AS_OF, "M")]
ident = txc[txc.customer_id != ""]
print(f"{len(txc):,} lines | {ident.customer_id.nunique():,} identified customers | {(txc.customer_id == '').mean()*100:.1f}% guest lines excluded from retention")
canon = {}

# %% [markdown]
# ## 1. Cohort retention with frozen history, key servers versus the rest
# A customer belongs to the quarter of their first order. Cell (cohort, k) = share who ordered in
# quarter cohort+k. Completed cells never change; the current partial quarter is blank.

# %%
ret_key = lib.cohort_retention(ident[ident.is_key], "Q", 6)
ret_oth = lib.cohort_retention(ident[~ident.is_key], "Q", 6)
ret_key.round(3).to_csv(lib.REPORTS / "a5_cohort_key_servers.csv"); ret_oth.round(3).to_csv(lib.REPORTS / "a5_cohort_other_servers.csv")
fig, axes = plt.subplots(1, 2, figsize=(15, 7.2))
for ax, r, title in zip(axes, [ret_key, ret_oth], ["S07 + S08", "other servers"]):
    r = r.loc["2022Q1":"2026Q1"]
    vals = r.values[:, 1:] * 100
    im = ax.imshow(vals, cmap=lib.CM_NAVY, vmin=0, vmax=40, aspect="auto")
    ax.set_yticks(range(len(r.index))); ax.set_yticklabels([str(i) for i in r.index], fontsize=8.5)
    ax.set_xticks(range(6)); ax.set_xticklabels([f"+{k}Q" for k in range(1, 7)]); ax.grid(False)
    for sp in ax.spines.values(): sp.set_visible(False)
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            v = vals[i, j]
            if not np.isnan(v): ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8, color="white" if v > 22 else lib.INK)
    first_late = list(r.index).index(pd.Period("2024Q3", "Q"))
    if title == "S07 + S08":
        ax.add_patch(plt.Rectangle((-0.5, first_late - 0.5), 6, len(r.index) - first_late, fill=False, ec=lib.AMBER, lw=2.5))
        ax.text(6.0, first_late + 1.5, "cohorts acquired\nfrom 2024Q3:\nrepeat rates fall\nand stay down", fontsize=9, color=lib.AMBER_INK, va="top")
        ax.set_title("S07 + S08", loc="left", fontsize=12, fontweight="bold", color=lib.AMBER_INK)
    else:
        ax.add_patch(plt.Rectangle((-0.5, first_late - 0.5), 6, len(r.index) - first_late, fill=False, ec=lib.FAINT, lw=1.5, ls="--"))
        ax.text(6.0, first_late + 1.5, "same quarters,\nother servers:\nnothing changes", fontsize=9, color=lib.MUTED, va="top")
        ax.set_title("other servers", loc="left", fontsize=12, fontweight="bold", color=lib.MUTED)
    ax.set_xlim(-0.5, 8.6)
lib.finish_fig(fig, "Repeat rates fall from the 2024Q3 cohorts on the key servers only", "quarterly cohort repeat rate %, frozen history: rows = acquisition quarter, columns = quarters later; blank = window not yet complete", y=0.99)
lib.save(fig, "a5_cohort_triangles")
plt.show()

# %% [markdown]
# ## 2. The lag: repeat rate by acquisition quarter
# Share of each quarterly cohort that ordered again within the next two quarters. The 2024-03 cost
# decision shows up in customers two quarters later - and only on the key servers.

# %%
def repeat_within(r, ks=(1, 2)):
    return r[list(ks)].max(axis=1)  # a customer counted if back in +1Q or +2Q (approximation via max of the two shares)
rk = ret_key.loc["2021Q3":][[1, 2]].mean(axis=1) * 100; ro = ret_oth.loc["2021Q3":][[1, 2]].mean(axis=1) * 100  # key servers launched 2021-03; earlier cohorts are tiny
fig, ax = plt.subplots(figsize=(12, 4.6))
ro = ro.loc["2021Q3":]; rk = rk.loc["2021Q3":]
ax.plot(ro.index.to_timestamp(), ro.values, color=lib.NAVY_SOFT, lw=2, marker="o", ms=3.5)
ax.plot(rk.index.to_timestamp(), rk.values, color=lib.AMBER, lw=2.6, marker="o", ms=4)
lib.label_end(ax, ro.index[-1].to_timestamp(), ro.values[-1], "other servers", lib.NAVY_MID); lib.label_end(ax, rk.index[-1].to_timestamp(), rk.values[-1], "S07 + S08", lib.AMBER_INK)
ax.set_ylim(0, 40); lib.kfmt(ax, pct=True); lib.story_band(ax, "Mar 2024 cost decision")
ax.axvline(pd.Timestamp("2024-07-01"), color=lib.AMBER, ls=":", lw=1.2)
lib.callout(ax, (pd.Timestamp("2024-07-01"), float(rk.loc["2024Q3"])), "two quarters later the\n2024Q3 cohort repeats\nat a fifth less", (30, -60))
lib.finish(ax, "Customers left two quarters after the cost decision - on the key servers only", "average share of each acquisition-quarter cohort ordering again in the next two quarters; completed cohorts only")
ax.set_ylabel("")
lib.save(fig, "a5_repeat_rate_lag")
plt.show()
canon["repeat_key_2023"] = round(float(rk.loc["2023Q1":"2023Q4"].mean()), 1)
canon["repeat_key_2025"] = round(float(rk.loc["2025Q1":"2025Q4"].mean()), 1)
canon["repeat_other_2023"] = round(float(ro.loc["2023Q1":"2023Q4"].mean()), 1)
canon["repeat_other_2025"] = round(float(ro.loc["2025Q1":"2025Q4"].mean()), 1)
canon

# %% [markdown]
# ## 3. Time to second order

# %%
o = ident.groupby(["customer_id", "txn_id"]).ts.min().reset_index().sort_values(["customer_id", "ts"])
o["n"] = o.groupby("customer_id").cumcount()
first2 = o[o.n <= 1].pivot(index="customer_id", columns="n", values="ts")
gap = (first2[1] - first2[0]).dt.days.dropna()
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(gap[gap <= 540], bins=54, color=lib.NAVY)
for d, lab in [(90, "90d"), (180, "180d"), (365, "1y")]:
    ax.axvline(d, color=lib.AMBER, ls="--"); ax.text(d + 3, ax.get_ylim()[1]*0.9, lab, color=lib.AMBER_INK, fontsize=9)
lib.finish(ax, f"Half of second orders arrive within {gap.median():.0f} days", "days between first and second order, customers with a second order; dashed = 90 days, 180 days, one year"); ax.set_yticks([])
lib.save(fig, "a5_time_to_second")
plt.show()
canon["median_days_to_second_order"] = int(gap.median())
canon["share_second_within_180d"] = round(float((gap <= 180).mean() * 100), 1)

# %% [markdown]
# ## 4. Customisation retains
# Customers grouped by their merchant's customisation share. Same frozen 12-month repeat definition:
# ordered again within four quarters of the acquisition quarter, cohorts complete by 2025Q2.

# %%
mc = dims["merchant"].set_index("merchant_id").custom_share
ident2 = ident.assign(cs=ident.merchant_id.map(mc))
ident2["cs_band"] = pd.cut(ident2.cs, [0, 0.25, 0.5, 1.0], labels=["low (<25%)", "mid (25-50%)", "high (>50%)"])
def repeat12(d):
    r = lib.cohort_retention(d, "Q", 4)
    r = r.loc[:"2025Q2"]
    return float(np.nanmean(r[[1, 2, 3, 4]].max(axis=1)) * 100)
band = pd.Series({b: repeat12(ident2[ident2.cs_band == b]) for b in ident2.cs_band.cat.categories})
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(band.index, band.values, color=[lib.NAVY_SOFT, lib.NAVY_MID, lib.AMBER])
for i, v in enumerate(band.values): ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=10)
lib.finish(ax, f"Customers of high-customisation merchants repeat {band.iloc[-1]-band.iloc[0]:.0f} points more", "peak quarterly repeat rate within a year of acquisition, by the merchant's share of sales on its own SKUs"); ax.set_ylim(0, band.max() * 1.15); lib.kfmt(ax, pct=True)
lib.save(fig, "a5_custom_share_retention")
plt.show()
canon["repeat_low_custom"] = round(float(band.iloc[0]), 1); canon["repeat_high_custom"] = round(float(band.iloc[-1]), 1)
band.round(1)

# %% [markdown]
# ## 5. Promotions: bigger first baskets, fewer second orders
# By acquisition channel from the customer dimension (available all five years), then by promotion
# type where the promotion table exists (2025 onward).

# %%
cust = dims["customer"].set_index("customer_id")
fo = ident.merge(ident.groupby("customer_id").ts.min().rename("first_ts"), on="customer_id")
fb = fo[fo.ts == fo.first_ts].groupby("customer_id").revenue.sum().rename("first_basket").to_frame()
fb["channel"] = cust.acq_channel.reindex(fb.index)
n_orders = ident.groupby("customer_id").txn_id.nunique()
fb["repeat"] = (n_orders.reindex(fb.index) >= 2)
fb["first_year"] = fo.groupby("customer_id").first_ts.min().dt.year.reindex(fb.index)
mature = fb[fb.first_year <= 2024]
ch = mature.groupby("channel").agg(customers=("repeat", "size"), first_basket=("first_basket", "mean"), repeat_rate=("repeat", "mean"))
ch["repeat_rate"] *= 100
fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
cols = [lib.AMBER if c == "promo" else lib.NAVY for c in ch.index]
axes[0].bar(ch.index, ch.first_basket, color=cols); lib.finish(axes[0], "Promotions buy a bigger first basket", "average first-order value by acquisition channel")
axes[1].bar(ch.index, ch.repeat_rate, color=cols); lib.finish(axes[1], "and a smaller future", "share who ever ordered a second time, customers acquired 2020-2024"); lib.kfmt(axes[1], pct=True)
for ax, col in zip(axes, ["first_basket", "repeat_rate"]):
    for i, v in enumerate(ch[col]): ax.text(i, v * 1.01, f"{v:.0f}" + ("%" if col == "repeat_rate" else ""), ha="center", fontsize=9)
lib.finish_fig(fig, "Promotion-acquired customers: the bigger basket and the smaller future", "amber = promotion-acquired; navy = the other channels", y=1.02)
lib.save(fig, "a5_promo_double_edge")
plt.show()
canon["promo_first_basket"] = round(float(ch.loc["promo", "first_basket"]), 1); canon["organic_first_basket"] = round(float(ch.loc["organic", "first_basket"]), 1)
canon["promo_repeat"] = round(float(ch.loc["promo", "repeat_rate"]), 1); canon["organic_repeat"] = round(float(ch.loc["organic", "repeat_rate"]), 1)
ch.round(1)

# %%
pr = dims["promotion"]
joined = txc[txc.promo_id != ""].merge(pr[["promo_id", "promo_type", "scope"]], on="promo_id", how="left")
joined["resolved"] = joined.promo_type.notna()
res_by_year = joined.groupby("year").resolved.mean() * 100
ob = txc.groupby("txn_id").agg(revenue=("revenue", "sum"), promo=("promo_id", "first"), year=("year", "first"))
ob = ob.merge(pr[["promo_id", "promo_type"]], left_on="promo", right_on="promo_id", how="left")
ob["kind"] = ob.promo_type.fillna(pd.Series(np.where(ob.promo != "", "unresolved promo", "no promo"), index=ob.index))
basket = ob[ob.year >= 2025].groupby("kind").revenue.agg(["mean", "size"]).sort_values("mean")
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
axes[0].bar(res_by_year.index, res_by_year.values, color=lib.NAVY); lib.finish(axes[0], "Promo ids resolve only from 2025", "share of promo-tagged lines whose promo_id has a promotion row, per year"); axes[0].set_ylim(0, 112); lib.kfmt(axes[0], pct=True)
axes[1].barh(basket.index, basket["mean"], color=[lib.AMBER if k not in ("no promo",) else lib.NAVY_SOFT for k in basket.index]); lib.finish(axes[1], "Flash and percent-off lift order value most", "average order value by promotion type, 2025 onward - the joinable window only"); axes[1].grid(axis="x"); axes[1].grid(False, axis="y")
for i, (v, n) in enumerate(zip(basket["mean"], basket["size"])): axes[1].text(v + 0.5, i, f"{v:.0f}  (n={n:,})", va="center", fontsize=8)
fig.tight_layout()
lib.save(fig, "a5_promo_types")
plt.show()

# %% [markdown]
# ## 6. The login funnel - on the two months that have logins
# Login -> viewed products -> added to cart -> purchased, by server group. Honest caveat: two
# months cannot show a trend or a season; this is a snapshot with the date on it.

# %%
lg["is_key"] = lg.server_id.isin(lib.KEY_SERVERS)
fun = lg.groupby("is_key").agg(logins=("customer_id", "size"), viewed=("viewed_products", lambda s: (s > 0).sum()), carted=("added_to_cart", "sum"), bought=("purchased", "sum"))
fun.index = ["other servers", "S07 + S08"]
fun_pct = fun.div(fun.logins, axis=0) * 100
fig, ax = plt.subplots(figsize=(10, 4.4))
stages = ["logins", "viewed", "carted", "bought"]; x = np.arange(4)
ax.bar(x - 0.2, fun_pct.loc["other servers", stages], 0.4, color=lib.NAVY, label="other servers")
ax.bar(x + 0.2, fun_pct.loc["S07 + S08", stages], 0.4, color=lib.AMBER, label="S07 + S08")
for i, s in enumerate(stages):
    ax.text(i - 0.2, fun_pct.loc["other servers", s] + 1, f"{fun_pct.loc['other servers', s]:.0f}%", ha="center", fontsize=9)
    ax.text(i + 0.2, fun_pct.loc["S07 + S08", s] + 1, f"{fun_pct.loc['S07 + S08', s]:.0f}%", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(stages); ax.legend(frameon=False, loc="upper right"); lib.kfmt(ax, pct=True); ax.set_ylim(0, 118)
lib.finish(ax, f"The key servers convert {fun_pct.loc['S07 + S08', 'bought']:.0f} percent of logins against {fun_pct.loc['other servers', 'bought']:.0f} elsewhere - on 69 days of data", f"login-to-purchase funnel, {lg.login_ts.min().date()} to {lg.login_ts.max().date()} only: a snapshot with a date on it, not a trend")
lib.save(fig, "a5_login_funnel")
plt.show()
canon["login_conv_key"] = round(float(fun_pct.loc["S07 + S08", "bought"]), 1); canon["login_conv_other"] = round(float(fun_pct.loc["other servers", "bought"]), 1)
canon["login_window_days"] = int((lg.login_ts.max() - lg.login_ts.min()).days + 1)
fun_pct.round(1)

# %% [markdown]
# ## 7. Customer growth accounting, whole platform
# Actives per month = new + retained + resurrected; the churned bar is what left. This is the
# customer-side identity every monthly review should open with.

# %%
cm = ident.groupby(["customer_id", "month"]).size().reset_index()[["customer_id", "month"]]
cm["prev"] = cm.groupby("customer_id").month.shift(); cm["first"] = cm.groupby("customer_id").month.transform("min")
cm["state"] = np.where(cm.month == cm["first"], "new", np.where((cm.month - cm.prev).map(lambda x: x.n if pd.notna(x) else 99) == 1, "retained", "resurrected"))
ga = cm.groupby(["month", "state"]).size().unstack(fill_value=0)
active_prev = cm.groupby("month").customer_id.nunique().shift(1).fillna(0)
ga["churned"] = -(active_prev - ga["retained"]).clip(lower=0)
ga = ga.loc["2020-06":]
fig, ax = plt.subplots(figsize=(13, 5))
bottom = np.zeros(len(ga))
for s, c in [("retained", lib.NAVY), ("resurrected", lib.NAVY_MID), ("new", lib.AMBER)]:
    ax.bar(ga.index.to_timestamp(), ga[s], bottom=bottom, width=24, color=c, label=s); bottom += ga[s].values
ax.bar(ga.index.to_timestamp(), ga["churned"], width=24, color=lib.FAINT, label="churned (active last month, not this)")
ax.axhline(0, color=lib.INK, lw=.8); ax.legend(ncol=4, fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.08)); lib.kfmt(ax)
lib.finish(ax, "Active customers grow, and churn grows with them", "monthly active identified customers: new + retained + resurrected above the axis, churned (active last month, not this) below")
lib.save(fig, "a5_customer_growth_accounting")
plt.show()

# %% [markdown]
# ## 9. Two decisions, one drop - which lever pulled it?
# March 2024 changed fulfilment cost; June 2024 cut the merchant-success team on the same servers.
# Split the key-server customers by whether their merchant survived to 2026. If the repeat-rate drop
# lives only among churned merchants, the June cut is the lever; if it shows in surviving merchants
# too, the customer experience itself changed.

# %%
mch = dims["merchant"].set_index("merchant_id")
surv = ident[ident.is_key].assign(merchant_alive=ident[ident.is_key].merchant_id.map(mch.churn_month == ""))
rows = []
for alive, lab in [(True, "merchant still active"), (False, "merchant later churned")]:
    r = lib.cohort_retention(surv[surv.merchant_alive == alive], "Q", 2)
    rr = r[[1, 2]].mean(axis=1) * 100
    for per, lab2 in [("2023Q1", "2023Q4"), ("2024Q4", "2025Q4")]:
        pass
    rows.append((lab, float(rr.loc["2023Q1":"2023Q4"].mean()), float(rr.loc["2024Q4":"2025Q4"].mean())))
conf = pd.DataFrame(rows, columns=["group", "cohorts 2023", "cohorts 2024Q4-2025Q4"]).set_index("group")
conf["drop (points)"] = conf["cohorts 2023"] - conf["cohorts 2024Q4-2025Q4"]
fig, ax = plt.subplots(figsize=(10, 4.2))
x = np.arange(2)
ax.bar(x - 0.2, conf["cohorts 2023"], 0.4, color=lib.NAVY_SOFT, label="cohorts acquired in 2023")
ax.bar(x + 0.2, conf["cohorts 2024Q4-2025Q4"], 0.4, color=lib.AMBER, label="cohorts acquired 2024Q4 to 2025Q4")
for i, (a, b) in enumerate(zip(conf["cohorts 2023"], conf["cohorts 2024Q4-2025Q4"])):
    ax.text(i - 0.2, a + 0.4, f"{a:.1f}", ha="center", fontsize=9); ax.text(i + 0.2, b + 0.4, f"{b:.1f}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(conf.index); ax.set_ylim(0, 36); ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False); ax.set_ylabel(""); lib.kfmt(ax, pct=True)
lib.finish(ax, "The drop appears whether the merchant stayed or left - the customer experience itself changed", "S07 + S08 customers by their merchant's fate; repeat rate in the two quarters after acquisition, 2023 cohorts versus 2024Q4-2025Q4 cohorts")
lib.save(fig, "a5_two_event_confound")
plt.show()
canon["confound_alive_2023"] = round(float(conf.iloc[0, 0]), 1); canon["confound_alive_late"] = round(float(conf.iloc[0, 1]), 1)
canon["confound_churned_2023"] = round(float(conf.iloc[1, 0]), 1); canon["confound_churned_late"] = round(float(conf.iloc[1, 1]), 1)
conf.round(1)

# %% [markdown]
# ## 8. The canon numbers the chairman pages quote
# Everything a page states as a number comes from this file, produced by this run.

# %%
srv_year = pd.read_csv(lib.REPORTS / "a2_server_year_summary.csv")
k = srv_year[srv_year.server_id.isin(lib.KEY_SERVERS)].groupby("year").agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
k["margin"] = k.profit / k.revenue * 100
canon["key_margin_2023"] = round(float(k.loc[2023, "margin"]), 1); canon["key_margin_2025"] = round(float(k.loc[2025, "margin"]), 1)
canon["key_revenue_2023_k"] = round(float(k.loc[2023, "revenue"] / 1e3)); canon["key_revenue_2024_k"] = round(float(k.loc[2024, "revenue"] / 1e3)); canon["key_revenue_2025_k"] = round(float(k.loc[2025, "revenue"] / 1e3))
canon["key_profit_2023_k"] = round(float(k.loc[2023, "profit"] / 1e3)); canon["key_profit_2025_k"] = round(float(k.loc[2025, "profit"] / 1e3))
bridge = pd.read_csv(lib.REPORTS / "a2_margin_bridge.csv", index_col=0)
canon["bridge_key_cost_k"] = round(float(bridge.loc["cost", "S07 + S08"] / 1e3)); canon["bridge_key_price_k"] = round(float(bridge.loc["price", "S07 + S08"] / 1e3)); canon["bridge_key_volume_k"] = round(float(bridge.loc["volume", "S07 + S08"] / 1e3)); canon["bridge_key_mix_k"] = round(float(bridge.loc["mix", "S07 + S08"] / 1e3))
canon["identified_customers"] = int(ident.customer_id.nunique()); canon["orders"] = int(txc.txn_id.nunique()); canon["merchants"] = int(dims["merchant"].shape[0]); canon["stores"] = int(dims["store"].shape[0])
canon["guest_share_2020"] = round(float((txc[txc.year == 2020].customer_id == "").mean() * 100), 1); canon["guest_share_2026"] = round(float((txc[txc.year == 2026].customer_id == "").mean() * 100), 1)
price = json.load(open(lib.REPORTS / "a2_price_of_decision.json")); canon.update({"price_" + k: v for k, v in price.items()})
lead = pd.read_csv(lib.REPORTS / "a4_leading_indicators.csv", index_col=0)
canon["lead_months_churned"] = round(float(lead.loc["churned", "months_to_first_sale"]), 1); canon["lead_months_active"] = round(float(lead.loc["still active", "months_to_first_sale"]), 1)
canon["lead_rev90_churned"] = round(float(lead.loc["churned", "first_90d_revenue"])); canon["lead_rev90_active"] = round(float(lead.loc["still active", "first_90d_revenue"]))
(lib.REPORTS / "canon.json").write_text(json.dumps(canon, indent=1))
pd.Series(canon)
