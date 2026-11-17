# Search log — PRISMA 2020 review for the open LED-matrix OCC benchmark paper

All searches were run on 2026-11-02 between 09:14 and 09:31 IST. Scripts: `search2.py` (per source); the first attempt (`search.py`, logs `*_attempt1*`) failed and is not used.

## Research questions (PICOC)
- **P (population):** optical camera communication (OCC) / image-sensor communication links, with LED, LED-array or LED-matrix transmitters.
- **I (intervention):** modulation schemes (LED-matrix spatial/hierarchical, IEEE 802.15.7 CSK), simulators, camera-channel models.
- **C (comparison):** other schemes or other simulators; experimental validation.
- **O (outcomes):** BER/SER, SNR, throughput; code availability; physics-grounded channel; statistical reporting.
- **C (context):** 2010–2026, peer-reviewed or archival technical reports.

RQ1: Which open, physics-grounded OCC simulators exist? RQ2: Do any of them benchmark several LED-matrix/CSK schemes under a common channel, with paired statistics? RQ3: Which camera-channel models and validation anchors are available? RQ4: How has 802.15.7 CSK been evaluated with camera receivers?

## Eligibility
Include: 2010–2026; camera/image-sensor receiver; contribution is a modulation scheme for LED/LED-array/LED-matrix transmitters, a simulator/framework, a camera-channel model, or a CSK evaluation.
Exclude: E1 outside 2010–2026; E2 no camera receiver (photodiode VLC/unrelated); E3 off-topic; E4 surveys (background only); E5 application/networking/localisation/security, or ML/DL detector or receiver-only contributions; E6 event-camera receivers (exception: Nguyen 2025 simulation framework, retained as a simulator); E7 not OCC, non-peer-reviewed or out of scope; E8 screen/display-to-camera (non-LED emitter); E9 single-link demo or receiver DSP without a scheme, simulator or channel-model contribution.

## Search strings and hits
OCC block = ("optical camera communication" OR "image sensor communication" OR "camera communication")

| Source | ID | String | Hits | Retrieved |
|---|---|---|---|---|
| OpenAlex (`search=`, 2010–2026) | S1 | OCC AND ("LED matrix" OR "LED array" OR "LED panel") AND modulation | 236 | 50 |
| OpenAlex | S2 | OCC AND (simulator OR "simulation framework" OR "simulation tool" OR benchmark OR reproducibility) | 475 | 50 |
| OpenAlex | S3 | OCC AND ("channel model" OR "system model") AND ("rolling shutter" OR blur OR noise OR "point spread function") | 369 | 50 |
| OpenAlex | S4 | ("color shift keying" OR "colour shift keying") AND (camera OR "image sensor") | 306 | 50 |
| Semantic Scholar bulk | S1 | "camera communication" + ("LED matrix" \| "LED array") + modulation | 16 | 16 |
| Semantic Scholar bulk | S2 | "camera communication" + (simulator \| simulation \| benchmark) | 94 | 50 |
| Semantic Scholar bulk | S3 | "camera communication" + "channel model" | 10 | 10 |
| Semantic Scholar bulk | S4 | "color shift keying" + (camera \| "image sensor") | 37 | 37 |
| Crossref (query.bibliographic, relevance-ranked, not Boolean) | S1 | same keywords | 2,289,472* | 50 |
| Crossref | S2 | same keywords | 3,145,035* | 50 |
| Crossref | S4 | same keywords | 1,353,614* | 50 |
| Crossref | S3 | — | failed (repeated HTTP 429) | 0 |

\*Crossref total-results counts match any keyword and are meaningless as hit counts. Only the top 50 relevance-ranked records were used.

**Total retrieved: 463** (OpenAlex 200, Semantic Scholar 113, Crossref 150).

## Sources not accessible
- **Scopus, Web of Science, IEEE Xplore:** not queried (no institutional access from this environment).
- **arXiv API:** HTTP 429 or timeouts on all four strings (both API and web fetch).
- **DBLP:** anti-bot interstitial page, so no results.
- **Google Scholar:** not used.

## Deduplication and screening
1. Within-source duplicates removed: 46, leaving 417 (OpenAlex 161, Crossref 149, S2 107).
2. Cross-source duplicates removed (DOI, then normalised title): 104, leaving **312 unique records**.
3. **Stage 1 (title/abstract, rule-based keyword rules, then spot-checked):** 122 excluded (E1 0, E2 59, E3 56, E4 7), leaving 190.
4. **Stage 2 (eligibility):** 190 assessed. Keyword-assisted classification by the reviewer, with manual decisions on inclusion. Full text was read only where it was open access: Moreno 2026 (MDPI), Narasimman 2024 (arXiv version), Matus 2019 (HAL) and Dong 2022 (open access). Gutiérrez 2025 is closed access, so its abstract and public GitHub repository were assessed instead. The other records were judged on title/abstract.
   - 147 excluded: E5 57 (30 application/networking/security, 27 ML/DL receiver-only); E6 4; E7 7; E8 22; E9 57.
   - 43 included. One of these is the OFC 2023 512-CSK paper, indexed under an Optica DOI and mapped to its Crossref/IEEE DOI.
5. **Other methods** (citation chasing of Moreno 2026 Table 1, the prior plan, and the HNCSM review): 12 records identified. 7 were excluded (5 photodiode-receiver simulators/CSK cited as background, E2; 2 surveys, E4) and 5 included (Li 2019, Liu 2022, Huang 2017, Le 2015, Ebihara 2015).
6. **Included in synthesis: 48** (see `extraction.csv`). Per-record decisions are in `screening_log.csv`.

## Caveats
- A single reviewer did the screening. Stage 1 was rule-assisted, so a second independent screener is recommended before submission.
- Retrieval was capped at 50 per OpenAlex/Crossref string, so the records cover the highest-relevance portion, not the full hit counts.
- Surveys and background works (Saeed 2019, Le 2017, Cahyadi 2020, Abdel-Hady 2026, Murata 2016, Georlette 2024, Aldalbahi 2017, Ullah 2021, Wei 2024, Monteiro 2014, Gutiérrez 2024) are cited but not extracted.
