"""
Diagnosis module for SolarSense.

Diagnosis = identifying the user's situation and the problems in it from the
evidence they gave. In SolarSense the diagnostic reasoning is done by the
existing IF-THEN rules (for example R022 diagnoses "Severe" load-shedding and
R039 diagnoses that the roof is too small). This module does NOT add new rules
and does NOT change any conclusion. It collects the diagnostic conclusions
reached during inference and organises them into a structured diagnosis report:

  1. Situation profile  - what condition the household is in
                          (consumption, peak load, tariff, outages, site, ...)
  2. Problems detected  - what is wrong or risky, with severity, category,
                          evidence and the rule that detected it
  3. Summary            - overall diagnosis level (the most serious problem
                          or condition found) and problem counts

Every finding carries the ID of the rule that produced it, so the diagnosis
can always be traced back to the knowledge base (explanation facility).
"""

# Severity levels, most serious first
SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]

# Status of a profile item, best first
STATUS_ORDER = ["Good", "Watch", "Concern", "Critical"]

# ---------------------------------------------------------------------------
# 1. Situation profile: facts set by classification rules
#    fact -> (title, {value: status}, evidence builder)
# ---------------------------------------------------------------------------
PROFILE = [
    ("consumption_level", "Energy consumption",
     {"Low": "Good", "Moderate": "Good", "High": "Watch", "Very High": "Concern"},
     lambda f: f"{f.get('daily_kwh')} kWh per day"),
    ("load_class", "Peak load",
     {"Light": "Good", "Medium": "Good", "Heavy": "Watch"},
     lambda f: f"{f.get('peak_load_kw')} kW peak (connected {f.get('connected_load_kw')} kW)"),
    ("tariff_band", "Electricity tariff",
     {"High": "Good", "Medium": "Good", "Low": "Watch"},
     lambda f: f"Rs {f.get('effective_tariff')} per unit (higher tariff = faster solar payback)"),
    ("outage_severity", "Load-shedding",
     {"None": "Good", "Mild": "Watch", "Moderate": "Concern", "Severe": "Concern", "Off-grid site": "Concern"},
     lambda f: ("no grid connection" if f.get("outage_severity") == "Off-grid site"
                else f"{f.get('outage_hours')} hours per day"
                + (", at night" if f.get("night_outages") else ""))),
    ("site_feasible", "Site suitability",
     {True: "Good", False: "Critical"},
     lambda f: f"usable area fits about {f.get('roof_capacity_kw', 0):.1f} kW of panels"),
    ("energy_independence", "Solar coverage",
     {"High": "Good", "Partial": "Watch", "Low": "Concern"},
     lambda f: f"solar covers about {f.get('solar_fraction_pct')}% of daily use"),
    ("budget_status", "Budget fit",
     {"Within budget": "Good", "Slightly over budget": "Watch", "Over budget": "Concern"},
     lambda f: f"budget Rs {float(f.get('budget', 0) or 0):,.0f} vs cost Rs {float(f.get('total_cost', 0) or 0):,.0f}"),
    ("financial_verdict", "Investment health",
     {"Excellent investment": "Good", "Good investment": "Good", "Fair investment": "Watch",
      "Weak investment": "Concern"},
     lambda f: f"payback about {f.get('payback_years')} years"),
]

DISPLAY_VALUES = {True: "Feasible", False: "Not feasible"}

# ---------------------------------------------------------------------------
# 2. Problems: rules whose advice is a diagnostic finding
#    rule id -> (problem name, category, severity)
# ---------------------------------------------------------------------------
PROBLEM_RULES = {
    "R038": ("No installation space", "Site", "Critical"),
    "R039": ("Roof too small for solar", "Site", "Critical"),
    "R041": ("Heavy shading", "Site", "High"),
    "R046": ("North-facing roof", "Site", "High"),
    "R056": ("Roof limits system size", "Site", "High"),
    "R061": ("No solar power during outages", "Backup", "High"),
    "R105": ("System exceeds sanctioned load", "Grid connection", "High"),
    "R116": ("Weak investment", "Finance", "High"),
    "R117": ("Leaving before payback", "Finance", "High"),
    "R121": ("Heavy array on sheet roof", "Structure", "High"),
    "R009": ("Wasteful non-inverter ACs", "Energy use", "Medium"),
    "R011": ("Energy-hungry electric geyser", "Energy use", "Medium"),
    "R017": ("Load too high for single-phase supply", "Grid connection", "Medium"),
    "R035": ("AC selected for battery backup", "Backup", "Medium"),
    "R054": ("Tenant needs owner's permission", "Ownership", "Medium"),
    "R055": ("Shared apartment roof", "Ownership", "Medium"),
    "R071": ("Low solar coverage", "Performance", "Medium"),
    "R083": ("Very large battery bank", "Cost", "Medium"),
    "R096": ("Large inverter on single-phase supply", "Grid connection", "Medium"),
    "R104": ("Single-phase may block net billing", "Grid connection", "Medium"),
    "R118": ("Tenant with slow payback", "Finance", "Medium"),
    "R012": ("Appliance list incomplete", "Data quality", "Low"),
    "R013": ("Appliance list overstates usage", "Data quality", "Low"),
    "R016": ("Low tariff slows payback", "Finance", "Low"),
    "R042": ("Partial shading", "Site", "Low"),
    "R045": ("East-West orientation loss", "Site", "Low"),
    "R072": ("Very small system (high cost per kW)", "Finance", "Low"),
}

ADVICE_LISTS = ("warnings", "recommendations", "notes")


def _rule_that_set(trace, fact):
    """Find which fired rule set a fact (searches the reasoning trace)."""
    for step in trace:
        for change in step["conclusions"]:
            if change.startswith(fact + " = "):
                return step
    return None


def _profile(facts, trace):
    items = []
    for fact, title, status_map, evidence in PROFILE:
        if fact not in facts:
            continue
        value = facts[fact]
        if value not in status_map:
            continue
        if fact == "tariff_band" and float(facts.get("monthly_units", 0) or 0) <= 0:
            continue  # no bill entered: tariff is only a default benchmark, not evidence
        step = _rule_that_set(trace, fact)
        items.append({
            "fact": fact,
            "title": title,
            "value": DISPLAY_VALUES.get(value, value) if isinstance(value, bool) else value,
            "status": status_map[value],
            "evidence": evidence(facts),
            "rule": step["id"] if step else "-",
            "rule_name": step["name"] if step else "",
        })
    return items


def _problems(facts, trace):
    cf_by_rule = {step["id"]: step["cf"] for step in trace}
    found = {}
    for list_name in ADVICE_LISTS:
        for entry in facts.get(list_name, []):
            rid = entry["rule"]
            if rid in PROBLEM_RULES and rid not in found:
                name, category, severity = PROBLEM_RULES[rid]
                found[rid] = {
                    "rule": rid,
                    "problem": name,
                    "category": category,
                    "severity": severity,
                    "finding": entry["text"],
                    "certainty": round(cf_by_rule.get(rid, 1.0) * 100),
                }
    return sorted(found.values(), key=lambda p: (SEVERITY_ORDER.index(p["severity"]), p["rule"]))


# A profile status counts towards the overall level like this
STATUS_TO_LEVEL = {"Critical": "Critical", "Concern": "Medium", "Watch": "Low", "Good": None}

HEADLINES = {
    "Critical": "Critical problem found - the plan cannot go ahead as entered.",
    "High": "Serious issues found - review them before buying a system.",
    "Medium": "Some issues found - manageable with the recommended actions.",
    "Low": "Only minor issues found - good conditions for solar.",
    "None": "No issues found - very good conditions for solar.",
}


def _summary(problems, profile):
    counts = {level: sum(1 for p in problems if p["severity"] == level) for level in SEVERITY_ORDER}
    levels = [p["severity"] for p in problems]
    levels += [STATUS_TO_LEVEL[i["status"]] for i in profile if STATUS_TO_LEVEL[i["status"]]]
    level = min(levels, key=SEVERITY_ORDER.index) if levels else "None"
    attention = [i["title"] for i in profile if i["status"] != "Good"]
    return {"level": level, "headline": HEADLINES[level], "counts": counts, "total": len(problems),
            "attention": attention}


def build_diagnosis(result):
    """
    Build the structured diagnosis from an inference result
    (the dictionary returned by InferenceEngine.run()).
    """
    facts = result["facts"]
    trace = result["trace"]
    problems = _problems(facts, trace)
    profile = _profile(facts, trace)
    return {
        "profile": profile,
        "problems": problems,
        "summary": _summary(problems, profile),
        "diagnostic_rules_fired": sorted({p["rule"] for p in problems}
                                         | {i["rule"] for i in profile if i["rule"] != "-"}),
    }
