"""
SolarSense knowledge base.

Every rule is an IF-THEN production rule written as data, separate from the
inference engine. Fields:
  id        unique rule number (R001 ...)
  module    knowledge module the rule belongs to
  name      short human-readable title
  if        list of conditions (fact, operator[, value]) joined with AND
  set       facts to assert                       } THEN part
  append    advice to add (warnings / recommendations / notes)
  calc      name of a calculation to run          }
  why       plain-English justification (shown by the explanation facility)
  salience  priority used for conflict resolution (higher fires first)
  cf        certainty factor of the conclusion (0-1)

Salience bands: 100 data derivation, 50-60 classification, 20-45 decisions,
0 normal, -50 defaults (only fire when nothing more specific applies).
"""

# Frequently used values ------------------------------------------------------
NO_GRID = "No grid connection"
BACKUP = "Reliable backup power"
SAVINGS = "Maximum bill savings"
CHEAPEST = "Lowest upfront cost"
BALANCED = "Balanced"
LITHIUM = "Lithium (LiFePO4)"
TUBULAR = "Tubular lead-acid"
OUTAGE_LEVELS = ["Mild", "Moderate", "Severe"]

MODULES = {
    "A": "Load Assessment",
    "B": "Outage & Backup Needs",
    "C": "Site & Roof Suitability",
    "D": "System Type & Sizing",
    "E": "Battery Selection",
    "F": "Inverter Selection",
    "G": "Net Billing (Grid Export)",
    "H": "Cost, Budget & Payback",
    "I": "Safety & Compliance",
    "J": "Final Verdict",
}

RULES = []


def rule(rid, module, name, conditions, why, set=None, append=None, calc=None,
         salience=0, cf=1.0):
    RULES.append({
        "id": rid,
        "module": f"{module}. {MODULES[module]}",
        "name": name,
        "if": conditions,
        "set": set or {},
        "append": append or {},
        "calc": calc,
        "why": why,
        "salience": salience,
        "cf": cf,
        "order": len(RULES),
    })


# =============================================================================
# MODULE A - LOAD ASSESSMENT
# =============================================================================
rule("R001", "A", "Analyse energy consumption",
     [("monthly_units", "exists"), ("appliances", "exists"), ("daily_kwh", "not_exists")],
     "Before any decision, the bill and appliance list are converted into daily energy (kWh), peak load (kW) and tariff.",
     calc="analyse_load", salience=100)
rule("R002", "A", "Low consumption household",
     [("daily_kwh", "<", 5)], "Under 5 kWh/day is a small load (fans, lights, fridge).",
     set={"consumption_level": "Low"}, salience=50)
rule("R003", "A", "Moderate consumption household",
     [("daily_kwh", "between", (5, 12))], "5-12 kWh/day is a typical home without heavy AC use.",
     set={"consumption_level": "Moderate"}, salience=50)
rule("R004", "A", "High consumption household",
     [("daily_kwh", "between", (12, 25))], "12-25 kWh/day usually means one or two ACs in summer.",
     set={"consumption_level": "High"}, salience=50)
rule("R005", "A", "Very high consumption",
     [("daily_kwh", ">=", 25)], "Above 25 kWh/day is a large home or commercial load.",
     set={"consumption_level": "Very High"}, salience=50)
rule("R006", "A", "Light peak load",
     [("peak_load_kw", "<", 3)], "Peak demand under 3 kW can run on a small inverter.",
     set={"load_class": "Light"}, salience=50)
rule("R007", "A", "Medium peak load",
     [("peak_load_kw", "between", (3, 6))], "3-6 kW peak demand needs a mid-size inverter.",
     set={"load_class": "Medium"}, salience=50)
rule("R008", "A", "Heavy peak load",
     [("peak_load_kw", ">=", 6)], "6 kW or more peak demand needs a large inverter.",
     set={"load_class": "Heavy"}, salience=50)
rule("R009", "A", "Non-inverter AC detected",
     [("noninverter_ac_count", ">", 0)],
     "Non-inverter ACs use roughly 30-50% more energy than inverter ACs, which inflates the solar system size.",
     set={"efficiency_upgrade": True},
     append={"recommendations": "Replace your {noninverter_ac_count} non-inverter AC(s) with inverter ACs. This cuts AC energy use by about a third and lets you buy a smaller solar system."},
     salience=50)
rule("R010", "A", "Motor load detected",
     [("has_motor_load", "==", True)],
     "Pumps and washing machines draw 3-5 times their running current at start-up.",
     append={"notes": "Motor loads (water pump / washing machine) are present, so the inverter is sized with extra surge capacity."},
     salience=50)
rule("R011", "A", "Electric geyser detected",
     [("has_geyser", "==", True)],
     "A 2 kW geyser can use more energy than the rest of the house and should not run from solar batteries.",
     append={"warnings": "Electric geysers are very energy-hungry. Use a gas or solar water heater instead, and never run a geyser on battery backup."},
     salience=50)
rule("R012", "A", "Appliance list incomplete",
     [("appliance_ratio", "<", 0.6), ("monthly_units", ">", 0)],
     "If listed appliances explain much less than the bill, some loads are missing; the bill is the more reliable figure.",
     append={"notes": "Your appliance list explains only about {appliance_ratio_pct}% of your bill. Sizing uses your actual bill units, which is more reliable."},
     salience=50)
rule("R013", "A", "Appliance list overestimates usage",
     [("appliance_ratio", ">", 1.5), ("monthly_units", ">", 0)],
     "If listed appliances exceed the bill by 50%, usage hours are probably overstated; the bill is used instead.",
     append={"notes": "Your appliance list suggests about {appliance_ratio_pct}% of your billed usage, so real usage hours are lower than assumed. Sizing follows your bill."},
     salience=50)
rule("R014", "A", "High electricity tariff",
     [("effective_tariff", ">=", 50)],
     "At Rs 50+ per unit every solar unit saves a lot of money, so solar pays back quickly.",
     set={"tariff_band": "High", "solar_attractiveness": "High"}, salience=50)
rule("R015", "A", "Medium electricity tariff",
     [("effective_tariff", "between", (30, 50))],
     "Rs 30-50 per unit still makes solar worthwhile.",
     set={"tariff_band": "Medium", "solar_attractiveness": "Medium"}, salience=50)
rule("R016", "A", "Low electricity tariff",
     [("effective_tariff", "<", 30)],
     "Below Rs 30 per unit, savings per solar unit are small and payback is slower.",
     set={"tariff_band": "Low", "solar_attractiveness": "Low"},
     append={"notes": "Your effective tariff is only Rs {effective_tariff}/unit, so savings per unit are modest and payback will be slower."},
     salience=50)
rule("R017", "A", "Very high load on single-phase supply",
     [("consumption_level", "==", "Very High"), ("phase", "==", "Single-phase")],
     "Very large loads on a single-phase connection often hit the connection's limit.",
     append={"warnings": "Your consumption is very high for a single-phase connection. Consider asking your DISCO for a three-phase connection."},
     salience=40)

# =============================================================================
# MODULE B - OUTAGE & BACKUP NEEDS
# =============================================================================
rule("R018", "B", "Site without grid",
     [("grid_status", "==", NO_GRID)],
     "With no grid connection, solar must supply all energy, day and night.",
     set={"outage_severity": "Off-grid site"}, salience=60)
rule("R019", "B", "No load-shedding",
     [("grid_status", "!=", NO_GRID), ("outage_hours", "==", 0)],
     "Zero daily outage hours means backup is not a priority.",
     set={"outage_severity": "None"}, salience=55)
rule("R020", "B", "Mild load-shedding",
     [("grid_status", "!=", NO_GRID), ("outage_hours", "between", (1, 4))],
     "1-3 hours of daily outages is mild.",
     set={"outage_severity": "Mild"}, salience=55)
rule("R021", "B", "Moderate load-shedding",
     [("grid_status", "!=", NO_GRID), ("outage_hours", "between", (4, 7))],
     "4-6 hours of daily outages seriously disrupts a household.",
     set={"outage_severity": "Moderate"}, salience=55)
rule("R022", "B", "Severe load-shedding",
     [("grid_status", "!=", NO_GRID), ("outage_hours", ">=", 7)],
     "7 or more hours of daily outages is severe.",
     set={"outage_severity": "Severe"}, salience=55)
rule("R023", "B", "Backup needed for critical loads",
     [("outage_severity", "in", ["Moderate", "Severe"]), ("critical_load_kw", ">", 0), ("backup_required", "not_exists")],
     "Moderate or severe outages plus essential loads means power must continue during outages.",
     set={"backup_required": True}, salience=50, cf=0.95)
rule("R024", "B", "Backup needed (no critical loads listed)",
     [("outage_severity", "in", ["Moderate", "Severe"]), ("critical_load_kw", "==", 0), ("backup_required", "not_exists")],
     "Long outages need backup even if the user did not mark critical loads; fans and lights are assumed.",
     set={"backup_required": True, "critical_assumed": True},
     append={"notes": "You did not mark any critical loads, so backup is sized for about 40% of your peak load (fans, lights, fridge)."},
     salience=50, cf=0.85)
rule("R025", "B", "User prioritises backup",
     [("priority", "==", BACKUP), ("grid_status", "!=", NO_GRID), ("backup_required", "not_exists")],
     "The user explicitly chose reliable backup as the top priority.",
     set={"backup_required": True}, salience=52)
rule("R026", "B", "Mild outages: battery optional",
     [("outage_severity", "==", "Mild"), ("priority", "not_in", [BACKUP, CHEAPEST]), ("backup_required", "not_exists")],
     "Short outages do not justify battery cost now, but a battery-ready system keeps the option open.",
     set={"backup_required": False, "battery_optional": True}, salience=50, cf=0.8)
rule("R027", "B", "Mild outages on a tight budget",
     [("outage_severity", "==", "Mild"), ("priority", "==", CHEAPEST), ("backup_required", "not_exists")],
     "When lowest cost matters most and outages are short, backup is skipped.",
     set={"backup_required": False}, salience=50, cf=0.85)
rule("R028", "B", "Reliable grid: no backup",
     [("outage_severity", "==", "None"), ("priority", "!=", BACKUP), ("backup_required", "not_exists")],
     "With no outages, batteries only add cost.",
     set={"backup_required": False}, salience=50, cf=0.95)
rule("R029", "B", "Off-grid site needs storage",
     [("outage_severity", "==", "Off-grid site"), ("backup_required", "not_exists")],
     "Without a grid, night-time power can only come from batteries.",
     set={"backup_required": True}, salience=50)
rule("R030", "B", "Night-time outages",
     [("night_outages", "==", True), ("backup_required", "==", True), ("grid_status", "!=", NO_GRID)],
     "There is no sunlight at night, so the battery alone must carry night outages.",
     append={"notes": "Outages happen at night, so the battery is sized to cover the full outage period without solar input."},
     salience=10)
rule("R031", "B", "Work out backup hours",
     [("backup_required", "==", True), ("grid_status", "!=", NO_GRID), ("backup_hours", "not_exists")],
     "Backup hours = the larger of the user's wish and the outage duration (halved for daytime outages, since solar helps).",
     calc="set_backup_hours", salience=40)
rule("R032", "B", "Existing UPS can be replaced",
     [("existing_backup", "==", "UPS / Inverter"), ("backup_required", "==", True)],
     "A hybrid inverter does the UPS's job and charges batteries from solar.",
     append={"recommendations": "Your hybrid inverter will replace the old UPS. Old batteries under about 2 years old may be reused only if they match the new system voltage."},
     salience=10)
rule("R033", "B", "Generator on site",
     [("existing_backup", "==", "Generator")],
     "Hybrid/off-grid inverters can use a generator as a backup charging source, cutting fuel use.",
     append={"recommendations": "Keep your generator as an emergency source. Choose an inverter with a generator input so solar handles daily backup and fuel use drops."},
     salience=10)
rule("R034", "B", "Voltage fluctuations reported",
     [("voltage_issues", "==", True)],
     "Hybrid and off-grid inverters supply regulated output, protecting appliances from unstable grid voltage.",
     append={"notes": "Because your grid voltage fluctuates, choose an inverter with a wide input voltage range and proper surge protection."},
     salience=10)
rule("R035", "B", "AC selected as critical load",
     [("critical_has_ac", "==", True), ("backup_required", "==", True)],
     "An AC on battery drains even a large battery bank within a few hours.",
     append={"warnings": "You marked an AC as a critical load. Running ACs on batteries needs a very large and expensive battery bank. Limit AC use during outages if possible."},
     salience=10)
rule("R036", "B", "Reliable grid confirmed",
     [("outage_severity", "==", "None"), ("backup_required", "==", False)],
     "No outages and no backup need is the cheapest and fastest-payback situation.",
     append={"notes": "Your grid is reliable, so no battery is needed. This gives the fastest payback."},
     salience=10)

# =============================================================================
# MODULE C - SITE & ROOF SUITABILITY
# =============================================================================
rule("R037", "C", "Analyse site and climate",
     [("city", "exists"), ("roof_area", "exists"), ("sun_hours", "not_exists")],
     "City determines sun hours and climate; roof area determines how many kW fit.",
     calc="analyse_site", salience=100)
rule("R038", "C", "No usable installation space",
     [("roof_type", "==", "No usable space"), ("site_feasible", "not_exists")],
     "Panels need roof or ground space; without it solar is not feasible.",
     set={"site_feasible": False},
     append={"warnings": "No usable roof or ground space was reported, so a solar installation is not feasible at this site."},
     salience=60)
rule("R039", "C", "Roof too small",
     [("roof_capacity_kw", "<", 1), ("roof_type", "!=", "No usable space"), ("site_feasible", "not_exists")],
     "Under about 75 sq ft cannot hold even 1 kW of panels.",
     set={"site_feasible": False},
     append={"warnings": "Your usable area fits less than 1 kW of panels (about {roof_capacity_kw:.1f} kW), which is too small for a practical system."},
     salience=60)
rule("R040", "C", "Site is feasible",
     [("site_feasible", "not_exists")],
     "If no feasibility problem has been found, the site is assumed suitable.",
     set={"site_feasible": True}, salience=-40)
rule("R041", "C", "Heavy shading",
     [("shading", "==", "Heavy shading")],
     "Heavy shade can cut output by a third or more.",
     set={"shading_factor": 0.65},
     append={"warnings": "Heavy shading cuts output by about 35%. Trim trees or move panels to an unshaded area if possible."},
     salience=50)
rule("R042", "C", "Partial shading",
     [("shading", "==", "Partial shading")],
     "Morning or evening shade reduces output by roughly 15%.",
     set={"shading_factor": 0.85},
     append={"notes": "Partial shading reduces output by about 15%. Panels are sized up to compensate."},
     salience=50)
rule("R043", "C", "No shading",
     [("shading", "==", "No shading")], "An unshaded site gets full output.",
     set={"shading_factor": 1.0}, salience=50)
rule("R044", "C", "South-facing or flat roof",
     [("orientation", "==", "South-facing / flat roof")],
     "In Pakistan (northern hemisphere) south-facing panels collect the most sunlight; flat roofs allow south tilt.",
     set={"orientation_factor": 1.0}, salience=50)
rule("R045", "C", "East-West roof",
     [("orientation", "==", "East-West")],
     "East-west panels lose about 10% compared with south-facing ones.",
     set={"orientation_factor": 0.9},
     append={"notes": "East-West orientation produces about 10% less energy than south-facing panels."},
     salience=50)
rule("R046", "C", "North-facing roof",
     [("orientation", "==", "North-facing")],
     "North-facing panels face away from the sun in Pakistan.",
     set={"orientation_factor": 0.78},
     append={"warnings": "North-facing panels lose over 20% output. Use a tilted structure so panels face south."},
     salience=50)
rule("R047", "C", "Dusty city",
     [("dusty", "==", True)],
     "Dust on panels reduces output; regular cleaning restores it.",
     set={"dust_factor": 0.95},
     append={"recommendations": "Your area is dusty. Clean the panels with plain water every 1-2 weeks to avoid losing 5-10% output."},
     salience=50)
rule("R048", "C", "Low-dust city",
     [("dusty", "==", False)], "Less dust means lower soiling losses.",
     set={"dust_factor": 0.98}, salience=50)
rule("R049", "C", "Coastal city",
     [("coastal", "==", True)],
     "Salty sea air corrodes ordinary steel structures and fasteners.",
     append={"recommendations": "Coastal city: use hot-dip galvanized or aluminium structures with stainless-steel bolts to prevent rust."},
     salience=10)
rule("R050", "C", "Hot climate",
     [("hot_climate", "==", True)],
     "Panels lose efficiency as they heat up; airflow under them helps.",
     append={"notes": "Hot climate: panels are mounted with an air gap underneath to reduce heat losses. Temperature loss is included in the performance ratio."},
     salience=10)
rule("R051", "C", "RCC concrete roof",
     [("roof_type", "==", "RCC concrete roof")],
     "Flat concrete roofs use elevated steel structures, which also keep roof space usable.",
     set={"mounting": "Elevated galvanized steel structure", "mounting_key": "RCC"}, salience=50)
rule("R052", "C", "Metal / tin roof",
     [("roof_type", "==", "Metal / tin sheet roof")],
     "Sheet roofs use rails clamped to the roof, which is cheaper but needs a strength check.",
     set={"mounting": "Rail-and-clamp mounting on metal roof", "mounting_key": "Metal"},
     append={"notes": "On a sheet roof, have the roof frame checked before installing panels."},
     salience=50)
rule("R053", "C", "Ground installation",
     [("roof_type", "==", "Ground / open space")],
     "Open ground allows ideal tilt and easy cleaning.",
     set={"mounting": "Ground-mounted steel frame", "mounting_key": "Ground"}, salience=50)
rule("R054", "C", "Tenant occupant",
     [("ownership", "==", "Tenant")],
     "Tenants need the owner's permission and may move before payback.",
     append={"warnings": "As a tenant you need written permission from the owner before installing panels."},
     salience=10)
rule("R055", "C", "Apartment / flat",
     [("property_type", "==", "Apartment / Flat")],
     "Apartment roofs are shared, so space and permission are limited.",
     append={"warnings": "Apartment roofs are usually shared. Get a no-objection letter from your building management or society first."},
     salience=10)
rule("R056", "C", "Roof limits system size",
     [("roof_limited", "==", True)],
     "If the needed kW does not fit, the system is capped at what the roof can hold.",
     append={"warnings": "You need about {required_kw:.1f} kW but your space fits only about {roof_capacity_kw:.1f} kW. The system has been capped to fit your roof."},
     salience=10)

# =============================================================================
# MODULE D - SYSTEM TYPE & SIZING
# =============================================================================
rule("R057", "D", "Off-grid system for no-grid site",
     [("grid_status", "==", NO_GRID), ("system_type", "not_exists")],
     "Without a grid connection, only an off-grid system with batteries can work.",
     set={"system_type": "Off-Grid"}, salience=40)
rule("R058", "D", "Hybrid system for backup needs",
     [("backup_required", "==", True), ("grid_status", "!=", NO_GRID), ("system_type", "not_exists")],
     "A hybrid inverter uses grid, solar and battery together, so power continues during outages.",
     set={"system_type": "Hybrid"}, salience=40, cf=0.95)
rule("R059", "D", "Battery-ready hybrid",
     [("backup_required", "==", False), ("battery_optional", "==", True), ("system_type", "not_exists")],
     "A hybrid inverter without batteries works like on-grid now, and batteries can be added later.",
     set={"system_type": "Hybrid"},
     append={"recommendations": "Start without batteries. Your hybrid inverter is battery-ready, so you can add batteries later if outages increase."},
     salience=40, cf=0.8)
rule("R060", "D", "On-grid system",
     [("backup_required", "==", False), ("grid_status", "!=", NO_GRID), ("system_type", "not_exists")],
     "With no backup need, an on-grid system is the cheapest and most efficient choice.",
     set={"system_type": "On-Grid"}, salience=30, cf=0.9)
rule("R061", "D", "On-grid shuts down during outages",
     [("system_type", "==", "On-Grid"), ("outage_severity", "in", OUTAGE_LEVELS)],
     "On-grid inverters must switch off when the grid fails (anti-islanding) to protect line workers.",
     append={"warnings": "An on-grid system switches OFF during load-shedding for safety. You will have no solar power during outages."},
     salience=10)
rule("R062", "D", "Off-grid sizing margin",
     [("system_type", "==", "Off-Grid"), ("coverage_target", "not_exists")],
     "Off-grid systems need extra generation to recharge batteries on cloudy days.",
     set={"coverage_target": 1.15}, salience=45)
rule("R063", "D", "Size for maximum savings",
     [("priority", "==", SAVINGS), ("system_type", "exists"), ("coverage_target", "not_exists")],
     "To maximise savings, solar should cover all daily usage.",
     set={"coverage_target": 1.0}, salience=30)
rule("R064", "D", "Size for balanced value",
     [("priority", "==", BALANCED), ("system_type", "exists"), ("coverage_target", "not_exists")],
     "Covering about 85% of usage gives most of the savings at lower cost.",
     set={"coverage_target": 0.85}, salience=30)
rule("R065", "D", "Size for lowest cost",
     [("priority", "==", CHEAPEST), ("system_type", "exists"), ("coverage_target", "not_exists")],
     "A smaller system (60% coverage) keeps the upfront cost low.",
     set={"coverage_target": 0.6}, salience=30)
rule("R066", "D", "Size for backup priority",
     [("priority", "==", BACKUP), ("system_type", "exists"), ("coverage_target", "not_exists")],
     "When backup matters most, part of the budget goes to batteries, so panels cover about 75%.",
     set={"coverage_target": 0.75}, salience=30)
rule("R067", "D", "Low export value",
     [("net_metering_interest", "==", "Yes"), ("export_value_ratio", "<", 0.5), ("grid_status", "!=", NO_GRID)],
     "Under net billing, exported units earn far less than the price of imported units, so oversizing for export does not pay.",
     append={"notes": "Exported units earn only Rs {export_rate}/unit, while you pay Rs {effective_tariff}/unit. The system is sized for self-use, not for selling power."},
     salience=10)
rule("R068", "D", "Calculate array size",
     [("coverage_target", "exists"), ("shading_factor", "exists"), ("orientation_factor", "exists"),
      ("dust_factor", "exists"), ("site_feasible", "==", True), ("daily_kwh", "exists"), ("system_kw", "not_exists")],
     "kW needed = daily kWh × coverage ÷ (sun hours × performance ratio × shading × orientation × dust), rounded up to whole panels.",
     calc="size_array", salience=20)
rule("R069", "D", "High solar coverage",
     [("solar_fraction", ">=", 0.9)], "Generating 90%+ of daily use gives high energy independence.",
     set={"energy_independence": "High"}, salience=10)
rule("R070", "D", "Partial solar coverage",
     [("solar_fraction", "between", (0.5, 0.9))], "50-90% coverage still cuts most daytime bills.",
     set={"energy_independence": "Partial"}, salience=10)
rule("R071", "D", "Low solar coverage",
     [("solar_fraction", "<", 0.5)], "Under 50% coverage leaves most consumption on the grid.",
     set={"energy_independence": "Low"},
     append={"notes": "Solar will cover only about {solar_fraction_pct}% of your usage. Consider reducing loads or adding space later."},
     salience=10)
rule("R072", "D", "Very small system",
     [("system_kw", "<", 2), ("system_type", "!=", "Off-Grid")],
     "Under 2 kW, fixed costs (inverter, installation) make each kW expensive.",
     append={"notes": "Very small systems have a higher cost per kW. Make sure the space and budget cannot support a larger system."},
     salience=10)

# =============================================================================
# MODULE E - BATTERY SELECTION
# =============================================================================
rule("R073", "E", "No battery required",
     [("backup_required", "==", False), ("battery_needed", "not_exists")],
     "Without a backup need, batteries only add cost and maintenance.",
     set={"battery_needed": False, "battery_type": "None", "battery_kwh": 0, "battery_units": 0},
     salience=35)
rule("R074", "E", "Off-grid storage",
     [("system_type", "==", "Off-Grid"), ("battery_needed", "not_exists")],
     "Off-grid homes run on batteries every night, about 14 hours from sunset to morning.",
     set={"battery_needed": True, "backup_hours": 14}, salience=35)
rule("R075", "E", "Hybrid storage",
     [("system_type", "==", "Hybrid"), ("backup_required", "==", True), ("battery_needed", "not_exists")],
     "A hybrid system with a backup need requires a battery bank.",
     set={"battery_needed": True}, salience=35)
rule("R076", "E", "Lithium for severe outages",
     [("battery_needed", "==", True), ("outage_severity", "==", "Severe"), ("battery_type", "not_exists")],
     "Daily deep cycling wears out lead-acid batteries; LiFePO4 lasts 3,000-6,000 cycles.",
     set={"battery_type": LITHIUM}, salience=25, cf=0.9)
rule("R077", "E", "Lithium for off-grid",
     [("battery_needed", "==", True), ("system_type", "==", "Off-Grid"), ("battery_type", "not_exists")],
     "Off-grid batteries cycle every day, so long-life lithium is the economic choice.",
     set={"battery_type": LITHIUM}, salience=25, cf=0.9)
rule("R078", "E", "Tubular for lowest cost",
     [("battery_needed", "==", True), ("priority", "==", CHEAPEST), ("battery_type", "not_exists")],
     "Tubular lead-acid batteries cost about half as much upfront.",
     set={"battery_type": TUBULAR}, salience=20, cf=0.85)
rule("R079", "E", "Lithium by default",
     [("battery_needed", "==", True), ("battery_type", "not_exists")],
     "LiFePO4 is safer, maintenance-free and cheaper over its life, so it is the default choice.",
     set={"battery_type": LITHIUM}, salience=-50, cf=0.75)
rule("R080", "E", "Lithium depth of discharge",
     [("battery_type", "==", LITHIUM), ("battery_dod", "not_exists")],
     "LiFePO4 can safely use 90% of its capacity.",
     set={"battery_dod": 0.9}, salience=30)
rule("R081", "E", "Lead-acid depth of discharge",
     [("battery_type", "==", TUBULAR), ("battery_dod", "not_exists")],
     "Lead-acid batteries should only be discharged to 50% to protect their life.",
     set={"battery_dod": 0.5}, salience=30)
rule("R082", "E", "Calculate battery bank",
     [("battery_needed", "==", True), ("battery_dod", "exists"), ("backup_hours", "exists"),
      ("inverter_kw", "exists"), ("battery_kwh", "not_exists")],
     "Capacity = backup load × hours ÷ (depth of discharge × efficiency), rounded to whole battery units.",
     calc="size_battery", salience=15)
rule("R083", "E", "Very large battery bank",
     [("battery_kwh", ">", 15)],
     "Banks over 15 kWh are expensive; trimming backup loads saves a lot.",
     append={"warnings": "The battery bank is large ({battery_kwh:.1f} kWh). Reducing critical loads or backup hours will cut cost noticeably."},
     salience=10)
rule("R084", "E", "Lead-acid maintenance",
     [("battery_type", "==", TUBULAR)],
     "Flooded tubular batteries need water top-ups and give off gas while charging.",
     append={"recommendations": "Tubular batteries: top up with distilled water monthly and keep them in a ventilated place."},
     salience=10)
rule("R085", "E", "Batteries in hot climate",
     [("hot_climate", "==", True), ("battery_needed", "==", True)],
     "Heat shortens battery life; every 10 °C rise can halve lead-acid life.",
     append={"recommendations": "Keep batteries indoors in a shaded, ventilated spot, away from direct sun."},
     salience=10)
rule("R086", "E", "Lithium compatibility",
     [("battery_type", "==", LITHIUM)],
     "LiFePO4 batteries need a BMS that communicates with the inverter for safe charging.",
     append={"recommendations": "Choose a LiFePO4 battery with a built-in BMS that communicates with your inverter (CAN or RS485)."},
     salience=10)
rule("R087", "E", "Battery can be added later",
     [("battery_optional", "==", True)],
     "Keeping the system battery-ready protects the user if outages get worse.",
     append={"notes": "If load-shedding increases later, a battery can be added to your hybrid inverter without replacing anything."},
     salience=10)

# =============================================================================
# MODULE F - INVERTER SELECTION
# =============================================================================
rule("R088", "F", "Surge margin for motors",
     [("has_motor_load", "==", True), ("surge_factor", "not_exists")],
     "Motors need a 50% inverter margin to start.",
     set={"surge_factor": 1.5}, salience=30)
rule("R089", "F", "Surge margin for ACs",
     [("ac_count", ">", 0), ("surge_factor", "not_exists")],
     "AC compressors need about 35% extra capacity at start-up.",
     set={"surge_factor": 1.35}, salience=25)
rule("R090", "F", "Standard surge margin",
     [("surge_factor", "not_exists")],
     "A 25% margin keeps the inverter from running at full load.",
     set={"surge_factor": 1.25}, salience=-50)
rule("R091", "F", "Calculate inverter size",
     [("system_kw", "exists"), ("system_type", "exists"), ("surge_factor", "exists"), ("inverter_kw", "not_exists")],
     "On-grid inverters are sized to the panels; hybrid/off-grid inverters must also carry peak load with surge margin.",
     calc="size_inverter", salience=18)
rule("R092", "F", "Grid-tie inverter",
     [("system_type", "==", "On-Grid")], "On-grid systems use a grid-tie string inverter.",
     set={"inverter_technology": "Grid-tie (on-grid) string inverter"}, salience=10)
rule("R093", "F", "Hybrid inverter",
     [("system_type", "==", "Hybrid")], "Hybrid systems need an inverter that handles grid, solar and battery together.",
     set={"inverter_technology": "Hybrid inverter with MPPT and battery port"}, salience=10)
rule("R094", "F", "Off-grid inverter",
     [("system_type", "==", "Off-Grid")], "Off-grid systems need an inverter with a built-in solar charge controller.",
     set={"inverter_technology": "Off-grid inverter with built-in MPPT charger"}, salience=10)
rule("R095", "F", "Three-phase inverter",
     [("phase", "==", "Three-phase"), ("inverter_kw", ">=", 10)],
     "Large inverters on a three-phase supply should balance power across all phases.",
     set={"inverter_phase": "Three-phase"}, salience=10)
rule("R096", "F", "Large inverter on single-phase",
     [("phase", "==", "Single-phase"), ("inverter_kw", ">=", 10)],
     "Inverters of 10 kW or more usually need a three-phase connection.",
     set={"inverter_phase": "Single-phase (three-phase upgrade advised)"},
     append={"warnings": "A {inverter_kw} kW inverter is large for a single-phase connection. Ask your DISCO about upgrading to three-phase."},
     salience=10)
rule("R097", "F", "Single-phase inverter",
     [("inverter_kw", "<", 10)], "Systems under 10 kW normally use a single-phase inverter.",
     set={"inverter_phase": "Single-phase"}, salience=10)
rule("R098", "F", "On-grid with unstable voltage",
     [("system_type", "==", "On-Grid"), ("voltage_issues", "==", True)],
     "Grid-tie inverters disconnect when voltage leaves the allowed range, losing generation.",
     append={"recommendations": "With unstable grid voltage, pick an on-grid inverter with a wide AC voltage window, and keep stabilizers on sensitive appliances."},
     salience=10)

# =============================================================================
# MODULE G - NET BILLING (GRID EXPORT)
# =============================================================================
rule("R099", "G", "Net billing not applicable",
     [("grid_status", "==", NO_GRID), ("net_metering_status", "not_exists")],
     "Exporting power requires a grid connection.",
     set={"net_metering_status": "Not applicable"}, salience=25)
rule("R100", "G", "User declines net billing",
     [("net_metering_interest", "==", "No"), ("grid_status", "!=", NO_GRID), ("net_metering_status", "not_exists")],
     "Without net billing, surplus solar is lost, so self-consumption should be maximised.",
     set={"net_metering_status": "Not opted"},
     append={"notes": "Without net billing, surplus daytime solar is wasted. Run heavy loads (washing, pumping, ironing) between 10 am and 3 pm."},
     salience=25)
rule("R101", "G", "Net billing recommended",
     [("net_metering_interest", "==", "Yes"), ("grid_status", "!=", NO_GRID), ("net_metering_status", "not_exists")],
     "A grid-connected user who wants to export should apply for net billing.",
     set={"net_metering_status": "Recommended"},
     append={"recommendations": "Apply to your DISCO for net billing. New users currently earn about Rs {export_rate}/unit for exported power under a 5-year agreement (verify current NEPRA terms)."},
     salience=25)
rule("R102", "G", "Unsure user with surplus",
     [("net_metering_interest", "==", "Not sure"), ("solar_fraction", ">=", 0.9), ("net_metering_status", "not_exists"), ("grid_status", "!=", NO_GRID)],
     "When solar covers nearly all usage, there will be daytime surplus worth exporting.",
     set={"net_metering_status": "Recommended"},
     append={"recommendations": "Your system will produce daytime surplus, so net billing is worth applying for even at the lower export rate."},
     salience=5, cf=0.8)
rule("R103", "G", "Unsure user with little surplus",
     [("net_metering_interest", "==", "Not sure"), ("solar_fraction", "<", 0.9), ("net_metering_status", "not_exists"), ("grid_status", "!=", NO_GRID)],
     "When solar covers only part of usage, most power is used at home and little would be exported.",
     set={"net_metering_status": "Optional"},
     append={"notes": "You will use most of your solar power yourself, so net billing is optional for you."},
     salience=5, cf=0.8)
rule("R104", "G", "Net billing on single-phase",
     [("net_metering_status", "==", "Recommended"), ("phase", "==", "Single-phase")],
     "DISCOs often require a three-phase connection for net-billing applications.",
     append={"warnings": "Many DISCOs require a three-phase connection for net billing. Check with your DISCO before applying."},
     salience=10)
rule("R105", "G", "System exceeds sanctioned load",
     [("net_metering_status", "==", "Recommended"), ("exceeds_sanctioned", "==", True)],
     "Export capacity is normally limited relative to the sanctioned load on the electricity bill.",
     append={"warnings": "Your {system_kw:.1f} kW system is larger than your sanctioned load ({sanctioned_load_kw} kW). You may need to increase your sanctioned load first."},
     salience=10)

# =============================================================================
# MODULE H - COST, BUDGET & PAYBACK
# =============================================================================
rule("R106", "H", "Estimate total cost",
     [("system_kw", "exists"), ("inverter_kw", "exists"), ("battery_kwh", "exists"),
      ("net_metering_status", "exists"), ("mounting_key", "exists"), ("total_cost", "not_exists")],
     "Cost = panels + inverter + structure + wiring + installation + batteries + net-billing fees.",
     calc="estimate_cost", salience=12)
rule("R107", "H", "Calculate savings and payback",
     [("total_cost", "exists"), ("payback_years", "not_exists")],
     "Savings = self-used units × tariff + exported units × export rate; payback = cost ÷ annual savings.",
     calc="financials", salience=12)
rule("R108", "H", "Within budget",
     [("budget_ratio", ">=", 1.0)], "The budget covers the full recommended system.",
     set={"budget_status": "Within budget"}, salience=10)
rule("R109", "H", "Slightly over budget",
     [("budget_ratio", "between", (0.75, 1.0))],
     "A gap of up to 25% can be closed with financing or small changes.",
     set={"budget_status": "Slightly over budget"},
     append={"recommendations": "You are slightly over budget. Consider a bank solar-financing scheme, or reduce the system to about {affordable_kw} kW."},
     salience=10)
rule("R110", "H", "Well over budget",
     [("budget_ratio", "<", 0.75)], "A large budget gap calls for a phased plan.",
     set={"budget_status": "Over budget"}, salience=10)
rule("R111", "H", "Phase plan: batteries later",
     [("budget_ratio", "<", 0.75), ("battery_needed", "==", True)],
     "Panels and a hybrid inverter start saving money immediately; batteries can follow.",
     set={"phase_plan": "Phase 1: install panels and the inverter now (about Rs {phase1_cost:,}). Phase 2: add batteries later when funds allow."},
     append={"recommendations": "Phase plan: install panels and the inverter first (about Rs {phase1_cost:,}), then add batteries later."},
     salience=10)
rule("R112", "H", "Phase plan: fewer panels first",
     [("budget_ratio", "<", 0.75), ("battery_needed", "==", False)],
     "Start with what the budget allows and add panels later on the same structure.",
     set={"phase_plan": "Phase 1: install about {affordable_kw} kW now. Phase 2: add the remaining panels later."},
     append={"recommendations": "Start with about {affordable_kw} kW within your budget, using an inverter large enough for the full system so panels can be added later."},
     salience=10)
rule("R113", "H", "Excellent payback",
     [("payback_years", "<=", 3)], "Payback within 3 years is an outstanding investment.",
     set={"financial_verdict": "Excellent investment"}, salience=10)
rule("R114", "H", "Good payback",
     [("payback_years", ">", 3), ("payback_years", "<=", 5)], "Payback in 3-5 years is a good investment.",
     set={"financial_verdict": "Good investment"}, salience=10)
rule("R115", "H", "Fair payback",
     [("payback_years", ">", 5), ("payback_years", "<=", 8)], "Payback in 5-8 years is acceptable for a 25-year asset.",
     set={"financial_verdict": "Fair investment"}, salience=10)
rule("R116", "H", "Weak payback",
     [("payback_years", ">", 8)], "Payback beyond 8 years is weak; batteries may need replacing before then.",
     set={"financial_verdict": "Weak investment"},
     append={"warnings": "Payback is over 8 years. Reduce battery size or improve appliance efficiency before investing."},
     salience=10)
rule("R117", "H", "Leaving before payback",
     [("stay_before_payback", "==", True)],
     "If the user moves before payback, they lose the investment unless they take the system along.",
     append={"warnings": "You plan to stay {stay_years} years but payback takes about {payback_years} years. Choose a removable structure so you can take the system with you."},
     salience=10)
rule("R118", "H", "Tenant with slow payback",
     [("ownership", "==", "Tenant"), ("payback_years", ">", 4)],
     "Tenants should only invest in systems that pay back quickly or can be moved.",
     append={"warnings": "As a tenant with payback over 4 years, keep the system small and portable."},
     salience=10)

# =============================================================================
# MODULE I - SAFETY & COMPLIANCE
# =============================================================================
rule("R119", "I", "Standard electrical protection",
     [("system_kw", ">", 0)],
     "Every PV system needs DC/AC isolation, surge protection and earthing for safety.",
     append={"recommendations": "Make sure the installer fits DC and AC breakers, surge protection devices (SPD) and a proper earthing pit."},
     salience=5)
rule("R120", "I", "Large system needs professional survey",
     [("system_kw", ">=", 10)],
     "Large systems need structural, cable-size and protection design by a qualified engineer.",
     append={"recommendations": "For a system of 10 kW or more, get a professional site survey and use an AEDB-certified installer."},
     salience=5)
rule("R121", "I", "Heavy array on sheet roof",
     [("mounting_key", "==", "Metal"), ("system_kw", ">", 5)],
     "Over 5 kW of panels adds significant weight and wind load to a sheet roof.",
     append={"warnings": "Over 5 kW of panels on a sheet roof needs a structural check. Consider partial ground mounting."},
     salience=5)
rule("R122", "I", "Battery circuit protection",
     [("battery_needed", "==", True), ("battery_kwh", ">", 0)],
     "Battery short circuits can cause fires; a DC fuse or breaker is mandatory.",
     append={"recommendations": "Install a properly rated DC breaker or fuse between the batteries and the inverter."},
     salience=5)
rule("R123", "I", "Commercial daytime load",
     [("property_type", "==", "Shop / Commercial")],
     "Shops use most power in daytime, which matches solar generation well.",
     append={"notes": "Commercial premises use power mainly in daytime, which matches solar production and improves savings."},
     salience=5)
rule("R124", "I", "Farm water pumping",
     [("property_type", "==", "Farmhouse / Rural"), ("has_motor_load", "==", True)],
     "Solar pumping with a VFD runs pumps directly from panels without batteries.",
     append={"recommendations": "For farm water pumping, consider a solar VFD pump drive. It runs the pump directly from panels, without batteries."},
     salience=5)

# =============================================================================
# MODULE J - FINAL VERDICT
# =============================================================================
rule("R125", "J", "Check stay duration against payback",
     [("stay_years", "exists"), ("payback_years", "exists"), ("stay_before_payback", "not_exists")],
     "Compares how long the user will stay with how long payback takes.",
     calc="compare_stay", salience=11)
rule("R126", "J", "Site not feasible",
     [("site_feasible", "==", False)],
     "When the site cannot host panels, the system recommends alternatives instead of a design.",
     set={"final_recommendation": "Solar is not feasible at this site. Consider a community solar scheme, a balcony mini-solar kit, or a battery UPS charged from the grid.",
          "overall_confidence": 95, "financial_verdict": "Not applicable"},
     salience=-60)
rule("R127", "J", "Compose final recommendation",
     [("site_feasible", "==", True), ("financial_verdict", "exists"), ("final_recommendation", "not_exists")],
     "Combines all decisions into one recommendation, with confidence equal to the weakest key decision.",
     calc="compose_summary", salience=-60)
rule("R128", "J", "High confidence result",
     [("overall_confidence", ">=", 90)], "Every key decision was made by strong, specific rules.",
     set={"confidence_label": "High"}, salience=-70)
rule("R129", "J", "Moderate confidence result",
     [("overall_confidence", "<", 90)], "At least one decision used a default or a judgement rule.",
     set={"confidence_label": "Moderate"},
     append={"notes": "Some decisions relied on general defaults. A site survey by an installer will confirm the details."},
     salience=-70)


def rules_by_module():
    grouped = {}
    for r in RULES:
        grouped.setdefault(r["module"], []).append(r)
    return grouped
