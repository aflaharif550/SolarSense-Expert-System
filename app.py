"""
SolarSense - Residential Solar & Backup Power Decision Expert System
Streamlit user interface (run with:  streamlit run app.py)
"""

import json
import os

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SolarSense | Solar Decision Expert System",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from engine.calculations import CALCULATIONS, load_parameters  # noqa: E402
from engine.inference import InferenceEngine, describe_actions, describe_condition  # noqa: E402
from engine.report import build_html_report  # noqa: E402
from knowledge_base.rules import MODULES, RULES  # noqa: E402
from ui import charts, styles  # noqa: E402
from ui.compat import show_chart, show_table  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# Data and engine
# --------------------------------------------------------------------------
PARAMS = load_parameters()
ENGINE = InferenceEngine(RULES, CALCULATIONS, PARAMS)

with open(os.path.join(BASE_DIR, "data", "personas.json"), "r", encoding="utf-8") as _fh:
    PERSONAS = json.load(_fh)

APPLIANCES = list(PARAMS["appliances"].keys())
CITIES = list(PARAMS["cities"].keys())

OPTIONS = {
    "property_type": ["House", "Apartment / Flat", "Shop / Commercial", "Farmhouse / Rural"],
    "phase": ["Single-phase", "Three-phase"],
    "grid_status": ["Grid with load-shedding", "Reliable grid", "No grid connection"],
    "existing_backup": ["None", "UPS / Inverter", "Generator"],
    "roof_type": ["RCC concrete roof", "Metal / tin sheet roof", "Ground / open space", "No usable space"],
    "shading": ["No shading", "Partial shading", "Heavy shading"],
    "orientation": ["South-facing / flat roof", "East-West", "North-facing"],
    "ownership": ["Owner", "Tenant"],
    "priority": ["Balanced", "Maximum bill savings", "Reliable backup power", "Lowest upfront cost"],
    "net_metering_interest": ["Yes", "No", "Not sure"],
}

INT_FIELDS = ["monthly_units", "monthly_bill", "outage_hours", "desired_backup_hours",
              "roof_area", "budget", "stay_years"]
FLOAT_FIELDS = ["sanctioned_load_kw"]
BOOL_FIELDS = ["night_outages", "voltage_issues"]
TEXT_FIELDS = ["city"] + list(OPTIONS.keys())

PAGES = ["🏠 Home", "🧭 Assessment", "📊 Results", "🧠 Explanation", "📚 Knowledge Base", "ℹ️ About"]


def app_key(name):
    """Session-state key for an appliance quantity widget."""
    return "app_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower())


# --------------------------------------------------------------------------
# Session state helpers
# --------------------------------------------------------------------------
def apply_inputs(inputs):
    ss = st.session_state
    for field in INT_FIELDS:
        ss["in_" + field] = int(inputs.get(field, 0) or 0)
    for field in FLOAT_FIELDS:
        ss["in_" + field] = float(inputs.get(field, 0) or 0)
    for field in BOOL_FIELDS:
        ss["in_" + field] = bool(inputs.get(field, False))
    ss["in_city"] = inputs.get("city", CITIES[0]) if inputs.get("city") in CITIES else CITIES[0]
    for field, choices in OPTIONS.items():
        value = inputs.get(field)
        ss["in_" + field] = value if value in choices else choices[0]
    quantities = inputs.get("appliances", {})
    for name in APPLIANCES:
        ss[app_key(name)] = int(quantities.get(name, 0) or 0)
    ss["in_critical_loads"] = [c for c in inputs.get("critical_loads", []) if c in APPLIANCES]


def init_state():
    ss = st.session_state
    if "initialized" not in ss:
        first = next(iter(PERSONAS.values()))
        apply_inputs(first["inputs"])
        ss["nav"] = PAGES[0]
        ss["result"] = None
        ss["result_inputs"] = None
        ss["run_errors"] = []
        ss["persona_choice"] = next(iter(PERSONAS.keys()))
        ss["initialized"] = True
    # Re-save widget values so they survive switching pages (Streamlit removes
    # the state of widgets that are not drawn on the current page).
    for key in list(ss.keys()):
        if key.startswith("in_") or key.startswith("app_"):
            ss[key] = ss[key]


def collect_inputs():
    ss = st.session_state
    data = {}
    for field in INT_FIELDS + FLOAT_FIELDS + BOOL_FIELDS + TEXT_FIELDS:
        data[field] = ss["in_" + field]
    data["appliances"] = {name: int(ss[app_key(name)]) for name in APPLIANCES if int(ss[app_key(name)]) > 0}
    data["critical_loads"] = [c for c in ss["in_critical_loads"] if c in data["appliances"]]
    return data


def validate(inputs):
    errors = []
    if inputs["grid_status"] != "No grid connection" and inputs["monthly_units"] <= 0 and not inputs["appliances"]:
        errors.append("Enter your monthly units (from your electricity bill) or add appliances in Step 2.")
    if inputs["grid_status"] == "No grid connection" and not inputs["appliances"]:
        errors.append("For a site without grid, add your appliances in Step 2 so energy use can be estimated.")
    if inputs["monthly_units"] > 0 and inputs["monthly_bill"] <= 0 and inputs["grid_status"] != "No grid connection":
        errors.append("Enter your monthly bill amount so your per-unit tariff can be calculated.")
    if inputs["roof_type"] != "No usable space" and inputs["roof_area"] <= 0:
        errors.append("Enter your usable roof or ground area in Step 4.")
    if inputs["budget"] <= 0:
        errors.append("Enter your budget in Step 5.")
    return errors


# --------------------------------------------------------------------------
# Callbacks (run before the page re-draws)
# --------------------------------------------------------------------------
def go_to(page):
    st.session_state["nav"] = page


def load_persona():
    name = st.session_state.get("persona_choice")
    if name in PERSONAS:
        apply_inputs(PERSONAS[name]["inputs"])
        st.session_state["run_errors"] = []


def reset_form():
    blank = {"city": "Karachi", "property_type": "House", "phase": "Single-phase",
             "grid_status": "Grid with load-shedding", "monthly_units": 0, "monthly_bill": 0,
             "sanctioned_load_kw": 0.0, "appliances": {}, "critical_loads": [], "outage_hours": 0,
             "night_outages": False, "desired_backup_hours": 0, "existing_backup": "None",
             "voltage_issues": False, "roof_type": "RCC concrete roof", "roof_area": 0,
             "shading": "No shading", "orientation": "South-facing / flat roof", "ownership": "Owner",
             "budget": 0, "priority": "Balanced", "net_metering_interest": "Not sure", "stay_years": 10}
    apply_inputs(blank)
    st.session_state["run_errors"] = []


def run_analysis():
    inputs = collect_inputs()
    errors = validate(inputs)
    st.session_state["run_errors"] = errors
    if errors:
        return
    st.session_state["result"] = ENGINE.run(inputs)
    st.session_state["result_inputs"] = inputs
    st.session_state["nav"] = "📊 Results"


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------
def rs(value):
    value = float(value or 0)
    if value >= 10_000_000:
        return f"Rs {value / 10_000_000:.2f} crore"
    if value >= 100_000:
        return f"Rs {value / 100_000:.2f} lakh"
    return f"Rs {value:,.0f}"


def html_block(markup):
    st.markdown(markup, unsafe_allow_html=True)


def rule_why(rule_id):
    for r in RULES:
        if r["id"] == rule_id:
            return r["why"]
    return ""


def deciding_rule(trace, fact):
    """Return the id of the rule that set a given fact (for 'why' explanations)."""
    for t in trace:
        for change in t["conclusions"]:
            if change.startswith(fact + " = "):
                return t["id"]
    return None


def rules_table():
    rows = []
    for r in RULES:
        rows.append({
            "ID": r["id"],
            "Module": r["module"],
            "Rule": r["name"],
            "IF": "  AND  ".join(describe_condition(c) for c in r["if"]),
            "THEN": "; ".join(describe_actions(r)),
            "Salience": r.get("salience", 0),
            "CF": r.get("cf", 1.0),
            "Why": r["why"],
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_home():
    html_block(styles.hero(
        "SolarSense",
        "A rule-based expert system that designs the right solar setup for Pakistani homes and shops: "
        "system type, panel and inverter size, battery choice, net billing, cost and payback, with every "
        "decision explained.",
        "AI EXPERT SYSTEM · DECISION SUPPORT",
    ))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        html_block(styles.kpi("IF-THEN rules", f"{len(RULES)}", "in the knowledge base"))
    with c2:
        html_block(styles.kpi("Knowledge modules", f"{len(MODULES)}", "load, outage, roof, battery..."))
    with c3:
        html_block(styles.kpi("Cities covered", f"{len(CITIES) - 1}", "with local sun hours"))
    with c4:
        html_block(styles.kpi("Appliance types", f"{len(APPLIANCES)}", "for load estimation"))

    html_block(styles.section_title("The problem SolarSense solves"))
    a, b, c = st.columns(3)
    with a:
        html_block(styles.card("💸", "Costly wrong choices",
                               "Buyers often pick the wrong inverter type, oversize or undersize panels, "
                               "or skip batteries they actually need."))
    with b:
        html_block(styles.card("⚡", "Load-shedding and policy",
                               "Outage hours, night-time backup and the new net-billing export rates all change "
                               "what the best system is."))
    with c:
        html_block(styles.card("🧠", "Expert advice, explained",
                               "SolarSense applies an installer's reasoning as IF-THEN rules and shows exactly "
                               "which rules led to each recommendation."))

    html_block(styles.section_title("How it works"))
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        html_block(styles.step(1, "Describe your site", "Bill, appliances, outages, roof and budget."))
    with s2:
        html_block(styles.step(2, "Facts enter memory", "Your answers become facts in working memory."))
    with s3:
        html_block(styles.step(3, "Rules fire", "The forward-chaining engine fires matching rules until done."))
    with s4:
        html_block(styles.step(4, "Get a design", "System design, costs, payback, warnings and reasoning."))

    st.write("")
    b1, b2, _ = st.columns([1, 1, 2])
    with b1:
        st.button("🚀 Start assessment", type="primary", on_click=go_to, args=("🧭 Assessment",))
    with b2:
        st.button("📚 Browse the rules", on_click=go_to, args=("📚 Knowledge Base",))


def page_assessment():
    ss = st.session_state
    st.title("🧭 Solar Assessment")
    st.caption("Answer the five steps below, then run the expert system. You can load a sample profile to try it quickly.")

    with st.container(border=True):
        p1, p2, p3 = st.columns([3, 1, 1])
        with p1:
            st.selectbox("Sample profile", list(PERSONAS.keys()), key="persona_choice")
            st.caption(PERSONAS.get(ss["persona_choice"], {}).get("description", ""))
        with p2:
            st.write("")
            st.button("📥 Load profile", on_click=load_persona)
        with p3:
            st.write("")
            st.button("🧹 Clear form", on_click=reset_form)

    t1, t2, t3, t4, t5 = st.tabs(["1 · Location & bill", "2 · Appliances", "3 · Outages & backup",
                                  "4 · Roof & site", "5 · Budget & goals"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("City", CITIES, key="in_city", help="Sets local sun hours, dust and coastal conditions.")
            st.selectbox("Property type", OPTIONS["property_type"], key="in_property_type")
            st.selectbox("Grid status", OPTIONS["grid_status"], key="in_grid_status")
            st.radio("Electricity connection", OPTIONS["phase"], key="in_phase", horizontal=True)
        with c2:
            st.number_input("Average monthly units (kWh)", min_value=0, max_value=20000, step=10,
                            key="in_monthly_units", help="Printed on your electricity bill as 'Units consumed'.")
            st.number_input("Average monthly bill (Rs)", min_value=0, max_value=5000000, step=500,
                            key="in_monthly_bill")
            st.number_input("Sanctioned load (kW)", min_value=0.0, max_value=200.0, step=0.5,
                            key="in_sanctioned_load_kw", help="Printed on your bill. Use 0 if unknown.")
            if ss["in_monthly_units"] > 0 and ss["in_monthly_bill"] > 0:
                st.info(f"Your effective tariff is about **Rs {ss['in_monthly_bill'] / ss['in_monthly_units']:.1f} per unit**.")
        if ss["in_grid_status"] == "No grid connection":
            st.warning("No grid: units and bill can stay 0. Energy use will be estimated from your appliance list.")

    with t2:
        st.caption("Enter how many of each appliance you use. Typical wattage and daily hours are shown in the help (?) icons.")
        cols = st.columns(3)
        for i, name in enumerate(APPLIANCES):
            spec = PARAMS["appliances"][name]
            with cols[i % 3]:
                st.number_input(name, min_value=0, max_value=100, step=1, key=app_key(name),
                                help=f"About {spec['watts']} W, used about {spec['hours']} h/day")
        connected = sum(PARAMS["appliances"][n]["watts"] * ss[app_key(n)] for n in APPLIANCES) / 1000
        daily = sum(PARAMS["appliances"][n]["watts"] * PARAMS["appliances"][n]["hours"] * ss[app_key(n)]
                    for n in APPLIANCES) / 1000
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Connected load", f"{connected:.2f} kW")
        with m2:
            st.metric("Estimated daily energy", f"{daily:.1f} kWh")

    with t3:
        c1, c2 = st.columns(2)
        with c1:
            st.slider("Load-shedding hours per day", 0, 18, key="in_outage_hours")
            st.checkbox("Outages happen at night", key="in_night_outages")
            st.slider("Backup hours you want", 0, 12, key="in_desired_backup_hours")
        with c2:
            st.selectbox("Existing backup", OPTIONS["existing_backup"], key="in_existing_backup")
            st.checkbox("Voltage fluctuations / low voltage problems", key="in_voltage_issues")
            owned = [n for n in APPLIANCES if ss[app_key(n)] > 0]
            ss["in_critical_loads"] = [c for c in ss["in_critical_loads"] if c in owned]
            st.multiselect("Critical loads to keep running during outages", owned, key="in_critical_loads",
                           help="Only appliances added in Step 2 appear here.")

    with t4:
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Where can panels be installed?", OPTIONS["roof_type"], key="in_roof_type")
            st.number_input("Usable shade-free area (sq ft)", min_value=0, max_value=50000, step=10,
                            key="in_roof_area", help="About 75 sq ft is needed per kW of panels.")
            if ss["in_roof_area"] > 0:
                st.info(f"This area fits roughly **{ss['in_roof_area'] / PARAMS['system']['sqft_per_kw']:.1f} kW** of panels.")
        with c2:
            st.radio("Shading", OPTIONS["shading"], key="in_shading", horizontal=True)
            st.selectbox("Roof orientation", OPTIONS["orientation"], key="in_orientation")
            st.radio("Ownership", OPTIONS["ownership"], key="in_ownership", horizontal=True)

    with t5:
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Budget (Rs)", min_value=0, max_value=100000000, step=25000, key="in_budget")
            if ss["in_budget"] > 0:
                st.caption(f"= {rs(ss['in_budget'])}")
            st.slider("How many more years will you live/work here?", 1, 25, key="in_stay_years")
        with c2:
            st.radio("What matters most to you?", OPTIONS["priority"], key="in_priority")
            st.radio("Interested in selling surplus power (net billing)?", OPTIONS["net_metering_interest"],
                     key="in_net_metering_interest", horizontal=True)

    st.write("")
    for err in ss.get("run_errors", []):
        st.error(err)
    st.button("⚡ Run SolarSense analysis", type="primary", on_click=run_analysis)
    st.caption("All five tabs are submitted together. Results open automatically.")


def no_result_notice():
    st.info("No analysis yet. Complete the assessment (or load a sample profile) and run the expert system.")
    st.button("🧭 Go to assessment", type="primary", on_click=go_to, args=("🧭 Assessment",))


def show_advice(f):
    groups = [("warnings", "warning", "⚠️ Warnings"),
              ("recommendations", "recommendation", "✅ Recommendations"),
              ("notes", "note", "ℹ️ Notes")]
    for key, kind, title in groups:
        entries = f.get(key, [])
        if entries:
            html_block(styles.section_title(f"{title} ({len(entries)})"))
            for e in entries:
                html_block(styles.advice_item(kind, e["rule"], e["text"]))


def page_results():
    ss = st.session_state
    st.title("📊 Your Solar Recommendation")
    result = ss.get("result")
    if not result:
        no_result_notice()
        return
    f = result["facts"]
    inputs = ss["result_inputs"]

    if not f.get("site_feasible", False):
        html_block(styles.verdict("Solar is not feasible at this site", f.get("final_recommendation", ""),
                                  styles.badge(f"Confidence {f.get('overall_confidence', '')}%", "bad"), bad=True))
        show_advice(f)
        return

    verdict_kind = {"Excellent investment": "good", "Good investment": "good",
                    "Fair investment": "warn", "Weak investment": "bad"}.get(f.get("financial_verdict"), "")
    budget_kind = {"Within budget": "good", "Slightly over budget": "warn", "Over budget": "bad"}.get(
        f.get("budget_status"), "")
    badges = (styles.badge(f.get("financial_verdict", ""), verdict_kind)
              + styles.badge(f.get("budget_status", ""), budget_kind)
              + styles.badge(f"Confidence {f.get('overall_confidence')}% ({f.get('confidence_label')})")
              + styles.badge(f"{len(result['trace'])} rules fired"))
    html_block(styles.verdict("Recommended system", f.get("final_recommendation", ""), badges))

    k = st.columns(6)
    battery_text = f"{f['battery_kwh']:.1f} kWh" if f.get("battery_needed") else "None"
    battery_sub = f.get("battery_type", "") if f.get("battery_needed") else "not required"
    cards = [
        ("System size", f"{f['system_kw']:.2f} kW", f"{f['panel_count']} × {f['panel_watt']} W panels"),
        ("System type", f["system_type"], f.get("inverter_phase", "")),
        ("Inverter", f"{f['inverter_kw']} kW", f["system_type"] + " inverter"),
        ("Battery", battery_text, battery_sub),
        ("Total cost", rs(f["total_cost"]), "indicative estimate"),
        ("Payback", f"{f['payback_years']} yrs", f.get("financial_verdict", "")),
    ]
    for col, (label, value, sub) in zip(k, cards):
        with col:
            html_block(styles.kpi(label, value, sub))
    st.write("")
    k2 = st.columns(4)
    cards2 = [
        ("Monthly savings", rs(f["monthly_savings"]), f"{rs(f['annual_savings'])} per year"),
        ("Bill reduction", f"{f['bill_reduction_pct']}%", "of your grid energy"),
        ("Solar generation", f"{f['annual_generation_kwh']:,} kWh", "per year"),
        ("CO₂ avoided", f"{f['co2_tonnes_per_year']} t", "per year"),
    ]
    for col, (label, value, sub) in zip(k2, cards2):
        with col:
            html_block(styles.kpi(label, value, sub))

    st.write("")
    tab1, tab2, tab3, tab4 = st.tabs(["🧩 System design", "💵 Financials", "⚠️ Advice & warnings", "📈 Energy profile"])

    with tab1:
        left, right = st.columns([3, 2])
        with left:
            battery_spec = (f"{f['battery_units']} × {f['battery_type']} units = {f['battery_kwh']:.2f} kWh "
                            f"({f.get('battery_voltage', '')}, about {f.get('estimated_backup_hours')} h backup "
                            f"for critical loads)" if f.get("battery_needed") else "Not required")
            spec = pd.DataFrame([
                ("System type", f["system_type"]),
                ("Solar panels", f"{f['panel_count']} × {f['panel_watt']} W = {f['system_kw']:.2f} kW"),
                ("Inverter", f"{f['inverter_kw']} kW · {f.get('inverter_technology', '')}"),
                ("Inverter phase", f.get("inverter_phase", "")),
                ("Battery bank", battery_spec),
                ("Mounting", f.get("mounting", "")),
                ("Net billing", f.get("net_metering_status", "")),
                ("Daily generation", f"{f['daily_generation_kwh']} kWh (usage {f['daily_kwh']} kWh)"),
                ("Energy independence", f.get("energy_independence", "")),
            ], columns=["Component", "Recommendation"])
            show_table(spec)
            if f.get("phase_plan"):
                st.info(f"**Phase plan:** {f['phase_plan']}")
        with right:
            show_chart(charts.coverage_gauge(f.get("solar_fraction_pct", 0)))

        html_block(styles.section_title("Why these decisions?"))
        for fact, label in [("system_type", "System type"), ("battery_type", "Battery"),
                            ("coverage_target", "Sizing target"), ("net_metering_status", "Net billing")]:
            rid = deciding_rule(result["trace"], fact)
            if rid:
                html_block(styles.advice_item("note", rid, f"{label}: {f.get(fact)} because {rule_why(rid)}"))

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            show_chart(charts.cost_breakdown(f["cost_breakdown"]))
        with c2:
            costs = pd.DataFrame([(k2_, f"Rs {v:,}") for k2_, v in f["cost_breakdown"].items()]
                                 + [("TOTAL", f"Rs {f['total_cost']:,}")], columns=["Item", "Cost"])
            show_table(costs)
            st.caption(f"Your budget: {rs(inputs['budget'])} · Budget status: **{f.get('budget_status')}**")
        show_chart(charts.cashflow(f["cashflow"]))
        st.caption(f"Assumes {PARAMS['system']['tariff_escalation'] * 100:.0f}% yearly tariff increase and "
                   f"{PARAMS['system']['panel_degradation'] * 100:.1f}% yearly panel degradation. "
                   f"Self-used solar: {f['self_used_kwh']:,} kWh/yr · exported: {f['exported_kwh']:,} kWh/yr · "
                   f"unused surplus: {f['wasted_kwh']:,} kWh/yr.")
        if f["system_type"] == "Off-Grid":
            st.caption("Off-grid savings are valued at the standard grid tariff as a benchmark (generator fuel usually costs more).")

    with tab3:
        show_advice(f)

    with tab4:
        s = PARAMS["system"]
        show_chart(charts.monthly_energy(f["daily_kwh"], f["daily_generation_kwh"],
                                         s["monthly_solar_factors"], s["monthly_consumption_factors"]))
        if f.get("appliance_breakdown"):
            show_chart(charts.appliance_energy(f["appliance_breakdown"]))
        st.caption(f"Peak load {f['peak_load_kw']} kW · connected load {f['connected_load_kw']} kW · "
                   f"local sun hours {f['sun_hours']} h/day · effective tariff Rs {f['effective_tariff']}/unit.")

    st.write("")
    report = build_html_report(inputs, result)
    d1, d2, _ = st.columns([1, 1, 2])
    with d1:
        st.download_button("⬇️ Download report (HTML)", data=report, file_name="SolarSense_Report.html",
                           mime="text/html", type="primary")
    with d2:
        st.button("🧠 See the reasoning", on_click=go_to, args=("🧠 Explanation",))
    st.caption("Open the downloaded report in a browser and use Print → Save as PDF for a PDF copy.")


def page_explanation():
    ss = st.session_state
    st.title("🧠 How SolarSense Reached Its Decision")
    result = ss.get("result")
    if not result:
        no_result_notice()
        return
    f = result["facts"]
    trace = result["trace"]

    c = st.columns(4)
    with c[0]:
        html_block(styles.kpi("Inference cycles", result["cycles"], "recognise-act cycles"))
    with c[1]:
        html_block(styles.kpi("Rules fired", len(trace), f"of {result['rules_total']} in knowledge base"))
    with c[2]:
        facts_count = len([k for k in f if not k.startswith("_")])
        html_block(styles.kpi("Facts in memory", facts_count, "inputs + derived facts"))
    with c[3]:
        html_block(styles.kpi("Confidence", f"{f.get('overall_confidence', '')}%", f.get("confidence_label", "")))

    with st.expander("How does the inference engine work?"):
        st.markdown(
            "SolarSense uses **forward chaining** (data-driven reasoning):\n\n"
            "1. **Match:** every rule whose IF part is true in working memory joins the *agenda*.\n"
            "2. **Conflict resolution:** the rule with the highest *salience* (priority) is chosen; "
            "ties go to the lower rule number.\n"
            "3. **Act:** the rule fires and adds new facts, advice, or runs a calculation.\n"
            "4. Repeat until no rule can fire. Each rule fires at most once (*refraction*).\n\n"
            "Each conclusion carries a **certainty factor (CF)**. Overall confidence equals the weakest CF "
            "among the key decisions (system type and battery type)."
        )

    tab1, tab2, tab3 = st.tabs(["🔗 Reasoning chain", "🗃️ Working memory", "🚫 Rules not fired"])
    with tab1:
        modules = ["All modules"] + sorted({t["module"] for t in trace})
        chosen = st.selectbox("Filter by module", modules, key="exp_module")
        for t in trace:
            if chosen != "All modules" and t["module"] != chosen:
                continue
            with st.expander(f"Cycle {t['cycle']} · {t['id']} — {t['name']}  ({t['module']})"):
                st.markdown("**IF**")
                for cond in t["conditions"]:
                    st.markdown(f"- `{cond}`")
                st.markdown("**THEN**")
                for change in t["conclusions"]:
                    st.markdown(f"- {change}")
                st.caption(f"Why: {t['explanation']} · salience {t['salience']} · CF {t['cf']} · "
                           f"{t['agenda_size']} rule(s) were on the agenda this cycle")
    with tab2:
        rows = []
        for key, value in f.items():
            if key.startswith("_") or isinstance(value, (dict, list)):
                continue
            source = "input" if key in ss["result_inputs"] else "derived"
            rows.append({"Fact": key, "Value": str(value), "Source": source})
        show_table(pd.DataFrame(rows), height=520)
    with tab3:
        fired = set(result["fired_ids"])
        rows = [{"ID": r["id"], "Rule": r["name"], "Module": r["module"],
                 "IF": "  AND  ".join(describe_condition(cnd) for cnd in r["if"])}
                for r in RULES if r["id"] not in fired]
        st.caption(f"{len(rows)} rules did not fire because their conditions were not true for this case.")
        show_table(pd.DataFrame(rows), height=480)


def page_knowledge_base():
    st.title("📚 Knowledge Base")
    st.caption("Every IF-THEN rule SolarSense uses, stored as data and kept separate from the inference engine.")
    df = rules_table()

    counts = df["Module"].value_counts().sort_index()
    cols = st.columns(5)
    for i, (module, count) in enumerate(counts.items()):
        with cols[i % 5]:
            html_block(styles.kpi(module.split(". ", 1)[1], count, f"Module {module.split('.')[0]}"))
    st.write("")

    c1, c2 = st.columns([1, 2])
    with c1:
        module = st.selectbox("Module", ["All modules"] + list(counts.index), key="kb_module")
    with c2:
        query = st.text_input("Search rules", placeholder="e.g. battery, shading, payback", key="kb_query")
    view = df
    if module != "All modules":
        view = view[view["Module"] == module]
    if query and not view.empty:
        mask = view.apply(lambda row: query.lower() in " ".join(str(v) for v in row.values).lower(), axis=1)
        view = view[mask]
    st.caption(f"Showing {len(view)} of {len(df)} rules")
    show_table(view, height=560)
    st.download_button("⬇️ Download rule table (CSV)", data=df.to_csv(index=False).encode("utf-8"),
                       file_name="SolarSense_Rules.csv", mime="text/csv")

    with st.expander("Editable parameters (data/parameters.json)"):
        st.caption(PARAMS["meta"]["note"])
        st.json(PARAMS)


ARCHITECTURE_DOT = """
    digraph G {
        rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11];
        UI [label="Streamlit UI\\n(assessment wizard)", fillcolor="#FFF1D6"];
        WM [label="Working memory\\n(facts)", fillcolor="#EEF3FB"];
        IE [label="Inference engine\\n(forward chaining)", fillcolor="#1B2A41", fontcolor="white"];
        KB [label="Knowledge base\\n(RULE_COUNT IF-THEN rules)", fillcolor="#FFF1D6"];
        CALC [label="Calculation module\\n(sizing, cost, payback)", fillcolor="#E3F4F1"];
        EXP [label="Explanation facility\\n(rule trace)", fillcolor="#E3F4F1"];
        OUT [label="Results dashboard\\n+ HTML report", fillcolor="#FFF1D6"];
        UI -> WM [label="user facts"]; WM -> IE; KB -> IE [label="rules"];
        IE -> WM [label="new facts"]; IE -> CALC [label="calc actions"]; CALC -> WM;
        IE -> EXP; WM -> OUT; EXP -> OUT;
    }
"""


def page_about():
    st.title("ℹ️ About SolarSense")
    st.markdown(
        "**SolarSense** is a rule-based expert system developed for the *Introduction to Artificial "
        "Intelligence* course. It acts like an experienced solar consultant: it collects facts about a "
        "home or shop, reasons over a knowledge base of production rules, and recommends a complete "
        "solar system with an explanation of every decision."
    )
    html_block(styles.section_title("Architecture"))
    st.graphviz_chart(ARCHITECTURE_DOT.replace("RULE_COUNT", str(len(RULES))))
    a, b = st.columns(2)
    with a:
        html_block(styles.section_title("Components"))
        st.markdown(
            f"- **Knowledge base:** `knowledge_base/rules.py`, with {len(RULES)} rules in {len(MODULES)} modules\n"
            "- **Inference engine:** `engine/inference.py`, forward chaining with salience-based conflict resolution and refraction\n"
            "- **Working memory:** dictionary of facts, growing as rules fire\n"
            "- **Explanation facility:** trace of fired rules with the values that matched\n"
            "- **Calculation module:** `engine/calculations.py` for sizing, costs and payback\n"
            "- **Parameters:** `data/parameters.json`, editable prices, sun hours and policy values"
        )
    with b:
        html_block(styles.section_title("Knowledge sources & limitations"))
        st.markdown(
            "- Sizing follows standard PV design practice (sun hours × performance ratio × loss factors).\n"
            f"- Grid export policy: {PARAMS['policy']['source_note']}\n"
            "- Prices and sun hours are **indicative** and should be updated before use.\n"
            "- Results support a decision but do not replace a site survey by a certified installer."
        )
    st.caption(f"Parameters last updated: {PARAMS['meta']['last_updated']}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    init_state()
    html_block(styles.CSS)

    with st.sidebar:
        st.markdown("## ☀️ SolarSense")
        st.caption("Solar & Backup Power Decision Expert System")
        st.radio("Navigate", PAGES, key="nav", label_visibility="collapsed")
        st.divider()
        result = st.session_state.get("result")
        if result and result["facts"].get("site_feasible"):
            f = result["facts"]
            st.success(f"Last result: {f['system_kw']:.2f} kW {f['system_type']}")
        elif result:
            st.warning("Last result: site not feasible")
        else:
            st.info("No analysis run yet")
        st.caption(f"{len(RULES)} rules · {len(MODULES)} modules · forward chaining")

    page = st.session_state["nav"]
    if page == "🏠 Home":
        page_home()
    elif page == "🧭 Assessment":
        page_assessment()
    elif page == "📊 Results":
        page_results()
    elif page == "🧠 Explanation":
        page_explanation()
    elif page == "📚 Knowledge Base":
        page_knowledge_base()
    else:
        page_about()

    html_block('<div class="ss-footer">SolarSense · Introduction to Artificial Intelligence semester project · '
               'Rule-based expert system built with Python & Streamlit</div>')


main()
