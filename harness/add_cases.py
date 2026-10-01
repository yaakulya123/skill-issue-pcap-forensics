#!/usr/bin/env python3
"""Append 5 validated cases to ground_truth.json. Every IOC below was transcribed
from the official MTA answer PDF and then checked against the pcap; corrections
(with curation_note) were applied where the published key disagreed with traffic."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GT = ROOT / "harness" / "ground_truth.json"

NEW = [
    {
        "id": "mta-2024-08-15", "date": "2024-08-15",
        "pcap": "datasets/evidence/mta-2024-08-15/2024-08-15-traffic-analysis-exercise.pcap",
        "scenario": "Windows host in 10.8.15.0/24 (lafontainebleu.org) infected with WarmCookie via a fake FedEx-themed download chain.",
        "malware_family": "WarmCookie", "difficulty": "hard",
        "environment": {"subnet": "10.8.15.0/24", "domain": "lafontainebleu.org", "dc": "10.8.15.4"},
        "iocs": [
            {"type": "victim_ip", "value": "10.8.15.133"},
            {"type": "victim_mac", "value": "00:1c:bf:03:54:82"},
            {"type": "victim_hostname", "value": "DESKTOP-H8ALZBV"},
            {"type": "victim_user", "value": "plucero", "aliases": ["Pierce Lucero"]},
            {"type": "malware_family", "value": "WarmCookie", "aliases": ["Warm Cookie"]},
            {"type": "c2_endpoint", "value": "72.5.43.29:80", "aliases": ["72.5.43.29"]},
            {"type": "domain", "value": "quote.checkfedexexp.com"},
            {"type": "domain", "value": "business.checkfedexexp.com"},
            {"type": "file_name", "value": "Invoice 876597035_003.zip"},
            {"type": "file_hash", "value": "798563fcf7600f7ef1a35996291a9dfb5f9902733404dd499e2e736ea1dc6fc5"},
            {"type": "file_hash", "value": "dab98819d1d7677a60f5d06be210d45b74ae5fd8cf0c24ec1b3766e25ce6dc2c"},
        ],
        "benign_context": [], "alerts_provided": False,
    },
    {
        "id": "mta-2022-01-07", "date": "2022-01-07",
        "pcap": "datasets/evidence/mta-2022-01-07/2022-01-07-traffic-analysis-exercise.pcap",
        "scenario": "Windows host in 192.168.1.0/24 (spoonwatch.net) infected with Oski Stealer exfiltrating over HTTP.",
        "malware_family": "Oski Stealer", "difficulty": "medium",
        "environment": {"subnet": "192.168.1.0/24", "domain": "spoonwatch.net", "dc": "192.168.1.2"},
        "iocs": [
            {"type": "victim_ip", "value": "192.168.1.216"},
            {"type": "victim_mac", "value": "95:5c:8e:32:58:f9"},
            {"type": "victim_hostname", "value": "DESKTOP-GXMYNO2"},
            {"type": "victim_user", "value": "steve.smith", "aliases": ["Steve Smith"]},
            {"type": "malware_family", "value": "Oski Stealer", "aliases": ["Oski", "OskiStealer"]},
            {"type": "c2_endpoint", "value": "2.56.57.108:80", "aliases": ["2.56.57.108"]},
            {"type": "url", "value": "/osk//main.php"},
            {"type": "url", "value": "/osk/"},
            {"type": "file_hash", "value": "16574f51785b0e2fc29c2c61477eb47bb39f714829999511dc8952b43ab17660"},
        ],
        "benign_context": [], "alerts_provided": False,
    },
    {
        "id": "mta-2021-09-10", "date": "2021-09-10",
        "pcap": "datasets/evidence/mta-2021-09-10/2021-09-10-traffic-analysis-exercise.pcap",
        "scenario": "Windows host in 10.9.10.0/24 (angrypoutine.com) infected with BazarLoader delivered through the TA551 campaign.",
        "malware_family": "BazarLoader", "difficulty": "hard",
        "environment": {"subnet": "10.9.10.0/24", "domain": "angrypoutine.com", "dc": "10.9.10.9"},
        "iocs": [
            {"type": "victim_ip", "value": "10.9.10.102"},
            {"type": "victim_mac", "value": "00:4f:49:b1:e8:c3"},
            {"type": "victim_hostname", "value": "DESKTOP-KKITB6Q"},
            {"type": "victim_user", "value": "hobart.gunnarsson", "aliases": ["Hobart Gunnarsson"]},
            {"type": "malware_family", "value": "BazarLoader", "aliases": ["Bazar", "BazaLoader", "TA551"]},
            {"type": "domain", "value": "simpsonsavingss.com"},
            {"type": "c2_endpoint", "value": "194.62.42.206:80", "aliases": ["194.62.42.206"]},
            {"type": "c2_endpoint", "value": "167.172.37.9:443", "aliases": ["167.172.37.9"]},
            {"type": "c2_endpoint", "value": "94.158.245.52:443", "aliases": ["94.158.245.52"]},
            {"type": "file_hash", "value": "eed363fc4af7a9070d69340592dcab7c78db4f90710357de29e3b6"},
        ],
        "benign_context": [], "alerts_provided": False,
    },
    {
        "id": "mta-2026-01-31", "date": "2026-01-31",
        "pcap": "datasets/evidence/mta-2026-01-31/2026-01-31-traffic-analysis-exercise.pcap",
        "scenario": "Windows host in 10.1.21.0/24 (win11office.com) infected with Lumma Stealer; multiple stealer C2 domains.",
        "malware_family": "Lumma Stealer", "difficulty": "hard",
        "environment": {"subnet": "10.1.21.0/24", "domain": "win11office.com", "dc": "10.1.21.2"},
        "iocs": [
            {"type": "victim_ip", "value": "10.1.21.58",
             "curation_note": "Answer PDF prints 10.1.28.58; corrected to 10.1.21.58. The Lumma C2 153.92.1.49 exchanges 2968 packets with 10.1.21.58 (matching the C2 packet count), same /24 as the DC 10.1.21.2; 10.1.28.58 is in zero packets."},
            {"type": "victim_mac", "value": "00:21:5d:c8:0e:f2"},
            {"type": "victim_hostname", "value": "DESKTOP-ES9F3ML"},
            {"type": "victim_user", "value": "gwyatt", "aliases": ["Gabriel Wyatt"]},
            {"type": "malware_family", "value": "Lumma Stealer", "aliases": ["Lumma", "LummaC2"]},
            {"type": "c2_endpoint", "value": "153.92.1.49:80", "aliases": ["153.92.1.49"]},
            {"type": "domain", "value": "communicationfirewall-security.cc"},
            {"type": "domain", "value": "holiday-forever.cc"},
            {"type": "domain", "value": "whitepepper.su"},
        ],
        "benign_context": [], "alerts_provided": False,
    },
    {
        "id": "mta-2026-02-28", "date": "2026-02-28",
        "pcap": "datasets/evidence/mta-2026-02-28/2026-02-28-traffic-analysis-exercise.pcap",
        "scenario": "Windows host in 10.2.28.0/24 (easyas123.tech) infected with NetSupport Manager RAT beaconing over TCP 443.",
        "malware_family": "NetSupport Manager RAT", "difficulty": "medium",
        "environment": {"subnet": "10.2.28.0/24", "domain": "easyas123.tech", "dc": "10.2.28.2"},
        "iocs": [
            {"type": "victim_ip", "value": "10.2.28.88"},
            {"type": "victim_mac", "value": "00:19:d1:b2:4d:ad"},
            {"type": "victim_hostname", "value": "DESKTOP-TEYQ2NR"},
            {"type": "victim_user", "value": "brolf"},
            {"type": "malware_family", "value": "NetSupport Manager RAT", "aliases": ["NetSupport", "NetSupport RAT", "NetSupport Manager"]},
            {"type": "c2_endpoint", "value": "45.131.214.85:443", "aliases": ["45.131.214.85"]},
        ],
        "benign_context": [], "alerts_provided": False,
    },
]


def main():
    gt = json.loads(GT.read_text())
    have = {c["id"] for c in gt["cases"]}
    added = 0
    for c in NEW:
        if c["id"] in have:
            # replace
            gt["cases"] = [x for x in gt["cases"] if x["id"] != c["id"]]
        gt["cases"].append(c)
        added += 1
    GT.write_text(json.dumps(gt, indent=2))
    print(f"ground truth now has {len(gt['cases'])} cases (+{added} added/replaced)")


if __name__ == "__main__":
    main()
