import os, sys, json, re

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def classify(text, rules):
    text_l = text.lower()
    for intent, pats in rules.items():
        for pat in pats:
            if re.search(pat, text_l):
                return intent
    return "unknown"

def main():
    intents_path = os.environ.get("INTENTS_JSON", "").strip() or "artifacts/examples/support_agent/intents.json"
    rules_path = os.environ.get("RULES_JSON", "").strip() or "artifacts/examples/support_agent/router_rules.json"
    acc_threshold = float(os.environ.get("ACC_THRESHOLD", "0.8"))

    if os.path.isdir(intents_path):
        intents_path = os.path.join(intents_path, "examples/support_agent/intents.json")
    if os.path.isdir(rules_path):
        rules_path = os.path.join(rules_path, "examples/support_agent/router_rules.json")

    intents = load_json(intents_path)  # list of {text, expected}
    rules = load_json(rules_path)      # {intent: [regex,...]}

    total = len(intents)
    correct = 0
    details = []

    for item in intents:
        text = item["text"]
        expected = item["expected"]
        pred = classify(text, rules)
        correct += 1 if pred == expected else 0
        details.append({"text": text, "expected": expected, "pred": pred})

    acc = (correct / total) if total else 0.0
    ok = acc >= acc_threshold

    print(json.dumps({"ok": ok, "accuracy": acc, "threshold": acc_threshold, "total": total, "correct": correct, "details": details}, indent=2))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
