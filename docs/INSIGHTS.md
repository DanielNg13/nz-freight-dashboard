# NZ Container Freight Flows: Three Findings for Capacity Planners

**Daniel Nguyen** | Analysis of Ministry of Transport FIGS container data, Jan 2012 – Jun 2026
Data extracted 18 September 2026 | [GitHub](https://github.com/DanielNg13/nz-freight-dashboard)
---

## Why this analysis

New Zealand's container ports publish monthly volumes through the Freight Information
Gathering System. Anyone planning freight capacity — carriers, 3PLs, port operators —
needs to know two things from that data: how much volume swings within a normal year,
and how far the last five years have deviated from normal. This note answers both, and
flags one data-quality issue that would mislead anyone reading the headline numbers.

Every figure below traces to a named SQL query in the repository.

---

## Finding 1 — The pandemic was not New Zealand's container disruption. 2023–24 was.

On a consistent eight-port panel, rolling 12-month volume fell to **97.0% of its 2019
level by November 2020** and was back to 100% by **August 2021** — a 3% dip, recovered
in nine months.

The real contraction came later. The index fell to **90.6% in January 2024**, its lowest
point in the series, and did not regain its 2019 level until **January 2026** — a
**24-month recovery from a trough three times deeper than the pandemic's**.

**So what:** capacity plans anchored on "recovery from COVID" are anchored on the wrong
event. A carrier that sized its fleet against a 2021 rebound was carrying excess capacity
through the two worst years in the series. The planning-relevant shock in NZ container
freight is a 2023–24 demand contraction, not a 2020 supply shock.

*Source: `sql/04_disruption_index.sql`*

---

## Finding 2 — Regional export ports swing more than twice as hard as the main gateways.

Indexing each port's monthly volume against its own 2012–2019 average:

| Port | Peak month | Trough month | Peak-to-trough ratio |
|---|---|---|---|
| Napier | Mar — 143.3 | Sep — 68.6 | **2.09×** |
| Nelson | May — 149.6 | Nov — 71.7 | **2.09×** |
| PrimePort Timaru | Dec — 136.3 | Aug — 56.8 | **2.40×** |
| Port of Tauranga | Oct — 107.6 | Feb — 87.0 | 1.24× |
| Ports of Auckland | Oct — 107.4 | Mar — 89.0 | 1.21× |

Napier and Nelson move more than twice as many containers in their peak month as in
their trough. Auckland and Tauranga are close to flat by comparison.

**So what:** a single national seasonality assumption is wrong for half the network.
Fleet and labour planned against a national average will be roughly 40% short at Napier
in March and 30% over-provisioned there in September. Regional export ports need
seasonal capacity contracts; the main gateways can be planned on steady-state.

*Source: `sql/02_seasonal_index.sql`*

---

## Finding 3 — Empty container flows run in opposite directions at the two largest ports.

Share of container moves that are empty, 2024:

| Port | Empty share of imports | Empty share of exports |
|---|---|---|
| Napier | **65.1%** | 5.5% |
| Port of Tauranga | 48.0% | 13.5% |
| Ports of Auckland | 4.2% | **51.8%** |

Auckland's export empty share peaked at **69.3% in 2021**. Napier's import empty share
has exceeded 60% in every year since 2012.

**So what:** these are two different repositioning problems on one network. Auckland is
an import market that must ship boxes back out; Napier is an export gateway that must
bring boxes in. Every empty move consumes berth, yard and road capacity while earning no
freight revenue. The asymmetry is structural and predictable, which makes it the most
addressable cost in the system — and it means an inland empty-repositioning corridor
between Auckland and the export ports has a volume case behind it.

*Source: `sql/05_empty_imbalance.sql`*

---

## Data quality: the headline decline is not real

Ports of Auckland stopped reporting to FIGS after **June 2025**. National volume for the
first half of 2026 is **19.4% below** the same period in 2025 — but Auckland accounted
for 279,480 TEU of that 2025 base and contributes nothing to 2026.

Comparing only the eight ports that reported in both periods, the same months are
**up 6.7%**.

The pipeline detects this rather than assuming it: `dim_date` carries a `ports_reporting`
count computed from the data, and every trend measure is restricted to continuously
reporting ports. The dashboard shows the reporting count alongside the volume index so
the break is visible rather than smoothed over.

**Validation:** FIGS-derived Port of Tauranga volume for FY26 (Jul 2025 – Jun 2026) is
894,761 TEU against a published import/export figure of 924,105 TEU — a 3.2% difference,
consistent with FIGS's documented exclusion of transhipment and its ~2% annual
under-capture at wharf gates.

---

## Method

Raw FIGS extracts → pandas cleaning (`src/02_clean.py`) → SQLite star schema
(`src/03_load_sqlite.py`) → five analysis queries (`sql/`) → Power BI.
Raw files are never edited by hand; the full pipeline reruns from source in one command.

**Limitations:** FIGS excludes container movement by road and omits approximately 2% of
containers annually. Seasonal indices are baselined on 2012–2019 and may not hold if
trade patterns have structurally changed. Port share analysis is restricted to 2012–2024,
the last year with complete national coverage.

**Source:** Ministry of Transport, Freight Information Gathering System (FIGS) —
Containers. Extracted 18 September 2026.
