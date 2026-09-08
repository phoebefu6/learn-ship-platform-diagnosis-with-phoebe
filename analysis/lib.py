"""Shared reader + helpers for every notebook in the course (one reader, one truth).

Every notebook imports from here. Nothing in notebooks/ parses a CSV on its own, so a schema
change lands in exactly one file.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
REPORTS = ROOT / "reports"
FIG.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

KEY_SERVERS = ["S07", "S08"]
AS_OF = pd.Timestamp("2026-09-07")  # last day of data; every "today" in the course is this date

# ---- the course palette (same navy/amber the pages use) ------------------------------------
NAVY, NAVY_DEEP, NAVY_MID, NAVY_SOFT, NAVY_50 = "#163E6A", "#0B2545", "#2A5C94", "#A9C1DE", "#E9F0F8"
AMBER, AMBER_INK, AMBER_50 = "#E39B0E", "#4A2E00", "#FDF1DA"
INK, MUTED, FAINT, HAIRLINE = "#14202E", "#5B6B7E", "#C3CEDB", "#E3E9F1"
RED = "#B91C1C"
SEQ = [NAVY, AMBER, NAVY_MID, "#6B8FB8", "#B8862B", NAVY_SOFT, MUTED, FAINT]  # categorical order


def server_color(sid: str) -> str:
    """Key servers are amber, everything else a navy shade - the whole course reads this way."""
    return AMBER if sid in KEY_SERVERS else NAVY_SOFT


def style() -> None:
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 300, "figure.facecolor": "white",
        "axes.facecolor": "white", "axes.edgecolor": FAINT, "axes.labelcolor": INK,
        "axes.titleweight": "bold", "axes.titlesize": 13, "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True,
        "axes.grid.axis": "y", "axes.axisbelow": True, "grid.color": HAIRLINE, "grid.linewidth": 0.7, "xtick.color": MUTED, "ytick.color": MUTED,
        "ytick.left": False, "xtick.major.size": 3, "axes.titlepad": 14, "legend.fontsize": 9,
        "text.color": INK, "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "legend.frameon": False, "axes.prop_cycle": mpl.cycler(color=SEQ),
    })


def save(fig: plt.Figure, name: str) -> Path:
    """Save PNG at 300 dpi into figures/. Returns the path (pages embed figures/<name>.png)."""
    out = FIG / f"{name}.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


# ---- readers --------------------------------------------------------------------------------
def load_transactions(dedupe: bool = False) -> pd.DataFrame:
    tx = pd.read_csv(DATA / "fact_transaction.csv.gz", parse_dates=["ts"],
                     dtype={"customer_id": "string", "promo_id": "string"})
    tx["customer_id"] = tx.customer_id.fillna("")
    tx["promo_id"] = tx.promo_id.fillna("")
    tx["month"] = tx.ts.dt.to_period("M")
    tx["year"] = tx.ts.dt.year
    tx["quarter"] = tx.ts.dt.to_period("Q")
    tx["is_key"] = tx.server_id.isin(KEY_SERVERS)
    if dedupe:
        tx = dedupe_lines(tx)
    return tx


def dedupe_lines(tx: pd.DataFrame) -> pd.DataFrame:
    """Exact duplicate order lines (same txn, sku, qty, price) are a load defect, not two sales."""
    key = ["txn_id", "sku_id", "qty", "unit_price", "unit_cost"]
    return tx.drop_duplicates(subset=key).copy()


def load_logins() -> pd.DataFrame:
    return pd.read_csv(DATA / "fact_login.csv.gz", parse_dates=["login_ts"])


def load_dims() -> dict[str, pd.DataFrame]:
    d = {n: pd.read_csv(DATA / f"dim_{n}.csv", dtype=str) for n in
         ["server", "merchant", "store", "customer", "product", "promotion"]}
    d["product"]["list_price"] = d["product"].list_price.astype(float)
    d["product"]["unit_cost"] = d["product"].unit_cost.astype(float)
    for c in ("merchant_id", "churn_month"):
        d["merchant"][c] = d["merchant"][c].fillna("")
    d["store"]["close_month"] = d["store"].close_month.fillna("")
    d["product"]["merchant_id"] = d["product"].merchant_id.fillna("")
    d["merchant"]["custom_share"] = d["merchant"].custom_share.astype(float)
    return d


def load_known_events() -> pd.DataFrame:
    e = pd.read_csv(DATA / "known_events.csv", parse_dates=["event_date"])
    return e.sort_values("event_date").reset_index(drop=True)


# ---- analysis helpers -----------------------------------------------------------------------
def monthly(tx: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """Revenue, cost, profit, margin, orders, active customers per month (and optional keys)."""
    keys = ["month"] + (by or [])
    g = tx.groupby(keys).agg(revenue=("revenue", "sum"), cost=("cost", "sum"), profit=("profit", "sum"),
                             orders=("txn_id", "nunique"), lines=("txn_id", "size"), units=("qty", "sum"),
                             customers=("customer_id", lambda s: s[s != ""].nunique())).reset_index()
    g["margin"] = g.profit / g.revenue
    g["aov"] = g.revenue / g.orders
    g["month_ts"] = g.month.dt.to_timestamp()
    return g


def cohort_retention(tx: pd.DataFrame, freq: str = "Q", horizon: int = 8) -> pd.DataFrame:
    """Forward-looking cohort retention with FROZEN history.

    A customer joins the cohort of their first order period. Retention at k = share of the cohort
    with any order in period first+k. A completed cell never restates; cells whose period has not
    fully elapsed by AS_OF are returned as NaN (never as a low number).
    """
    t = tx[tx.customer_id != ""][["customer_id", "ts"]].copy()
    t["p"] = t.ts.dt.to_period(freq)
    first = t.groupby("customer_id").p.min().rename("cohort")
    t = t.join(first, on="customer_id")
    t["k"] = (t.p - t.cohort).apply(lambda x: x.n)
    t = t[t.k <= horizon]
    size = first.value_counts().sort_index()
    mat = t.drop_duplicates(["customer_id", "k"]).groupby(["cohort", "k"]).customer_id.nunique().unstack(fill_value=0)
    mat = mat.reindex(columns=range(horizon + 1), fill_value=0)
    ret = mat.div(size, axis=0)
    last_complete = pd.Period(AS_OF, freq=freq) - 1  # the current period is partial
    for coh in ret.index:
        for k in ret.columns:
            if coh + k > last_complete:
                ret.loc[coh, k] = np.nan
    ret.index.name = "cohort"
    return ret


def margin_bridge(a: pd.DataFrame, b: pd.DataFrame) -> dict[str, float]:
    """Decompose profit change between two slices into volume, price, cost and mix.

    Per-SKU rate effects so that mix is a real term, not an algebraic zero:
      volume = (units_b - units_a) x average unit profit in a
      price  = sum over SKUs sold in both periods of (unit price_b - unit price_a) x units_b
      cost   = - sum over the same SKUs of (unit cost_b - unit cost_a) x units_b
      mix    = what is left: SKU composition shifts and SKUs sold in only one period
    """
    def per_sku(d: pd.DataFrame) -> pd.DataFrame:
        g = d.groupby("sku_id").agg(units=("qty", "sum"), revenue=("revenue", "sum"), cost=("cost", "sum"))
        g["p"] = g.revenue / g.units
        g["c"] = g.cost / g.units
        return g
    ga, gb = per_sku(a), per_sku(b)
    both = ga.index.intersection(gb.index)
    ua, ub = ga.units.sum(), gb.units.sum()
    prof_a, prof_b = a.profit.sum(), b.profit.sum()
    volume = (ub - ua) * (prof_a / ua)
    price = float(((gb.loc[both, "p"] - ga.loc[both, "p"]) * gb.loc[both, "units"]).sum())
    cost = -float(((gb.loc[both, "c"] - ga.loc[both, "c"]) * gb.loc[both, "units"]).sum())
    mix = (prof_b - prof_a) - (volume + price + cost)
    return {"start": prof_a, "volume": volume, "price": price, "cost": cost, "mix": mix, "end": prof_b}


def coverage(frames: dict[str, pd.DataFrame], date_cols: dict[str, str]) -> pd.DataFrame:
    """Rows per month per table - the data-availability heatmap input."""
    out = {}
    for name, df in frames.items():
        col = date_cols[name]
        m = pd.to_datetime(df[col]).dt.to_period("M")
        out[name] = m.value_counts().sort_index()
    cov = pd.DataFrame(out).fillna(0).astype(int)
    idx = pd.period_range("2020-01", AS_OF.to_period("M"), freq="M")
    return cov.reindex(idx, fill_value=0)


def pair_lift(tx: pd.DataFrame, level: str = "product_line", min_support: float = 0.002) -> pd.DataFrame:
    """Pairwise co-purchase support, confidence and lift at a product level (pandas only)."""
    b = tx[["txn_id", level]].drop_duplicates()
    n = b.txn_id.nunique()
    item_p = b[level].value_counts() / n
    m = b.merge(b, on="txn_id")
    m = m[m[f"{level}_x"] < m[f"{level}_y"]]
    pairs = m.groupby([f"{level}_x", f"{level}_y"]).txn_id.nunique().rename("n").reset_index()
    pairs["support"] = pairs.n / n
    pairs = pairs[pairs.support >= min_support]
    pairs["conf_x_to_y"] = pairs.support / pairs[f"{level}_x"].map(item_p)
    pairs["lift"] = pairs.support / (pairs[f"{level}_x"].map(item_p) * pairs[f"{level}_y"].map(item_p))
    return pairs.sort_values("lift", ascending=False).reset_index(drop=True)


def annotate_events(ax: plt.Axes, events: pd.DataFrame, scope_filter: str | None = None, fig: plt.Figure | None = None) -> None:
    """Known-events overlay: numbered markers on thin vertical lines, with the key printed under the
    figure. Captions never sit inside the plot, so they cannot collide with lines, legends or each other."""
    import textwrap
    ev = events if scope_filter is None else events[events.scope.str.contains(scope_filter) | (events.scope == "platform")]
    ev = ev.reset_index(drop=True)
    ymax = ax.get_ylim()[1]
    for i, r in enumerate(ev.itertuples()):
        c = AMBER if r.event_type == "business" else FAINT
        ax.axvline(r.event_date, color=c, lw=1, ls="--", alpha=.9)
        ax.text(r.event_date, ymax * (0.985 if i % 2 == 0 else 0.92), str(i + 1), fontsize=7.5,  # alternate heights so neighbours never touch color="white", ha="center", va="top", fontweight="bold",
                bbox=dict(boxstyle="circle,pad=0.25", fc=AMBER if r.event_type == "business" else MUTED, ec="none"))
    key = "   ".join(f"{i+1} {r.event_date.strftime('%Y-%m')} {r.description}" for i, r in enumerate(ev.itertuples()))
    f = fig or ax.figure
    f.text(0.01, -0.01, "\n".join(textwrap.wrap("Known events: " + key, 150)), fontsize=7.5, color=MUTED, va="top", ha="left")


def spread_labels(ys: list[float], min_gap: float) -> list[float]:
    """Push label y-positions apart so none sit closer than min_gap, preserving order. Returns new ys."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    out = list(ys)
    last = None
    for i in order:
        if last is not None and out[i] - last < min_gap:
            out[i] = last + min_gap
        last = out[i]
    return out


# ---- the visual grammar (one place, every chart) ------------------------------------------------
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker

CM_NAVY = mcolors.LinearSegmentedColormap.from_list("navy_seq", ["#FFFFFF", NAVY_50, NAVY_SOFT, NAVY_MID, NAVY, NAVY_DEEP])
CM_AMBER = mcolors.LinearSegmentedColormap.from_list("amber_seq", ["#FFFFFF", AMBER_50, "#F3C46A", AMBER, "#9A6A0A"])
STORY_START, STORY_END = pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-31")


def finish(ax: plt.Axes, title: str, sub: str | None = None) -> None:
    """Finding as the title, the what-and-grain as a muted subtitle underneath. Title = the message."""
    ax.set_title(title, loc="left", fontsize=13.5, fontweight="bold", color=INK, pad=22 if sub else 12)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5, color=MUTED, va="bottom", ha="left")


def finish_fig(fig: plt.Figure, title: str, sub: str | None = None, y: float | None = None, top: float = 0.86) -> None:
    """Figure-level finding title + subtitle. Owns the layout: panels are packed below `top` so the
    title can never collide with a panel title. Call it LAST; do not call tight_layout after it."""
    fig.tight_layout(rect=[0, 0, 1, top])
    fig.subplots_adjust(top=top - 0.02)  # gridspec figures ignore the rect; force the ceiling
    fig.text(0.01, 0.975, title, fontsize=14, fontweight="bold", color=INK, ha="left", va="top")
    if sub:
        fig.text(0.01, 0.975 - 0.045 * (6.4 / fig.get_size_inches()[1]), sub, fontsize=9.5, color=MUTED, ha="left", va="top")


def kfmt(ax: plt.Axes, axis: str = "y", pct: bool = False) -> None:
    """Axis ticks as 200k / 1.2M / 42%, never 200000."""
    def f(v, _):
        if pct:
            return f"{v:.0f}%" if abs(v - round(v)) < 0.05 else f"{v:.1f}%"
        a = abs(v)
        if a >= 1e6:
            return f"{v/1e6:.1f}M"
        if a >= 1e3:
            k = v / 1e3
            return f"{k:.0f}k" if abs(k - round(k)) < 0.05 else f"{k:.1f}k"
        return f"{v:.0f}"
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(mticker.FuncFormatter(f))


def story_band(ax: plt.Axes, label: str | None = "Mar 2024 decision", start=STORY_START, end=STORY_END) -> None:
    """The amber band every long time series carries at the decision month."""
    ax.axvspan(start, end, color=AMBER_50, zorder=0)
    ax.axvline(start, color=AMBER, lw=1, ls="--", alpha=.8)
    if label:
        ax.text(start, ax.get_ylim()[1], " " + label, fontsize=8, color=AMBER_INK, va="top", ha="left")


def label_end(ax: plt.Axes, x, y: float, text: str, color: str, dx: float = 0.0, fontsize: float = 9.5) -> None:
    """Direct label at the end of a line instead of a legend."""
    ax.annotate(text, (x, y), xytext=(6 + dx, 0), textcoords="offset points", va="center", ha="left",
                fontsize=fontsize, color=color, fontweight="bold", annotation_clip=False)


def callout(ax: plt.Axes, xy, text: str, xytext, color: str = AMBER_INK, fontsize: float = 9.5) -> None:
    """One annotated so-what per chart: text box with a thin arrow to the evidence."""
    ax.annotate(text, xy=xy, xytext=xytext, textcoords="offset points", fontsize=fontsize, color=color,
                ha="left", va="center", bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=FAINT, lw=0.8),
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=0, shrinkB=3))


def mute(ax: plt.Axes) -> None:
    """Context panel: smaller ticks, no title weight."""
    ax.tick_params(labelsize=7.5)
    ax.grid(False)
