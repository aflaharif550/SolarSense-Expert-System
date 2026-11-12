"""Builds a self-contained, printable HTML report of one SolarSense consultation."""

import datetime
import html

from engine.diagnosis import build_diagnosis

INPUT_LABELS = [
    ("city", "City"), ("property_type", "Property type"), ("phase", "Electricity connection"),
    ("grid_status", "Grid status"), ("monthly_units", "Monthly units (kWh)"),
    ("monthly_bill", "Monthly bill (Rs)"), ("sanctioned_load_kw", "Sanctioned load (kW)"),
    ("outage_hours", "Load-shedding (hours/day)"), ("night_outages", "Outages at night"),
    ("desired_backup_hours", "Desired backup (hours)"), ("existing_backup", "Existing backup"),
    ("voltage_issues", "Voltage fluctuations"), ("roof_type", "Installation space"),
    ("roof_area", "Usable area (sq ft)"), ("shading", "Shading"), ("orientation", "Orientation"),
    ("ownership", "Ownership"), ("budget", "Budget (Rs)"), ("priority", "Priority"),
    ("net_metering_interest", "Interested in net billing"), ("stay_years", "Planned stay (years)"),
]


def _e(value):
    return html.escape(str(value))


def _fmt(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:,}"
    return str(value)


def build_html_report(inputs, result):
    f = result["facts"]
    now = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
    feasible = f.get("site_feasible", False)

    rows_in = "".join(f"<tr><td>{_e(label)}</td><td>{_e(_fmt(inputs.get(key, '')))}</td></tr>"
                      for key, label in INPUT_LABELS)
    appliances = ", ".join(f"{k} × {v}" for k, v in inputs.get("appliances", {}).items() if v) or "None listed"
    critical = ", ".join(inputs.get("critical_loads", [])) or "None selected"

    design = ""
    if feasible:
        battery = (f"{f.get('battery_kwh', 0):.2f} kWh {f.get('battery_type')} "
                   f"({f.get('battery_units')} units, {f.get('battery_voltage', '')})"
                   if f.get("battery_needed") else "Not required")
        spec = [
            ("System type", f.get("system_type")),
            ("Solar array", f"{f.get('system_kw')} kW ({f.get('panel_count')} × {f.get('panel_watt')} W panels)"),
            ("Inverter", f"{f.get('inverter_kw')} kW {f.get('inverter_technology')} ({f.get('inverter_phase')})"),
            ("Battery bank", battery),
            ("Mounting", f.get("mounting")),
            ("Net billing", f.get("net_metering_status")),
            ("Estimated cost", f"Rs {f.get('total_cost', 0):,}"),
            ("Budget status", f.get("budget_status")),
            ("Annual savings", f"Rs {f.get('annual_savings', 0):,}"),
            ("Payback period", f"{f.get('payback_years')} years ({f.get('financial_verdict')})"),
            ("Solar coverage", f"{f.get('solar_fraction_pct')}% of daily usage"),
            ("CO2 avoided", f"{f.get('co2_tonnes_per_year')} tonnes per year"),
        ]
        design = "".join(f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in spec)
        costs = "".join(f"<tr><td>{_e(k)}</td><td>Rs {v:,}</td></tr>"
                        for k, v in f.get("cost_breakdown", {}).items())
        design = (f"<h2>Recommended system</h2><table>{design}</table>"
                  f"<h2>Cost breakdown</h2><table>{costs}"
                  f"<tr class='total'><td>Total</td><td>Rs {f.get('total_cost', 0):,}</td></tr></table>")
        if f.get("phase_plan"):
            design += f"<p><b>Phase plan:</b> {_e(f['phase_plan'])}</p>"

    def items(name, title):
        entries = f.get(name, [])
        if not entries:
            return ""
        lis = "".join(f"<li><b>{_e(e['rule'])}</b> {_e(e['text'])}</li>" for e in entries)
        return f"<h2>{title}</h2><ul>{lis}</ul>"

    diag = build_diagnosis(result)
    summary = diag["summary"]
    profile_rows = "".join(
        f"<tr><td>{_e(i['title'])}</td><td>{_e(i['value'])}</td><td>{_e(i['status'])}</td>"
        f"<td>{_e(i['evidence'])}</td><td>{_e(i['rule'])}</td></tr>" for i in diag["profile"])
    problem_rows = "".join(
        f"<tr><td class='sev-{_e(p['severity'])}'>{_e(p['severity'])}</td><td>{_e(p['problem'])}</td>"
        f"<td>{_e(p['category'])}</td><td>{_e(p['finding'])}</td><td>{_e(p['rule'])}</td></tr>"
        for p in diag["problems"]) or "<tr><td colspan='5'>No problems detected.</td></tr>"
    diagnosis_html = (
        f"<h2>Diagnosis</h2><div class='diag'><b>Overall: {_e(summary['level'])}.</b> {_e(summary['headline'])}</div>"
        f"<h3>Situation profile</h3><table><tr><th>Aspect</th><th>Result</th><th>Status</th><th>Evidence</th>"
        f"<th>Rule</th></tr>{profile_rows}</table>"
        f"<h3>Problems detected ({summary['total']})</h3><table><tr><th>Severity</th><th>Problem</th>"
        f"<th>Category</th><th>Finding</th><th>Rule</th></tr>{problem_rows}</table>")

    trace = "".join(
        f"<tr><td>{t['cycle']}</td><td>{_e(t['id'])}</td><td>{_e(t['name'])}</td>"
        f"<td>{_e(t['module'])}</td></tr>" for t in result["trace"])

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SolarSense Report</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; color: #1f2937; max-width: 900px; margin: 30px auto; padding: 0 16px; }}
header {{ background: #1B2A41; color: #fff; padding: 22px 26px; border-radius: 12px; }}
header h1 {{ margin: 0 0 4px 0; }} header p {{ margin: 0; color: #e5e7eb; }}
.verdict {{ background: #FFF8E7; border: 1px solid #F5D58C; padding: 14px 18px; border-radius: 10px; margin: 18px 0; }}
h2 {{ color: #1B2A41; border-bottom: 2px solid #F5A623; padding-bottom: 4px; margin-top: 28px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
td, th {{ border: 1px solid #e5e7eb; padding: 7px 10px; text-align: left; font-size: 14px; vertical-align: top; }}
td:first-child {{ color: #4b5563; }}
tr.total td {{ font-weight: bold; background: #FFF8E7; }}
li {{ margin-bottom: 6px; }}
.small {{ font-size: 12px; color: #6b7280; }}
h3 {{ color: #1B2A41; margin: 18px 0 4px 0; font-size: 15px; }}
.diag {{ background: #F8FAFC; border: 1px solid #e5e7eb; padding: 10px 14px; border-radius: 8px; }}
td.sev-Critical {{ color: #B42318; font-weight: bold; }} td.sev-High {{ color: #E76F51; font-weight: bold; }}
td.sev-Medium {{ color: #9a6206; font-weight: bold; }} td.sev-Low {{ color: #4C8BF5; font-weight: bold; }}
</style></head><body>
<header><h1>☀️ SolarSense Consultation Report</h1>
<p>Rule-based expert system for residential solar decisions in Pakistan · Generated {now}</p></header>
<div class="verdict"><b>Recommendation:</b> {_e(f.get('final_recommendation', ''))}<br>
<b>Confidence:</b> {_e(f.get('overall_confidence', ''))}% ({_e(f.get('confidence_label', ''))})</div>
{diagnosis_html}
{design}
{items('warnings', 'Warnings')}
{items('recommendations', 'Recommendations')}
{items('notes', 'Notes')}
<h2>Your inputs</h2><table>{rows_in}
<tr><td>Appliances</td><td>{_e(appliances)}</td></tr>
<tr><td>Critical loads during outages</td><td>{_e(critical)}</td></tr></table>
<h2>Reasoning trace ({len(result['trace'])} rules fired in {result['cycles']} cycles)</h2>
<table><tr><th>Cycle</th><th>Rule</th><th>Name</th><th>Module</th></tr>{trace}</table>
<p class="small">Prices, sun hours and policy values are indicative estimates. This report supports a decision but does not
replace a site survey by a qualified installer. Tip: use your browser's Print → Save as PDF to keep a PDF copy.</p>
</body></html>"""
