"""
Exports the knowledge base to docs/Rule_Table.md and docs/Rule_Table.csv.
Use these files in your project report appendix and as a viva cheat-sheet.

Run from the project folder with:
    python tools/export_rules.py
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.inference import describe_actions, describe_condition  # noqa: E402
from knowledge_base.rules import MODULES, RULES, rules_by_module  # noqa: E402


def main():
    docs = os.path.join(ROOT, "docs")
    os.makedirs(docs, exist_ok=True)

    with open(os.path.join(docs, "Rule_Table.csv"), "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ID", "Module", "Rule", "IF", "THEN", "Salience", "CF", "Why"])
        for r in RULES:
            writer.writerow([r["id"], r["module"], r["name"],
                             " AND ".join(describe_condition(c) for c in r["if"]),
                             "; ".join(describe_actions(r)), r["salience"], r["cf"], r["why"]])

    lines = ["# SolarSense Rule Table", "",
             f"Total rules: **{len(RULES)}** in **{len(MODULES)}** modules.", ""]
    for module, rules in rules_by_module().items():
        lines += [f"## {module} ({len(rules)} rules)", ""]
        for r in rules:
            cond = " **AND** ".join(f"`{describe_condition(c)}`" for c in r["if"])
            then = "; ".join(describe_actions(r))
            lines += [f"**{r['id']} - {r['name']}**  ",
                      f"IF {cond}  ",
                      f"THEN {then}  ",
                      f"*Why:* {r['why']}  ",
                      f"*Salience:* {r['salience']} · *CF:* {r['cf']}", ""]
    with open(os.path.join(docs, "Rule_Table.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"Exported {len(RULES)} rules to docs/Rule_Table.md and docs/Rule_Table.csv")


if __name__ == "__main__":
    main()
