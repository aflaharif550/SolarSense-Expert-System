# SolarSense Rule Table

Total rules: **129** in **10** modules.

## A. Load Assessment (17 rules)

**R001 - Analyse energy consumption**  
IF `monthly_units is known` **AND** `appliances is known` **AND** `daily_kwh is not yet known`  
THEN run calculation analyse_load()  
*Why:* Before any decision, the bill and appliance list are converted into daily energy (kWh), peak load (kW) and tariff.  
*Salience:* 100 · *CF:* 1.0

**R002 - Low consumption household**  
IF `daily_kwh < 5`  
THEN consumption_level = 'Low'  
*Why:* Under 5 kWh/day is a small load (fans, lights, fridge).  
*Salience:* 50 · *CF:* 1.0

**R003 - Moderate consumption household**  
IF `daily_kwh ≥ 5 AND < 12`  
THEN consumption_level = 'Moderate'  
*Why:* 5-12 kWh/day is a typical home without heavy AC use.  
*Salience:* 50 · *CF:* 1.0

**R004 - High consumption household**  
IF `daily_kwh ≥ 12 AND < 25`  
THEN consumption_level = 'High'  
*Why:* 12-25 kWh/day usually means one or two ACs in summer.  
*Salience:* 50 · *CF:* 1.0

**R005 - Very high consumption**  
IF `daily_kwh ≥ 25`  
THEN consumption_level = 'Very High'  
*Why:* Above 25 kWh/day is a large home or commercial load.  
*Salience:* 50 · *CF:* 1.0

**R006 - Light peak load**  
IF `peak_load_kw < 3`  
THEN load_class = 'Light'  
*Why:* Peak demand under 3 kW can run on a small inverter.  
*Salience:* 50 · *CF:* 1.0

**R007 - Medium peak load**  
IF `peak_load_kw ≥ 3 AND < 6`  
THEN load_class = 'Medium'  
*Why:* 3-6 kW peak demand needs a mid-size inverter.  
*Salience:* 50 · *CF:* 1.0

**R008 - Heavy peak load**  
IF `peak_load_kw ≥ 6`  
THEN load_class = 'Heavy'  
*Why:* 6 kW or more peak demand needs a large inverter.  
*Salience:* 50 · *CF:* 1.0

**R009 - Non-inverter AC detected**  
IF `noninverter_ac_count > 0`  
THEN efficiency_upgrade = Yes; add recommendation: "Replace your {noninverter_ac_count} non-inverter AC(s) with inverter ACs. This cuts AC energy use by about a third and lets you buy a smaller solar system."  
*Why:* Non-inverter ACs use roughly 30-50% more energy than inverter ACs, which inflates the solar system size.  
*Salience:* 50 · *CF:* 1.0

**R010 - Motor load detected**  
IF `has_motor_load = Yes`  
THEN add note: "Motor loads (water pump / washing machine) are present, so the inverter is sized with extra surge capacity."  
*Why:* Pumps and washing machines draw 3-5 times their running current at start-up.  
*Salience:* 50 · *CF:* 1.0

**R011 - Electric geyser detected**  
IF `has_geyser = Yes`  
THEN add warning: "Electric geysers are very energy-hungry. Use a gas or solar water heater instead, and never run a geyser on battery backup."  
*Why:* A 2 kW geyser can use more energy than the rest of the house and should not run from solar batteries.  
*Salience:* 50 · *CF:* 1.0

**R012 - Appliance list incomplete**  
IF `appliance_ratio < 0.6` **AND** `monthly_units > 0`  
THEN add note: "Your appliance list explains only about {appliance_ratio_pct}% of your bill. Sizing uses your actual bill units, which is more reliable."  
*Why:* If listed appliances explain much less than the bill, some loads are missing; the bill is the more reliable figure.  
*Salience:* 50 · *CF:* 1.0

**R013 - Appliance list overestimates usage**  
IF `appliance_ratio > 1.5` **AND** `monthly_units > 0`  
THEN add note: "Your appliance list suggests about {appliance_ratio_pct}% of your billed usage, so real usage hours are lower than assumed. Sizing follows your bill."  
*Why:* If listed appliances exceed the bill by 50%, usage hours are probably overstated; the bill is used instead.  
*Salience:* 50 · *CF:* 1.0

**R014 - High electricity tariff**  
IF `effective_tariff ≥ 50`  
THEN tariff_band = 'High'; solar_attractiveness = 'High'  
*Why:* At Rs 50+ per unit every solar unit saves a lot of money, so solar pays back quickly.  
*Salience:* 50 · *CF:* 1.0

**R015 - Medium electricity tariff**  
IF `effective_tariff ≥ 30 AND < 50`  
THEN tariff_band = 'Medium'; solar_attractiveness = 'Medium'  
*Why:* Rs 30-50 per unit still makes solar worthwhile.  
*Salience:* 50 · *CF:* 1.0

**R016 - Low electricity tariff**  
IF `effective_tariff < 30`  
THEN tariff_band = 'Low'; solar_attractiveness = 'Low'; add note: "Your effective tariff is only Rs {effective_tariff}/unit, so savings per unit are modest and payback will be slower."  
*Why:* Below Rs 30 per unit, savings per solar unit are small and payback is slower.  
*Salience:* 50 · *CF:* 1.0

**R017 - Very high load on single-phase supply**  
IF `consumption_level = 'Very High'` **AND** `phase = 'Single-phase'`  
THEN add warning: "Your consumption is very high for a single-phase connection. Consider asking your DISCO for a three-phase connection."  
*Why:* Very large loads on a single-phase connection often hit the connection's limit.  
*Salience:* 40 · *CF:* 1.0

## B. Outage & Backup Needs (19 rules)

**R018 - Site without grid**  
IF `grid_status = 'No grid connection'`  
THEN outage_severity = 'Off-grid site'  
*Why:* With no grid connection, solar must supply all energy, day and night.  
*Salience:* 60 · *CF:* 1.0

**R019 - No load-shedding**  
IF `grid_status ≠ 'No grid connection'` **AND** `outage_hours = 0`  
THEN outage_severity = 'None'  
*Why:* Zero daily outage hours means backup is not a priority.  
*Salience:* 55 · *CF:* 1.0

**R020 - Mild load-shedding**  
IF `grid_status ≠ 'No grid connection'` **AND** `outage_hours ≥ 1 AND < 4`  
THEN outage_severity = 'Mild'  
*Why:* 1-3 hours of daily outages is mild.  
*Salience:* 55 · *CF:* 1.0

**R021 - Moderate load-shedding**  
IF `grid_status ≠ 'No grid connection'` **AND** `outage_hours ≥ 4 AND < 7`  
THEN outage_severity = 'Moderate'  
*Why:* 4-6 hours of daily outages seriously disrupts a household.  
*Salience:* 55 · *CF:* 1.0

**R022 - Severe load-shedding**  
IF `grid_status ≠ 'No grid connection'` **AND** `outage_hours ≥ 7`  
THEN outage_severity = 'Severe'  
*Why:* 7 or more hours of daily outages is severe.  
*Salience:* 55 · *CF:* 1.0

**R023 - Backup needed for critical loads**  
IF `outage_severity is one of 'Moderate', 'Severe'` **AND** `critical_load_kw > 0` **AND** `backup_required is not yet known`  
THEN backup_required = Yes  
*Why:* Moderate or severe outages plus essential loads means power must continue during outages.  
*Salience:* 50 · *CF:* 0.95

**R024 - Backup needed (no critical loads listed)**  
IF `outage_severity is one of 'Moderate', 'Severe'` **AND** `critical_load_kw = 0` **AND** `backup_required is not yet known`  
THEN backup_required = Yes; critical_assumed = Yes; add note: "You did not mark any critical loads, so backup is sized for about 40% of your peak load (fans, lights, fridge)."  
*Why:* Long outages need backup even if the user did not mark critical loads; fans and lights are assumed.  
*Salience:* 50 · *CF:* 0.85

**R025 - User prioritises backup**  
IF `priority = 'Reliable backup power'` **AND** `grid_status ≠ 'No grid connection'` **AND** `backup_required is not yet known`  
THEN backup_required = Yes  
*Why:* The user explicitly chose reliable backup as the top priority.  
*Salience:* 52 · *CF:* 1.0

**R026 - Mild outages: battery optional**  
IF `outage_severity = 'Mild'` **AND** `priority is not one of 'Reliable backup power', 'Lowest upfront cost'` **AND** `backup_required is not yet known`  
THEN backup_required = No; battery_optional = Yes  
*Why:* Short outages do not justify battery cost now, but a battery-ready system keeps the option open.  
*Salience:* 50 · *CF:* 0.8

**R027 - Mild outages on a tight budget**  
IF `outage_severity = 'Mild'` **AND** `priority = 'Lowest upfront cost'` **AND** `backup_required is not yet known`  
THEN backup_required = No  
*Why:* When lowest cost matters most and outages are short, backup is skipped.  
*Salience:* 50 · *CF:* 0.85

**R028 - Reliable grid: no backup**  
IF `outage_severity = 'None'` **AND** `priority ≠ 'Reliable backup power'` **AND** `backup_required is not yet known`  
THEN backup_required = No  
*Why:* With no outages, batteries only add cost.  
*Salience:* 50 · *CF:* 0.95

**R029 - Off-grid site needs storage**  
IF `outage_severity = 'Off-grid site'` **AND** `backup_required is not yet known`  
THEN backup_required = Yes  
*Why:* Without a grid, night-time power can only come from batteries.  
*Salience:* 50 · *CF:* 1.0

**R030 - Night-time outages**  
IF `night_outages = Yes` **AND** `backup_required = Yes` **AND** `grid_status ≠ 'No grid connection'`  
THEN add note: "Outages happen at night, so the battery is sized to cover the full outage period without solar input."  
*Why:* There is no sunlight at night, so the battery alone must carry night outages.  
*Salience:* 10 · *CF:* 1.0

**R031 - Work out backup hours**  
IF `backup_required = Yes` **AND** `grid_status ≠ 'No grid connection'` **AND** `backup_hours is not yet known`  
THEN run calculation set_backup_hours()  
*Why:* Backup hours = the larger of the user's wish and the outage duration (halved for daytime outages, since solar helps).  
*Salience:* 40 · *CF:* 1.0

**R032 - Existing UPS can be replaced**  
IF `existing_backup = 'UPS / Inverter'` **AND** `backup_required = Yes`  
THEN add recommendation: "Your hybrid inverter will replace the old UPS. Old batteries under about 2 years old may be reused only if they match the new system voltage."  
*Why:* A hybrid inverter does the UPS's job and charges batteries from solar.  
*Salience:* 10 · *CF:* 1.0

**R033 - Generator on site**  
IF `existing_backup = 'Generator'`  
THEN add recommendation: "Keep your generator as an emergency source. Choose an inverter with a generator input so solar handles daily backup and fuel use drops."  
*Why:* Hybrid/off-grid inverters can use a generator as a backup charging source, cutting fuel use.  
*Salience:* 10 · *CF:* 1.0

**R034 - Voltage fluctuations reported**  
IF `voltage_issues = Yes`  
THEN add note: "Because your grid voltage fluctuates, choose an inverter with a wide input voltage range and proper surge protection."  
*Why:* Hybrid and off-grid inverters supply regulated output, protecting appliances from unstable grid voltage.  
*Salience:* 10 · *CF:* 1.0

**R035 - AC selected as critical load**  
IF `critical_has_ac = Yes` **AND** `backup_required = Yes`  
THEN add warning: "You marked an AC as a critical load. Running ACs on batteries needs a very large and expensive battery bank. Limit AC use during outages if possible."  
*Why:* An AC on battery drains even a large battery bank within a few hours.  
*Salience:* 10 · *CF:* 1.0

**R036 - Reliable grid confirmed**  
IF `outage_severity = 'None'` **AND** `backup_required = No`  
THEN add note: "Your grid is reliable, so no battery is needed. This gives the fastest payback."  
*Why:* No outages and no backup need is the cheapest and fastest-payback situation.  
*Salience:* 10 · *CF:* 1.0

## C. Site & Roof Suitability (20 rules)

**R037 - Analyse site and climate**  
IF `city is known` **AND** `roof_area is known` **AND** `sun_hours is not yet known`  
THEN run calculation analyse_site()  
*Why:* City determines sun hours and climate; roof area determines how many kW fit.  
*Salience:* 100 · *CF:* 1.0

**R038 - No usable installation space**  
IF `roof_type = 'No usable space'` **AND** `site_feasible is not yet known`  
THEN site_feasible = No; add warning: "No usable roof or ground space was reported, so a solar installation is not feasible at this site."  
*Why:* Panels need roof or ground space; without it solar is not feasible.  
*Salience:* 60 · *CF:* 1.0

**R039 - Roof too small**  
IF `roof_capacity_kw < 1` **AND** `roof_type ≠ 'No usable space'` **AND** `site_feasible is not yet known`  
THEN site_feasible = No; add warning: "Your usable area fits less than 1 kW of panels (about {roof_capacity_kw:.1f} kW), which is too small for a practical system."  
*Why:* Under about 75 sq ft cannot hold even 1 kW of panels.  
*Salience:* 60 · *CF:* 1.0

**R040 - Site is feasible**  
IF `site_feasible is not yet known`  
THEN site_feasible = Yes  
*Why:* If no feasibility problem has been found, the site is assumed suitable.  
*Salience:* -40 · *CF:* 1.0

**R041 - Heavy shading**  
IF `shading = 'Heavy shading'`  
THEN shading_factor = 0.65; add warning: "Heavy shading cuts output by about 35%. Trim trees or move panels to an unshaded area if possible."  
*Why:* Heavy shade can cut output by a third or more.  
*Salience:* 50 · *CF:* 1.0

**R042 - Partial shading**  
IF `shading = 'Partial shading'`  
THEN shading_factor = 0.85; add note: "Partial shading reduces output by about 15%. Panels are sized up to compensate."  
*Why:* Morning or evening shade reduces output by roughly 15%.  
*Salience:* 50 · *CF:* 1.0

**R043 - No shading**  
IF `shading = 'No shading'`  
THEN shading_factor = 1.0  
*Why:* An unshaded site gets full output.  
*Salience:* 50 · *CF:* 1.0

**R044 - South-facing or flat roof**  
IF `orientation = 'South-facing / flat roof'`  
THEN orientation_factor = 1.0  
*Why:* In Pakistan (northern hemisphere) south-facing panels collect the most sunlight; flat roofs allow south tilt.  
*Salience:* 50 · *CF:* 1.0

**R045 - East-West roof**  
IF `orientation = 'East-West'`  
THEN orientation_factor = 0.9; add note: "East-West orientation produces about 10% less energy than south-facing panels."  
*Why:* East-west panels lose about 10% compared with south-facing ones.  
*Salience:* 50 · *CF:* 1.0

**R046 - North-facing roof**  
IF `orientation = 'North-facing'`  
THEN orientation_factor = 0.78; add warning: "North-facing panels lose over 20% output. Use a tilted structure so panels face south."  
*Why:* North-facing panels face away from the sun in Pakistan.  
*Salience:* 50 · *CF:* 1.0

**R047 - Dusty city**  
IF `dusty = Yes`  
THEN dust_factor = 0.95; add recommendation: "Your area is dusty. Clean the panels with plain water every 1-2 weeks to avoid losing 5-10% output."  
*Why:* Dust on panels reduces output; regular cleaning restores it.  
*Salience:* 50 · *CF:* 1.0

**R048 - Low-dust city**  
IF `dusty = No`  
THEN dust_factor = 0.98  
*Why:* Less dust means lower soiling losses.  
*Salience:* 50 · *CF:* 1.0

**R049 - Coastal city**  
IF `coastal = Yes`  
THEN add recommendation: "Coastal city: use hot-dip galvanized or aluminium structures with stainless-steel bolts to prevent rust."  
*Why:* Salty sea air corrodes ordinary steel structures and fasteners.  
*Salience:* 10 · *CF:* 1.0

**R050 - Hot climate**  
IF `hot_climate = Yes`  
THEN add note: "Hot climate: panels are mounted with an air gap underneath to reduce heat losses. Temperature loss is included in the performance ratio."  
*Why:* Panels lose efficiency as they heat up; airflow under them helps.  
*Salience:* 10 · *CF:* 1.0

**R051 - RCC concrete roof**  
IF `roof_type = 'RCC concrete roof'`  
THEN mounting = 'Elevated galvanized steel structure'; mounting_key = 'RCC'  
*Why:* Flat concrete roofs use elevated steel structures, which also keep roof space usable.  
*Salience:* 50 · *CF:* 1.0

**R052 - Metal / tin roof**  
IF `roof_type = 'Metal / tin sheet roof'`  
THEN mounting = 'Rail-and-clamp mounting on metal roof'; mounting_key = 'Metal'; add note: "On a sheet roof, have the roof frame checked before installing panels."  
*Why:* Sheet roofs use rails clamped to the roof, which is cheaper but needs a strength check.  
*Salience:* 50 · *CF:* 1.0

**R053 - Ground installation**  
IF `roof_type = 'Ground / open space'`  
THEN mounting = 'Ground-mounted steel frame'; mounting_key = 'Ground'  
*Why:* Open ground allows ideal tilt and easy cleaning.  
*Salience:* 50 · *CF:* 1.0

**R054 - Tenant occupant**  
IF `ownership = 'Tenant'`  
THEN add warning: "As a tenant you need written permission from the owner before installing panels."  
*Why:* Tenants need the owner's permission and may move before payback.  
*Salience:* 10 · *CF:* 1.0

**R055 - Apartment / flat**  
IF `property_type = 'Apartment / Flat'`  
THEN add warning: "Apartment roofs are usually shared. Get a no-objection letter from your building management or society first."  
*Why:* Apartment roofs are shared, so space and permission are limited.  
*Salience:* 10 · *CF:* 1.0

**R056 - Roof limits system size**  
IF `roof_limited = Yes`  
THEN add warning: "You need about {required_kw:.1f} kW but your space fits only about {roof_capacity_kw:.1f} kW. The system has been capped to fit your roof."  
*Why:* If the needed kW does not fit, the system is capped at what the roof can hold.  
*Salience:* 10 · *CF:* 1.0

## D. System Type & Sizing (16 rules)

**R057 - Off-grid system for no-grid site**  
IF `grid_status = 'No grid connection'` **AND** `system_type is not yet known`  
THEN system_type = 'Off-Grid'  
*Why:* Without a grid connection, only an off-grid system with batteries can work.  
*Salience:* 40 · *CF:* 1.0

**R058 - Hybrid system for backup needs**  
IF `backup_required = Yes` **AND** `grid_status ≠ 'No grid connection'` **AND** `system_type is not yet known`  
THEN system_type = 'Hybrid'  
*Why:* A hybrid inverter uses grid, solar and battery together, so power continues during outages.  
*Salience:* 40 · *CF:* 0.95

**R059 - Battery-ready hybrid**  
IF `backup_required = No` **AND** `battery_optional = Yes` **AND** `system_type is not yet known`  
THEN system_type = 'Hybrid'; add recommendation: "Start without batteries. Your hybrid inverter is battery-ready, so you can add batteries later if outages increase."  
*Why:* A hybrid inverter without batteries works like on-grid now, and batteries can be added later.  
*Salience:* 40 · *CF:* 0.8

**R060 - On-grid system**  
IF `backup_required = No` **AND** `grid_status ≠ 'No grid connection'` **AND** `system_type is not yet known`  
THEN system_type = 'On-Grid'  
*Why:* With no backup need, an on-grid system is the cheapest and most efficient choice.  
*Salience:* 30 · *CF:* 0.9

**R061 - On-grid shuts down during outages**  
IF `system_type = 'On-Grid'` **AND** `outage_severity is one of 'Mild', 'Moderate', 'Severe'`  
THEN add warning: "An on-grid system switches OFF during load-shedding for safety. You will have no solar power during outages."  
*Why:* On-grid inverters must switch off when the grid fails (anti-islanding) to protect line workers.  
*Salience:* 10 · *CF:* 1.0

**R062 - Off-grid sizing margin**  
IF `system_type = 'Off-Grid'` **AND** `coverage_target is not yet known`  
THEN coverage_target = 1.15  
*Why:* Off-grid systems need extra generation to recharge batteries on cloudy days.  
*Salience:* 45 · *CF:* 1.0

**R063 - Size for maximum savings**  
IF `priority = 'Maximum bill savings'` **AND** `system_type is known` **AND** `coverage_target is not yet known`  
THEN coverage_target = 1.0  
*Why:* To maximise savings, solar should cover all daily usage.  
*Salience:* 30 · *CF:* 1.0

**R064 - Size for balanced value**  
IF `priority = 'Balanced'` **AND** `system_type is known` **AND** `coverage_target is not yet known`  
THEN coverage_target = 0.85  
*Why:* Covering about 85% of usage gives most of the savings at lower cost.  
*Salience:* 30 · *CF:* 1.0

**R065 - Size for lowest cost**  
IF `priority = 'Lowest upfront cost'` **AND** `system_type is known` **AND** `coverage_target is not yet known`  
THEN coverage_target = 0.6  
*Why:* A smaller system (60% coverage) keeps the upfront cost low.  
*Salience:* 30 · *CF:* 1.0

**R066 - Size for backup priority**  
IF `priority = 'Reliable backup power'` **AND** `system_type is known` **AND** `coverage_target is not yet known`  
THEN coverage_target = 0.75  
*Why:* When backup matters most, part of the budget goes to batteries, so panels cover about 75%.  
*Salience:* 30 · *CF:* 1.0

**R067 - Low export value**  
IF `net_metering_interest = 'Yes'` **AND** `export_value_ratio < 0.5` **AND** `grid_status ≠ 'No grid connection'`  
THEN add note: "Exported units earn only Rs {export_rate}/unit, while you pay Rs {effective_tariff}/unit. The system is sized for self-use, not for selling power."  
*Why:* Under net billing, exported units earn far less than the price of imported units, so oversizing for export does not pay.  
*Salience:* 10 · *CF:* 1.0

**R068 - Calculate array size**  
IF `coverage_target is known` **AND** `shading_factor is known` **AND** `orientation_factor is known` **AND** `dust_factor is known` **AND** `site_feasible = Yes` **AND** `daily_kwh is known` **AND** `system_kw is not yet known`  
THEN run calculation size_array()  
*Why:* kW needed = daily kWh × coverage ÷ (sun hours × performance ratio × shading × orientation × dust), rounded up to whole panels.  
*Salience:* 20 · *CF:* 1.0

**R069 - High solar coverage**  
IF `solar_fraction ≥ 0.9`  
THEN energy_independence = 'High'  
*Why:* Generating 90%+ of daily use gives high energy independence.  
*Salience:* 10 · *CF:* 1.0

**R070 - Partial solar coverage**  
IF `solar_fraction ≥ 0.5 AND < 0.9`  
THEN energy_independence = 'Partial'  
*Why:* 50-90% coverage still cuts most daytime bills.  
*Salience:* 10 · *CF:* 1.0

**R071 - Low solar coverage**  
IF `solar_fraction < 0.5`  
THEN energy_independence = 'Low'; add note: "Solar will cover only about {solar_fraction_pct}% of your usage. Consider reducing loads or adding space later."  
*Why:* Under 50% coverage leaves most consumption on the grid.  
*Salience:* 10 · *CF:* 1.0

**R072 - Very small system**  
IF `system_kw < 2` **AND** `system_type ≠ 'Off-Grid'`  
THEN add note: "Very small systems have a higher cost per kW. Make sure the space and budget cannot support a larger system."  
*Why:* Under 2 kW, fixed costs (inverter, installation) make each kW expensive.  
*Salience:* 10 · *CF:* 1.0

## E. Battery Selection (15 rules)

**R073 - No battery required**  
IF `backup_required = No` **AND** `battery_needed is not yet known`  
THEN battery_needed = No; battery_type = 'None'; battery_kwh = 0; battery_units = 0  
*Why:* Without a backup need, batteries only add cost and maintenance.  
*Salience:* 35 · *CF:* 1.0

**R074 - Off-grid storage**  
IF `system_type = 'Off-Grid'` **AND** `battery_needed is not yet known`  
THEN battery_needed = Yes; backup_hours = 14  
*Why:* Off-grid homes run on batteries every night, about 14 hours from sunset to morning.  
*Salience:* 35 · *CF:* 1.0

**R075 - Hybrid storage**  
IF `system_type = 'Hybrid'` **AND** `backup_required = Yes` **AND** `battery_needed is not yet known`  
THEN battery_needed = Yes  
*Why:* A hybrid system with a backup need requires a battery bank.  
*Salience:* 35 · *CF:* 1.0

**R076 - Lithium for severe outages**  
IF `battery_needed = Yes` **AND** `outage_severity = 'Severe'` **AND** `battery_type is not yet known`  
THEN battery_type = 'Lithium (LiFePO4)'  
*Why:* Daily deep cycling wears out lead-acid batteries; LiFePO4 lasts 3,000-6,000 cycles.  
*Salience:* 25 · *CF:* 0.9

**R077 - Lithium for off-grid**  
IF `battery_needed = Yes` **AND** `system_type = 'Off-Grid'` **AND** `battery_type is not yet known`  
THEN battery_type = 'Lithium (LiFePO4)'  
*Why:* Off-grid batteries cycle every day, so long-life lithium is the economic choice.  
*Salience:* 25 · *CF:* 0.9

**R078 - Tubular for lowest cost**  
IF `battery_needed = Yes` **AND** `priority = 'Lowest upfront cost'` **AND** `battery_type is not yet known`  
THEN battery_type = 'Tubular lead-acid'  
*Why:* Tubular lead-acid batteries cost about half as much upfront.  
*Salience:* 20 · *CF:* 0.85

**R079 - Lithium by default**  
IF `battery_needed = Yes` **AND** `battery_type is not yet known`  
THEN battery_type = 'Lithium (LiFePO4)'  
*Why:* LiFePO4 is safer, maintenance-free and cheaper over its life, so it is the default choice.  
*Salience:* -50 · *CF:* 0.75

**R080 - Lithium depth of discharge**  
IF `battery_type = 'Lithium (LiFePO4)'` **AND** `battery_dod is not yet known`  
THEN battery_dod = 0.9  
*Why:* LiFePO4 can safely use 90% of its capacity.  
*Salience:* 30 · *CF:* 1.0

**R081 - Lead-acid depth of discharge**  
IF `battery_type = 'Tubular lead-acid'` **AND** `battery_dod is not yet known`  
THEN battery_dod = 0.5  
*Why:* Lead-acid batteries should only be discharged to 50% to protect their life.  
*Salience:* 30 · *CF:* 1.0

**R082 - Calculate battery bank**  
IF `battery_needed = Yes` **AND** `battery_dod is known` **AND** `backup_hours is known` **AND** `inverter_kw is known` **AND** `battery_kwh is not yet known`  
THEN run calculation size_battery()  
*Why:* Capacity = backup load × hours ÷ (depth of discharge × efficiency), rounded to whole battery units.  
*Salience:* 15 · *CF:* 1.0

**R083 - Very large battery bank**  
IF `battery_kwh > 15`  
THEN add warning: "The battery bank is large ({battery_kwh:.1f} kWh). Reducing critical loads or backup hours will cut cost noticeably."  
*Why:* Banks over 15 kWh are expensive; trimming backup loads saves a lot.  
*Salience:* 10 · *CF:* 1.0

**R084 - Lead-acid maintenance**  
IF `battery_type = 'Tubular lead-acid'`  
THEN add recommendation: "Tubular batteries: top up with distilled water monthly and keep them in a ventilated place."  
*Why:* Flooded tubular batteries need water top-ups and give off gas while charging.  
*Salience:* 10 · *CF:* 1.0

**R085 - Batteries in hot climate**  
IF `hot_climate = Yes` **AND** `battery_needed = Yes`  
THEN add recommendation: "Keep batteries indoors in a shaded, ventilated spot, away from direct sun."  
*Why:* Heat shortens battery life; every 10 °C rise can halve lead-acid life.  
*Salience:* 10 · *CF:* 1.0

**R086 - Lithium compatibility**  
IF `battery_type = 'Lithium (LiFePO4)'`  
THEN add recommendation: "Choose a LiFePO4 battery with a built-in BMS that communicates with your inverter (CAN or RS485)."  
*Why:* LiFePO4 batteries need a BMS that communicates with the inverter for safe charging.  
*Salience:* 10 · *CF:* 1.0

**R087 - Battery can be added later**  
IF `battery_optional = Yes`  
THEN add note: "If load-shedding increases later, a battery can be added to your hybrid inverter without replacing anything."  
*Why:* Keeping the system battery-ready protects the user if outages get worse.  
*Salience:* 10 · *CF:* 1.0

## F. Inverter Selection (11 rules)

**R088 - Surge margin for motors**  
IF `has_motor_load = Yes` **AND** `surge_factor is not yet known`  
THEN surge_factor = 1.5  
*Why:* Motors need a 50% inverter margin to start.  
*Salience:* 30 · *CF:* 1.0

**R089 - Surge margin for ACs**  
IF `ac_count > 0` **AND** `surge_factor is not yet known`  
THEN surge_factor = 1.35  
*Why:* AC compressors need about 35% extra capacity at start-up.  
*Salience:* 25 · *CF:* 1.0

**R090 - Standard surge margin**  
IF `surge_factor is not yet known`  
THEN surge_factor = 1.25  
*Why:* A 25% margin keeps the inverter from running at full load.  
*Salience:* -50 · *CF:* 1.0

**R091 - Calculate inverter size**  
IF `system_kw is known` **AND** `system_type is known` **AND** `surge_factor is known` **AND** `inverter_kw is not yet known`  
THEN run calculation size_inverter()  
*Why:* On-grid inverters are sized to the panels; hybrid/off-grid inverters must also carry peak load with surge margin.  
*Salience:* 18 · *CF:* 1.0

**R092 - Grid-tie inverter**  
IF `system_type = 'On-Grid'`  
THEN inverter_technology = 'Grid-tie (on-grid) string inverter'  
*Why:* On-grid systems use a grid-tie string inverter.  
*Salience:* 10 · *CF:* 1.0

**R093 - Hybrid inverter**  
IF `system_type = 'Hybrid'`  
THEN inverter_technology = 'Hybrid inverter with MPPT and battery port'  
*Why:* Hybrid systems need an inverter that handles grid, solar and battery together.  
*Salience:* 10 · *CF:* 1.0

**R094 - Off-grid inverter**  
IF `system_type = 'Off-Grid'`  
THEN inverter_technology = 'Off-grid inverter with built-in MPPT charger'  
*Why:* Off-grid systems need an inverter with a built-in solar charge controller.  
*Salience:* 10 · *CF:* 1.0

**R095 - Three-phase inverter**  
IF `phase = 'Three-phase'` **AND** `inverter_kw ≥ 10`  
THEN inverter_phase = 'Three-phase'  
*Why:* Large inverters on a three-phase supply should balance power across all phases.  
*Salience:* 10 · *CF:* 1.0

**R096 - Large inverter on single-phase**  
IF `phase = 'Single-phase'` **AND** `inverter_kw ≥ 10`  
THEN inverter_phase = 'Single-phase (three-phase upgrade advised)'; add warning: "A {inverter_kw} kW inverter is large for a single-phase connection. Ask your DISCO about upgrading to three-phase."  
*Why:* Inverters of 10 kW or more usually need a three-phase connection.  
*Salience:* 10 · *CF:* 1.0

**R097 - Single-phase inverter**  
IF `inverter_kw < 10`  
THEN inverter_phase = 'Single-phase'  
*Why:* Systems under 10 kW normally use a single-phase inverter.  
*Salience:* 10 · *CF:* 1.0

**R098 - On-grid with unstable voltage**  
IF `system_type = 'On-Grid'` **AND** `voltage_issues = Yes`  
THEN add recommendation: "With unstable grid voltage, pick an on-grid inverter with a wide AC voltage window, and keep stabilizers on sensitive appliances."  
*Why:* Grid-tie inverters disconnect when voltage leaves the allowed range, losing generation.  
*Salience:* 10 · *CF:* 1.0

## G. Net Billing (Grid Export) (7 rules)

**R099 - Net billing not applicable**  
IF `grid_status = 'No grid connection'` **AND** `net_metering_status is not yet known`  
THEN net_metering_status = 'Not applicable'  
*Why:* Exporting power requires a grid connection.  
*Salience:* 25 · *CF:* 1.0

**R100 - User declines net billing**  
IF `net_metering_interest = 'No'` **AND** `grid_status ≠ 'No grid connection'` **AND** `net_metering_status is not yet known`  
THEN net_metering_status = 'Not opted'; add note: "Without net billing, surplus daytime solar is wasted. Run heavy loads (washing, pumping, ironing) between 10 am and 3 pm."  
*Why:* Without net billing, surplus solar is lost, so self-consumption should be maximised.  
*Salience:* 25 · *CF:* 1.0

**R101 - Net billing recommended**  
IF `net_metering_interest = 'Yes'` **AND** `grid_status ≠ 'No grid connection'` **AND** `net_metering_status is not yet known`  
THEN net_metering_status = 'Recommended'; add recommendation: "Apply to your DISCO for net billing. New users currently earn about Rs {export_rate}/unit for exported power under a 5-year agreement (verify current NEPRA terms)."  
*Why:* A grid-connected user who wants to export should apply for net billing.  
*Salience:* 25 · *CF:* 1.0

**R102 - Unsure user with surplus**  
IF `net_metering_interest = 'Not sure'` **AND** `solar_fraction ≥ 0.9` **AND** `net_metering_status is not yet known` **AND** `grid_status ≠ 'No grid connection'`  
THEN net_metering_status = 'Recommended'; add recommendation: "Your system will produce daytime surplus, so net billing is worth applying for even at the lower export rate."  
*Why:* When solar covers nearly all usage, there will be daytime surplus worth exporting.  
*Salience:* 5 · *CF:* 0.8

**R103 - Unsure user with little surplus**  
IF `net_metering_interest = 'Not sure'` **AND** `solar_fraction < 0.9` **AND** `net_metering_status is not yet known` **AND** `grid_status ≠ 'No grid connection'`  
THEN net_metering_status = 'Optional'; add note: "You will use most of your solar power yourself, so net billing is optional for you."  
*Why:* When solar covers only part of usage, most power is used at home and little would be exported.  
*Salience:* 5 · *CF:* 0.8

**R104 - Net billing on single-phase**  
IF `net_metering_status = 'Recommended'` **AND** `phase = 'Single-phase'`  
THEN add warning: "Many DISCOs require a three-phase connection for net billing. Check with your DISCO before applying."  
*Why:* DISCOs often require a three-phase connection for net-billing applications.  
*Salience:* 10 · *CF:* 1.0

**R105 - System exceeds sanctioned load**  
IF `net_metering_status = 'Recommended'` **AND** `exceeds_sanctioned = Yes`  
THEN add warning: "Your {system_kw:.1f} kW system is larger than your sanctioned load ({sanctioned_load_kw} kW). You may need to increase your sanctioned load first."  
*Why:* Export capacity is normally limited relative to the sanctioned load on the electricity bill.  
*Salience:* 10 · *CF:* 1.0

## H. Cost, Budget & Payback (13 rules)

**R106 - Estimate total cost**  
IF `system_kw is known` **AND** `inverter_kw is known` **AND** `battery_kwh is known` **AND** `net_metering_status is known` **AND** `mounting_key is known` **AND** `total_cost is not yet known`  
THEN run calculation estimate_cost()  
*Why:* Cost = panels + inverter + structure + wiring + installation + batteries + net-billing fees.  
*Salience:* 12 · *CF:* 1.0

**R107 - Calculate savings and payback**  
IF `total_cost is known` **AND** `payback_years is not yet known`  
THEN run calculation financials()  
*Why:* Savings = self-used units × tariff + exported units × export rate; payback = cost ÷ annual savings.  
*Salience:* 12 · *CF:* 1.0

**R108 - Within budget**  
IF `budget_ratio ≥ 1.0`  
THEN budget_status = 'Within budget'  
*Why:* The budget covers the full recommended system.  
*Salience:* 10 · *CF:* 1.0

**R109 - Slightly over budget**  
IF `budget_ratio ≥ 0.75 AND < 1.0`  
THEN budget_status = 'Slightly over budget'; add recommendation: "You are slightly over budget. Consider a bank solar-financing scheme, or reduce the system to about {affordable_kw} kW."  
*Why:* A gap of up to 25% can be closed with financing or small changes.  
*Salience:* 10 · *CF:* 1.0

**R110 - Well over budget**  
IF `budget_ratio < 0.75`  
THEN budget_status = 'Over budget'  
*Why:* A large budget gap calls for a phased plan.  
*Salience:* 10 · *CF:* 1.0

**R111 - Phase plan: batteries later**  
IF `budget_ratio < 0.75` **AND** `battery_needed = Yes`  
THEN phase_plan = 'Phase 1: install panels and the inverter now (about Rs {phase1_cost:,}). Phase 2: add batteries later when funds allow.'; add recommendation: "Phase plan: install panels and the inverter first (about Rs {phase1_cost:,}), then add batteries later."  
*Why:* Panels and a hybrid inverter start saving money immediately; batteries can follow.  
*Salience:* 10 · *CF:* 1.0

**R112 - Phase plan: fewer panels first**  
IF `budget_ratio < 0.75` **AND** `battery_needed = No`  
THEN phase_plan = 'Phase 1: install about {affordable_kw} kW now. Phase 2: add the remaining panels later.'; add recommendation: "Start with about {affordable_kw} kW within your budget, using an inverter large enough for the full system so panels can be added later."  
*Why:* Start with what the budget allows and add panels later on the same structure.  
*Salience:* 10 · *CF:* 1.0

**R113 - Excellent payback**  
IF `payback_years ≤ 3`  
THEN financial_verdict = 'Excellent investment'  
*Why:* Payback within 3 years is an outstanding investment.  
*Salience:* 10 · *CF:* 1.0

**R114 - Good payback**  
IF `payback_years > 3` **AND** `payback_years ≤ 5`  
THEN financial_verdict = 'Good investment'  
*Why:* Payback in 3-5 years is a good investment.  
*Salience:* 10 · *CF:* 1.0

**R115 - Fair payback**  
IF `payback_years > 5` **AND** `payback_years ≤ 8`  
THEN financial_verdict = 'Fair investment'  
*Why:* Payback in 5-8 years is acceptable for a 25-year asset.  
*Salience:* 10 · *CF:* 1.0

**R116 - Weak payback**  
IF `payback_years > 8`  
THEN financial_verdict = 'Weak investment'; add warning: "Payback is over 8 years. Reduce battery size or improve appliance efficiency before investing."  
*Why:* Payback beyond 8 years is weak; batteries may need replacing before then.  
*Salience:* 10 · *CF:* 1.0

**R117 - Leaving before payback**  
IF `stay_before_payback = Yes`  
THEN add warning: "You plan to stay {stay_years} years but payback takes about {payback_years} years. Choose a removable structure so you can take the system with you."  
*Why:* If the user moves before payback, they lose the investment unless they take the system along.  
*Salience:* 10 · *CF:* 1.0

**R118 - Tenant with slow payback**  
IF `ownership = 'Tenant'` **AND** `payback_years > 4`  
THEN add warning: "As a tenant with payback over 4 years, keep the system small and portable."  
*Why:* Tenants should only invest in systems that pay back quickly or can be moved.  
*Salience:* 10 · *CF:* 1.0

## I. Safety & Compliance (6 rules)

**R119 - Standard electrical protection**  
IF `system_kw > 0`  
THEN add recommendation: "Make sure the installer fits DC and AC breakers, surge protection devices (SPD) and a proper earthing pit."  
*Why:* Every PV system needs DC/AC isolation, surge protection and earthing for safety.  
*Salience:* 5 · *CF:* 1.0

**R120 - Large system needs professional survey**  
IF `system_kw ≥ 10`  
THEN add recommendation: "For a system of 10 kW or more, get a professional site survey and use an AEDB-certified installer."  
*Why:* Large systems need structural, cable-size and protection design by a qualified engineer.  
*Salience:* 5 · *CF:* 1.0

**R121 - Heavy array on sheet roof**  
IF `mounting_key = 'Metal'` **AND** `system_kw > 5`  
THEN add warning: "Over 5 kW of panels on a sheet roof needs a structural check. Consider partial ground mounting."  
*Why:* Over 5 kW of panels adds significant weight and wind load to a sheet roof.  
*Salience:* 5 · *CF:* 1.0

**R122 - Battery circuit protection**  
IF `battery_needed = Yes` **AND** `battery_kwh > 0`  
THEN add recommendation: "Install a properly rated DC breaker or fuse between the batteries and the inverter."  
*Why:* Battery short circuits can cause fires; a DC fuse or breaker is mandatory.  
*Salience:* 5 · *CF:* 1.0

**R123 - Commercial daytime load**  
IF `property_type = 'Shop / Commercial'`  
THEN add note: "Commercial premises use power mainly in daytime, which matches solar production and improves savings."  
*Why:* Shops use most power in daytime, which matches solar generation well.  
*Salience:* 5 · *CF:* 1.0

**R124 - Farm water pumping**  
IF `property_type = 'Farmhouse / Rural'` **AND** `has_motor_load = Yes`  
THEN add recommendation: "For farm water pumping, consider a solar VFD pump drive. It runs the pump directly from panels, without batteries."  
*Why:* Solar pumping with a VFD runs pumps directly from panels without batteries.  
*Salience:* 5 · *CF:* 1.0

## J. Final Verdict (5 rules)

**R125 - Check stay duration against payback**  
IF `stay_years is known` **AND** `payback_years is known` **AND** `stay_before_payback is not yet known`  
THEN run calculation compare_stay()  
*Why:* Compares how long the user will stay with how long payback takes.  
*Salience:* 11 · *CF:* 1.0

**R126 - Site not feasible**  
IF `site_feasible = No`  
THEN final_recommendation = 'Solar is not feasible at this site. Consider a community solar scheme, a balcony mini-solar kit, or a battery UPS charged from the grid.'; overall_confidence = 95; financial_verdict = 'Not applicable'  
*Why:* When the site cannot host panels, the system recommends alternatives instead of a design.  
*Salience:* -60 · *CF:* 1.0

**R127 - Compose final recommendation**  
IF `site_feasible = Yes` **AND** `financial_verdict is known` **AND** `final_recommendation is not yet known`  
THEN run calculation compose_summary()  
*Why:* Combines all decisions into one recommendation, with confidence equal to the weakest key decision.  
*Salience:* -60 · *CF:* 1.0

**R128 - High confidence result**  
IF `overall_confidence ≥ 90`  
THEN confidence_label = 'High'  
*Why:* Every key decision was made by strong, specific rules.  
*Salience:* -70 · *CF:* 1.0

**R129 - Moderate confidence result**  
IF `overall_confidence < 90`  
THEN confidence_label = 'Moderate'; add note: "Some decisions relied on general defaults. A site survey by an installer will confirm the details."  
*Why:* At least one decision used a default or a judgement rule.  
*Salience:* -70 · *CF:* 1.0
