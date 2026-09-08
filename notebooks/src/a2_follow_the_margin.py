# %% [markdown]
# # a2 - Follow the margin
# learn-ship-platform-diagnosis-with-phoebe - by Phoebe Fu
#
# Five years of transactions at the line grain. First the whole platform, then the same series per
# server, then the decomposition that names the mechanism behind the 2024 break on S07 and S08.
# Every chart is full history first; the lookback-window panel shows what a three-month view sees.

# %%
import sys, json
sys.path.insert(0, "../analysis")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, matplotlib.dates as mdates
import lib
lib.style()
tx = lib.load_transactions(dedupe=True)
events = lib.load_known_events()
complete = tx.month < pd.Period(lib.AS_OF, "M")          # the current month is partial - never chart it as a value
txc = tx[complete]
print(f"{len(tx):,} lines after dedupe; charting {txc.month.nunique()} complete months")

# %% [markdown]
# ## 1. The platform, whole
# Revenue, profit and margin per month with the team's known events overlaid. The overlay is the
# first thing a reader looks for when a line bends, so it is on every long series.

# %%
plat = lib.monthly(txc)
fig, axes = plt.subplots(2, 1, figsize=(13, 7.6), sharex=True, gridspec_kw={"height_ratios": [2, 1], "hspace": 0.42})
ax = axes[0]
ax.plot(plat.month_ts, plat.revenue / 1e3, color=lib.NAVY, lw=2)
ax.plot(plat.month_ts, plat.profit / 1e3, color=lib.AMBER, lw=2)
lib.label_end(ax, plat.month_ts.iloc[-1], plat.revenue.iloc[-1] / 1e3, "revenue", lib.NAVY)
lib.label_end(ax, plat.month_ts.iloc[-1], plat.profit.iloc[-1] / 1e3, "profit", lib.AMBER)
lib.kfmt(ax)
lib.finish(ax, "Blended, the platform looks healthy: revenue climbs, seasons repeat", "monthly revenue and profit in k, all ten servers, order-line grain, complete months only")
lib.annotate_events(ax, events, fig=fig)
ax2 = axes[1]
ax2.plot(plat.month_ts, plat.margin * 100, color=lib.NAVY_MID, lw=2)
ax2.set_ylabel(""); lib.finish(ax2, "The blend turns a thirteen-point cliff on two servers into a two-point drift", "blended margin %, all servers")
ax2.set_ylim(25, 50); lib.kfmt(ax2, pct=True); lib.story_band(ax2, None)
lib.save(fig, "a2_platform_monthly")
plt.show()

# %% [markdown]
# Blended, the platform looks healthy: revenue climbs, seasonality repeats, margin drifts down a
# few points from 2024. Blends hide. The next chart un-blends by server.

# %% [markdown]
# ## 2. The same series, one panel per server
# Key servers in amber. This is the chart that should have been on the wall since 2024.

# %%
srv = lib.monthly(txc, ["server_id"])
servers = sorted(srv.server_id.unique())
fig = plt.figure(figsize=(15, 6.4))
gs = fig.add_gridspec(2, 6, height_ratios=[1, 1], width_ratios=[2.2, 2.2, 1, 1, 1, 1], hspace=0.45, wspace=0.25)
big = {"S07": fig.add_subplot(gs[:, 0]), "S08": fig.add_subplot(gs[:, 1])}
others = [s for s in servers if s not in lib.KEY_SERVERS]
small = {s: fig.add_subplot(gs[i // 4, 2 + i % 4]) for i, s in enumerate(others)}
for s, ax in {**big, **small}.items():
    d = srv[srv.server_id == s]
    is_key = s in lib.KEY_SERVERS
    ax.plot(d.month_ts, d.margin * 100, color=lib.AMBER if is_key else lib.NAVY_SOFT, lw=2.2 if is_key else 1.2)
    ax.axvline(pd.Timestamp("2024-03-01"), color=lib.FAINT, ls="--", lw=1)
    ax.set_ylim(20, 50); ax.set_xlim(pd.Timestamp("2020-01-01"), pd.Timestamp("2026-09-01"))
    if is_key:
        ax.set_title(f"{s} - key server", loc="left", fontsize=12, fontweight="bold", color=lib.AMBER_INK)
        ax.set_yticks([20, 30, 40, 50]); lib.kfmt(ax, pct=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        pre = d[d.month < pd.Period("2024-03", "M")].margin.mean() * 100; post = d[d.month >= pd.Period("2024-03", "M")].margin.mean() * 100
        ax.text(pd.Timestamp("2021-06-01"), 47, f"{pre:.0f}% before", fontsize=9, color=lib.MUTED)
        ax.text(pd.Timestamp("2024-06-01"), 24, f"{post:.0f}% after", fontsize=9, color=lib.AMBER_INK, fontweight="bold")
    else:
        ax.set_title(s, loc="left", fontsize=9, color=lib.MUTED, pad=4); lib.mute(ax)
        ax.set_yticks([]); ax.set_xticks([])
        for sp in ax.spines.values(): sp.set_visible(False)
lib.finish_fig(fig, "The break lives on S07 and S08 only - the other eight servers never moved", "margin % per month, 2020-2026; the two key servers large, the eight others as small context on the same scale", top=0.80)
lib.save(fig, "a2_server_margin_grid")
plt.show()

# %% [markdown]
# ## 3. Volume held, margin fell
# The chairman's question in one picture: did we sell less? Orders and revenue on the key servers,
# indexed to the average of the six months before March 2024 = 100, against margin.

# %%
key = lib.monthly(txc[txc.is_key])
base = key[(key.month >= pd.Period("2023-09", "M")) & (key.month <= pd.Period("2024-02", "M"))]
idx = key[(key.month >= pd.Period("2023-03", "M")) & (key.month <= pd.Period("2025-02", "M"))].copy()
for c in ["orders", "revenue", "profit"]:
    idx[c + "_i"] = idx[c] / base[c].mean() * 100
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(idx.month_ts, idx.orders_i, color=lib.NAVY_SOFT, lw=2)
ax.plot(idx.month_ts, idx.revenue_i, color=lib.NAVY, lw=2)
ax.plot(idx.month_ts, idx.profit_i, color=lib.AMBER, lw=2.6)
ax.axhline(100, color=lib.FAINT, lw=1)
last = idx.iloc[-1]
lib.label_end(ax, last.month_ts, last.orders_i, "orders", lib.NAVY_SOFT); lib.label_end(ax, last.month_ts, last.revenue_i, "revenue", lib.NAVY, dx=0); lib.label_end(ax, last.month_ts, last.profit_i, "profit", lib.AMBER)
lib.story_band(ax)
lib.finish(ax, "Orders and revenue held; profit fell by a third in the same months", "S07 + S08, indexed to the Sep 2023 - Feb 2024 average = 100")
lib.save(fig, "a2_volume_held_margin_fell")
plt.show()
pre = key[(key.month >= pd.Period("2023-12", "M")) & (key.month <= pd.Period("2024-02", "M"))]
post = key[(key.month >= pd.Period("2024-04", "M")) & (key.month <= pd.Period("2024-06", "M"))]
summary = pd.DataFrame({"Dec23-Feb24": pre[["orders", "revenue", "profit"]].sum(), "Apr24-Jun24": post[["orders", "revenue", "profit"]].sum()})
summary.loc["margin %"] = [pre.profit.sum() / pre.revenue.sum() * 100, post.profit.sum() / post.revenue.sum() * 100]
summary["change %"] = (summary["Apr24-Jun24"] / summary["Dec23-Feb24"] - 1) * 100
summary.round(1)

# %% [markdown]
# ## 4. The lookback trap
# What the same S07 profit series looks like through a 3-month window, a 12-month window, and the
# full history, each drawn as of August 2024, five months after the break.

# %%
s07 = srv[srv.server_id == "S07"].set_index("month")
asof = pd.Period("2024-08", "M")
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, n, label in zip(axes, [3, 12, 60], ["last 3 months", "last 12 months", "full history"]):
    d = s07.loc[asof - n + 1: asof]
    ax.plot(d.month_ts, d.margin * 100, color=lib.AMBER, lw=2.2, marker="o" if n == 3 else None)
    ax.set_title(label, loc="left", fontsize=11, color=lib.MUTED); lib.kfmt(ax, pct=True)
    ax.set_ylim(20, 50)
    if n > 3:
        ax.axvline(pd.Timestamp("2024-03-01"), color=lib.FAINT, ls="--")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval={3: 1, 12: 2, 60: 12}[n]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y" if n < 60 else "%Y"))
lib.finish_fig(fig, "Three months reads as noise; sixty months reads as a decision", "the same S07 margin % series as of August 2024, five months after the break, through three lookback windows", y=1.0)
lib.save(fig, "a2_lookback_windows")
plt.show()

# %% [markdown]
# ## 5. Name the mechanism: the margin bridge
# Profit change between the six months before and the six months after the break, split into
# volume, price, cost and mix. Key servers versus the rest of the platform.

# %%
def slice_(d, a, b):
    return d[(d.month >= pd.Period(a, "M")) & (d.month <= pd.Period(b, "M"))]
bridges = {}
for name, d in [("S07 + S08", txc[txc.is_key]), ("other servers", txc[~txc.is_key])]:
    bridges[name] = lib.margin_bridge(slice_(d, "2023-09", "2024-02"), slice_(d, "2024-04", "2024-09"))
bridge = pd.DataFrame(bridges).round(0)
bridge.to_csv(lib.REPORTS / "a2_margin_bridge.csv")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, (name, b) in zip(axes, bridges.items()):
    steps = ["start", "volume", "price", "cost", "mix", "end"]
    vals = [b[s] for s in steps]
    cum = 0; bottoms = []; heights = []; colors = []
    for s, v in zip(steps, vals):
        if s in ("start", "end"):
            bottoms.append(0); heights.append(v); colors.append(lib.NAVY); cum = v
        else:
            bottoms.append(cum if v >= 0 else cum + v); heights.append(abs(v)); colors.append(lib.NAVY_SOFT if v >= 0 else lib.AMBER); cum += v
    ax.bar(steps, heights, bottom=bottoms, color=colors)
    for i, (s, v) in enumerate(zip(steps, vals)):
        ax.text(i, bottoms[i] + heights[i] + max(vals) * 0.01, f"{v/1e3:+.0f}k" if s not in ("start", "end") else f"{v/1e3:.0f}k", ha="center", fontsize=9)
    ax.set_title(name, loc="left", fontsize=11.5, fontweight="bold", color=lib.AMBER_INK if "S07" in name else lib.MUTED); lib.kfmt(ax)
    if "S07" in name:
        lib.callout(ax, (3, bottoms[3] + heights[3] / 2), "cost is the whole story:\nprice, volume and mix\nbarely register", (28, 55))
lib.finish_fig(fig, "On the key servers the entire profit change is cost; elsewhere cost did nothing", "profit bridge, six months before the break (Sep23-Feb24) to six months after (Apr24-Sep24), per-SKU price and cost effects", y=1.0)
lib.save(fig, "a2_margin_bridge")
plt.show()
bridge

# %% [markdown]
# Price did nothing, mix did little, volume was seasonal and similar on both groups. The cost term
# is the whole story on S07 and S08. That is a decision, not a market: someone changed what an
# order costs to fulfil. `known_events` has a candidate dated 2024-03-01.

# %% [markdown]
# ## 6. Change-point scan - let the data date the break
# Rolling z-score of the month-over-month margin change per server. A step shows as one large
# negative z followed by nothing.

# %%
piv = srv.pivot(index="month", columns="server_id", values="margin")
dz = piv.diff()
z = (dz - dz.rolling(12, min_periods=6).mean().shift(1)) / dz.rolling(12, min_periods=6).std().shift(1)
hits = z.stack().reset_index(); hits.columns = ["month", "server_id", "z"]
top = hits.sort_values("z").head(6)
top.to_csv(lib.REPORTS / "a2_changepoints.csv", index=False)
fig, ax = plt.subplots(figsize=(13, 4))
for s in servers:
    ax.plot(z.index.to_timestamp(), z[s], color=lib.AMBER if s in lib.KEY_SERVERS else lib.FAINT, lw=1.6 if s in lib.KEY_SERVERS else 1)
ax.axhline(-3, color=lib.RED, ls=":", lw=1)
lib.finish(ax, "The data dates the break to March 2024, on two servers, and fires nowhere else", "rolling z-score of month-over-month margin change, every server; amber = S07 and S08; dotted = -3 threshold")
lib.save(fig, "a2_changepoint")
plt.show()
top

# %% [markdown]
# The detector is validated on its nulls as much as its hits: eight servers with no decision produce
# no spike beyond noise. A detector that fires everywhere is a random number generator with a title.

# %% [markdown]
# ## 7. Seasonality, so nobody mistakes November for a strategy

# %%
plat["moy"] = plat.month.dt.month
seas = plat[plat.month.dt.year.between(2021, 2025)].groupby("moy").revenue.mean()
seas = seas / seas.mean() * 100
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.bar(seas.index, seas.values, color=[lib.AMBER if v > 120 else lib.NAVY for v in seas.values])
ax.axhline(100, color=lib.FAINT)
ax.set_xticks(range(1, 13)); ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
lib.finish(ax, "Q4 carries the year and February is the trough - November is not a strategy", "revenue by month of year, 2021-2025 average = 100")
lib.save(fig, "a2_seasonality")
plt.show()

# %% [markdown]
# ## 9. Price the decision
# Pre-shift margin (the twelve months to February 2024) applied to every month of post-shift revenue
# on S07 and S08. The gap between what profit would have been at the old margin and what it was is
# the running cost of the March 2024 decision - stated as an assumption, because the attribution is
# tested in a5, not here.

# %%
pre12 = key[(key.month >= pd.Period("2023-03", "M")) & (key.month <= pd.Period("2024-02", "M"))]
old_margin = pre12.profit.sum() / pre12.revenue.sum()
post = key[key.month >= pd.Period("2024-03", "M")].copy()
post["counterfactual"] = post.revenue * old_margin
post["gap"] = post.counterfactual - post.profit
post["cum_gap"] = post.gap.cumsum()
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [1.4, 1], "hspace": 0.35})
ax.fill_between(post.month_ts, post.profit / 1e3, post.counterfactual / 1e3, color=lib.AMBER_50)
ax.plot(post.month_ts, post.counterfactual / 1e3, color=lib.NAVY_SOFT, lw=2, ls="--")
ax.plot(post.month_ts, post.profit / 1e3, color=lib.AMBER, lw=2.2)
lib.label_end(ax, post.month_ts.iloc[-1], post.counterfactual.iloc[-1] / 1e3, f"at the old {old_margin*100:.0f}% margin", lib.NAVY_MID)
lib.label_end(ax, post.month_ts.iloc[-1], post.profit.iloc[-1] / 1e3, "actual profit", lib.AMBER_INK)
ax.set_ylabel("monthly profit, k"); lib.kfmt(ax)
lib.finish(ax, f"The March 2024 decision has cost {post.gap.sum()/1e3:.0f}k of profit so far, about {post.gap.mean()/1e3:.0f}k a month", f"S07 + S08 monthly profit against profit at the pre-shift margin, Mar 2024 to {post.month.max()}; attribution tested in a5")
ax2.plot(post.month_ts, post.cum_gap / 1e3, color=lib.INK, lw=1.8)
ax2.fill_between(post.month_ts, 0, post.cum_gap / 1e3, color=lib.NAVY_50)
lib.label_end(ax2, post.month_ts.iloc[-1], post.cum_gap.iloc[-1] / 1e3, f"{post.gap.sum()/1e3:.0f}k", lib.INK)
ax2.set_ylabel("cumulative gap, k"); lib.kfmt(ax2)
ax2.set_title("cumulative gap", loc="left", fontsize=10, color=lib.MUTED)
lib.save(fig, "a2_price_of_decision")
plt.show()
price = {"old_margin_pct": round(old_margin * 100, 1), "cum_gap_k": round(post.gap.sum() / 1e3), "months": int(len(post)), "avg_gap_per_month_k": round(post.gap.mean() / 1e3, 1)}
json.dump(price, open(lib.REPORTS / "a2_price_of_decision.json", "w"), indent=1)
price

# %% [markdown]
# ## 8. Export the series for the in-browser window widget
# The chairman page lets a reader drag the lookback window over the REAL monthly numbers below.
# Serialised with `json.dumps`, never string-built.

# %%
export = {}
for s in ["S07", "S08", "S03", "S01"]:
    d = srv[srv.server_id == s]
    export[s] = {"months": [str(m) for m in d.month], "revenue": [round(v) for v in d.revenue],
                 "profit": [round(v) for v in d.profit], "orders": [int(v) for v in d.orders],
                 "margin": [round(v * 100, 1) for v in d.margin]}
export["platform"] = {"months": [str(m) for m in plat.month], "revenue": [round(v) for v in plat.revenue],
                      "profit": [round(v) for v in plat.profit], "orders": [int(v) for v in plat.orders],
                      "margin": [round(v * 100, 1) for v in plat.margin]}
(lib.ROOT / "assets" / "diagnosis-data.js").write_text("window.DIAG_SERIES = " + json.dumps(export) + ";\n")
yr = txc.groupby(["server_id", "year"]).agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("txn_id", "nunique")).reset_index()
yr["margin"] = yr.profit / yr.revenue
yr.round(3).to_csv(lib.REPORTS / "a2_server_year_summary.csv", index=False)
print("wrote assets/diagnosis-data.js and reports/a2_server_year_summary.csv")
yr.pivot(index="server_id", columns="year", values="margin").round(3)
