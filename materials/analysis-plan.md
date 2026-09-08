# Analysis plan - five-year platform diagnosis (Printwell case)

Built 2026-09-07. This is the fact base every page in the course draws from and the exploration
plan a B2B client team can lift as-is. Figures cited on pages come from the notebooks in
`notebooks/` running on `data/` (seeded, reproducible). Numbers are re-derived from the executed
notebooks, never typed by hand.

## 1. The business and its data

**Printwell** (fictional) runs a print-on-demand merchandise platform. It acquires merchants;
merchants open stores and onboard their own customers; customers buy either the platform's standard
goods or the merchant's customised versions of the same lines.

Hierarchy: `platform > server > merchant > store > customer`. Product: `category > product line > SKU`,
with an `owner` axis (platform SKU vs merchant SKU).

| Table | Grain | Span in the case | Real-world analogue |
|---|---|---|---|
| fact_transaction | order line (txn x sku) | 2020-01 .. 2026-09-07 | order lines with cost attached |
| fact_login | login session | **2026-07-01 .. 2026-09-07 only** | app / web analytics export |
| dim_promotion | campaign | **2025-01 onward only**, but `promo_id` is stamped on transactions since 2020 | promo module launched late |
| dim_merchant / dim_store / dim_customer / dim_product / dim_server | entity | full | master data |
| known_events | dated event the team remembers | 9 rows, hand-written | there is no event log; this is the gap |

**Ownership map (added after the mentor round - a gap is an ownership gap before it is a tech gap).**

| Table | Owning domain | Contract it should expose | Gap today |
|---|---|---|---|
| fact_transaction | platform commerce | order line with cost attached, daily, immutable after close | cost is a unit constant, not the fulfilment cost actually paid |
| fact_login | platform product analytics | session events, retained 5 years | 60-day retention only; started 2026-07 |
| dim_promotion | merchant marketing (merchant promos) and platform marketing (platform promos) | promo_id resolvable for its whole life | started 2025-01; 2020-2024 ids orphaned |
| dim_customer | each merchant (their customer) | identity that survives guest checkout | 6 -> 12 percent guest lines with no id |
| dim_store / dim_merchant | platform merchant-success | open/close/status as events, not overwritten fields | dead stores never closed on the books |
| event log | platform engineering (releases, incidents) and the leadership team (decisions) | dated, scoped, owned events joined to the metric layer | does not exist; nine remembered rows |

Grain matters: revenue and cost live at the line, orders are `txn_id` distinct counts, customers are
`customer_id` distinct counts **excluding blanks** (guest checkout). Every notebook states its grain.

## 2. The chairman storyline (six acts)

1. **What we look at, and what it hides.** A three-month window sees noise; five years see the shape.
   The same S07 profit series under a 3-month, 12-month and 60-month lookback (the signature widget).
2. **The platform in one picture.** Scale, growth, mix by server, the key-server share.
3. **The break.** 2024: revenue flat, profit down on S07/S08. Decomposition names the mechanism
   (unit cost, not price, not volume, not mix).
4. **The lag.** Customer repeat rates on S07/S08 fall two quarters later; merchant churn rises; store
   dormancy climbs. One decision, three delayed symptoms.
5. **What went right.** Customisation retains; bundles exist and are unsold; bags rose while
   stationery faded; S03's playbook.
6. **What we cannot see, and what to collect.** The availability heatmap; the event log we owe
   ourselves; the identity gap; the decisions this enables.

## 3. Nine angles - the exploration plan

Each angle: the questions, the cuts, the charts, the method, the trap, the session that carries it.

| # | Angle | Questions | Cuts | Charts | Method | Trap | Session |
|---|---|---|---|---|---|---|---|
| 1 | Transactions | Trend of revenue, cost, profit, margin, orders, AOV, units? Where did the 2024 break happen and why? | month, server, year | small-multiples by server, indexed lines (2023=100), margin bridge waterfall, seasonal decomposition | full-history monthly series, price/cost/volume/mix bridge, change-point by rolling z-score on margin | reading a 3-month rolling window; blending pre/post shift months into one year | a2, c1, c2 |
| 2 | User behaviour | Login to purchase funnel, device mix, session depth, by server; how much of a 5-year question can 2 months answer? | server, device, week | funnel bars, daily login vs order overlay | funnel on the 2-month window with explicit caveat; proxy behaviour from order cadence for the years without logins | treating 2 months as representative; seasonality unknowable in 2 months | a5, c3 |
| 3 | Product hierarchy | Which categories, lines, SKUs grew or faded? Mix shift? Pareto of profit? Platform vs merchant SKUs? | category, line, sku, owner, year | stacked share area, Pareto curve, slope chart 2021 vs 2025, owner margin bars | share-of-revenue by year, cumulative profit share, margin by owner | mixing price changes with mix changes; long-tail SKUs hidden by category totals | a3, c2 |
| 4 | Merchant / store | Who are the merchants (segment, vertical, server)? Concentration? Store activity and dormancy? | segment, vertical, server, store | concentration curve (HHI), dormant-store share over time, merchant heatmap | active-store definition (order in last 90 days), HHI per server, merchant revenue rank stability | counting stores not active stores; top-merchant dependency hidden by totals | a4, c2 |
| 5 | Promotions | Does a promo lift the basket? Do promo-acquired customers come back? Which types work? | promo type, scope, first vs repeat order | basket-size boxplots, repeat-rate bars promo vs non-promo, orphan promo_id timeline | compare first-basket size and 12-month repeat by acquisition channel; join coverage of promo_id | attributing lift without a baseline; orphan promo ids before 2025 | a5, c2, c3 |
| 6 | Merchant / store acquisition and retention | Merchant onboarding by year and server; survival; churn hazard before and after 2024-06 on key servers | onboard year, server, segment | acquisition bars, Kaplan-Meier by server tier, vintage revenue curves | survival analysis (lifelines), merchant vintage cohorts, active merchant count with frozen history | survivorship (only surviving merchants in a revenue chart); censoring ignored | a4, c2 |
| 7 | Customer retention and activity | Quarterly cohort repeat rates by server, frozen history; repeat rate trend; time-to-second-order; per-merchant customer preference | cohort quarter, server, merchant custom share, acquisition channel | cohort triangle heatmap per server tier, retention curves pre vs post 2024-Q3 cohorts, repeat-rate line | forward-looking cohort retention with frozen history (immutable completed cells, partial cells blank) | trailing look-back retention that restates history; mixing guest orders in | a5, c1, c2 |
| 8 | Data availability | Which table covers which months? Which questions are unanswerable and until when? Quality defects (duplicates, blank ids, orphan keys) | table x month | coverage heatmap, defect table | row counts per table-month, key-integrity joins, exact-duplicate scan | assuming a table's history equals the business's history | a1, c3 |
| 9 | Other angles | Basket analysis (pair lift), bundle candidates, cross-sell and upsell paths, frequently-bought items per merchant, customer preference per merchant, seasonality per category, price ladder per line, store type performance, weekday and hour patterns, geography by server region | see each | lift matrix, bundle candidate table, calendar heatmap | pairwise support / confidence / lift in pandas | lift on tiny supports; confusing co-occurrence with causation | a3, a5, c2 |

### The decision column (added after the mentor round)

An angle without a decision is a museum exhibit. For each angle: what action changes with the answer,
and what the default is if the data says nothing.

| # | Angle | The decision it serves | Default if the data is silent |
|---|---|---|---|
| 1 | Transactions | Reverse, keep or re-price the 2024 fulfilment change on S07/S08; whether to review the same cost line elsewhere | keep the change |
| 2 | User behaviour | Where in the login-to-purchase path to spend product effort first; whether to fund login history | fund nothing |
| 3 | Product hierarchy | Which lines to expand, retire or re-price; whether to push merchant SKUs | keep the catalogue |
| 4 | Merchant / store | Which merchants get a success manager this quarter; whether to clean the store dimension | serve the loudest |
| 5 | Promotions | Whether acquisition promos continue at current depth; which types are allowed | keep running them |
| 6 | Merchant acquisition and retention | Which server tiers and verticals to acquire in; whether to restore the VN merchant-success team | acquire everywhere |
| 7 | Customer retention | Whether retention gets a target and an owner per server; which cohorts to win back | no target |
| 8 | Data availability | Which three collection gaps to close this quarter | close none |
| 9 | Other angles | Which bundles to launch; which merchants get a preference profile | none |

## 4. Methodology laws (the professional norm, with reasons)

- **Full history first, then window.** Any metric shown in a window is first shown over the
  entire history, because a window cannot distinguish a step from noise.
- **Decompose before you narrate.** Profit change = volume + price + cost + mix. Name the term
  before naming a cause.
- **Cohort retention is forward-looking with frozen history.** A completed cohort cell never
  restates; the current partial cell is shown blank and labelled. Trailing look-back retention
  restates history every day and is never used for reporting.
- **Overlay what you know.** Every long series carries the known-events lines. The team's
  memory is data too; the gap is that it is not stored.
- **Say the grain.** Line, order, customer, merchant, store: every chart title states which.
- **Count active, not existing.** A store or merchant is active if it transacted in the last 90
  days; existence in a dimension table is not activity.
- **Availability before analysis.** Coverage heatmap first; a question a table cannot answer is
  filed as a data-collection recommendation, not silently dropped.

## 5. Recommendations framework (what c3 ships)

**Business.** Merchant acquisition strategy by server tier and vertical (where retention is
earned); customisation as the retention lever (push merchant SKUs); bundle and cross-sell
programme from measured lift (mug + t-shirt, poster + cushion, notebook set); upsell ladder
inside lines; product diversification (bags up, stationery down - reallocate); per-merchant
customer preference profiles handed to merchants; promo policy (acquisition promos buy baskets,
not customers); S07/S08 unit-economics review of the 2024 fulfilment decision.

**Tech.** A **release and incident event log** (deploy, outage, checkout change, pricing change)
with timestamp, scope (server / merchant), owner, joined to the metric layer; **business decision
log** the same way; guest-checkout identity (hash of email or phone) so retention includes
guests; login history retained beyond 60 days; promo_id resolvable for its whole life; duplicate
guard on order ingestion; a metric layer that computes cohorts with frozen history so no team
restates numbers.

**Data to collect.** Login and session events for all years going forward; product views and
cart events; fulfilment cost per order (shipping, supplier, returns) so cost is not a unit
constant; delivery time and returns; customer satisfaction or support tickets; merchant health
signals (logins, catalogue edits, campaign activity); marketing spend by channel and server;
competitor price references per line.

### Owner, number, review date (every recommendation ships with all three)

A recommendation without an owner and a metric is pilot purgatory with better charts. c3 carries a
table: recommendation, outcome metric, owner role, first review date, and a one-line pre-mortem
("it is 2027 and this failed - why"). The pre-mortem answer is usually the real recommendation: an
event log nobody writes to fails because writing to it is nobody's job; the fix is a release-gate
field, not a wiki page.

## 6. Session map

| Session | Title | Carries angles | Notebook | Key figures |
|---|---|---|---|---|
| c1 | Five years in one picture | 1, 7 (widget), storyline | - | window widget, platform anatomy |
| c2 | What went right, what went wrong | 1, 3, 4, 5, 6, 7, 9 | - | findings gallery from a2-a5 |
| c3 | Decisions and the data we owe ourselves | 2, 5, 8 + recommendations | - | availability heatmap, priority matrix |
| a1 | Map the data before you read it | 8, G, entity model, quality | a1_data_map.ipynb | coverage heatmap, defect table, join graph |
| a2 | Follow the margin | 1, B, F | a2_follow_the_margin.ipynb | server small multiples, bridge waterfall, change-point, price of the decision |
| a3 | Products and baskets | 3, 9 | a3_products_and_baskets.ipynb | share area, Pareto, lift matrix, bundle table |
| a4 | Merchants and stores | 4, 6, D | a4_merchants_and_stores.ipynb | acquisition, Kaplan-Meier, dormancy, HHI, leading indicators |
| a5 | Customers, promotions and the gaps | 2, 5, 7, C | a5_customers_promotions_gaps.ipynb | cohort triangles, repeat-rate lag, two-event confound, promo comparison, funnel |

Letters refer to the angles added by the mentor round in `materials/mentor-review.md`.

## 7. Not covered by design

Causal attribution of the 2024 decision (no counterfactual server); forecasting; customer-level
churn prediction (taught in learn-customer-retention-with-phoebe a7); real Printwell data (the case
is synthetic with planted truths listed in `data/generate_data.py`).
