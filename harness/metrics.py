#!/usr/bin/env python3
"""Score an agent's forensic output against vetted ground truth.

Format-agnostic by design: the base task asks for a prose incident report, so we do
not assume JSON. Recall is measured by grounded value matching; hallucination is
measured against the PCAP universe (tokens the agent asserts that never appear in the
traffic). This keeps the schema component a genuine treatment, not a scoring crutch."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")
SHA256 = re.compile(r"\b[0-9a-fA-F]{64}\b")
DOMAIN = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"(?:com|net|org|online|health|info|xyz|top|ru|io|cc|su|tech|biz|site|shop)\b")

# Well-known documentation / reference / platform domains an analyst may cite in a
# report but would never label as C2. Excluded from hallucination counting so prose
# references do not inflate the fabricated-indicator metric. Documented in the paper.
BENIGN_REFERENCE_DOMAINS = {
    "malware-traffic-analysis.net", "www.malware-traffic-analysis.net",
    "github.com", "githubusercontent.com", "objects.githubusercontent.com",
    "linkedin.com", "www.linkedin.com", "x.com", "twitter.com",
    "virustotal.com", "www.virustotal.com", "urlscan.io", "any.run",
    "google.com", "microsoft.com", "mitre.org", "attack.mitre.org",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def value_present(value: str, aliases, hay: str) -> bool:
    cands = [value] + list(aliases or [])
    return any(norm(c) and norm(c) in hay for c in cands)


def _ip_to_int(ip):
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def in_subnet(ip, cidr):
    """True if ip is inside cidr (e.g. 172.16.1.0/24)."""
    try:
        net, bits = cidr.split("/")
        bits = int(bits)
        mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
        return (_ip_to_int(ip) & mask) == (_ip_to_int(net) & mask)
    except Exception:
        return False


def local_ips(case):
    """Named local infrastructure not to be counted as hallucinated (gw, DC)."""
    env = case.get("environment", {})
    return {env[k] for k in ("gateway", "dc") if env.get(k)}


def score(output_text: str, case: dict, universe: dict) -> dict:
    hay = norm(output_text)

    # ---- Recall over vetted IOCs ----
    iocs = case["iocs"]
    found = [i for i in iocs if value_present(i["value"], i.get("aliases"), hay)]
    recall = len(found) / len(iocs) if iocs else 0.0

    by_type = {}
    for i in iocs:
        t = i["type"]
        hit = value_present(i["value"], i.get("aliases"), hay)
        by_type.setdefault(t, [0, 0])
        by_type[t][1] += 1
        if hit:
            by_type[t][0] += 1

    # ---- Victim identity (the 4 canonical fields) ----
    victim_fields = {}
    for t in ("victim_ip", "victim_mac", "victim_hostname", "victim_user"):
        gt = next((i for i in iocs if i["type"] == t), None)
        if gt:
            victim_fields[t] = value_present(gt["value"], gt.get("aliases"), hay)
    victim_correct = sum(1 for v in victim_fields.values() if v)

    # ---- Malware family ----
    fam = next((i for i in iocs if i["type"] == "malware_family"), None)
    family_correct = value_present(fam["value"], fam.get("aliases"), hay) if fam else None

    # ---- Hallucination: IOC-shaped tokens the agent asserts that are absent from traffic ----
    uni_ips = set(universe["ips"])
    uni_doms = set(universe["domains"])
    safe_ips = uni_ips | local_ips(case)
    subnet = case.get("environment", {}).get("subnet", "")

    out_ips = set(IPV4.findall(output_text))
    out_ips = {ip for ip in out_ips if all(0 <= int(o) <= 255 for o in ip.split("."))}
    out_doms = {d.lower() for d in DOMAIN.findall(output_text)}

    # A hallucinated indicator is a fabricated EXTERNAL token absent from traffic.
    # Local-subnet addresses (victim, gateway, DC, network, broadcast) are
    # infrastructure the report legitimately names, never fabricated C2, so exclude them.
    halluc_ips = sorted(ip for ip in out_ips
                        if ip not in safe_ips and not in_subnet(ip, subnet))
    # a domain counts as hallucinated only if no observed domain endswith/contains it
    def dom_seen(d):
        return any(d == u or u.endswith("." + d) or d.endswith("." + u) or d in u for u in uni_doms)
    halluc_doms = sorted(d for d in out_doms
                         if not dom_seen(d) and d not in BENIGN_REFERENCE_DOMAINS)

    total_ioc_tokens = len(out_ips) + len(out_doms)
    halluc_count = len(halluc_ips) + len(halluc_doms)
    halluc_rate = halluc_count / total_ioc_tokens if total_ioc_tokens else 0.0

    return {
        "recall": round(recall, 4),
        "iocs_found": len(found),
        "iocs_total": len(iocs),
        "recall_by_type": {t: {"found": v[0], "total": v[1]} for t, v in by_type.items()},
        "victim_fields": victim_fields,
        "victim_correct": victim_correct,
        "victim_total": len(victim_fields),
        "family_correct": family_correct,
        "hallucinated_ips": halluc_ips,
        "hallucinated_domains": halluc_doms,
        "hallucination_count": halluc_count,
        "ioc_tokens_emitted": total_ioc_tokens,
        "hallucination_rate": round(halluc_rate, 4),
    }


if __name__ == "__main__":
    import sys
    from pcap_universe import get_universe
    gt = json.loads((ROOT / "harness" / "ground_truth.json").read_text())
    # self-test: feed each case's own answer text as a perfect oracle
    for case in gt["cases"]:
        ans = ROOT / (Path(case["pcap"]).parent / "answers.txt")
        text = ans.read_text() if ans.exists() else ""
        uni = get_universe(case["id"], str(ROOT / case["pcap"]))
        s = score(text, case, uni)
        print(f"{case['id']}: oracle recall={s['recall']} "
              f"victim={s['victim_correct']}/{s['victim_total']} "
              f"family={s['family_correct']} halluc={s['hallucination_count']} "
              f"(ips={s['hallucinated_ips'][:3]})")
