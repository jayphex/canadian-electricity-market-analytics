# Prince Edward Island electricity supply, 2016–2025

PEI generated more electricity locally in 2025 than in 2016, but electricity available for use grew much faster. Net receipts from other provinces accounted for most of the increase. Wind still dominated local generation, even as solar gained ground and the Hermanville/Clearspring wind farm experienced a marked decline and recovery.

## Electricity supply and interprovincial trade

Electricity available for use increased by 281,076 MWh (20.0%) between 2016 and 2025. Local generation increased by 31,392 MWh (5.2%), while net receipts increased by 249,684 MWh. Higher net receipts accounted for about 89% of the increase in available electricity.

| Calendar year | Local generation (MWh) | Gross receipts (MWh) | Deliveries (MWh) | Net receipts (MWh) | Available for use (MWh) | Net receipts share |
|---|---:|---:|---:|---:|---:|---:|
| 2016 | 602,584 | 1,080,223 | 274,205 | 806,018 | 1,408,602 | 57.2% |
| 2023 | 504,199 | 1,416,992 | 248,340 | 1,168,652 | 1,672,851 | 69.9% |
| 2025 | 633,976 | 1,367,062 | 311,360 | 1,055,702 | 1,689,678 | 62.5% |

Net receipts are gross receipts minus deliveries. They supplied more than half of PEI's electricity available for use in every year studied. The share peaked in 2023 and eased by 2025 as local generation recovered. [Statistics Canada, electricity supply and disposition](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2510001601)

## Wind generation and Hermanville/Clearspring

Calendar-year wind output fell from 596,542 MWh in 2021 to 498,010 MWh in 2023, then recovered to 578,080 MWh in 2025. To compare the province with Hermanville/Clearspring, the analysis sums monthly provincial wind output over the same April–March fiscal years as the farm's annual report. [Provincial generation data](../data/processed/provincial_history/provincial_generation_monthly_wide.csv) · [PEI Energy Corporation annual report](https://www.princeedwardisland.ca/en/publication/pei-energy-corporation-annual-report-2024-2025)

| Fiscal year | PEI wind (MWh) | Hermanville wind (MWh) | Hermanville turbine availability |
|---|---:|---:|---:|
| 2021/22 | 592,862 | 81,686 | 80.5% |
| 2022/23 | 506,761 | 39,750 | 58.2% |
| 2023/24 | 511,798 | 33,441 | 34.1% |
| 2024/25 | 548,196 | 71,472 | 71.8% |

Hermanville accounted for about 49% of the provincial decline from 2021/22 to 2022/23 (41,936 of 86,101 MWh). In 2024/25, the farm gained 38,031 MWh while estimated output across the rest of PEI fell by 1,633 MWh, yielding a provincial increase of 36,398 MWh.

PEI Energy Corporation reported improved output following major repairs in 2023 and 2024. It also documented a precautionary shutdown at Hermanville during the February 2023 polar vortex. The aligned totals measure the farm's contribution to provincial output changes. The annual data leave the individual effects of repairs, weather, and other operating conditions unquantified. [PEI Energy Corporation response to IRAC, questions 11 and 13](https://irac.pe.ca/wp-content/uploads/Exhibit-EC-11-PEIEC-Response-to-IRAC-Interrogatories-March-13-2026.pdf)

## Solar diversified local generation

Wind's share of local generation fell from 98.4% in 2016 to 91.2% in 2025. Solar output rose from zero to 48,684 MWh over the same period. The Summerside Sunbank solar farm and Slemon Park solar microgrid were announced in 2020, before Hermanville's sharp 2022/23 production decline. The announcements support interpreting the buildout as part of a broader clean-energy strategy. Slemon Park also included battery storage for peak load management. [Provincial annual generation data](../data/processed/provincial_history/provincial_generation_annual.csv) · [Summerside announcement](https://www.princeedwardisland.ca/en/news/summerside-to-benefit-from-a-new-solar-farm) · [Slemon Park announcement](https://www.canada.ca/en/housing-infrastructure-communities/news/2020/08/canada-and-prince-edward-island-work-together-to-benefit-from-new-solar-array.html) · [Slemon Park project objectives](https://natural-resources.canada.ca/funding-partnerships/slemon-park-microgrid-project)

## Reproduce the fiscal-year comparison

From the repository root, run:

```bash
python -m src.analyze_hermanville_wind
```

The script writes `data/processed/pei_balance/hermanville_wind_fiscal_comparison.csv` and includes only fiscal years with 12 valid monthly observations and a matching Hermanville record.
