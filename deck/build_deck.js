// Deck for "Skill Issue" built per the academic-pptx skill: Structured Argument mode,
// action-title takeaways, ghost-deck test, minimal design (white bg, one sans-serif,
// <=3 colors), figure-left/bullets-right result slides, in-slide citations, References.
const pptxgen = require("pptxgenjs");
const path = require("path");

const P = new pptxgen();
P.defineLayout({ name: "W16x9", width: 13.333, height: 7.5 });
P.layout = "W16x9";
P.author = "Yaakulya Sabbani";
P.title = "Skill Issue";

const NAVY = "1F4E79";     // primary
const BLUE = "2E75B6";     // accent
const ALERT = "C00000";    // emphasis
const MUTED = "808080";    // citations only
const FONT = "Arial";
const IMG = (f) => path.join(__dirname, "img", f);
const MX = 0.6;            // left/right margin

function actionTitle(slide, text) {
  slide.addText(text, {
    x: MX, y: 0.32, w: 13.333 - 2 * MX, h: 1.0, fontFace: FONT, fontSize: 25,
    bold: true, color: NAVY, align: "left", valign: "top",
  });
}
function cite(slide, text) {
  slide.addText(text, {
    x: MX, y: 7.02, w: 13.333 - 2 * MX, h: 0.35, fontFace: FONT, fontSize: 12,
    color: MUTED, align: "left",
  });
}
// figure-left, interpretive bullets-right
function resultSlide(title, img, bullets, source, opts = {}) {
  const s = P.addSlide();
  s.background = { color: "FFFFFF" };
  actionTitle(s, title);
  s.addImage({ path: IMG(img), x: MX, y: 1.5, w: 6.7, h: 5.0, sizing: { type: "contain", w: 6.7, h: 5.0 } });
  const items = bullets.map((b) => ({
    text: b.t,
    options: { bullet: { code: "2022" }, color: b.c || "404040", bold: !!b.b, fontSize: 18, paraSpaceAfter: 10, breakLine: true },
  }));
  s.addText(items, {
    x: 7.7, y: 1.6, w: 5.0, h: 4.8, fontFace: FONT, align: "left", valign: "top",
  });
  if (source) cite(s, source);
  return s;
}
function sep(v) { return { line: { color: "D9D9D9", width: 1 } }; }

// ---------- 1. Title ----------
{
  const s = P.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("Skill Issue", { x: MX, y: 2.2, w: 12.1, h: 1.0, fontFace: FONT, fontSize: 46, bold: true, color: NAVY });
  s.addText("Decomposing Procedural Knowledge Injection for LLM-Agent Network Forensics", {
    x: MX, y: 3.3, w: 12.1, h: 0.9, fontFace: FONT, fontSize: 24, color: BLUE });
  s.addText("Yaakulya Sabbani", { x: MX, y: 4.5, w: 12.1, h: 0.5, fontFace: FONT, fontSize: 18, color: "404040" });
  s.addText("ORCID 0009-0001-3689-3109", { x: MX, y: 4.95, w: 12.1, h: 0.4, fontFace: FONT, fontSize: 14, color: MUTED });
}

// ---------- 2. Problem ----------
{
  const s = P.addSlide(); s.background = { color: "FFFFFF" };
  actionTitle(s, "Agent Skills now specialize LLM agents, yet no study tests whether they make a packet-forensics agent competent, or which part does the work");
  s.addText([
    { text: "Skills package procedural knowledge (workflow, tool recipes, output contracts) injected into a generalist model at inference time.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "Cross-domain evaluation reports cybersecurity as the largest-gain domain, but treats the skill as one atomic block.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "Open question 1: does a skill make a tshark-driving agent a competent analyst, measured against vetted ground truth?", options: { bullet: { code: "2022" }, breakLine: true, color: NAVY, bold: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "Open question 2: which component of a skill produces any gain?", options: { bullet: { code: "2022" }, breakLine: true, color: NAVY, bold: true, fontSize: 19 } },
  ], { x: MX, y: 1.7, w: 12.1, h: 4.8, fontFace: FONT, align: "left", valign: "top" });
  cite(s, "SkillsBench 2026; Anthropic Agent Skills; agentskills.io");
}

// ---------- 3. Method ----------
{
  const s = P.addSlide(); s.background = { color: "FFFFFF" };
  actionTitle(s, "We hold the model and toolbox fixed and vary only the injected skill across six arms, isolating each component by ablation");
  const rows = [
    [{ text: "Arm", options: { bold: true, color: "FFFFFF", fill: NAVY } }, { text: "Injected skill", options: { bold: true, color: "FFFFFF", fill: NAVY } }, { text: "Components", options: { bold: true, color: "FFFFFF", fill: NAVY } }],
    ["A", "none (vanilla)", "baseline"],
    ["B", "community Wireshark skill", "external"],
    ["C", "custom IOC-forensics skill", "workflow + recipes + schema"],
    ["D1", "C minus workflow", "recipes + schema"],
    ["D2", "C minus recipes", "workflow + schema"],
    ["D3", "C minus schema", "workflow + recipes"],
  ];
  s.addTable(rows, { x: MX, y: 1.7, w: 8.2, colW: [1.0, 3.7, 3.5], fontFace: FONT, fontSize: 15, color: "404040", border: { type: "solid", color: "D9D9D9", pt: 1 }, valign: "middle", rowH: 0.45 });
  s.addText([
    { text: "Same neutral task: investigate the evidence, write an incident report.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 17, paraSpaceAfter: 10 } },
    { text: "Ablations remove one marked section verbatim, so each differs from C by one component only.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 17, paraSpaceAfter: 10 } },
    { text: "Runtime: Claude Code CLI, read-only tools, web and file-transfer denied.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 17 } },
  ], { x: 9.2, y: 1.7, w: 3.5, h: 4.5, fontFace: FONT, align: "left", valign: "top" });
  cite(s, "Metrics: IOC recall, victim-ID accuracy, family attribution, hallucination, tool calls, cost");
}

// ---------- 4. Data integrity ----------
{
  const s = P.addSlide(); s.background = { color: "FFFFFF" };
  actionTitle(s, "Validating every indicator against packets exposed wrong C2 IPs in three of nine published answer keys");
  s.addText([
    { text: "9 real malware-infection captures (RAT, stealer, loader families) with official analyst writeups.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "We transcribed each writeup to a typed IOC set, then checked every indicator with tshark.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "3 of 9 answer keys printed a C2 IP absent from every packet (e.g. STRRAT key says 141.98.10.69; port-12132 traffic goes to 141.98.10.79).", options: { bullet: { code: "2022" }, breakLine: true, color: ALERT, bold: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "Corrected against primary evidence. Forensic ground truth must be validated, not trusted.", options: { bullet: { code: "2022" }, breakLine: true, color: NAVY, bold: true, fontSize: 19 } },
  ], { x: MX, y: 1.7, w: 12.1, h: 4.8, fontFace: FONT, align: "left", valign: "top" });
  cite(s, "Malware-Traffic-Analysis.net; validation via tshark 4.6");
}

// ---------- 5. Base strong ----------
resultSlide(
  "A capable base model already identifies the victim host in 97 percent of cases, so skills barely move accuracy",
  "fig_main_bars.png",
  [
    { t: "Victim-ID accuracy is identical (0.97) across all six arms.", b: true, c: NAVY },
    { t: "IOC recall spans a narrow 0.87 to 0.91." },
    { t: "A skill does not turn a capable model into an analyst; it already is one for routine work." },
    { t: "So we look past recall: efficiency, faithfulness, and where the components matter." },
  ],
  "Mean across 9 cases, up to 3 reps each (111 valid runs)"
);

// ---------- 6. Generic skill hurts ----------
resultSlide(
  "A generic community skill is net-negative: it has the worst attribution and the most fabricated indicators",
  "fig_halluc.png",
  [
    { t: "Official skill (B): highest hallucination (0.85 fabricated IOCs per case).", b: true, c: ALERT },
    { t: "Also the worst family attribution (0.50 vs 0.625)." },
    { t: "No recall benefit over the untreated baseline." },
    { t: "Injecting off-the-shelf procedural knowledge is not free." },
  ],
  "Hallucination = IOC-shaped tokens asserted but absent from the capture"
);

// ---------- 7. Custom skill efficiency ----------
resultSlide(
  "A purpose-built skill buys efficiency and safety, not accuracy: equal recall with 37 percent fewer tshark commands",
  "fig_pareto.png",
  [
    { t: "Custom skill (C): best recall (0.907) at the lowest command count.", b: true, c: NAVY },
    { t: "37% fewer tshark commands than vanilla (10.7 vs 17.0)." },
    { t: "Lower hallucination than both vanilla and the generic skill." },
    { t: "The win is a leaner, more faithful investigation, not a higher ceiling." },
  ],
  "Each point is one arm's mean over 9 cases"
);

// ---------- 8. Ablation ----------
resultSlide(
  "Ablation shows the workflow and recipes carry the benefit, while the output schema is the largest driver of fabrication",
  "fig_ablation.png",
  [
    { t: "Removing workflow (D1): recall and attribution drop to the generic-skill level.", b: true, c: NAVY },
    { t: "Removing recipes (D2): lowest recall, higher hallucination." },
    { t: "Removing schema (D3): recall unchanged, hallucination falls to 0.15 (best in study).", b: true, c: ALERT },
    { t: "The rigid IOC template appears to induce fabrication: named slots invite filling." },
  ],
  "Contribution = full skill (C) minus the ablation that removes each component"
);

// ---------- 9. Grammar ----------
resultSlide(
  "The investigation grammar shows the custom skill runs a leaner, more targeted inquiry",
  "fig_grammar.png",
  [
    { t: "The mix of command categories each arm issues, normalized." },
    { t: "The custom skill concentrates on victim-ID and statistics passes." },
    { t: "It issues fewer commands overall while covering the same evidence." },
    { t: "After a fix, all arms inventory the directory and read available IDS alerts." },
  ],
  "Commands classified from full agent trajectories"
);

// ---------- 10. Attribution ceiling ----------
resultSlide(
  "Family attribution is the hard ceiling: no arm exceeds six of nine, bounded by alert-free behavioral cases",
  "fig_heatmap.png",
  [
    { t: "Per-case IOC recall by arm; most cases sit near the ceiling." },
    { t: "Where Suricata alerts are present, all arms read them and attribute correctly." },
    { t: "Where alerts are absent, no skill closes the attribution gap.", b: true, c: NAVY },
    { t: "This bounds the promise of packet-only agentic attribution." },
  ],
  "Rows are cases; columns are arms"
);

// ---------- 11. Recommendations ----------
{
  const s = P.addSlide(); s.background = { color: "FFFFFF" };
  actionTitle(s, "Skill authors should invest in workflow and recipes, prefer evidence-gated output, and widen the evidence an agent considers");
  s.addText([
    { text: "On a strong base model, a skill is an efficiency and safety tool, not a capability unlock.", options: { bullet: { code: "2022" }, breakLine: true, color: NAVY, bold: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "Prefer evidence-gated output (emit an indicator only with a citation) over fixed templates that pressure the model to fabricate.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "Design skills that widen, not narrow, the evidence considered; a narrow skill can suppress useful exploration (the skill-issue effect).", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19, paraSpaceAfter: 12 } },
    { text: "We release the harness, the evidence-validated dataset, and all skill variants.", options: { bullet: { code: "2022" }, breakLine: true, fontSize: 19 } },
  ], { x: MX, y: 1.7, w: 12.1, h: 4.8, fontFace: FONT, align: "left", valign: "top" });
  cite(s, "Effects are modest vs case variance (n=9); the schema effect on hallucination is the most robust");
}

// ---------- 12. References ----------
{
  const s = P.addSlide(); s.background = { color: "FFFFFF" };
  s.addText("References", { x: MX, y: 0.4, w: 12.1, h: 0.8, fontFace: FONT, fontSize: 28, bold: true, color: NAVY });
  const refs = [
    "[1] CyberSleuth: Autonomous Blue-Team LLM Agent for Web Attack Forensics. arXiv:2508.20643.",
    "[2] Holmes: Evidence-Grounded LLM Agent for Auditable DDoS Investigation. arXiv:2601.14601.",
    "[3] Before You Hand Over the Wheel: Evaluating LLMs for Security Incident Analysis. arXiv:2603.06422.",
    "[4] SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks. arXiv:2602.12670.",
    "[5] Malware-Traffic-Analysis.net, B. Duncan. Traffic analysis exercises.",
    "[6] Wireshark and tshark, Wireshark Foundation, v4.6.",
  ];
  s.addText(refs.map((r) => ({ text: r, options: { fontSize: 15, color: "404040", paraSpaceAfter: 10 } })),
    { x: MX, y: 1.4, w: 12.1, h: 5.0, fontFace: FONT, align: "left", valign: "top" });
}

const out = path.join(__dirname, "Skill_Issue_talk.pptx");
P.writeFile({ fileName: out }).then(() => console.log("WROTE " + out));
