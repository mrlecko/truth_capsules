import os, sys, re, json, glob

def find_files(path):
    if os.path.isdir(path):
        for ext in ("*.txt", "*.md", "*.log"):
            for p in glob.glob(os.path.join(path, ext)):
                yield p
    else:
        if os.path.exists(path):
            yield path

EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE = re.compile(r"(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})")
CCARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
GOVID = re.compile(r"\b(?:SSN|NIN|SIN|CPF|DNI|Aadhar)\b", re.I)
ADDRESS = re.compile(r"\b\d{1,5}\s+\w+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Lane|Ln|Dr|Drive)\b", re.I)
IPADDR = re.compile(r"\b(?:(?:\d{1,3}\.){3}\d{1,3})\b")

MASKED_TOKENS = re.compile(r"\*\*\*|\[redacted\]|\[masked\]", re.I)

def main():
    examples_path = os.environ.get("EXAMPLES_PATH", "").strip()
    fail_on_any = os.environ.get("FAIL_ON_ANY", "true").lower() == "true"

    if not examples_path:
        print(json.dumps({"ok": False, "error": "EXAMPLES_PATH not set"}))
        sys.exit(2)

    patterns = {
        "email": EMAIL,
        "phone": PHONE,
        "credit_card": CCARD,
        "government_id": GOVID,
        "street_address": ADDRESS,
        "ip_address": IPADDR,
    }

    findings = []
    total_lines = 0

    for fp in find_files(examples_path):
        with open(fp, "r", errors="ignore") as f:
            for ln, line in enumerate(f, 1):
                total_lines += 1
                if MASKED_TOKENS.search(line):
                    continue
                for tag, rx in patterns.items():
                    for m in rx.finditer(line):
                        findings.append({"file": fp, "line": ln, "tag": tag, "match": m.group(0)[:64]})

    ok = len(findings) == 0
    result = {"ok": ok, "total_lines": total_lines, "violations": findings}

    print(json.dumps(result, indent=2))
    sys.exit(0 if (ok or not fail_on_any) else 1)

if __name__ == "__main__":
    main()
