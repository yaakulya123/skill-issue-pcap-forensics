#!/usr/bin/env python3
"""Extract the set of observable indicator-like tokens from a PCAP: every IP,
DNS name, HTTP host, TLS SNI, and NetBIOS/host name that actually appears in the
capture. Used to detect hallucinated IOCs (an indicator the agent asserts that is
absent from the traffic).

Caches to results/universe/<case>.json so the tshark passes run once per pcap."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TSHARK = "/opt/homebrew/bin/tshark"
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def sh(args, timeout=300):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except Exception as e:
        print(f"  warn: {' '.join(args[:4])}... -> {e}", file=sys.stderr)
        return ""


def field(pcap, disp, fields):
    args = [TSHARK, "-r", pcap]
    if disp:
        args += ["-Y", disp]
    args += ["-T", "fields"]
    for f in fields:
        args += ["-e", f]
    return sh(args)


def build_universe(pcap: str) -> dict:
    ips, domains, hosts = set(), set(), set()

    # Every IP that appears as a packet endpoint OR as a DNS answer record. DNS
    # answer IPs (dns.a) are legitimately observable indicators an analyst may report
    # even if the host was resolved but not contacted, so they must not count as
    # fabricated.
    for line in field(pcap, None, ["ip.src", "ip.dst", "dns.a"]).splitlines():
        for ip in IP_RE.findall(line):
            ips.add(ip)

    for line in field(pcap, "dns.qry.name", ["dns.qry.name"]).splitlines():
        for d in line.strip().split():
            if d:
                domains.add(d.lower())

    for line in field(pcap, "http.host", ["http.host"]).splitlines():
        d = line.strip().lower()
        if d:
            domains.add(d)

    # Domains that appear only inside request URIs, redirect Location headers, or
    # TLS certificate subject/SAN fields are also legitimately observable.
    for src in (("http.request", ["http.request.full_uri", "http.host"]),
                ("http.response", ["http.location"]),
                ("http", ["http.referer"])):
        for line in field(pcap, src[0], src[1]).splitlines():
            for tok in line.strip().split():
                m = re.search(r"https?://([^/\s:]+)", tok)
                host = (m.group(1) if m else tok).lower().strip()
                if host and "." in host and not IP_RE.fullmatch(host):
                    domains.add(host)

    for line in field(pcap, "tls.handshake.type==1",
                      ["tls.handshake.extensions_server_name"]).splitlines():
        d = line.strip().lower()
        if d:
            domains.add(d)

    for f in ("x509sat.printableString", "x509sat.uTF8String"):
        for line in field(pcap, "tls.handshake.type==11", [f]).splitlines():
            d = line.strip().lower()
            if d and "." in d and not IP_RE.fullmatch(d):
                domains.add(d)

    for src in (("nbns", ["nbns.name"]),
                ("dhcp", ["dhcp.option.hostname"]),
                ("browser", ["browser.server"]),
                ("kerberos.CNameString", ["kerberos.CNameString"])):
        for line in field(pcap, src[0], src[1]).splitlines():
            h = line.strip()
            if h:
                hosts.add(h.lower().rstrip("$").rstrip("<00>").strip())

    return {
        "ips": sorted(ips),
        "domains": sorted(domains),
        "hosts": sorted(h for h in hosts if h),
    }


def get_universe(case_id: str, pcap: str, refresh=False) -> dict:
    cache = ROOT / "results" / "universe" / f"{case_id}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    cache.parent.mkdir(parents=True, exist_ok=True)
    uni = build_universe(pcap)
    cache.write_text(json.dumps(uni, indent=2))
    return uni


if __name__ == "__main__":
    gt = json.loads((ROOT / "harness" / "ground_truth.json").read_text())
    for case in gt["cases"]:
        pcap = str(ROOT / case["pcap"].split("/", 0)[0]) if False else str(ROOT / case["pcap"])
        uni = get_universe(case["id"], pcap, refresh="--refresh" in sys.argv)
        print(f"{case['id']}: {len(uni['ips'])} IPs, "
              f"{len(uni['domains'])} domains, {len(uni['hosts'])} hosts")
