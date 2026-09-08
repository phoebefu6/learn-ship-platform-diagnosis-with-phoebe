# Fan-out brief - canon numbers and figure inventory

Every number a page states comes from here (reports/canon.json, produced by the executed notebooks). Never type a number that is not in this file or in the notebook outputs. Figures are embedded as `<img src="../figures/<name>">` inside `figure.zoomable` with a figcaption starting with the magnifier emoji.

## Canon numbers

- `repeat_key_2023` = 28.8
- `repeat_key_2025` = 17.2
- `repeat_other_2023` = 27.4
- `repeat_other_2025` = 26.8
- `median_days_to_second_order` = 118
- `share_second_within_180d` = 65.2
- `repeat_low_custom` = 28.1
- `repeat_high_custom` = 33.9
- `promo_first_basket` = 91.8
- `organic_first_basket` = 84.7
- `promo_repeat` = 63.4
- `organic_repeat` = 71.5
- `login_conv_key` = 16.8
- `login_conv_other` = 26.9
- `login_window_days` = 69
- `confound_alive_2023` = 29.2
- `confound_alive_late` = 17.7
- `confound_churned_2023` = 27.4
- `confound_churned_late` = 15.5
- `key_margin_2023` = 42.3
- `key_margin_2025` = 29.3
- `key_revenue_2023_k` = 686
- `key_revenue_2024_k` = 884
- `key_revenue_2025_k` = 765
- `key_profit_2023_k` = 290
- `key_profit_2025_k` = 224
- `bridge_key_cost_k` = -54
- `bridge_key_price_k` = 6
- `bridge_key_volume_k` = -18
- `bridge_key_mix_k` = 5
- `identified_customers` = 56908
- `orders` = 145640
- `merchants` = 140
- `stores` = 342
- `guest_share_2020` = 6.3
- `guest_share_2026` = 11.9
- `price_old_margin_pct` = 42.4
- `price_cum_gap_k` = 251
- `price_months` = 30
- `price_avg_gap_per_month_k` = 8.4
- `lead_months_churned` = 3.8
- `lead_months_active` = 1.3
- `lead_rev90_churned` = 0
- `lead_rev90_active` = 399

## Figures by notebook (embed the ones your page covers; every figure needs alt text that states the finding)

- figures/a1_coverage_heatmap.png
- figures/a1_duplicates_heatmap.png
- figures/a1_identity_gaps.png
- figures/a2_changepoint.png
- figures/a2_lookback_windows.png
- figures/a2_margin_bridge.png
- figures/a2_platform_monthly.png
- figures/a2_price_of_decision.png
- figures/a2_seasonality.png
- figures/a2_server_margin_grid.png
- figures/a2_volume_held_margin_fell.png
- figures/a3_attach_rates.png
- figures/a3_basket_size.png
- figures/a3_category_share.png
- figures/a3_line_slope.png
- figures/a3_merchant_preference.png
- figures/a3_owner_margin.png
- figures/a3_pair_lift.png
- figures/a3_pareto.png
- figures/a3_price_ladder.png
- figures/a4_active_merchants.png
- figures/a4_concentration.png
- figures/a4_leading_indicators.png
- figures/a4_merchant_acquisition.png
- figures/a4_merchant_growth_accounting.png
- figures/a4_segment_vertical.png
- figures/a4_store_dormancy.png
- figures/a4_survival_hazard.png
- figures/a4_vintage_curves.png
- figures/a5_cohort_triangles.png
- figures/a5_custom_share_retention.png
- figures/a5_customer_growth_accounting.png
- figures/a5_login_funnel.png
- figures/a5_promo_double_edge.png
- figures/a5_promo_types.png
- figures/a5_repeat_rate_lag.png
- figures/a5_time_to_second.png
- figures/a5_two_event_confound.png

## Widget

The lookback window widget: `<div class="lb" data-series="S07" data-asof="2024-08"></div>` with, before app.js, `<script src="../assets/diagnosis-data.js?v=1"></script><script src="../assets/lookback-live.js?v=1"></script>`. Series available: S07, S08, S03, S01, platform. Only c1 and a2 carry it.

## Planted truths (from data/generate_data.py docstring) - what the notebooks recover

- 2024-03: fulfilment shift on S07/S08 raises unit cost ~22 percent, prices and volumes unchanged; margin 42 to 29-30 percent.
- 2024-09: repeat-purchase propensity on S07/S08 falls (retention lag, two quarters after the cost break).
- 2024-06: merchant-success team cut on VN; merchant churn hazard on S07/S08 roughly doubles (1.26 to 2.39 percent per month).
- Customised merchant SKUs earn 8-10 margin points more; customers of high-customisation merchants repeat more.
- Category mix: drinkware and home spiked in 2020, stationery declining since 2023, bags rising.
- Baskets: mug + t-shirt, poster + cushion, notebook + sticker pack + pen set co-occur above chance (lift ~1.3-1.6); attach rates exceed base rates.
- Promo-acquired customers: bigger first basket, lower ever-repeat rate.
- Data quality: S02 duplicated ~3.4 percent of lines in 2021-H1; guest checkout 6 to 12 percent; ~65 percent of dead stores never closed in dim_store.
- Availability: logins only 2026-07-01 .. 2026-09-07 (69 days); dim_promotion from 2025-01; promo_id orphaned before that; no event log (9 remembered rows).
- Merchants that later churned took 3.8 months to first sale vs 1.3, median first-90-day revenue 0 vs 399.
- Two-event confound: repeat-rate drop appears in customers of surviving AND churned merchants (29.2 to 17.7 and 27.4 to 15.5), so the customer experience itself changed, not only merchant loss.
