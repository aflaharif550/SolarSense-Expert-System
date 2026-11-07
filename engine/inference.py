"""
Forward-chaining inference engine for SolarSense.

How it works (the recognise-act cycle):
  1. MATCH    - find every rule whose IF conditions are true in working memory
                and that has not fired yet (this set is called the agenda).
  2. RESOLVE  - conflict resolution: pick the rule with the highest salience
                (priority); ties go to the lower rule number.
  3. ACT      - fire that rule: set facts, append advice, or run a calculation.
  4. Repeat until the agenda is empty (no rule can fire).

Each rule fires at most once (refraction). Every firing is logged with the
values that satisfied its conditions, which powers the explanation facility.
"""

import copy

OPERATORS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "between": lambda a, b: b[0] <= a < b[1],
    "contains": lambda a, b: b in a,
}

OPERATOR_SYMBOLS = {
    "==": "=", "!=": "≠", ">": ">", ">=": "≥", "<": "<", "<=": "≤",
    "in": "is one of", "not_in": "is not one of", "between": "is between",
    "contains": "contains", "exists": "is known", "not_exists": "is not yet known",
}

LIST_FACTS = ("warnings", "recommendations", "notes")


def _fmt_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, tuple)) and len(value) == 2 and all(isinstance(v, (int, float)) for v in value):
        return f"{value[0]} and {value[1]}"
    if isinstance(value, (list, tuple, set)):
        return ", ".join(f"'{v}'" for v in value)
    if isinstance(value, str):
        return f"'{value}'"
    return str(value)


def describe_condition(cond):
    fact, op = cond[0], cond[1]
    symbol = OPERATOR_SYMBOLS.get(op, op)
    if op in ("exists", "not_exists"):
        return f"{fact} {symbol}"
    if op == "between":
        return f"{fact} ≥ {cond[2][0]} AND < {cond[2][1]}"
    return f"{fact} {symbol} {_fmt_value(cond[2])}"


def describe_actions(rule):
    parts = []
    for fact, value in rule.get("set", {}).items():
        parts.append(f"{fact} = {_fmt_value(value)}")
    for fact, value in rule.get("append", {}).items():
        items = value if isinstance(value, list) else [value]
        for item in items:
            parts.append(f"add {fact[:-1]}: \"{item}\"")
    if rule.get("calc"):
        parts.append(f"run calculation {rule['calc']}()")
    return parts


def safe_format(template, facts):
    try:
        return template.format(**facts)
    except (KeyError, ValueError, IndexError, TypeError, AttributeError):
        return template


class InferenceEngine:
    def __init__(self, rules, calculations, parameters, max_cycles=1000):
        self.rules = rules
        self.calculations = calculations
        self.parameters = parameters
        self.max_cycles = max_cycles
        self._check_rules()

    def _check_rules(self):
        ids = [r["id"] for r in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate rule IDs in knowledge base")
        for r in self.rules:
            if r.get("calc") and r["calc"] not in self.calculations:
                raise ValueError(f"{r['id']} refers to unknown calculation {r['calc']}")
            for cond in r["if"]:
                if cond[1] not in OPERATORS and cond[1] not in ("exists", "not_exists"):
                    raise ValueError(f"{r['id']} uses unknown operator {cond[1]}")

    # ---------------------------------------------------------------- matching
    @staticmethod
    def _test(cond, facts):
        fact, op = cond[0], cond[1]
        if op == "exists":
            return fact in facts
        if op == "not_exists":
            return fact not in facts
        if fact not in facts:
            return False
        try:
            return bool(OPERATORS[op](facts[fact], cond[2]))
        except TypeError:
            return False

    def _matches(self, rule, facts):
        return all(self._test(c, facts) for c in rule["if"])

    # ----------------------------------------------------------------- acting
    def _fire(self, rule, facts, confidence):
        changes = []
        cf = rule.get("cf", 1.0)
        for fact, value in rule.get("set", {}).items():
            if isinstance(value, str):
                value = safe_format(value, facts)
            facts[fact] = value
            confidence[fact] = cf
            changes.append(f"{fact} = {_fmt_value(value)}")
        for fact, value in rule.get("append", {}).items():
            items = value if isinstance(value, list) else [value]
            for item in items:
                text = safe_format(item, facts)
                facts.setdefault(fact, []).append({"rule": rule["id"], "text": text})
                changes.append(f"{fact[:-1]}: {text}")
        if rule.get("calc"):
            new_facts = self.calculations[rule["calc"]](facts, self.parameters)
            for k, v in new_facts.items():
                facts[k] = v
                confidence.setdefault(k, cf)
            shown = [k for k, v in new_facts.items() if not isinstance(v, (dict, list))]
            changes.append(f"{rule['calc']}() derived: " + ", ".join(f"{k} = {new_facts[k]}" for k in shown))
        return changes

    # -------------------------------------------------------------------- run
    def run(self, initial_facts):
        facts = copy.deepcopy(initial_facts)
        for name in LIST_FACTS:
            facts.setdefault(name, [])
        confidence = {}
        facts["_confidence"] = confidence
        fired_ids = set()
        trace = []
        cycle = 0

        while cycle < self.max_cycles:
            agenda = [r for r in self.rules
                      if r["id"] not in fired_ids and self._matches(r, facts)]
            if not agenda:
                break
            cycle += 1
            agenda.sort(key=lambda r: (-r.get("salience", 0), r["order"]))
            rule = agenda[0]
            evidence = []
            for cond in rule["if"]:
                text = describe_condition(cond)
                if cond[1] not in ("exists", "not_exists") and cond[0] in facts:
                    actual = facts[cond[0]]
                    if not isinstance(actual, (dict, list)):
                        text += f"   [actual: {_fmt_value(actual)}]"
                evidence.append(text)
            changes = self._fire(rule, facts, confidence)
            fired_ids.add(rule["id"])
            trace.append({
                "cycle": cycle,
                "id": rule["id"],
                "name": rule["name"],
                "module": rule["module"],
                "salience": rule.get("salience", 0),
                "cf": rule.get("cf", 1.0),
                "agenda_size": len(agenda),
                "conditions": evidence,
                "conclusions": changes,
                "explanation": rule["why"],
            })

        return {
            "facts": facts,
            "trace": trace,
            "fired_ids": [t["id"] for t in trace],
            "cycles": cycle,
            "rules_total": len(self.rules),
        }
