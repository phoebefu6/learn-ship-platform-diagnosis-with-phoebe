# Mentor roundtable - the five-year platform diagnosis plan

Run 2026-09-07 on `materials/analysis-plan.md` and the first executed pass of notebooks a1-a5.
Panel build 2026-09-04 (40 seats, 9 groups). Nine voices pulled from Data Craft, Enterprise,
Commercial & Risk, AI Frontier, Brand/Product and Leadership. Fidelity note: every position below is
the mentor's published method applied to this plan; nothing is an invented quote.

## The problem on the table

A B2B print-on-demand platform has five years of order lines and has only ever looked at the last
three months. A 2024 decision on two servers broke margin without moving volume, customers left two
quarters later, and the chairman wants to know what went right, what went wrong, and what to
collect so it cannot happen unseen again. The plan covers nine angles, three tracks of
recommendations, and ships as a course B2B clients can run on their own data.

## The conversation

**Cassie Kozyrkov (Kozyr):** Nine angles and I cannot find the decision in any of them. Before a
single chart goes upstairs, every angle gets a column called "what action changes if the answer is
X versus Y". If nothing changes, it is a museum exhibit, not analysis. And write down the default -
what the chairman does if the data says nothing - because that is what he is actually choosing
between.

**Cole Nussbaumer Knaflic (Storytelling with Data):** Agreeing with Cassie and pushing it into the
deck: one finding, one chart, one sentence in the title that is the finding. "Margin % by server"
is a label; "S07 and S08 lost thirteen margin points in March 2024 while selling the same volume" is
a title. Every chairman page ends in a call to action or it has not earned its slide.

**Aswath Damodaran (NYU Stern):** Let me put numbers on Cole's sentence. The plan describes the
break; it never prices it. Take the pre-shift margin, apply it to post-shift revenue, and the gap is
the cost of that decision per quarter - then the retention loss on top, at the old repeat rate. Name
the assumption doing the work while you do it: you are assuming the March cost change caused the
margin drop and not merely coincided with it.

**Adam Grant (Wharton):** That assumption is the one I would rethink first. The question "what went
wrong" presumes a wrong decision, but there were two decisions three months apart - the fulfilment
change in March and the merchant-success cut in June. The data show a retention drop; they do not
show which lever pulled it. Split the customers by whether their merchant survived. If the drop
lives only among churned merchants, it is the June cut, not the March cost.

**Hamel Husain (Parlance Labs):** Before anyone splits anything - has someone read fifty raw order
lines from S07 after March 2024? Look at your data. The `unit_cost` column carries the whole
story, so ask what it actually is: a live supplier cost, or an allocation somebody typed into a
table. And validate the change-point detector on a server where nothing happened. A detector that
only ever fires is not a detector.

**Zhamak Dehghani (Nextdata):** The availability gaps in section 8 are drawn as tech gaps. They are
ownership gaps. Who owns the promotion table as a product with a contract? Nobody, so it started
when a module launched. Who owns "what changed and when"? Nobody, so it lives in nine remembered
rows. Draw the ownership map first - platform domain, merchant domain, product domain - and the
event log becomes a product someone is accountable for, not a wish.

**Mark Roberge (Stage 2 / HBS):** Zhamak's ownership map gives you accountability; I want leading
indicators. Merchant churn in month 30 was visible in month 3 - time from onboarding to first sale,
and first-90-day revenue, predict survival. Section 6 measures the funeral. Measure the
readiness signals and the merchant-success team gets a list, not a eulogy. And the acquisition side
has no funnel data at all: how many merchants were pitched, trialled, onboarded? That is a
collection recommendation.

**Ayesha Khanna (Addo AI):** Every recommendation in section 5 needs an owner and a number or it
is pilot purgatory with better charts. "Bundle programme" - whose target, measured how, by when?
And the servers map to countries: VN, PH, ID. Fulfilment cost, delivery time and regulation differ
by market; the S07/S08 story may partly be a Vietnam story. Add the regional cut, and pair the
merchant-success recommendation with upskilling - the humans in that team were the retention
lever, and the data just proved it.

**Shreyas Doshi (ex-Stripe):** I will name the thing everyone here is circling. The three-month
lookback was not a dashboard failure; it was a strategy failure wearing a dashboard costume. The
company chose not to own long-horizon metrics, so nobody could see a step from a wobble. Run a
pre-mortem on the top three recommendations before shipping them: it is 2027, the event log exists
and nobody writes to it - why? The answer is the real recommendation.

**Cassie Kozyrkov (Kozyr):** Shreyas just gave you the decision column for section 5. Good. One
more: the customisation finding is the only one that points at growth rather than repair. Make
sure the chairman hears one thing that went right with the same rigour as the four things that
went wrong, or the room walks out defensive and nothing changes.

**Cole Nussbaumer Knaflic (Storytelling with Data):** Which means the storyline order matters:
open on what the three-month view hid, land the break, price it, then turn - "and here is what the
same data says we should double down on". The turn is where the call to action lives.

## Synthesis

**Consensus.** Add a decision to every angle. Price the 2024 break instead of describing it. Give
every recommendation an owner and a number. Treat the data gaps as ownership gaps and the event
log as a data product. Lead the chairman through a turn from repair to growth.

**Productive disagreement.** Damodaran wants the cost of the decision priced now; Grant says the
attribution is unproven and the two-event confound must be separated first. Both are right in
order: separate, then price what survives. Hamel sits between them - neither is worth doing until
someone has read the raw rows and knows what `unit_cost` means.

**The key insight.** The company's failure was not a missing chart. It chose a horizon that could
not tell a step from a wobble. Every recommendation that does not change who owns a long-horizon
metric is decoration.

## Angles added to the plan

| # | Angle | Method | Lands in |
|---|---|---|---|
| A | Decision column on all nine angles | what action changes; what is the default | analysis-plan section 3, c3 |
| B | Price of the 2024 decision | pre-shift margin on post-shift revenue, cumulative profit gap; retention loss at old repeat rate | a2 section 9, c2 |
| C | Two-event confound | repeat rate of customers whose merchant survived vs churned, key servers, 2024Q3+ cohorts | a5 section 9, c2 |
| D | Merchant leading indicators | months to first sale and first-90-day revenue versus survival | a4 section 8, c3 |
| E | Raw-row read and cost-field semantics | fifty lines from S07 after 2024-03; is unit_cost live or allocated | a2 section 5 prose, c3 data-to-collect |
| F | Detector validated on a null | the change-point z on a quiet server must not fire | a2 section 6 |
| G | Ownership map | table -> owning domain -> contract -> gap | analysis-plan section 1, c3 |
| H | Owner and number per recommendation | outcome, metric, owner, review date | c3 |
| I | Regional cut | server -> country; cost, delivery, regulation differ | a2 prose, data-to-collect |
| J | Pre-mortem on the top three recommendations | it is 2027 and it failed - why | c3 |
| K | One chart, one message, one call to action | chairman deck spec | c1, c2, c3 titles |
| L | The turn to growth | customisation and bundles carried with the same rigour as the breaks | c2 order |

## Actions

| Priority | Action | Timeline | Mentor source |
|---|---|---|---|
| 🔴 | Add the decision column and the default action to every angle | this build | Cassie |
| 🔴 | Split the retention drop by merchant survival before pricing it | this build | Grant, Damodaran |
| 🔴 | Price the decision: cumulative profit gap and retention loss | this build | Damodaran |
| 🔴 | Merchant time-to-first-sale and first-90-day revenue as leading indicators | this build | Roberge |
| 🟡 | Ownership map of every table; event log specified as a data product with an owner | c3 | Zhamak |
| 🟡 | Owner, metric and review date on every recommendation; pre-mortem on the top three | c3 | Ayesha, Shreyas |
| 🟡 | Chairman titles rewritten as findings; the storyline turns from repair to growth | c1-c3 | Cole |
| 🟢 | Regional cut and marketing-spend, funnel and fulfilment-cost collection | data-to-collect list | Ayesha, Roberge |
| 🔵 | Read fifty raw rows before trusting any cost story; validate every detector on a null | every engagement | Hamel |
