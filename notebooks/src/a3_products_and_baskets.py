# %% [markdown]
# # a3 - Products and baskets
# learn-ship-platform-diagnosis-with-phoebe - by Phoebe Fu
#
# Category > product line > SKU, plus the owner axis (platform SKU vs merchant-customised SKU).
# What grew, what faded, where profit concentrates, and what sits together in a basket - the raw
# material for bundles, cross-sell and per-merchant customer preference.

# %%
import sys
sys.path.insert(0, "../analysis")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import lib
lib.style()
tx = lib.load_transactions(dedupe=True)
dims = lib.load_dims()
txc = tx[tx.month < pd.Period(lib.AS_OF, "M")]
full_years = txc[txc.year.between(2020, 2025)]
print(f"{len(txc):,} lines | {txc.sku_id.nunique():,} SKUs sold | {txc.product_line.nunique()} lines | {txc.category.nunique()} categories")

# %% [markdown]
# ## 1. Category mix by year
# Share of revenue, not absolute revenue: a share chart separates "we grew" from "we shifted".

# %%
share = full_years.groupby(["year", "category"]).revenue.sum().unstack()
share = share.div(share.sum(axis=1), axis=0) * 100
order = share.loc[2025].sort_values(ascending=False).index
fig, ax = plt.subplots(figsize=(11, 5))
ax.stackplot(share.index, [share[c] for c in order], labels=order, colors=lib.SEQ[:5], alpha=.95)
ax.set_xticks(share.index); ax.set_ylim(0, 100)
lib.finish(ax, "Bags rose, stationery faded; drinkware and home spiked in the lockdown year", "share of revenue by category, 2020-2025 complete years")
ax.legend(loc="upper center", ncol=5, fontsize=9, bbox_to_anchor=(0.5, -0.08), frameon=False); ax.grid(False); lib.kfmt(ax, pct=True)
lib.save(fig, "a3_category_share")
plt.show()
share.round(1)

# %% [markdown]
# ## 2. Product lines: 2021 versus 2025
# A slope chart per line. Lines that fell are amber.

# %%
ln = full_years[full_years.year.isin([2021, 2025])].groupby(["year", "product_line"]).revenue.sum().unstack(0)
ln = ln.div(ln.sum()) * 100
fig, ax = plt.subplots(figsize=(9, 8))
gap = 0.55
left_y = lib.spread_labels(list(ln[2021]), gap); right_y = lib.spread_labels(list(ln[2025]), gap)
for (line, r), ly, ry in zip(ln.iterrows(), left_y, right_y):
    c = lib.AMBER if r[2025] < r[2021] * 0.8 else lib.NAVY
    ax.plot([0, 1], [r[2021], r[2025]], color=c, lw=2, marker="o")
    ax.text(-0.04, ly, f"{line} {r[2021]:.1f}%", ha="right", va="center", fontsize=9, color=c)
    ax.text(1.04, ry, f"{r[2025]:.1f}% {line}", ha="left", va="center", fontsize=9, color=c)
ax.set_xticks([0, 1]); ax.set_xticklabels(["2021", "2025"]); ax.set_xlim(-0.75, 1.75)
lib.finish(ax, "Five product lines lost more than a fifth of their share", "share of revenue by product line, 2021 versus 2025; amber = fell by a fifth or more"); ax.set_yticks([])
ax.grid(False)
lib.save(fig, "a3_line_slope")
plt.show()

# %% [markdown]
# ## 3. Where profit concentrates: the SKU Pareto

# %%
sku = txc.groupby(["sku_id", "owner"]).agg(profit=("profit", "sum"), revenue=("revenue", "sum"), units=("qty", "sum")).reset_index()
sku = sku.sort_values("profit", ascending=False).reset_index(drop=True)
sku["cum_profit"] = sku.profit.cumsum() / sku.profit.sum() * 100
sku["cum_skus"] = (sku.index + 1) / len(sku) * 100
p80 = sku[sku.cum_profit >= 80].cum_skus.iloc[0]
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(sku.cum_skus, sku.cum_profit, color=lib.NAVY, lw=2.2)
ax.axhline(80, color=lib.FAINT, ls="--"); ax.axvline(p80, color=lib.AMBER, ls="--")
ax.text(p80 + 1, 40, f"{p80:.0f}% of SKUs\nmake 80% of profit", color=lib.AMBER_INK, fontsize=10)
ax.set_xlabel("% of SKUs, ranked by profit"); ax.set_ylabel("% of cumulative profit")
lib.finish(ax, f"{p80:.0f} percent of SKUs make 80 percent of profit", "cumulative profit share across every SKU sold, 2020-2026")
lib.save(fig, "a3_pareto")
plt.show()
sku.groupby("owner").agg(skus=("sku_id", "count"), profit=("profit", "sum"), revenue=("revenue", "sum")).assign(margin=lambda d: (d.profit / d.revenue).round(3), profit_share=lambda d: (d.profit / d.profit.sum()).round(3))

# %% [markdown]
# ## 4. Platform SKUs versus merchant-customised SKUs
# Margin by owner per year, and the customised share per server. Customisation is the platform's
# thesis; the data says whether the thesis pays.

# %%
own = full_years.groupby(["year", "owner"]).agg(revenue=("revenue", "sum"), profit=("profit", "sum")).reset_index()
own["margin"] = own.profit / own.revenue * 100
srv_share = txc.groupby(["server_id", "owner"]).revenue.sum().unstack(); srv_share = srv_share["merchant"] / srv_share.sum(axis=1) * 100
fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
for o, c in [("platform", lib.NAVY), ("merchant", lib.AMBER)]:
    d = own[own.owner == o]
    axes[0].plot(d.year, d.margin, color=c, lw=2.2, marker="o", label=f"{o} SKUs")
lib.finish(axes[0], "Customised SKUs earn about 8 margin points more, every year", "margin % by SKU owner, complete years"); axes[0].set_ylim(25, 55); lib.kfmt(axes[0], pct=True)
dl = own[own.year == own.year.max()]
for o, c in [("platform", lib.NAVY), ("merchant", lib.AMBER)]:
    r = dl[dl.owner == o].iloc[0]; lib.label_end(axes[0], r.year, r.margin, f"{o} SKUs", c)
axes[0].set_xticks(sorted(own.year.unique()))
axes[1].bar(srv_share.index, srv_share.values, color=[lib.server_color(s) for s in srv_share.index])
lib.finish(axes[1], "The key servers sell the most customised goods", "share of revenue on merchant-customised SKUs, per server"); lib.kfmt(axes[1], pct=True)
for s, v in srv_share.items(): axes[1].text(s, v + 1, f"{v:.0f}%", ha="center", fontsize=8.5, color=lib.MUTED)
lib.save(fig, "a3_owner_margin")
plt.show()

# %% [markdown]
# ## 5. Baskets: what sits together
# Pairwise co-purchase at the product-line level: support, confidence, lift. Lift above 1.5 with
# real support is a bundle candidate; lift on a handful of orders is noise.

# %%
pairs = lib.pair_lift(txc, "product_line", min_support=0.002)
pairs.to_csv(lib.REPORTS / "a3_bundle_candidates.csv", index=False)
lines = sorted(txc.product_line.unique())
mat = pd.DataFrame(1.0, index=lines, columns=lines)
for r in pairs.itertuples():
    mat.loc[r.product_line_x, r.product_line_y] = r.lift; mat.loc[r.product_line_y, r.product_line_x] = r.lift
fig, ax = plt.subplots(figsize=(9.5, 8))
im = ax.imshow(mat.values, cmap=lib.CM_NAVY, vmin=0.5, vmax=2.5)
ax.set_xticks(range(len(lines))); ax.set_xticklabels(lines, rotation=60, ha="right", fontsize=9)
ax.set_yticks(range(len(lines))); ax.set_yticklabels(lines, fontsize=9); ax.grid(False)
for i in range(len(lines)):
    for j in range(len(lines)):
        if i != j and mat.values[i, j] >= 1.5:
            ax.text(j, i, f"{mat.values[i, j]:.1f}", ha="center", va="center", fontsize=8, color="white" if mat.values[i, j] > 2 else lib.INK)
lib.finish(ax, "Three pairs sit in the same basket well above chance", "co-purchase lift between product lines, all orders; numbers shown where lift >= 1.5")
cb = fig.colorbar(im, ax=ax, shrink=0.5, pad=0.02); cb.set_label("lift", color=lib.MUTED); cb.outline.set_visible(False)
lib.save(fig, "a3_pair_lift")
plt.show()
pairs.head(8).round(3)

# %% [markdown]
# ## 6. Attach rate: the cross-sell offer in one bar
# Given a mug is in the basket, how often is a t-shirt? Against the base rate of t-shirts in any
# basket. The gap is the unsold bundle.

# %%
b = txc[["txn_id", "product_line"]].drop_duplicates()
n = b.txn_id.nunique()
base_rate = b.product_line.value_counts() / n * 100
def attach(a, c):
    with_a = set(b[b.product_line == a].txn_id)
    return b[b.txn_id.isin(with_a) & (b.product_line == c)].txn_id.nunique() / len(with_a) * 100
combos = [("Mug", "T-shirt"), ("Poster", "Cushion"), ("Notebook", "Sticker pack"), ("Sticker pack", "Pen set"), ("Tote", "T-shirt"), ("Hoodie", "Cap")]
att = pd.DataFrame([(f"{a}\n-> {c}", attach(a, c), base_rate[c]) for a, c in combos], columns=["pair", "attach %", "base rate %"])
fig, ax = plt.subplots(figsize=(11, 4.5))
x = np.arange(len(att))
ax.bar(x - 0.2, att["attach %"], 0.4, color=lib.AMBER, label="attach rate given the first item")
ax.bar(x + 0.2, att["base rate %"], 0.4, color=lib.NAVY_SOFT, label="base rate of the second item")
ax.set_xticks(x); ax.set_xticklabels(att.pair, fontsize=9)
lib.finish(ax, "Five of six bundle candidates beat their base rate, and none is sold as a bundle", "attach rate: share of orders holding the first item that also hold the second; base rate: share of all orders holding the second"); ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False); lib.kfmt(ax, pct=True)
for i, (a_, b_) in enumerate(zip(att["attach %"], att["base rate %"])):
    ax.text(i - 0.2, a_ + 0.3, f"{a_:.0f}", ha="center", fontsize=8.5, color=lib.AMBER_INK); ax.text(i + 0.2, b_ + 0.3, f"{b_:.0f}", ha="center", fontsize=8.5, color=lib.MUTED)
lib.save(fig, "a3_attach_rates")
plt.show()
att.assign(pair=att.pair.str.replace("\n", " ")).round(1)

# %% [markdown]
# ## 7. Basket size over time

# %%
bs = txc.groupby(["year", "txn_id"]).size().reset_index(name="lines")
dist = bs.groupby("year").lines.value_counts(normalize=True).unstack().fillna(0) * 100
dist = dist[[c for c in dist.columns if c <= 4]]
fig, ax = plt.subplots(figsize=(10, 4))
bottom = np.zeros(len(dist))
for c, col in zip(dist.columns, [lib.NAVY_SOFT, lib.NAVY_MID, lib.NAVY, lib.AMBER]):
    ax.bar(dist.index, dist[c], bottom=bottom, color=col, label=f"{c} line{'s' if c > 1 else ''}"); bottom += dist[c].values
lib.finish(ax, "Most baskets are a single line - the cross-sell headroom has not moved in six years", "orders by number of product lines, share per year"); ax.legend(ncol=4, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.1), frameon=False); lib.kfmt(ax, pct=True); ax.grid(False)
lib.save(fig, "a3_basket_size")
plt.show()

# %% [markdown]
# ## 8. Customer preference per merchant
# Every merchant has a top line and a breadth score (how spread its sales are across lines). This is
# the table a merchant success team hands to each merchant.

# %%
mp = txc.groupby(["merchant_id", "product_line"]).revenue.sum().unstack(fill_value=0)
shares = mp.div(mp.sum(axis=1), axis=0)
pref = pd.DataFrame({"top_line": shares.idxmax(axis=1), "top_line_share": shares.max(axis=1).round(3),
                     "breadth (effective lines)": np.exp(-(shares * np.log(shares.where(shares > 0, 1))).sum(axis=1)).round(2),
                     "revenue": mp.sum(axis=1).round(0)})
pref = pref.join(dims["merchant"].set_index("merchant_id")[["server_id", "segment", "vertical", "custom_share"]])
pref.sort_values("revenue", ascending=False).to_csv(lib.REPORTS / "a3_merchant_preference.csv")
fig, ax = plt.subplots(figsize=(10, 5))
ax.scatter(pref.custom_share, pref["breadth (effective lines)"], s=np.sqrt(pref.revenue) / 6 + 8, c=[lib.server_color(s) for s in pref.server_id], alpha=.75, edgecolor="white")
ax.set_xlabel("merchant customisation share (share of sales on own SKUs)"); ax.set_ylabel("breadth - effective number of lines sold")
lib.finish(ax, "Merchants that customise more sell a narrower range - the preference profile writes itself", "one bubble per merchant; size = revenue; amber = key servers; x = customisation share, y = effective number of lines sold")
lib.save(fig, "a3_merchant_preference")
plt.show()
pref.sort_values("revenue", ascending=False).head(10)

# %% [markdown]
# ## 9. Price ladder inside a line
# List price per SKU, platform versus merchant, for the three biggest lines. The ladder is the
# upsell path: where the rungs are missing, there is nothing to upsell to.

# %%
pr = dims["product"]
top_lines = txc.groupby("product_line").revenue.sum().sort_values(ascending=False).head(3).index
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=False)
for ax, l in zip(axes, top_lines):
    for o, c, off in [("platform", lib.NAVY, -0.15), ("merchant", lib.AMBER, 0.15)]:
        v = pr[(pr.product_line == l) & (pr.owner == o)].list_price
        ax.scatter(np.full(len(v), off) + np.random.default_rng(1).normal(0, 0.04, len(v)), v, s=14, color=c, alpha=.6, label=o)
    ax.set_xticks([-0.15, 0.15]); ax.set_xticklabels(["platform", "merchant"]); ax.set_title(l, loc="left", fontsize=11, color=lib.MUTED)
lib.finish_fig(fig, "Merchant SKUs sit one price rung above platform SKUs on every line - that rung is the upsell", "list price per SKU, platform versus merchant-customised, three biggest lines", y=1.0)
lib.save(fig, "a3_price_ladder")
plt.show()
