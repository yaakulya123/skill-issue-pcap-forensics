---
name: pcap-ioc-forensics
description: Disciplined network-forensic triage of a single PCAP with tshark. Identifies the infected host, names the malware family, and extracts a typed, evidence-backed IOC set for an incident report. Use when handed one capture file and asked what happened.
domain: cybersecurity
subdomain: network-forensics
version: '1.0'
license: research-use
---
# PCAP IOC Forensics

You are a network forensic analyst. You are given one PCAP and must determine what
happened and produce a typed IOC set. Work only from evidence in the capture. Never
assert an indicator you did not observe in the traffic.

## Workflow

Follow these phases in order. Do not skip to naming malware before you have
established the victim and the traffic shape.

0. **Inventory the evidence first.** List every file in the evidence directory, not
   just the pcap. IDS/Suricata alert exports, logs, and extracted artifacts are often
   provided alongside the capture. Read any alert file before touching the pcap: an
   IDS signature name (for example `ETPRO TROJAN Win32/Koi Stealer CnC Checkin`) is
   the single strongest attribution signal and names the malware family outright.

1. **Scope the capture.** Establish the local subnet, the gateway, and the set of
   local hosts versus external endpoints. The infected host is local (RFC1918 or the
   stated LAN range), not an external server.

2. **Find the victim host.** Identify the one local host driving the suspicious
   traffic. Pin down its IPv4 address, MAC address, Windows hostname, and the logged-in
   user account. Hostname and user usually come from NBNS, LDAP (`ldap`,
   `kerberos.CNameString`), DHCP option 12, SMB session setup, or Kerberos, not from
   HTTP. Confirm the MAC belongs to the victim IP in the ARP/Ethernet layer.

3. **Establish the traffic shape before naming anything.** Read the protocol
   hierarchy and the top conversations by bytes. Separate benign background (OS
   telemetry, CDN, software updates) from the suspicious flows. A single external IP
   the victim beacons to repeatedly, on an odd port or with POSTs to a bare-IP host,
   is the C2 candidate.

4. **Name the malware family from behavior, not guesswork.** Use the concrete
   signals: the C2 URI pattern (for example `/foots.php`, `/index.php?id&subid=`),
   the port, the delivery chain (fake-software site, malspam attachment, FakeUpdates
   lure), and any provided IDS/Suricata alert text. If alerts are provided, the alert
   name is strong evidence for the family. If behavior is ambiguous, name the closest
   family and say the attribution is behavioral, not signature-confirmed.

5. **Extract the delivery chain and artifacts.** Trace how the infection arrived:
   the lure domain, the redirect, the download URL, and any transferred file. Hash
   any file you can export (`--export-objects`) with SHA256.

6. **Cross-check every IOC against the capture.** Before you report an IP, domain,
   URL, hash, hostname, MAC, or user, confirm it appears in the traffic. Drop anything
   you cannot ground. Distinguish malicious IOCs from benign context and label the
   benign ones as context, not indicators.

## tshark recipes

All commands read a saved capture with `-r <pcap>`. Prefer field extraction
(`-T fields`) over reading raw packet summaries.

```bash
# Scope: protocol hierarchy and byte-ranked conversations
tshark -r c.pcap -q -z io,phs
tshark -r c.pcap -q -z conv,ip
tshark -r c.pcap -q -z endpoints,ip

# Victim host identity
tshark -r c.pcap -Y "nbns" -T fields -e nbns.name -e ip.src | sort -u          # NetBIOS name
tshark -r c.pcap -Y "dhcp" -T fields -e dhcp.option.hostname -e dhcp.hw.mac_addr | sort -u
tshark -r c.pcap -Y "kerberos.CNameString" -T fields -e kerberos.CNameString | sort -u  # username
tshark -r c.pcap -Y 'ldap.AttributeDescription=="givenName"' -T fields -e ldap.AttributeValue
tshark -r c.pcap -Y "arp" -T fields -e arp.src.proto_ipv4 -e arp.src.hw_mac | sort -u   # IP<->MAC

# Suspicious flows and C2
tshark -r c.pcap -Y "http.request" -T fields -e ip.dst -e http.host -e http.request.method -e http.request.uri | sort -u
tshark -r c.pcap -Y "http.request.method==POST" -T fields -e ip.dst -e http.host -e http.request.uri
tshark -r c.pcap -Y "dns.qry.name" -T fields -e dns.qry.name | sort -u
tshark -r c.pcap -Y "tls.handshake.type==1" -T fields -e ip.dst -e tls.handshake.extensions_server_name | sort -u

# Beaconing / odd-port TCP to one external host
tshark -r c.pcap -Y "tcp.flags.syn==1 && tcp.flags.ack==0" -T fields -e ip.dst -e tcp.dstport | sort | uniq -c | sort -rn | head

# Artifact export and hashing
tshark -r c.pcap --export-objects "http,/tmp/objs" -q
find /tmp/objs -type f -exec shasum -a 256 {} \;

# Follow a suspected C2 stream to read the protocol
tshark -r c.pcap -q -z follow,tcp,ascii,<stream_index>
```

Practical notes: bare-IP `http.host` (host equals the destination IP) is a strong C2
tell. A local host that issues repeated POSTs to the same external IP on a fixed
interval is beaconing. Odd high ports carrying persistent TCP (for example 12132) with
no TLS handshake are commodity-RAT C2.

## Required output schema

End your analysis with exactly one fenced ```json block matching this structure. Emit
only IOCs you grounded in the capture. Use the exact type strings shown.

```json
{
  "victim": {"ip": "", "mac": "", "hostname": "", "user": ""},
  "malware_family": "",
  "attribution_confidence": "signature-confirmed | behavioral | uncertain",
  "iocs": [
    {"type": "c2_endpoint", "value": "IP:port", "evidence": "how you saw it"},
    {"type": "domain", "value": "", "evidence": ""},
    {"type": "url", "value": "", "evidence": ""},
    {"type": "file_hash", "value": "sha256", "evidence": ""},
    {"type": "file_name", "value": "", "evidence": ""}
  ],
  "benign_context": [],
  "incident_summary": "2-3 sentences: who was infected, with what, via what delivery chain."
}
```

Rules for the schema: every IOC needs an `evidence` string naming the packets or the
tshark output that justifies it. `victim.mac` must be the Ethernet address bound to
`victim.ip`. Put OS/CDN/update noise in `benign_context`, never in `iocs`.
