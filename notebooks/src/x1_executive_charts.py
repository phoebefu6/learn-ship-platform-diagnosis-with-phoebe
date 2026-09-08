# %% [markdown]
# # x1 - Executive charts for the chairman track
# learn-ship-platform-diagnosis-with-phoebe - by Phoebe Fu
#
# One message per chart, one series highlighted, the so-what written on the canvas. These are the
# figures the chairman pages carry; the analyst pages keep the fuller analyst versions. Every number
# is computed here from the same reader the analyst notebooks use.

# %%
import sys, json
sys.path.insert(0, "../analysis")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, matplotlib.dates as mdates
from lifelines import KaplanMeierFitter
import lib
lib.style()
plt.rcParams.update({"axes.titlesize": 15, "font.size": 11})
tx = lib.load_transactions(dedupe=True); dims = lib.load_dims(); lg = lib.load_logins(); events = lib.load_known_events()
txc = tx[tx.month < pd.Period(lib.AS_OF, "M")]
srv = lib.monthly(txc, ["server_id"]); key = lib.monthly(txc[txc.is_key]); plat = lib.monthly(txc)
GREY = lib.NAVY_SOFT
def big(figsize=(12.5, 5.6)):
    fig, ax = plt.subplots(figsize=figsize); ax.tick_params(labelsize=10.5); return fig, ax
print(f"{len(txc):,} lines")

# %% [markdown]
# ## x1 - what the quarterly review saw

# %%
s07 = srv[srv.server_id == "S07"].set_index("month"); asof = pd.Period("2024-08", "M")
fig, ax = big()
ax.plot(s07.month_ts, s07.margin * 100, color=lib.AMBER, lw=2.4)
win = s07.loc[asof - 2: asof]
ax.add_patch(plt.Rectangle((win.month_ts.iloc[0] - pd.Timedelta(days=12), 24), win.month_ts.iloc[-1] - win.month_ts.iloc[0] + pd.Timedelta(days=24), 10, fill=False, ec=lib.INK, lw=1.6, ls="--"))
lib.callout(ax, (win.month_ts.iloc[1], 34), "what the quarterly review saw:\n28%, 31%, 30% - \"stable\"", (-230, 70), color=lib.INK, fontsize=11)
pre = s07[s07.index < pd.Period("2024-03", "M")].margin.mean() * 100; post = s07[s07.index >= pd.Period("2024-03", "M")].margin.mean() * 100
ax.text(pd.Timestamp("2022-01-01"), 47.5, f"{pre:.0f}% for three years", fontsize=11.5, color=lib.MUTED)
ax.text(pd.Timestamp("2024-06-01"), 23, f"{post:.0f}% since March 2024", fontsize=11.5, color=lib.AMBER_INK, fontweight="bold")
ax.set_ylim(20, 52); lib.kfmt(ax, pct=True); ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
lib.finish(ax, "The same number, two horizons: the quarter said stable, the five years said a decision", "server S07 margin %, every month since launch; the dashed box is the three-month window reviewed in August 2024")
lib.save(fig, "x1_window_trap"); plt.show()

# %% [markdown]
# ## x2 - the break lives on two servers

# %%
fig, ax = big()
for s in sorted(srv.server_id.unique()):
    d = srv[srv.server_id == s]
    if s not in lib.KEY_SERVERS: ax.plot(d.month_ts, d.margin * 100, color=GREY, lw=1.1, alpha=.8)
ax.plot(key.month_ts, key.margin * 100, color=lib.AMBER, lw=2.8)
lib.label_end(ax, key.month_ts.iloc[-1], key.margin.iloc[-1] * 100, "S07 + S08", lib.AMBER_INK, fontsize=11)
oth = lib.monthly(txc[~txc.is_key]); lib.label_end(ax, oth.month_ts.iloc[-1], oth.margin.iloc[-1] * 100 + 1.2, "each other server", lib.MUTED, fontsize=10)
lib.story_band(ax, None); ax.set_ylim(20, 52); lib.kfmt(ax, pct=True)
lib.callout(ax, (pd.Timestamp("2024-03-15"), 36), "March 2024: thirteen margin\npoints gone in one month", (40, -40), fontsize=11)
lib.finish(ax, "Two of ten servers broke in March 2024; the other eight never moved", "margin % per month; amber = S07 and S08 combined, grey = each of the other eight servers")
lib.save(fig, "x2_break_two_servers"); plt.show()

# %% [markdown]
# ## x3 - volume held, profit fell

# %%
base = key[(key.month >= pd.Period("2023-09", "M")) & (key.month <= pd.Period("2024-02", "M"))]
idx = key[(key.month >= pd.Period("2023-06", "M")) & (key.month <= pd.Period("2025-02", "M"))].copy()
for c in ["orders", "revenue", "profit"]: idx[c + "_i"] = idx[c] / base[c].mean() * 100
fig, ax = big()
ax.plot(idx.month_ts, idx.orders_i, color=GREY, lw=2.2); ax.plot(idx.month_ts, idx.profit_i, color=lib.AMBER, lw=2.8)
ax.axhline(100, color=lib.FAINT, lw=1); lib.story_band(ax)
post = idx[(idx.month >= pd.Period("2024-04", "M")) & (idx.month <= pd.Period("2024-09", "M"))]
lib.label_end(ax, idx.month_ts.iloc[-1], idx.orders_i.iloc[-1], "orders", lib.MUTED, fontsize=11); lib.label_end(ax, idx.month_ts.iloc[-1], idx.profit_i.iloc[-1], "profit", lib.AMBER_INK, fontsize=11)
lib.callout(ax, (pd.Timestamp("2024-07-01"), post.profit_i.mean()), f"six months after: orders at {post.orders_i.mean():.0f},\nprofit at {post.profit_i.mean():.0f}", (30, 55), fontsize=11)
lib.finish(ax, "The business sold the same amount and kept a third less of it", "S07 + S08 orders and profit, indexed to the six months before the decision = 100")
lib.save(fig, "x3_volume_held_profit_fell"); plt.show()

# %% [markdown]
# ## x4 - the bridge, executive form

# %%
def slice_(d, a, b): return d[(d.month >= pd.Period(a, "M")) & (d.month <= pd.Period(b, "M"))]
b = lib.margin_bridge(slice_(txc[txc.is_key], "2023-09", "2024-02"), slice_(txc[txc.is_key], "2024-04", "2024-09"))
steps = ["start", "volume", "price", "cost", "mix", "end"]; vals = [b[s] for s in steps]
fig, ax = big((12.5, 5.8)); cum = 0; bottoms = []; heights = []
for s, v in zip(steps, vals):
    if s in ("start", "end"): bottoms.append(0); heights.append(v); cum = v
    else: bottoms.append(cum if v >= 0 else cum + v); heights.append(abs(v)); cum += v
colors = [lib.NAVY, GREY, GREY, lib.AMBER, GREY, lib.NAVY]
ax.bar(["profit before", "volume", "price", "cost", "mix", "profit after"], heights, bottom=bottoms, color=colors, width=0.62)
for i, (s, v) in enumerate(zip(steps, vals)):
    ax.text(i, bottoms[i] + heights[i] + max(vals) * 0.015, f"{v/1e3:+.0f}k" if s not in ("start", "end") else f"{v/1e3:.0f}k", ha="center", fontsize=12, fontweight="bold" if s == "cost" else "normal", color=lib.AMBER_INK if s == "cost" else lib.INK)
lib.kfmt(ax); ax.set_ylim(0, max(vals) * 1.18)
lib.callout(ax, (3, bottoms[3] + heights[3] / 2), "cost did all of it - price,\nvolume and mix are rounding", (40, 60), fontsize=11.5)
lib.finish(ax, "Of the profit lost, cost explains all of it", "S07 + S08 profit, six months before the March 2024 decision to six months after, split into what changed")
lib.save(fig, "x4_bridge_exec"); plt.show()

# %% [markdown]
# ## x5 - the running price

# %%
pre12 = key[(key.month >= pd.Period("2023-03", "M")) & (key.month <= pd.Period("2024-02", "M"))]; old_margin = pre12.profit.sum() / pre12.revenue.sum()
post = key[key.month >= pd.Period("2024-03", "M")].copy(); post["gap"] = post.revenue * old_margin - post.profit; post["cum"] = post.gap.cumsum()
fig, ax = big()
ax.fill_between(post.month_ts, 0, post.cum / 1e3, color=lib.AMBER_50); ax.plot(post.month_ts, post.cum / 1e3, color=lib.AMBER, lw=2.8)
for k in (100, 200):
    hit = post[post.cum >= k * 1e3].iloc[0]; ax.plot([hit.month_ts], [hit.cum / 1e3], "o", color=lib.AMBER_INK, ms=6); ax.text(hit.month_ts, hit.cum / 1e3 + 9, f"{k}k by {hit.month_ts:%b %Y}", fontsize=10.5, color=lib.AMBER_INK, ha="center")
lib.label_end(ax, post.month_ts.iloc[-1], post.cum.iloc[-1] / 1e3, f"{post.gap.sum()/1e3:.0f}k so far", lib.AMBER_INK, fontsize=12)
lib.kfmt(ax); ax.set_ylim(0, post.cum.max() / 1e3 * 1.15); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
lib.finish(ax, f"The decision costs about {post.gap.mean()/1e3:.0f}k of profit every month it stands", f"S07 + S08: profit at the pre-March-2024 margin ({old_margin*100:.0f}%) minus actual profit, accumulated since March 2024; assumes the cost change is the cause - tested in analyst session a5")
lib.save(fig, "x5_price_exec"); plt.show()

# %% [markdown]
# ## x6 - the lag

# %%
ident = txc[txc.customer_id != ""]
rk = lib.cohort_retention(ident[ident.is_key], "Q", 2)[[1, 2]].mean(axis=1).loc["2022Q1":] * 100
ro = lib.cohort_retention(ident[~ident.is_key], "Q", 2)[[1, 2]].mean(axis=1).loc["2022Q1":] * 100
fig, ax = big()
ax.plot(ro.index.to_timestamp(), ro.values, color=GREY, lw=2.2, marker="o", ms=4); ax.plot(rk.index.to_timestamp(), rk.values, color=lib.AMBER, lw=2.8, marker="o", ms=5)
lib.label_end(ax, ro.index[-1].to_timestamp(), ro.values[-1], "other servers", lib.MUTED, fontsize=11); lib.label_end(ax, rk.index[-1].to_timestamp(), rk.values[-1], "S07 + S08", lib.AMBER_INK, fontsize=11)
lib.story_band(ax, "Mar 2024 decision"); ax.set_ylim(0, 40); lib.kfmt(ax, pct=True)
before = rk.loc["2023Q1":"2023Q4"].mean(); after = rk.loc["2024Q4":].mean()
lib.callout(ax, (pd.Timestamp("2024-07-01"), float(rk.loc["2024Q3"])), f"customers acquired from 2024Q3 come back\nat {after:.0f}% instead of {before:.0f}% - the drop arrives\ntwo quarters after the decision", (-330, -90), fontsize=11)
lib.finish(ax, "Customers noticed two quarters later, and only on the two servers", "share of each quarter's new customers who ordered again within two quarters; completed cohorts only, guests excluded")
lib.save(fig, "x6_lag_exec"); plt.show()

# %% [markdown]
# ## x7 - merchants followed

# %%
m = dims["merchant"].copy(); m["onboard"] = pd.PeriodIndex(m.onboard_month, freq="M"); as_of_m = pd.Period(lib.AS_OF, "M")
m["end"] = np.where(m.churn_month != "", m.churn_month, str(as_of_m)); m["dur"] = (pd.PeriodIndex(m.end, freq="M") - m.onboard).map(lambda x: x.n).clip(lower=1); m["event"] = (m.churn_month != "").astype(int)
rows = []
for r in m[m.server_id.isin(lib.KEY_SERVERS)].itertuples():
    for k in range(r.dur): rows.append((str(r.onboard + k), 1 if (r.event and k == r.dur - 1) else 0))
hz = pd.DataFrame(rows, columns=["month", "churn"]); hz["month"] = pd.PeriodIndex(hz.month, freq="M")
hz["period"] = np.where(hz.month >= pd.Period("2024-06", "M"), "after", "before")
haz = hz.groupby("period").churn.mean().reindex(["before", "after"]) * 100
fig, ax = big((12.5, 3.9))
ax.barh(["after the June 2024\nmerchant-success cut", "before June 2024"], [haz["after"], haz["before"]], color=[lib.AMBER, GREY], height=0.55)
for y, v in zip([0, 1], [haz["after"], haz["before"]]):
    ax.text(v + 0.05, y, f"{v:.2f}% of merchants leave each month   =   one in {100/v:.0f}", va="center", fontsize=12, color=lib.AMBER_INK if y == 0 else lib.MUTED, fontweight="bold" if y == 0 else "normal")
ax.set_xlim(0, haz.max() * 1.9); ax.grid(False); ax.set_xticks([]); ax.tick_params(labelsize=11.5)
lib.finish(ax, "Merchants on the two servers now leave at twice the rate", "monthly churn hazard of S07 + S08 merchants, before and after June 2024, all merchant-months at risk")
lib.save(fig, "x7_merchants_exec"); plt.show()

# %% [markdown]
# ## x8 - customisation retains

# %%
mc = dims["merchant"].set_index("merchant_id").custom_share
ident2 = ident.assign(cs=ident.merchant_id.map(mc)); ident2["band"] = pd.cut(ident2.cs, [0, 0.25, 0.5, 1.0], labels=["merchants selling\nmostly standard goods", "mixed", "merchants selling\nmostly their own designs"])
def repeat12(d):
    r = lib.cohort_retention(d, "Q", 4).loc[:"2025Q2"]; return float(np.nanmean(r[[1, 2, 3, 4]].max(axis=1)) * 100)
band = pd.Series({b: repeat12(ident2[ident2.band == b]) for b in ident2.band.cat.categories})
fig, ax = big((12.5, 5.2))
ax.bar(band.index, band.values, color=[GREY, lib.NAVY_MID, lib.AMBER], width=0.6)
for i, v in enumerate(band.values): ax.text(i, v + 0.6, f"{v:.0f}%", ha="center", fontsize=14, fontweight="bold", color=lib.AMBER_INK if i == 2 else lib.INK)
ax.set_ylim(0, band.max() * 1.32); lib.kfmt(ax, pct=True); ax.tick_params(labelsize=11.5)
lib.callout(ax, (2, band.iloc[2] + 2.5), f"+{band.iloc[2]-band.iloc[0]:.0f} points of repeat purchase,\nand 8 points more margin per sale", (-330, 28), fontsize=11.5)
lib.finish(ax, "Customers of merchants who customise come back more - the growth lever the data already proves", "peak quarterly repeat rate within a year of acquisition, by how much of the merchant's sales are its own customised SKUs")
lib.save(fig, "x8_customisation_exec"); plt.show()

# %% [markdown]
# ## x9 - the bundles nobody sells (dumbbell)

# %%
bsk = txc[["txn_id", "product_line"]].drop_duplicates(); n = bsk.txn_id.nunique(); base_rate = bsk.product_line.value_counts() / n * 100
def attach(a, c):
    w = set(bsk[bsk.product_line == a].txn_id); return bsk[bsk.txn_id.isin(w) & (bsk.product_line == c)].txn_id.nunique() / len(w) * 100
combos = [("Mug", "T-shirt"), ("Poster", "Cushion"), ("Notebook", "Sticker pack"), ("Sticker pack", "Pen set"), ("Tote", "T-shirt")]
att = pd.DataFrame([(f"{a} + {c}", attach(a, c), base_rate[c]) for a, c in combos], columns=["pair", "attach", "base"]).sort_values("attach")
fig, ax = big((12.5, 5.2))
for i, r in enumerate(att.itertuples()):
    ax.plot([r.base, r.attach], [i, i], color=lib.FAINT, lw=3, zorder=1); ax.plot(r.base, i, "o", color=GREY, ms=11, zorder=2); ax.plot(r.attach, i, "o", color=lib.AMBER, ms=11, zorder=3)
    ax.text(r.attach + 0.4, i, f"{r.attach:.0f}%", va="center", fontsize=11.5, color=lib.AMBER_INK, fontweight="bold"); ax.text(r.base - 0.4, i, f"{r.base:.0f}%", va="center", ha="right", fontsize=10.5, color=lib.MUTED)
ax.set_yticks(range(len(att))); ax.set_yticklabels(att.pair, fontsize=11.5); ax.grid(False); ax.set_xlim(0, att.attach.max() * 1.25); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
lib.finish(ax, "Five bundles already happen in the basket and none is offered as one", "grey = how often the second item is in any basket; amber = how often it is there when the first item is; all orders 2020-2026")
lib.save(fig, "x9_bundles_exec"); plt.show()

# %% [markdown]
# ## x10 - what the data can and cannot answer

# %%
rows = [("orders, revenue, cost, profit", pd.Timestamp("2020-03-01"), lib.AS_OF, "answers every five-year question", lib.NAVY),
        ("who the customer was", pd.Timestamp("2020-03-01"), lib.AS_OF, "6 to 12 percent of lines are guests - blind spot grows", lib.NAVY_MID),
        ("promotions", pd.Timestamp("2025-01-01"), lib.AS_OF, "20 months; every earlier promo id points at nothing", lib.AMBER),
        ("logins and behaviour", lg.login_ts.min(), lg.login_ts.max(), "69 days; no trend, no season", lib.AMBER),
        ("what we changed and when", None, None, "nine remembered rows; there is no event log", lib.RED)]
fig, ax = big((12.5, 4.8))
for i, (name, a, b, verdict, c) in enumerate(rows[::-1]):
    if a is not None: ax.barh(i, (b - a).days, left=a, color=c, height=0.5)
    else:
        for e in events.event_date: ax.plot(e, i, "|", color=c, ms=16, mew=2.5)
    ax.text(pd.Timestamp("2026-10-15"), i, verdict, va="center", fontsize=10.5, color=c if c != lib.NAVY else lib.MUTED, fontweight="bold" if c in (lib.AMBER, lib.RED) else "normal")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=11.5); ax.grid(False)
ax.set_xlim(pd.Timestamp("2019-12-01"), pd.Timestamp("2029-06-01")); ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y")); ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2020, 2027)])
lib.finish(ax, "Three of the chairman's questions cannot be answered by any table the company keeps", "months each table covers, 2020 to today; the verdict for a five-year question at right")
lib.save(fig, "x10_gaps_exec"); plt.show()
print("executive set done")
