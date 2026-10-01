# Skill Issue: Agent Skills for LLM Network Forensics

Does injecting an Agent Skill (packaged procedural knowledge) make an LLM agent that drives
`tshark` a better network forensic analyst? And which part of the skill does the work?

This repo holds a controlled experiment that answers both: the harness, every skill variant,
evidence-validated ground truth for 9 real malware-infection captures, and all run results.

## Experiment design

The skill is the only thing that changes. Same model, same `tshark` toolbox, same captures,
nine arms:

| Arm | Skill |
|---|---|
| A | no skill (baseline) |
| B1 to B4 | four widely used community skills from the two most-starred public skill repositories |
| C | custom IOC-forensics skill: workflow + `tshark` recipes + strict output schema |
| D1 | C without the workflow |
| D2 | C without the recipes |
| D3 | C without the schema |

Comparing A, B and C shows whether a skill helps. Comparing C with D1 to D3 shows which
component carries the effect.

## Metrics

Per run: IOC recall against vetted indicators, victim identification (IP, MAC, hostname,
user), malware family attribution, fabricated indicators (checked against every token
observable in the capture), `tshark` command count, output tokens, and wall-clock time.

## Headline result

482 valid runs (243 Sonnet, 239 Haiku). The custom skill issues 30% fewer `tshark` commands
than no skill (paired p < 0.001; 35% on Haiku) and 22% fewer than the community skills, with
no significant change in accuracy or fabrication. Of its three components, only the command
recipes add commands when removed, on both models.

## Ground truth

9 exercises from Malware-Traffic-Analysis.net. Every network indicator in the published
answer keys was re-checked against the packets; 4 of 9 keys had a wrong primary indicator
(two C2 IPs, one victim IP, one victim MAC), corrected in `harness/ground_truth.json`.
The PCAPs themselves are not redistributed; sources are listed in `datasets/mta-index.html`.

## Layout

```
harness/     runner, scoring, statistics, figure and diagram generators
skills/      custom skill, community skills, and the three ablations
results/     per-run JSON results, summary.csv, statistics
figures/     plots and diagrams (.drawio sources included)
paper/       LaTeX write-up of the results
arxiv/       self-contained LaTeX source bundle
datasets/    capture index (PCAPs not included)
```

## Running it

- `tshark` 4.6+, offline read only
- Python 3 with numpy, pandas, scipy, matplotlib
- The `claude` CLI as the agent runtime

```
bash harness/run_night.sh 1                       # one rep over all arms and cases
python harness/analyze.py && python harness/stats.py
```
