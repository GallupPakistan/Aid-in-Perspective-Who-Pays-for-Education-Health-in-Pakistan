# Aid in Perspective: Who Pays for Education & Health in Pakistan

Interactive Streamlit dashboard comparing what **households**, the **government** and **international aid**
spend on education and health in Pakistan.

*Prepared by Gallup Pakistan · Digital Analytics · Draft for discussion · November 2026*

## Pages
Key findings · Who pays · Aid overview · 2025 aid cuts · Education aid · Health aid ·
Pipeline & priorities · Government spending · Household spending · Methodology

## Run it
```
pip install -r requirements.txt
streamlit run app.py
```

## Data sources
| Topic | Source |
|---|---|
| International aid | OECD Creditor Reporting System (CRS), 2015–2024; OECD DAC1 preliminary 2025 |
| Government education spending | Pakistan Institute of Education, *Public Financing in Education 2025-26* |
| Government health spending | Pakistan Economic Survey 2024-25 and 2025-26 (Finance Division) |
| Household spending | HIES 2018-19 and 2024-25 (Pakistan Bureau of Statistics) |
| Households, population | Census 2017 and 2023 (Pakistan Bureau of Statistics) |

Methods, assumptions and limitations are on the dashboard's **Methodology** page.
To update, replace a CSV with a newer one that has the same columns.
