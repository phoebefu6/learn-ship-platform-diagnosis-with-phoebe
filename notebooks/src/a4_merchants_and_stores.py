# %% [markdown]
# # a4 - Merchants and stores
# learn-ship-platform-diagnosis-with-phoebe - by Phoebe Fu
#
# The platform's customers are merchants. Who was acquired when and where, who survived, which
# stores are actually active, how concentrated revenue is, and how each onboarding vintage matured.
# Survivorship and censoring are the traps here: a revenue chart of surviving merchants flatters.

# %%
import sys
sys.path.insert(0, "../analysis")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter
import lib
lib.style()
tx = lib.load_transactions(dedupe=True)
dims = lib.load_dims()
m = dims["merchant"].copy(); st = dims["store"].copy(); sv = dims["server"].set_index("server_id")
m["tier"] = m.server_id.map(sv.tier); m["onboard"] = pd.PeriodIndex(m.onboard_month, freq="M"); m["year"] = m.onboard.dt.year
m["is_key"] = m.server_id.isin(lib.KEY_SERVERS)
txc = tx[tx.month < pd.Period(lib.AS_OF, "M")]
print(f"{len(m)} merchants ({m.churn_month.ne('').sum()} churned) | {len(st)} stores | tiers: {m.tier.value_counts().to_dict()}")

# %% [markdown]
# ## 1. Acquisition: merchants onboarded per year, by server group

# %%
grp = np.where(m.is_key, "S07 + S08", "other servers")
acq = m.assign(grp=grp).groupby(["year", "grp"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(acq.index - 0.2, acq["other servers"], 0.4, color=lib.NAVY, label="other servers")
ax.bar(acq.index + 0.2, acq["S07 + S08"], 0.4, color=lib.AMBER, label="S07 + S08")
for x, v in zip(acq.index, acq["S07 + S08"]): ax.text(x + 0.2, v + 0.3, str(v), ha="center", fontsize=9)
lib.finish(ax, "The key servers were the 2021-2023 growth engine; acquisition stalled from 2024", "merchants onboarded per year, key servers versus the other eight"); ax.legend(frameon=False, loc="upper right")
lib.save(fig, "a4_merchant_acquisition")
plt.show()
acq

# %% [markdown]
# ## 2. Active merchants and growth accounting
# A merchant is active in a month if any of its stores transacted. New, churned and net per
# quarter - the merchant version of the growth-accounting identity.

# %%
act = txc.groupby(["month", "merchant_id"]).size().reset_index()[["month", "merchant_id"]]
act = act.merge(m[["merchant_id", "is_key"]], on="merchant_id")
active = act.groupby(["month", "is_key"]).merchant_id.nunique().unstack()
active.columns = ["other servers", "S07 + S08"]
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(active.index.to_timestamp(), active["other servers"], color=lib.NAVY, lw=2, label="other servers")
ax.plot(active.index.to_timestamp(), active["S07 + S08"], color=lib.AMBER, lw=2, label="S07 + S08")
ax.axvline(pd.Timestamp("2024-06-01"), color=lib.FAINT, ls="--")
lib.label_end(ax, active.index[-1].to_timestamp(), active["other servers"].iloc[-1], "other servers", lib.NAVY); lib.label_end(ax, active.index[-1].to_timestamp(), active["S07 + S08"].iloc[-1], "S07 + S08", lib.AMBER_INK)
lib.finish(ax, "Active merchants on the key servers peaked in early 2024 and have fallen since", "merchants with at least one order in the month")
lib.save(fig, "a4_active_merchants")
plt.show()

# %%
first = act.groupby("merchant_id").month.min(); last = act.groupby("merchant_id").month.max()
q = pd.period_range("2020Q1", "2026Q2", freq="Q")
rows = []
for grp_name, flag in [("S07 + S08", True), ("other servers", False)]:
    ids = m[m.is_key == flag].merchant_id
    for qq in q:
        f = first.reindex(ids).dropna(); l = last.reindex(ids).dropna()  # merchants that never sold have no first or last order
        new = (f.dt.asfreq("Q") == qq).sum()
        churned = (l.dt.asfreq("Q") == qq - 1).sum()  # last order in the previous quarter -> churned this quarter
        rows.append((qq, grp_name, new, -churned))
ga = pd.DataFrame(rows, columns=["quarter", "grp", "new", "churned"])
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2), sharey=True)
for ax, g in zip(axes, ["S07 + S08", "other servers"]):
    d = ga[ga.grp == g]
    x = d.quarter.dt.to_timestamp()
    ax.bar(x, d.new, width=70, color=lib.NAVY if g != "S07 + S08" else lib.AMBER, label="new merchants")
    ax.bar(x, d.churned, width=70, color=lib.FAINT, label="churned (last order in prior quarter)")
    ax.plot(x, (d.new + d.churned).cumsum() / 4, color=lib.INK, lw=1.2, ls=":", label="cumulative net / 4")
    ax.axhline(0, color=lib.INK, lw=.8); ax.set_title(g, loc="left", fontsize=11, color=lib.AMBER_INK if "S07" in g else lib.MUTED); ax.legend(fontsize=8, frameon=False, loc="upper left")
lib.finish_fig(fig, "From mid-2024 the key servers lose more merchants than they add", "new merchants above the axis, churned below (last order in the prior quarter), cumulative net dotted", y=1.0)
lib.save(fig, "a4_merchant_growth_accounting")
plt.show()

# %% [markdown]
# ## 3. Survival: how long does a merchant stay?
# Kaplan-Meier handles the merchants who are still here (censored) instead of dropping them.
# Two cuts: by server group, and key-server merchants before versus after the June 2024 change,
# measured as the hazard of leaving in any given month.

# %%
as_of_m = pd.Period(lib.AS_OF, "M")
m["end"] = np.where(m.churn_month != "", m.churn_month, str(as_of_m))
m["dur"] = (pd.PeriodIndex(m.end, freq="M") - m.onboard).map(lambda x: x.n).clip(lower=1)
m["event"] = (m.churn_month != "").astype(int)
kmf = KaplanMeierFitter()
fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
for flag, c, lab in [(False, lib.NAVY, "other servers"), (True, lib.AMBER, "S07 + S08")]:
    d = m[m.is_key == flag]
    kmf.fit(d.dur, d.event, label=f"{lab} (n={len(d)})").plot_survival_function(ax=axes[0], color=c, ci_alpha=.12)
lib.finish(axes[0], "Key-server merchants leave faster: a third gone by month 30", "Kaplan-Meier survival since onboarding, still-active merchants censored"); axes[0].set_xlabel("months since onboarding"); axes[0].set_ylim(0, 1); axes[0].legend(frameon=False)
# monthly churn hazard, key servers, before vs after 2024-06: merchants at risk each month
mm = []
for r in m[m.is_key].itertuples():
    for k in range(r.dur):
        per = r.onboard + k
        mm.append((str(per), 1 if (r.event and k == r.dur - 1) else 0))
hz = pd.DataFrame(mm, columns=["month", "churn"]); hz["month"] = pd.PeriodIndex(hz.month, freq="M")
hz["period"] = np.where(hz.month >= pd.Period("2024-06", "M"), "Jun 2024 onward", "before Jun 2024")
haz = hz.groupby("period").churn.agg(["sum", "count"]).reindex(["before Jun 2024", "Jun 2024 onward"]); haz["monthly hazard %"] = haz["sum"] / haz["count"] * 100
axes[1].bar(haz.index, haz["monthly hazard %"], color=[lib.NAVY_SOFT, lib.AMBER])
for i, v in enumerate(haz["monthly hazard %"]): axes[1].text(i, v + 0.05, f"{v:.2f}% / month", ha="center", fontsize=10)
axes[1].set_ylim(0, 3.0); lib.finish(axes[1], "The hazard doubled after the June 2024 merchant-success cut", "S07 + S08 merchants, monthly churn hazard, merchant-months at risk"); lib.kfmt(axes[1], pct=True)
fig.tight_layout()
lib.save(fig, "a4_survival_hazard")
plt.show()
haz.to_csv(lib.REPORTS / "a4_key_server_hazard.csv")
haz

# %% [markdown]
# ## 4. Stores that exist versus stores that sell
# Active store = at least one order in the trailing 90 days. The dimension table says a store exists
# until someone closes the record, and nobody closes records. The gap is dormancy plus dead stores
# still on the books - the earliest merchant-churn signal there is, and a store count nobody should trust.

# %%
st["open"] = pd.PeriodIndex(st.open_month, freq="M"); st["close"] = st.close_month.replace("", str(as_of_m)); st["close"] = pd.PeriodIndex(st.close, freq="M")
st["is_key"] = st.server_id.isin(lib.KEY_SERVERS)
months = pd.period_range("2020-06", as_of_m - 1, freq="M")
last_order = txc.groupby(["store_id", "month"]).size().reset_index()[["store_id", "month"]]
rows = []
for per in months:
    existing = st[(st.open <= per) & (st.close >= per)]
    recent = set(last_order[(last_order.month <= per) & (last_order.month >= per - 2)].store_id)
    for flag in [True, False]:
        e = existing[existing.is_key == flag]
        rows.append((per, "S07 + S08" if flag else "other servers", len(e), e.store_id.isin(recent).sum()))
dorm = pd.DataFrame(rows, columns=["month", "grp", "existing", "active"]); dorm["dormant %"] = (1 - dorm.active / dorm.existing) * 100
fig, axes = plt.subplots(1, 2, figsize=(14, 4.4), sharey=True)
for ax, g, c in zip(axes, ["S07 + S08", "other servers"], [lib.AMBER, lib.NAVY]):
    d = dorm[dorm.grp == g]
    ax.plot(d.month.dt.to_timestamp(), d.existing, color=lib.FAINT, lw=2, label="stores that exist")
    ax.plot(d.month.dt.to_timestamp(), d.active, color=c, lw=2, label="stores active (order in last 90 days)")
    ax.fill_between(d.month.dt.to_timestamp(), d.active, d.existing, color=lib.AMBER_50); ax.set_title(g, loc="left", fontsize=11, color=lib.AMBER_INK if "S07" in g else lib.MUTED); ax.legend(fontsize=9, frameon=False, loc="upper left")
lib.finish_fig(fig, "Stores on the books outnumber stores that sell - the dimension never closes a record", "stores that exist in dim_store versus stores with an order in the trailing 90 days; the shaded band is dormancy", y=1.0)
lib.save(fig, "a4_store_dormancy")
plt.show()
dorm[dorm.month.isin([pd.Period(x, "M") for x in ["2023-12", "2024-12", "2025-12", "2026-08"]])].round(1).pivot(index="month", columns="grp", values="dormant %")

# %% [markdown]
# ## 5. Concentration: who carries each server?
# Herfindahl index of merchant revenue per server per year, and the top-5 merchant share. High
# concentration is fragility; one merchant leaving is a server-level event.

# %%
mr = txc.groupby(["server_id", "year", "merchant_id"]).revenue.sum().reset_index()
def hhi(g):
    s = g.revenue / g.revenue.sum(); return pd.Series({"hhi": (s ** 2).sum() * 10000, "top5 share %": s.sort_values(ascending=False).head(5).sum() * 100, "merchants": len(s)})
conc = mr.groupby(["server_id", "year"]).apply(hhi).reset_index()
conc.round(1).to_csv(lib.REPORTS / "a4_concentration.csv", index=False)
piv = conc[conc.year == 2025].set_index("server_id")
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.bar(piv.index, piv["top5 share %"], color=[lib.server_color(s) for s in piv.index])
for s, v, n in zip(piv.index, piv["top5 share %"], piv.merchants): ax.text(s, v + 1, f"{v:.0f}%\n({int(n)} m)", ha="center", fontsize=8)
ax.set_ylim(0, 115); lib.finish(ax, "The smaller the server, the more one merchant matters", "share of 2025 server revenue carried by its five largest merchants; (n) = merchants on the server"); lib.kfmt(ax, pct=True)
lib.save(fig, "a4_concentration")
plt.show()

# %% [markdown]
# ## 6. Vintage curves: how each onboarding year matured
# Revenue per surviving-or-not merchant by months since onboarding (all merchants of the vintage in
# the denominator, so churn shows as decline rather than disappearing).

# %%
mrev = txc.groupby(["merchant_id", "month"]).revenue.sum().reset_index().merge(m[["merchant_id", "onboard", "year", "is_key"]], on="merchant_id")
mrev["k"] = (mrev.month - mrev.onboard).map(lambda x: x.n)
vint = mrev[mrev.k.between(0, 36)].groupby(["year", "k"]).revenue.sum().unstack(0)
n_by_year = m.groupby("year").size()
vint = vint.div(n_by_year, axis=1)
fig, ax = plt.subplots(figsize=(11, 5))
for i, y in enumerate([2020, 2021, 2022, 2023, 2024]):
    if y in vint: ax.plot(vint.index, vint[y].rolling(3, min_periods=1).mean(), lw=2, label=f"onboarded {y} (n={n_by_year[y]})", color=lib.SEQ[i])
ax.set_xlabel("months since onboarding"); ax.set_ylabel("monthly revenue per merchant of the vintage")
lib.finish(ax, "The 2021 and 2022 vintages carried the platform; later vintages matured lower", "monthly revenue per merchant of the onboarding year, all merchants of the vintage in the denominator, 3-month smoothing"); ax.legend(frameon=False, loc="upper left"); lib.kfmt(ax)
lib.save(fig, "a4_vintage_curves")
plt.show()

# %% [markdown]
# ## 7. Segment and vertical: where does a merchant-month earn most?

# %%
mm_rev = txc.groupby(["merchant_id", "month"]).revenue.sum().reset_index().merge(m[["merchant_id", "segment", "vertical"]], on="merchant_id")
seg = mm_rev.groupby("segment").revenue.mean().reindex(["SMB", "Mid", "Enterprise"])
ver = mm_rev.groupby("vertical").revenue.mean().sort_values()
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
axes[0].bar(seg.index, seg.values, color=lib.NAVY); lib.finish(axes[0], f"An enterprise merchant-month earns {seg['Enterprise']/seg['SMB']:.1f}x an SMB one", "average revenue per merchant-month by segment"); lib.kfmt(axes[0])
for i, v in enumerate(seg.values): axes[0].text(i, v * 1.02, f"{v:,.0f}", ha="center", fontsize=9, color=lib.MUTED)
axes[1].barh(ver.index, ver.values, color=lib.NAVY_MID); lib.finish(axes[1], f"{ver.index[-1].capitalize()} and {ver.index[-2]} merchants earn the most per month", "average revenue per merchant-month by vertical"); lib.kfmt(axes[1], axis="x"); axes[1].grid(axis="x")
fig.tight_layout()
lib.save(fig, "a4_segment_vertical")
plt.show()
pd.concat([seg.rename("per merchant-month"), ver.rename("per merchant-month")]).round(0)

# %% [markdown]
# ## 8. Leading indicators: the churn was visible in month three
# Months from onboarding to first sale, and revenue in the first 90 days, against whether the
# merchant later churned. Measured on merchants onboarded by 2023 so every one has had time to
# churn or not.

# %%
mo = txc.groupby("merchant_id").agg(first_sale=("month", "min")).join(m.set_index("merchant_id")[["onboard", "event", "year", "is_key"]])
mo["months_to_first_sale"] = (mo.first_sale - mo.onboard).map(lambda x: x.n)
r90 = txc.merge(m[["merchant_id", "onboard"]], on="merchant_id")
r90 = r90[(r90.month - r90.onboard).map(lambda x: x.n) <= 2].groupby("merchant_id").revenue.sum().rename("first_90d_revenue")
mo = mo.join(r90).fillna({"first_90d_revenue": 0})
never = m[(m.year <= 2023) & ~m.merchant_id.isin(mo.index)]
print(f"{len(never)} merchants onboarded by 2023 never recorded a sale - all {int(never.event.sum())} of them churned")
mature = mo[mo.year <= 2023].copy()
mature["outcome"] = np.where(mature.event == 1, "churned", "still active")
lead = mature.groupby("outcome").agg(merchants=("event", "size"), months_to_first_sale=("months_to_first_sale", "mean"), first_90d_revenue=("first_90d_revenue", "median"))
lead.to_csv(lib.REPORTS / "a4_leading_indicators.csv")
fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
for ax, col, title in zip(axes, ["months_to_first_sale", "first_90d_revenue"], ["Average months from onboarding to first sale", "Median revenue in the first 90 days after onboarding"]):
    ax.bar(lead.index, lead[col], color=[lib.AMBER, lib.NAVY])
    for i, v in enumerate(lead[col]): ax.text(i, v * 1.02, f"{v:,.0f}" if col != "months_to_first_sale" else f"{v:.1f}", ha="center", fontsize=10)
    ax.set_title(title, loc="left", fontsize=11, color=lib.MUTED)
lib.finish_fig(fig, "The churn was visible in month three: slow first sale, empty first quarter", "merchants onboarded by 2023, medians by eventual outcome", y=1.0)
lib.save(fig, "a4_leading_indicators")
plt.show()
lead.round(1)
