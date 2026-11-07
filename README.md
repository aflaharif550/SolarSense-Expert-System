# ☀️ SolarSense — Solar & Backup Power Decision Expert System

SolarSense is a **rule-based expert system** that recommends the right solar setup for homes and shops in Pakistan.
It decides the system type (On-Grid / Hybrid / Off-Grid), panel count, inverter size, battery type and capacity,
net-billing advice, cost, payback and safety warnings, and **explains every decision** with the rules that fired.

Built for the *Introduction to Artificial Intelligence* course with **Python** and **Streamlit**.

**Live app:** `https://YOUR-APP-NAME.streamlit.app` ← replace with your deployed URL

## Key features

- **129 IF-THEN rules** in 10 knowledge modules (load, outages, site, system type, battery, inverter, net billing, finance, safety, verdict)
- **Forward-chaining inference engine** with salience-based conflict resolution, refraction and certainty factors
- **Explanation facility**: step-by-step reasoning chain, working memory and "rules not fired"
- **Knowledge-base browser** with search and CSV export
- 11 ready-made **sample profiles** for demos (together they fire every rule)
- Interactive charts, KPI dashboard and a downloadable HTML report

## Project structure

```
SolarSense/
├── app.py                     # Streamlit user interface (entry point)
├── requirements.txt           # Python libraries
├── .streamlit/config.toml     # Theme (solar amber + navy)
├── knowledge_base/rules.py    # Knowledge base: all IF-THEN rules
├── engine/inference.py        # Forward-chaining inference engine
├── engine/calculations.py     # Sizing, battery, cost and payback calculations
├── engine/report.py           # Downloadable HTML report
├── ui/                        # Styles, charts, Streamlit compatibility helpers
├── data/parameters.json       # Editable prices, sun hours, policy values
├── data/personas.json         # Sample profiles / test cases
├── tests/test_engine.py       # Automated tests (15 tests incl. rule coverage)
├── tools/export_rules.py      # Regenerates docs/Rule_Table.md and .csv
└── docs/                      # Rule table for the report and viva
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501. Full beginner instructions are in **SETUP_AND_DEPLOYMENT_GUIDE.md**.

## Run the tests

```bash
python -m unittest discover tests -v
```

## Updating prices or policy

Edit `data/parameters.json` (panel price, battery price, sun hours, export rate, etc.). No code changes are needed.

## Disclaimer

Prices, sun hours and policy values are indicative. Results support a decision but do not replace a site survey
by a certified installer.
