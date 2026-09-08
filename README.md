<!-- learn-with-phoebe hub banner -->
> ### 📚 Part of [**Learn with Phoebe**](https://phoebefu6.github.io/learn-with-phoebe/)
> The shelf of 105 free, hands-on courses on AI, data, and the craft around them. **[Browse every course ↗](https://phoebefu6.github.io/learn-with-phoebe/)**
<!-- /learn-with-phoebe hub banner -->

# learn-ship-platform-diagnosis-with-phoebe

A two-track interactive course on diagnosing a platform business from five years of its own data, by Phoebe Fu.

**Live site:** https://phoebefu6.github.io/learn-ship-platform-diagnosis-with-phoebe/

## The case

Printwell (fictional) is a B2B print-on-demand platform: it hosts merchants on ten regional servers, merchants open stores and onboard their own customers, customers buy the platform's standard goods or the merchant's customised versions. The company reviewed a rolling quarter for five years and never saw a thirteen-point margin break on two servers in March 2024, because revenue kept growing. Customers left two quarters later; merchants followed.

## Tracks

- **Chairman track (c1-c3)** - no code. The lookback trap on real monthly numbers (a live window widget), the platform anatomy and the grain question, the nine-angle diagnosis map with a decision on every row; the findings - the break, its price, the lag, the turn to what went right; and the decisions, each with an owner, a metric, a review date and a pre-mortem.
- **Analyst track (a1-a5)** - pandas build-alongs with an executed notebook per session. Data map and availability heatmap; the per-SKU margin bridge and change-point; products and baskets; merchant survival, store dormancy and leading indicators; frozen-history cohort retention, the two-event confound, promotions, the 69-day login funnel, and the canon numbers the chairman pages quote.

## Repo layout

- `courses/` - the 8 session pages (static HTML, no build step)
- `assets/lookback-live.js` + `assets/diagnosis-data.js` - the in-browser window widget over real monthly series exported by notebook a2
- `analysis/lib.py` - the one shared reader and helper module every notebook imports
- `analysis/nbgen.py` - builds and executes notebooks from `notebooks/src/*.py`; a failed run leaves no notebook behind
- `notebooks/` - 6 executed notebooks (a1-a5 analyst, x1 executive charts); `notebooks/src/` their cell-marked sources
- `data/generate_data.py` - seeded generator (rerun reproduces every CSV); the docstring lists the planted truths
- `figures/` - 48 charts at 300 dpi (38 analyst, 10 executive), embedded in the pages
- `reports/` - CSV and JSON outputs, including `canon.json` (every number a page states)
- `materials/analysis-plan.md` - the exploration plan and fact base; `materials/mentor-review.md` - the roundtable that added twelve angles; `materials/fanout-brief.md` - the page-authoring brief

## Reproduce

```bash
python3 data/generate_data.py
python3 analysis/nbgen.py --all
```

Part of [Learn with Phoebe](https://phoebefu6.github.io/learn-with-phoebe/).
