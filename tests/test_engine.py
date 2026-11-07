"""
Automated tests for the SolarSense expert system.

Run from the project folder with:
    python -m unittest discover tests -v
"""

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.calculations import CALCULATIONS, load_parameters  # noqa: E402
from engine.inference import InferenceEngine  # noqa: E402
from knowledge_base.rules import RULES  # noqa: E402

PARAMS = load_parameters()
ENGINE = InferenceEngine(RULES, CALCULATIONS, PARAMS)
with open(os.path.join(ROOT, "data", "personas.json"), encoding="utf-8") as fh:
    PERSONAS = json.load(fh)


def run(name, **changes):
    inputs = dict(PERSONAS[name]["inputs"])
    inputs.update(changes)
    return ENGINE.run(inputs)


class TestKnowledgeBase(unittest.TestCase):
    def test_minimum_rule_count(self):
        self.assertGreaterEqual(len(RULES), 50)

    def test_unique_ids(self):
        ids = [r["id"] for r in RULES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_rule_fires_in_some_persona(self):
        fired = set()
        for name in PERSONAS:
            fired |= set(ENGINE.run(PERSONAS[name]["inputs"])["fired_ids"])
        never = [r["id"] for r in RULES if r["id"] not in fired]
        self.assertEqual(never, [], f"Rules never fired: {never}")


class TestDecisions(unittest.TestCase):
    def test_no_grid_gives_off_grid_with_lithium(self):
        f = run("Bahawalpur off-grid farmhouse")["facts"]
        self.assertEqual(f["system_type"], "Off-Grid")
        self.assertTrue(f["battery_needed"])
        self.assertEqual(f["battery_type"], "Lithium (LiFePO4)")
        self.assertEqual(f["net_metering_status"], "Not applicable")

    def test_reliable_grid_gives_on_grid_without_battery(self):
        f = run("Lahore bungalow (reliable grid, max savings)")["facts"]
        self.assertEqual(f["system_type"], "On-Grid")
        self.assertFalse(f["battery_needed"])
        self.assertEqual(f["inverter_phase"], "Three-phase")

    def test_load_shedding_gives_hybrid(self):
        f = run("Karachi family home (load-shedding, backup)")["facts"]
        self.assertEqual(f["system_type"], "Hybrid")
        self.assertGreater(f["battery_kwh"], 0)

    def test_budget_priority_gives_tubular(self):
        f = run("Hyderabad home (budget backup)")["facts"]
        self.assertEqual(f["battery_type"], "Tubular lead-acid")
        self.assertEqual(f["battery_dod"], 0.5)

    def test_mild_outages_battery_ready(self):
        f = run("Quetta house (mild outages, battery-ready)")["facts"]
        self.assertEqual(f["system_type"], "Hybrid")
        self.assertFalse(f["battery_needed"])
        self.assertTrue(f["battery_optional"])

    def test_tiny_roof_not_feasible(self):
        f = run("Gwadar flat (roof too small)")["facts"]
        self.assertFalse(f["site_feasible"])
        self.assertNotIn("system_kw", f)

    def test_roof_caps_system_size(self):
        f = run("Islamabad rented flat (tight budget)")["facts"]
        self.assertTrue(f["roof_limited"])
        self.assertLessEqual(f["system_kw"], f["roof_capacity_kw"])

    def test_heavy_shading_increases_size(self):
        clear = run("Lahore bungalow (reliable grid, max savings)")["facts"]["system_kw"]
        shaded = run("Lahore bungalow (reliable grid, max savings)", shading="Heavy shading")["facts"]["system_kw"]
        self.assertGreater(shaded, clear)

    def test_more_outage_hours_never_shrinks_battery(self):
        small = run("Karachi family home (load-shedding, backup)", outage_hours=5, desired_backup_hours=0)
        large = run("Karachi family home (load-shedding, backup)", outage_hours=10, desired_backup_hours=0)
        self.assertGreaterEqual(large["facts"]["battery_kwh"], small["facts"]["battery_kwh"])

    def test_low_budget_triggers_phase_plan(self):
        f = run("Multan shop (severe outages)")["facts"]
        self.assertEqual(f["budget_status"], "Over budget")
        self.assertIn("phase_plan", f)

    def test_payback_is_positive(self):
        for name in PERSONAS:
            f = ENGINE.run(PERSONAS[name]["inputs"])["facts"]
            if f.get("site_feasible"):
                self.assertGreater(f["payback_years"], 0, name)
                self.assertGreater(f["total_cost"], 0, name)

    def test_explanation_trace_is_complete(self):
        result = run("Karachi family home (load-shedding, backup)")
        self.assertEqual(len(result["trace"]), len(result["fired_ids"]))
        for step in result["trace"]:
            self.assertTrue(step["conditions"])
            self.assertTrue(step["conclusions"])


if __name__ == "__main__":
    unittest.main()
