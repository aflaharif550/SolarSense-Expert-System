"""
Calculation helpers for SolarSense.

The inference engine calls these functions when a rule with a "calc" action
fires. Each function receives the current working memory (facts) and the
parameter set, and returns a dictionary of NEW facts to add.

Keeping the arithmetic here (and the decisions in the rule base) is a deliberate
design choice: rules decide WHAT to do, calculations work out HOW MUCH.
"""

import json
import math
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAMETERS_PATH = os.path.join(_BASE_DIR, "data", "parameters.json")


def load_parameters(path=PARAMETERS_PATH):
    """Load the editable parameter file (prices, sun hours, policy values)."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Module A - load analysis
# --------------------------------------------------------------------------
def analyse_load(f, P):
    catalogue = P["appliances"]
    system = P["system"]
    appliances = f.get("appliances", {}) or {}
    critical = set(f.get("critical_loads", []) or [])

    total_w = 0.0
    appliance_daily = 0.0
    breakdown = {}
    has_motor = False
    has_geyser = False
    ac_count = 0
    noninverter_ac = 0
    critical_w = 0.0
    critical_has_ac = False

    for name, qty in appliances.items():
        qty = int(qty or 0)
        if qty <= 0 or name not in catalogue:
            continue
        spec = catalogue[name]
        watts = spec["watts"] * qty
        kwh = spec["watts"] * spec["hours"] * qty / 1000.0
        total_w += watts
        appliance_daily += kwh
        breakdown[name] = round(kwh, 2)
        if spec.get("motor"):
            has_motor = True
        if spec.get("geyser"):
            has_geyser = True
        if spec.get("ac"):
            ac_count += qty
            if name.startswith("Non-inverter"):
                noninverter_ac += qty
        if name in critical:
            critical_w += watts
            if spec.get("ac"):
                critical_has_ac = True

    monthly_units = float(f.get("monthly_units", 0) or 0)
    monthly_bill = float(f.get("monthly_bill", 0) or 0)
    bill_daily = monthly_units / 30.0

    if bill_daily > 0:
        daily_kwh = bill_daily
        appliance_ratio = appliance_daily / bill_daily if appliance_daily > 0 else 1.0
    else:
        daily_kwh = appliance_daily
        appliance_ratio = 1.0
    daily_kwh = max(daily_kwh, 0.5)

    if monthly_units > 0 and monthly_bill > 0:
        tariff = monthly_bill / monthly_units
    else:
        tariff = float(system["default_tariff"])

    export_rate = float(P["policy"]["export_rate"])

    return {
        "daily_kwh": round(daily_kwh, 2),
        "annual_kwh": round(daily_kwh * 365, 1),
        "appliance_daily_kwh": round(appliance_daily, 2),
        "appliance_ratio": round(appliance_ratio, 2),
        "appliance_ratio_pct": round(appliance_ratio * 100),
        "appliance_breakdown": breakdown,
        "connected_load_kw": round(total_w / 1000.0, 2),
        "peak_load_kw": round(total_w / 1000.0 * system["diversity_factor"], 2),
        "has_motor_load": has_motor,
        "has_geyser": has_geyser,
        "ac_count": ac_count,
        "noninverter_ac_count": noninverter_ac,
        "critical_load_kw": round(critical_w / 1000.0, 2),
        "critical_has_ac": critical_has_ac,
        "effective_tariff": round(tariff, 1),
        "export_rate": export_rate,
        "export_value_ratio": round(export_rate / tariff, 2) if tariff > 0 else 0,
    }


# --------------------------------------------------------------------------
# Module C - site analysis
# --------------------------------------------------------------------------
def analyse_site(f, P):
    cities = P["cities"]
    city = f.get("city", "Other city")
    data = cities.get(city, cities["Other city"])
    roof_area = float(f.get("roof_area", 0) or 0)
    roof_capacity = roof_area / P["system"]["sqft_per_kw"]
    if f.get("roof_type") == "No usable space":
        roof_capacity = 0.0
    return {
        "sun_hours": data["sun_hours"],
        "coastal": bool(data["coastal"]),
        "hot_climate": bool(data["hot_climate"]),
        "dusty": bool(data["dusty"]),
        "roof_capacity_kw": round(roof_capacity, 2),
    }


# --------------------------------------------------------------------------
# Module B - backup duration
# --------------------------------------------------------------------------
def set_backup_hours(f, P):
    outage = int(f.get("outage_hours", 0) or 0)
    desired = int(f.get("desired_backup_hours", 0) or 0)
    # Night outages must be carried fully by the battery; daytime outages are
    # partly covered by live solar, so roughly half is enough.
    needed = outage if f.get("night_outages") else math.ceil(outage / 2)
    hours = max(desired, needed, 2)
    return {"backup_hours": int(min(hours, 12))}


# --------------------------------------------------------------------------
# Module D - array sizing
# --------------------------------------------------------------------------
def size_array(f, P):
    s = P["system"]
    yield_per_kw = (f["sun_hours"] * s["performance_ratio"] * f["shading_factor"]
                    * f["orientation_factor"] * f["dust_factor"])
    required_kw = f["daily_kwh"] * f["coverage_target"] / yield_per_kw
    roof_cap = f["roof_capacity_kw"]
    panel_w = s["panel_watt"]

    roof_limited = required_kw > roof_cap
    if roof_limited:
        panels = max(1, int(math.floor(roof_cap * 1000 / panel_w)))
    else:
        panels = max(2, int(math.ceil(required_kw * 1000 / panel_w)))

    system_kw = panels * panel_w / 1000.0
    daily_gen = system_kw * yield_per_kw
    sanctioned = float(f.get("sanctioned_load_kw", 0) or 0)

    return {
        "yield_per_kw": round(yield_per_kw, 2),
        "required_kw": round(required_kw, 2),
        "roof_limited": roof_limited,
        "panel_count": panels,
        "panel_watt": panel_w,
        "system_kw": round(system_kw, 2),
        "daily_generation_kwh": round(daily_gen, 1),
        "annual_generation_kwh": round(daily_gen * 365),
        "solar_fraction": round(daily_gen / f["daily_kwh"], 2),
        "solar_fraction_pct": round(daily_gen / f["daily_kwh"] * 100),
        "exceeds_sanctioned": bool(sanctioned > 0 and system_kw > sanctioned),
    }


# --------------------------------------------------------------------------
# Module F - inverter sizing
# --------------------------------------------------------------------------
def _next_standard_size(need, sizes):
    for size in sizes:
        if size >= need:
            return size
    return int(math.ceil(need / 5.0) * 5)


def size_inverter(f, P):
    s = P["system"]
    if f["system_type"] == "On-Grid":
        need = f["system_kw"] / s["dc_ac_ratio_ongrid"]
    else:
        need = max(f["peak_load_kw"] * f["surge_factor"],
                   f["system_kw"] / s["hybrid_pv_ratio"])
    return {"inverter_kw": _next_standard_size(need, s["inverter_sizes_kw"]),
            "inverter_need_kw": round(need, 2)}


# --------------------------------------------------------------------------
# Module E - battery sizing
# --------------------------------------------------------------------------
def size_battery(f, P):
    s = P["system"]
    if f["system_type"] == "Off-Grid":
        energy = f["daily_kwh"] * s["offgrid_night_fraction"]
    else:
        load_kw = f["critical_load_kw"] if f.get("critical_load_kw", 0) > 0 else f["peak_load_kw"] * 0.4
        energy = load_kw * s["critical_load_duty"] * f["backup_hours"]
    nominal = energy / (f["battery_dod"] * s["battery_efficiency"])

    if f["battery_type"].startswith("Lithium"):
        unit = s["lithium_module_kwh"]
        units = max(1, int(math.ceil(nominal / unit)))
        voltage = "51.2 V"
    else:
        unit = s["tubular_unit_kwh"]
        string = 2 if f["inverter_kw"] <= 3 else 4
        units = max(string, int(math.ceil(nominal / unit / string) * string))
        voltage = "24 V" if string == 2 else "48 V"

    kwh = units * unit
    usable = kwh * f["battery_dod"]
    load_kw = f["critical_load_kw"] if f.get("critical_load_kw", 0) > 0 else f["peak_load_kw"] * 0.4
    est_hours = usable * s["battery_efficiency"] / max(load_kw * s["critical_load_duty"], 0.05)

    return {
        "battery_energy_needed_kwh": round(energy, 2),
        "battery_units": units,
        "battery_kwh": round(kwh, 2),
        "battery_usable_kwh": round(usable, 2),
        "battery_voltage": voltage,
        "estimated_backup_hours": round(est_hours, 1),
    }


# --------------------------------------------------------------------------
# Module H - cost and finance
# --------------------------------------------------------------------------
def estimate_cost(f, P):
    c = P["costs"]
    kw = f["system_kw"]
    stype = f["system_type"]
    breakdown = {
        "Solar panels": kw * 1000 * c["panel_per_watt"],
        "Inverter": max(c["inverter_min"][stype], c["inverter_per_kw"][stype] * f["inverter_kw"]),
        "Mounting structure": kw * c["structure_per_kw"][f["mounting_key"]],
        "Cables, breakers & earthing": kw * c["bos_per_kw"],
        "Installation": kw * c["installation_per_kw"],
    }
    battery_cost = 0.0
    if f.get("battery_kwh", 0) > 0:
        battery_cost = f["battery_kwh"] * c["battery_per_kwh"][f["battery_type"]]
        breakdown["Batteries"] = battery_cost
    if f.get("net_metering_status") == "Recommended":
        breakdown["Net-billing application & meter"] = c["net_billing_fixed"]

    breakdown = {k: round(v) for k, v in breakdown.items()}
    total = sum(breakdown.values())
    budget = float(f.get("budget", 0) or 0)
    ratio = budget / total if total > 0 else 0
    return {
        "cost_breakdown": breakdown,
        "total_cost": total,
        "battery_cost": round(battery_cost),
        "phase1_cost": round(total - battery_cost),
        "budget_ratio": round(ratio, 2),
        "affordable_kw": round(max(kw * min(ratio, 1.0), 0), 1),
    }


def financials(f, P):
    s = P["system"]
    gen = f["annual_generation_kwh"]
    consumption = f["annual_kwh"]
    tariff = f["effective_tariff"]

    if f["system_type"] == "Off-Grid":
        share = 1.0
    elif f.get("battery_needed"):
        share = s["self_use_with_battery"]
    else:
        share = s["self_use_no_battery"]

    self_used = min(gen * share, consumption)
    surplus = max(gen - self_used, 0)
    exported = surplus if f.get("net_metering_status") == "Recommended" else 0
    annual_savings = self_used * tariff + exported * f["export_rate"]
    payback = f["total_cost"] / annual_savings if annual_savings > 0 else 99.0

    # Cumulative cash flow with tariff escalation and panel degradation
    cumulative = [-float(f["total_cost"])]
    for year in range(1, s["analysis_years"] + 1):
        factor = ((1 + s["tariff_escalation"]) ** (year - 1)) * ((1 - s["panel_degradation"]) ** (year - 1))
        cumulative.append(cumulative[-1] + annual_savings * factor)

    return {
        "self_used_kwh": round(self_used),
        "exported_kwh": round(exported),
        "wasted_kwh": round(surplus - exported),
        "annual_savings": round(annual_savings),
        "monthly_savings": round(annual_savings / 12),
        "payback_years": round(payback, 1),
        "bill_reduction_pct": round(min(self_used / consumption, 1.0) * 100) if consumption else 0,
        "co2_tonnes_per_year": round(gen * s["grid_emission_factor_kg_per_kwh"] / 1000, 2),
        "cashflow": [round(v) for v in cumulative],
        "net_gain_period": round(cumulative[-1]),
    }


def compare_stay(f, P):
    stay = float(f.get("stay_years", 0) or 0)
    return {"stay_before_payback": bool(stay > 0 and stay < f["payback_years"])}


# --------------------------------------------------------------------------
# Module J - final summary and confidence
# --------------------------------------------------------------------------
def compose_summary(f, P):
    cf = f.get("_confidence", {})
    keys = ["system_type"] + (["battery_type"] if f.get("battery_needed") else [])
    confidence = min([cf.get(k, 1.0) for k in keys] or [1.0])
    battery = (f"{f['battery_kwh']:.1f} kWh {f['battery_type']} battery bank"
               if f.get("battery_needed") else "no battery")
    text = (f"Install a {f['system_kw']:.2f} kW {f['system_type']} solar system "
            f"({f['panel_count']} × {f['panel_watt']} W panels) with a {f['inverter_kw']} kW inverter "
            f"and {battery}.")
    return {"final_recommendation": text, "overall_confidence": round(confidence * 100)}


CALCULATIONS = {
    "analyse_load": analyse_load,
    "analyse_site": analyse_site,
    "set_backup_hours": set_backup_hours,
    "size_array": size_array,
    "size_inverter": size_inverter,
    "size_battery": size_battery,
    "estimate_cost": estimate_cost,
    "financials": financials,
    "compare_stay": compare_stay,
    "compose_summary": compose_summary,
}
