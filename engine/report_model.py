"""The report as data (plan §8.2). `build(inputs)` returns the sections in their fixed order; both
`report_html` and `report_md` render the same model, so the two reports never disagree.

Blocks: ("md", text) · ("kpis", [(label, value, mod)]) · ("table", head, rows, foot) ·
("callout", label, text) · ("details", cls, summary, chips, blocks) · ("grid", points) ·
("banner", text). Table cells: plain strings, or tuples ("n", text) numeric, ("ball", pref, k, text),
("band", t, u), ("chip", text, mod).

Every number comes from the JSON inputs; narrative text comes from the report builder's
`sections/<id>.md` files, or from fixed sentences built from the numbers when none exist.
"""
import re
import statistics

from .common import CRITERIA, CRITERION_NAMES, FEATURE_NAMES, FEATURES, GROUPS, LEVELS, PROFILES

ORDER = ["header", "lead", "panorama", "assessed", "matrix", "features", "autonomy", "tokens",
         "robustness", "profiles", "fitgap", "decisions", "limitations", "footer"]
TITLES = {"header": "AI development methods: comparative assessment", "lead": "Overview",
          "panorama": "Panorama", "assessed": "How we assessed", "matrix": "Per-criterion matrix (L1)",
          "features": "Features (L4)", "autonomy": "Autonomy × safety (C8) × maturity", "tokens": "Tokens (L5)",
          "robustness": "Ranking robustness", "profiles": "Method profiles", "fitgap": "Fit-gap and roadmap",
          "decisions": "Decisions and open questions", "limitations": "Assumptions and limitations",
          "footer": "Footer"}
PRIVATE_BANNER = "Private: contains the assessment of a private target"
CROSS_ROUND_BANNER = "Cross-round: at least one method was scored in a different round; no verdict is drawn across rounds"
KEY = re.compile(r"^\*\*Key message:\*\*\s*(.+)$")


def n(v, fmt="{:.1f}"):
    return ("n", "n/m" if v is None else fmt.format(v))


def i_(v):
    return ("n", "n/m" if v is None else f"{v:,}")


def chip(text, mod=""):
    return ("chip", text, mod)


def parse_section(text):
    """Split a report-builder section into (key message, remaining Markdown)."""
    lines = (text or "").replace("\r\n", "\n").strip().split("\n")
    if lines and KEY.match(lines[0].strip()):
        return KEY.match(lines[0].strip()).group(1).strip(), "\n".join(lines[1:]).strip()
    return None, "\n".join(lines).strip()


class Model:
    def __init__(self, inputs):
        self.x = inputs
        self.res = inputs["results"]
        self.rk = inputs["ranking"]
        self.sens = inputs.get("sensitivity") or {}
        self.sup = inputs.get("superiority") or {}
        self.reg = inputs.get("registry") or {}
        self.sections = inputs.get("sections") or {}
        self.meta = inputs.get("meta") or {}
        self.order = [r["slug"] for r in self.rk["profiles"]["baseline"]]
        self.cols = self.order + sorted(m for m in self.res if m not in self.order)   # ranked first, then ranges
        self.targets = sorted(m for m, e in self.res.items() if e.get("role") == "target")
        self.bench = sorted(m for m, e in self.res.items() if e.get("role") == "reference" and e.get("benchmark"))
        self.private = any(e.get("private") for e in self.res.values())
        self.cross = any(e.get("comparison") == "cross-round" for e in self.res.values())

    # ---------------------------------------------------------------- helpers
    def name(self, m):
        return self.res[m].get("name") or m

    def role_chip(self, m):
        e = self.res[m]
        if e.get("role") == "target":
            return chip("target · self-assessment" if e.get("self_assessment") else "target", "org")
        return chip("benchmark" if e.get("benchmark") else "additional reference")

    def rank_of(self, m, p="baseline"):
        for r in self.rk["profiles"][p]:
            if r["slug"] == m:
                return r["rank"]
        return None

    def tie_group(self):
        return sorted(m for m, g in self.rk.get("margins", {}).items() if g["reading"] in ("leader", "technical-tie"))

    def narrative(self, sid, default_key):
        key, body = parse_section(self.sections.get(sid))
        blocks = [("md", body)] if body else []
        return key or default_key, blocks

    def section(self, sid, default_key, blocks, sub=None):
        key, extra = self.narrative(sid, default_key)
        return {"id": sid, "title": TITLES[sid], "key": key, "sub": sub, "blocks": extra + blocks}

    # ---------------------------------------------------------------- sections
    def header(self):
        m = self.meta
        rows = [("Date-base", m.get("date", "")), ("Methodology", m.get("methodology_hash", "")),
                ("Rubric", m.get("rubric_hash", "")), ("Methods", str(len(self.res)))]
        if m.get("round_id"):
            rows.append(("Round", m["round_id"]))
        banners = []
        if self.private:
            banners.append(("banner", PRIVATE_BANNER))
        if self.cross:
            banners.append(("banner", CROSS_ROUND_BANNER))
        return {"id": "header", "title": m.get("title") or TITLES["header"], "key": None, "meta": rows,
                "blocks": banners}

    def lead(self):
        key, body = parse_section(self.sections.get("lead"))
        if body:
            return {"id": "lead", "title": TITLES["lead"], "key": key, "blocks": [("md", body)]}
        lead = self.rk["leaders"]["baseline"]["leader"]
        e = self.res[lead]
        tie = [t for t in self.tie_group() if t != lead]
        nb, nt = len(self.bench), len(self.targets)
        p1 = (f"This report compares {len(self.res)} AI development methods on 16 weighted criteria (L1) and four "
              f"lenses (L2 to L5), under methodology v1.0 and rubric v2.0. The data are the shipped baseline round "
              f"{self.meta.get('round_id') or '(unstated)'}: each public method was read at a pinned commit, listed in the footer"
              + (f", plus {nt} target run{'s' if nt != 1 else ''}." if nt else "."))
        p2 = (f"The {nb} frozen benchmarks form the comparison set. Two scorers rated each method independently, "
              "a reconciler merged their sheets, and every lens reading was audited.")
        p3 = (f"Under baseline weights, {self.name(lead)} leads at {e['L1']['baseline']:.1f} ± {e['U']['baseline']:.1f}"
              + (f"; {', '.join(self.name(t) for t in tie)} {'is' if len(tie) == 1 else 'are'} within the margin "
                 "(technical tie)." if tie else ", clear of the margin."))
        return {"id": "lead", "title": TITLES["lead"], "key": None, "blocks": [("md", p1), ("md", p2), ("md", p3)]}

    def panorama(self):
        lead = self.rk["leaders"]["baseline"]["leader"]
        le = self.res[lead]
        tgt = self.targets[0] if self.targets else None
        kpis = [("Methods assessed", str(len(self.res)), ""),
                ("Leader (baseline)", f"{self.name(lead)} {le['L1']['baseline']:.1f}", "org"),
                ("Target", f"{self.name(tgt)} {self.res[tgt]['L1']['baseline']:.1f}" if tgt else "n/a", ""),
                ("Target position", f"{self.rank_of(tgt)} of {len(self.order)}" if tgt and self.rank_of(tgt) else "n/a", ""),
                ("Technical-tie group", str(len(self.tie_group())), "")]
        rows = []
        mg = self.rk.get("margins", {})
        for r in self.rk["profiles"]["baseline"]:
            m = r["slug"]
            g = mg.get(m, {})
            rows.append([("n", str(r["rank"])), self.name(m), self.role_chip(m), n(r["total"]), n(r["U"]),
                         ("band", r["total"], r["U"]),
                         g.get("reading", ""), n(g.get("delta")) if g else ""])
        blocks = [("kpis", kpis),
                  ("table", ["#", "Method", "Role", "Total", "± U", "Band (0–100)", "Reading", "Δ vs leader"], rows, None)]
        for m in self.rk.get("not_ranked", []):
            rr = (self.res[m].get("range") or {})
            if rr:
                blocks.append(("md", f"**{self.name(m)}** (documentation-only) is reported as a range, not ranked: "
                               f"floor {rr['floor']['totals']['baseline']:.1f}, centre {rr['centre']['totals']['baseline']:.1f}, "
                               f"ceiling {rr['ceiling']['totals']['baseline']:.1f}."))
        blocks.append(("callout", "How to read",
                       "Each total is the 0–100 weighted sum of the 16 criteria on scenario R, with baseline weights; "
                       "the denominator is the full 16-criterion scale, the same for every method. The band runs from "
                       "T − U to T + U with a tick at T. Two methods differ only when the gap exceeds the margin "
                       "M = 1.645·√(U₁² + U₂²); a smaller gap is a technical tie. Role chips mark the 9 frozen "
                       "benchmarks, additional references (outside verdicts) and targets."))
        tie = self.tie_group()
        key = (f"{self.name(lead)} leads under baseline weights; {len(tie)} method{'s' if len(tie) != 1 else ''} "
               "share the technical-tie group.")
        return self.section("panorama", key, blocks)

    def assessed(self):
        rows = [[c, CRITERION_NAMES[i]] + [n(PROFILES[p][i], "{:g}") for p in PROFILES] for i, c in enumerate(CRITERIA)]
        foot = ["", "Total"] + [n(sum(PROFILES[p]), "{:g}") for p in PROFILES]
        legend = [["Criteria (0–5)"] + [("ball", "c", k, str(k)) for k in range(6)],
                  ["Features (0–2)", ("ball", "f", 0, "0 absent"), ("ball", "f", 1, "1 opt-in or partial"),
                   ("ball", "f", 2, "2 default path"), "", "", ""],
                  ["Groups (%)", ("ball", "g", 0, "0–12"), ("ball", "g", 1, "13–37"), ("ball", "g", 2, "38–62"),
                   ("ball", "g", 3, "63–87"), ("ball", "g", 4, "88–100"), ""]]
        text = ("Every method is judged on reference scenario R: a team of 3–8 engineers adds a medium-sized feature "
                "to an existing production web service, with version control, CI and review before merge, using one "
                "supported AI coding agent. A mechanism counts when a user following the main entry point meets it "
                "without opting in.\n\n"
                "- **L1** scores the 16 criteria from 0 to 5 against anchored scales; the weights below give the 0–100 totals.\n"
                "- **L2** is the ceiling: the best score any shipped path reaches.\n"
                "- **L3** is the autonomy level (A0 to A5).\n"
                "- **L4** checks 34 features in 9 groups (0 absent, 1 opt-in or partial, 2 on the default path).\n"
                "- **L5** counts the static tokens a method loads (a proxy, not a measured cost).\n\n"
                "Evidence must cite a file and line at the pinned commit; roadmaps and claims do not count. Two scorers "
                "work blind to each other, a reconciler merges their sheets, a red team contests cells, and "
                "Krippendorff's α measures their agreement.")
        blocks = [("md", text),
                  ("table", ["#", "Criterion"] + [p.capitalize() for p in PROFILES], rows, foot),
                  ("table", ["Legend", "0", "1", "2", "3", "4", "5"], legend, None)]
        return self.section("assessed", "Sixteen weighted criteria on one scenario, plus four lenses, with every score cited.", blocks)

    def matrix(self):
        head = ["#", "Criterion", "Weight"] + [self.name(m) for m in self.cols]
        rows = []
        for i, c in enumerate(CRITERIA):
            rows.append([c, CRITERION_NAMES[i], n(PROFILES["baseline"][i], "{:g}")] +
                        [("ball", "c", self.res[m]["L1_scores"][i], f"{self.res[m]['L1_scores'][i]:g}") for m in self.cols])
        foot = ["", "Total (baseline)", n(100, "{:g}")] + [n(self.res[m]["L1"]["baseline"]) for m in self.cols]
        lrows = []
        for c in CRITERIA:
            lc = self.rk["leaders_criterion"][c]
            tv = ", ".join(f"{self.name(t)} {v:g}" for t, v in sorted(lc.get("target", {}).items()))
            lrows.append([c, n(lc["max"], "{:g}"), ", ".join(self.name(m) for m in lc["leaders"]),
                          n(lc["median_refs"], "{:g}"), tv or "—"])
        blocks = [("table", head, rows, foot), ("md", "**Who leads each criterion** (benchmark set)"),
                  ("table", ["#", "Max", "Leaders", "Benchmark median", "Target"], lrows, None)]
        return self.section("matrix", "No method leads every criterion; the leaders change from criterion to criterion.", blocks,
                            sub="Columns in baseline ranking order. The number sits beside each ball.")

    def features(self):
        cols = [m for m in self.cols if self.res[m].get("L4_groups")]
        head = ["Group"] + [self.name(m) for m in cols]
        rows = [[g] + [("ball", "g", _gb(self.res[m]["L4_groups"][g]), f"{self.res[m]['L4_groups'][g]}%") for m in cols]
                for g in GROUPS]
        foot = ["Coverage"] + [("n", f"{self.res[m]['L4_coverage']}%") for m in cols]
        frows = []
        for i, f in enumerate(FEATURES):
            cells = []
            for m in cols:
                v = self.res[m]["L4"].get(f, 0)
                cells.append("NA" if v == "NA" else ("ball", "f", v, str(v)))
            frows.append([f, FEATURE_NAMES[i]] + cells)
        blocks = [("table", head, rows, foot),
                  ("details", "cp", "All 34 features", [],
                   [("table", ["#", "Feature"] + [self.name(m) for m in cols], frows, None)])]
        return self.section("features", "Feature coverage is uneven across the nine groups; no method covers them all.", blocks,
                            sub="Group cells show the share of the group's points (2 per feature); coverage is over all 34 features.")

    def autonomy(self):
        a = self.rk.get("autonomy_safety", {})
        rows = [[self.name(m), a[m]["L3"] or "n/m", n(a[m]["C8"], "{:g}"), n(a[m]["L1"]), a[m]["reading"]]
                for m in self.order if m in a]
        pts = [(self.name(m), LEVELS.index(a[m]["L3"]) if a[m]["L3"] in LEVELS else None, a[m]["C8"])
               for m in self.order if m in a]
        blocks = [("table", ["Method", "L3 autonomy", "C8 safety", "L1 (baseline)", "Reading"], rows, None),
                  ("grid", [p for p in pts if p[1] is not None and p[2] is not None]),
                  ("callout", "Autonomy is not quality",
                   "A higher L3 level means the method runs longer without a person; it says nothing about the quality "
                   "of the result. Read it together with C8, the safety of autonomous execution.")]
        return self.section("autonomy", "Several methods offer more autonomy than their safety controls cover.", blocks)

    def tokens(self):
        rows = []
        for m in self.cols:
            t = self.res[m].get("L5")
            if not t:
                rows.append([self.name(m), ("n", "n/m"), ("n", "n/m"), ("n", "n/m"), ("n", "n/m"), "n/m"])
                continue
            pre = "" if t.get("comparable") else "approx. "
            cell = lambda v: ("n", "n/m" if v is None else f"{pre}{v:,}")
            rows.append([self.name(m), cell(t.get("T1")), cell(t.get("T2")), cell(t.get("T3")), cell(t.get("T0")),
                         t.get("tokenizer") or ""])
        blocks = [("table", ["Method", "T1", "T2", "T3", "T0", "Tokenizer"], rows, None),
                  ("callout", "Proxy",
                   "Static token counts of the files a method ships, not measured runtime cost. T1 is what loads at "
                   "start, T2 one typical step, T3 the default path for scenario R, T0 the whole method root. "
                   "n/m means not measurable; approx. means not comparable with the other rows.")]
        return self.section("tokens", "Static footprints differ by an order of magnitude across methods.", blocks)

    def robustness(self):
        profs = list(PROFILES)
        rows = []
        for m in self.order:
            cells = []
            for p in profs:
                e = next(r for r in self.rk["profiles"][p] if r["slug"] == m)
                cells.append(("n", f"{e['total']:.1f} ({e['rank']})"))
            rows.append([self.name(m)] + cells)
        foot = ["Leader"] + [self.name(self.rk["leaders"][p]["leader"]) for p in profs]
        blocks = [("table", ["Method"] + [f"{p.capitalize()} total (rank)" for p in profs], rows, foot)]
        sups = [(t, self.sup[t]) for t in self.targets if t in self.sup]
        for t, s in sups:
            blocks.append(("md", f"**Superiority test: {self.name(t)}** (methodology §9)"))
            blocks.append(_superiority_table(s))
        pf = self.sens.get("p_first") or {}
        mr = self.sens.get("mean_rank") or {}
        smp = ["centred", "uniform", "score_perturbation"]
        if pf:
            prow = [[self.name(m)] + [n(pf[s].get(m), "{:.3f}") for s in smp] + [n(mr.get("centred", {}).get(m), "{:.2f}")]
                    for m in self.order if m in pf.get("centred", {})]
            blocks.append(("md", f"**P(first)** over {self.sens.get('draws', 0):,} draws per sampler (seed {self.sens.get('seed')})."))
            blocks.append(("table", ["Method", "Centred", "Uniform", "Score perturbation", "Mean rank (centred)"], prow, None))
        torn = self.sens.get("tornado") or []
        if torn:
            trows = []
            for c in CRITERIA:
                tr = [t for t in torn if t["c"] == c]
                moved = max((sum(1 for v in t["changes"].values() if v) for t in tr), default=0)
                firsts = sorted({m for t in tr for m, r in t["ranks"].items() if r == 1})
                trows.append([c, ("n", str(moved)), ", ".join(self.name(m) for m in firsts)])
            blocks.append(("md", "**Tornado** (each weight × 0.5 and × 1.5): methods whose rank moves, and who is first."))
            blocks.append(("table", ["#", "Methods moved (max)", "First under the change"], trows, None))
        loo = self.sens.get("loo") or []
        if loo:
            lrows = [[r["c"], ", ".join(self.name(m) for m in r["first"])] for r in loo]
            blocks.append(("md", "**Leave-one-out** (each criterion removed in turn)."))
            blocks.append(("table", ["Removed", "First"], lrows, None))
        lead = self.rk["leaders"]["baseline"]["leader"]
        p = pf.get("centred", {}).get(lead)
        key = (f"{self.name(lead)} is first in {p:.0%} of centred weight draws; the lead depends on the weighting."
               if p is not None else "The ranking is tested across profiles and weight draws.")
        return self.section("robustness", key, blocks)

    def profiles(self):
        blocks = []
        best, med = self.rk.get("best_refs") or [], self.rk.get("median_refs") or []
        for m in self.cols:
            e = self.res[m]
            r = self.reg.get(m, {})
            card = [["Name", e.get("name") or m], ["Origin", e.get("origin") or "—"], ["Role", self.role_chip(m)],
                    ["Type", e.get("type") or "—"], ["Status", e.get("status") or "—"], ["Host", e.get("host") or "—"]]
            if r:
                card += [["Licence", r.get("licence") or "—"], ["Pin", (r.get("pin") or "")[:12] or "—"],
                         ["Source", r.get("url") or "—"]]
            inner = [("table", ["Field", "Value"], card, None)]
            rk = self.rank_of(m)
            if rk:
                inner.append(("md", f"**Key message:** ranks {rk} of {len(self.order)} under baseline weights at "
                                    f"{e['L1']['baseline']:.1f} ± {e['U']['baseline']:.1f}."))
            l1 = [[c, CRITERION_NAMES[i], ("ball", "c", e["L1_scores"][i], f"{e['L1_scores'][i]:g}"),
                   n(e["u"][i], "{:g}")] for i, c in enumerate(CRITERIA)]
            inner.append(("table", ["#", "Criterion", "L1", "u"], l1, None))
            lens = [["L2 ceiling (baseline)", n((e.get("L2") or {}).get("baseline"))],
                    ["L3 autonomy", f"{e.get('L3') or 'n/m'}" + (f" (confidence {e['L3_conf']})" if e.get("L3_conf") else "")],
                    ["L4 coverage", ("n", f"{e['L4_coverage']}%") if e.get("L4_coverage") is not None else ("n", "n/m")],
                    ["L5 T1 tokens", i_((e.get("L5") or {}).get("T1"))]]
            inner.append(("table", ["Lens", "Value"], lens, None))
            if best and e.get("role") == "reference":
                strong = [CRITERIA[i] for i in range(16) if e["L1_scores"][i] >= best[i]]
                inner.append(("md", "**Strengths** (at the benchmark best): " + (", ".join(strong) or "none") + "."))
            weak = (self.rk.get("weakest_vs_median") or {}).get(m) or []
            if weak:
                wrows = [[w["c"], n(w["s"], "{:g}"), n(w["median"], "{:g}"), n(w["best"], "{:g}"),
                          ", ".join(self.name(x) for x in w["leaders"])] for w in weak]
                inner.append(("md", "**Weakest three versus the benchmark median**"))
                inner.append(("table", ["#", "Score", "Median", "Best", "Leaders"], wrows, None))
            if e.get("design"):
                d = e["design"]
                inner.append(("md", f"**Design-only:** design total {d['design_total']['baseline']:.1f}, realization-adjusted "
                                    f"total {d['RA_total']['baseline']:.1f}, realization gap {d['realization_gap']['baseline']:.1f}."))
                drows = [[c, n(d["D_scores"][i], "{:g}"), n(d["r"][i], "{:g}"), n(d["RA_scores"][i], "{:g}")]
                         for i, c in enumerate(CRITERIA)]
                inner.append(("table", ["#", "D", "r", "RA"], drows, None))
            if e.get("range"):
                rr = e["range"]
                rrows = [[k, n(rr[k]["totals"]["baseline"]), n(rr[k]["position"]["baseline"], "{:g}")]
                         for k in ("floor", "centre", "ceiling")]
                inner.append(("md", "**Documentation-only range** (baseline weights; position among the benchmarks)."))
                inner.append(("table", ["Reading", "Total", "Position"], rrows, None))
            key, body = parse_section(self.sections.get(f"profile-{m}"))
            if key:
                inner.insert(1, ("md", f"**Key message:** {key}"))
            if body:
                inner.append(("md", body))
            chips = [chip(f"{e['L1']['baseline']:.1f}"), self.role_chip(m)]
            blocks.append(("details", "pr", self.name(m), chips, inner))
        return self.section("profiles", "Each profile shows the card, the scores and the weakest criteria.", blocks,
                            sub="Open a method to see its card, L1 table, lenses and weakest criteria.")

    def fitgap(self):
        pre = self.x.get("fitgap_pre")
        if not pre:
            return None
        crows = [[g["c"], n(g["target"], "{:g}"), n(g["best"], "{:g}"), n(g["gap_points_baseline"], "{:.2f}"),
                  ", ".join(self.name(m) for m in g["leaders"])] for g in pre["criteria"]]
        frows = [[f["f"], FEATURE_NAMES[FEATURES.index(f["f"])], str(f["target"]),
                  ", ".join(self.name(m) for m in f["refs_at_2"]) or "—"] for f in pre["features"]]
        blocks = [("table", ["#", "Target", "Best", "Gap (baseline points)", "Leaders"], crows,
                   ["Total", "", "", n(pre["total_gap_points_baseline"], "{:.2f}"), ""]),
                  ("details", "cp", "Feature gaps", [], [("table", ["#", "Feature", "Target", "At 2 in"], frows, None)])]
        fg = self.x.get("fitgap") or {}
        items = fg.get("items") or []
        if items:
            irows = [[it.get("id", ""), it.get("horizon", ""), ", ".join(it.get("c") or []), it.get("mechanism", ""),
                      ", ".join(self.name(m) if m in self.res else m for m in it.get("learn_from") or []),
                      it.get("effort", ""), n(it.get("impact_points"), "{:.1f}"), it.get("owner_role", "")]
                     for it in sorted(items, key=lambda it: (["now", "30", "60-90"].index(it.get("horizon", "now"))
                                                             if it.get("horizon") in ("now", "30", "60-90") else 3, it.get("id", "")))]
            blocks.append(("table", ["ID", "Horizon", "Criteria", "Mechanism", "Learn from", "Effort", "Impact", "Owner"], irows, None))
        pj = self.x.get("projection")
        if pj:
            prow = [["Current", n(pj["current"])]] + [[f"If done: {h}", n(v)] for h, v in pj["baseline_total_if_done"].items()]
            blocks.append(("table", ["Horizon (cumulative)", "Baseline total"], prow, None))
            blocks.append(("callout", "Hypothesis", pj.get("label") or "A projection, not a score."))
        return self.section("fitgap", f"The target trails the best reference on {len(pre['criteria'])} criteria.", blocks)

    def decisions(self):
        if not self.sections.get("decisions"):
            return None
        return self.section("decisions", None, [])

    def limitations(self):
        items = []
        tg = [self.res[t] for t in self.targets]
        meta = self.meta
        items.append(f"**Isolation mode:** {meta.get('isolation') or ('not applicable: no target run in this report' if not tg else 'not recorded')}.")
        if tg:
            for t in self.targets:
                mm = self.res[t].get("models")
                items.append(f"**Host and models ({self.name(t)}):** host {self.res[t].get('host') or 'not recorded'}; "
                             + (", ".join(f"{k} {v}" for k, v in sorted(mm.items())) if mm else "model IDs not recorded") + ".")
        else:
            items.append("**Host and models:** the baseline references were scored in the reference round; per-stage model IDs are not part of the shipped data.")
        items += [
            "**Accepted risk (#95):** `requests/log/` is writable throughout a run, so any agent could append log lines or submit an owner answer. The log is informational; owner answers are recorded as \"via orchestrator\" and the adjudicator treats them only as claims of fact that still need cited evidence.",
            "**Isolation note (#86):** scorer stages run per instance, but while they run in parallel and the hook cannot identify agents, one scorer could write into another's sealed folder. Write isolation between parallel scorers is then prompt-only.",
            "**Residual state-integrity risk (#78):** where the hook cannot tell sessions apart, non-privileged state commands for the running stage are bounded by declared-output and hash checks but not prevented."]
        ex = [(self.name(t), d) for t in self.targets for d in (self.res[t].get("excluded_dirs") or [])]
        items.append("**Excluded directories:** " + ("; ".join(f"{a}: {d if isinstance(d, str) else d.get('path', d)}" for a, d in ex) if ex else "none.") )
        adds = sorted(m for m, e in self.res.items() if e.get("role") == "reference" and not e.get("benchmark"))
        items.append(f"**Comparison set:** the {len(self.bench)} frozen benchmarks" +
                     (f"; additional references outside verdicts: {', '.join(self.name(m) for m in adds)}." if adds else "; no additional references."))
        items.append("**Cross-round status:** " + ("at least one method is cross-round; no verdict is drawn across rounds." if self.cross else "all methods are same-round."))
        sa = [self.name(t) for t in self.targets if self.res[t].get("self_assessment")]
        items.append("**Self-assessment:** " + (f"{', '.join(sa)} assessed by its own authors' tool run." if sa else "none."))
        al = [(self.name(t), self.res[t].get("reliability")) for t in self.targets]
        al = [(a, r) for a, r in al if r and r.get("alpha") is not None]
        items.append("**Krippendorff's α:** " + ("; ".join(f"{a} α = {r['alpha']:.3f}" + (f" (90% interval {r['ci90'][0]:.3f}–{r['ci90'][1]:.3f})" if r.get("ci90") else "")
                                                         for a, r in al) + "; with few rated units the interval is wide." if al
                                                else "not applicable: no target run in this report."))
        if "kiro" in self.res:
            items.append("**Kiro:** scored from a 2026-11-26 documentation snapshot that cannot be re-fetched.")
        cal = [(self.name(t), (self.res[t].get("reliability") or {}).get("calibration")) for t in self.targets]
        cal = [(a, c) for a, c in cal if c]
        items.append("**Calibration drift:** " + ("; ".join(f"{a}: raw deltas {c['delta_raw']}, reconciled deltas {c['delta_reconciled']}, drift {'yes' if c['drift'] else 'no'}" for a, c in cal)
                                                  if cal else "not applicable: no calibration in this report."))
        items.append("**U_recorded versus derived u:** for the references, the baseline-profile U is the value recorded in the reference round; every other profile, and every target, uses the U derived from per-criterion u.")
        toks = sorted({(e.get("L5") or {}).get("tokenizer") for e in self.res.values() if e.get("L5")} - {None})
        items.append(f"**Tokenizer:** {', '.join(toks) or 'not recorded'}; counts are static proxies.")
        items.append("**Evidence caps:** closed products scored mostly from documentation are capped at 4 (methodology §12); documentation-only targets are capped as their range assessment states.")
        items.append("**Single-assessor ranges:** documentation-only ranges come from one assessor and carry low confidence." if any(e.get("range") for e in self.res.values())
                     else "**Single-assessor ranges:** none in this report.")
        items.append(f"**Confidence:** {meta.get('confidence') or 'medium: scores rest on cited evidence and two independent scorers, but the weights are judgment and the field outcomes are not measured.'}")
        return self.section("limitations", "The numbers are cited and reproducible; the weights and the field effect are not measured.",
                            [("md", "\n".join(f"- {x}" for x in items))])

    def footer(self):
        m = self.meta
        links = [(self.reg[s].get("name") or s, self.reg[s]["url"]) for s in sorted(self.reg) if self.reg[s].get("url") and s in self.res]
        return {"id": "footer", "title": "", "key": None, "blocks": [], "links": links,
                "lines": [f"Generated by ai-sdlc-method-analyzer {m.get('version', '')} on {m.get('date', '')}.",
                          f"Methodology {m.get('methodology_hash', '')} · rubric {m.get('rubric_hash', '')}.",
                          "Code and shipped data are under the MIT licence; each reference method keeps its own licence and is not redistributed.",
                          "No telemetry: the tool sends nothing anywhere. The AI provider that runs the agents processes "
                          "the files they read under its own terms."]}

    def build(self):
        out = []
        for sid in ORDER:
            s = getattr(self, sid)()
            if s is not None:
                out.append(s)
        return out


def _gb(p):
    from .svg import group_band
    return group_band(p)


def _superiority_table(s):
    if s.get("verdict") == "none":
        return ("table", ["Condition", "Value"], [["Verdict", "none"], ["Reason", s.get("reason", "")]], None)
    tick = lambda ok: "✓" if ok else "✗"
    S2 = s["S2"]["profiles"]
    s3 = s["S3"]["checks"]
    rows = [["S1 margin (base)", f"ΔT = {s['S1']['delta']:.1f}", f"M = {s['S1']['M']:.1f}", tick(s["S1"]["pass"])],
            ["S2 per profile", " / ".join(f"{p} {S2[p]['delta']:.1f}" for p in S2), "M(P) each", tick(s["S2"]["pass"])],
            ["S3 rank-1 prob.", " / ".join(f"{k} {tick(v)}" for k, v in s3.items()), ".90/.75/.90; 16/16", tick(s["S3"]["pass"])],
            ["S4 criteria below median", ", ".join(s["S4"]["below_median"]) or "none", "none", tick(s["S4"]["pass"])],
            ["S5 best-in-class count", f"{len(s['S5']['best_in_class'])} (core {len(s['S5']['core'])})", "≥6 (≥3 core)", tick(s["S5"]["pass"])],
            ["S6 audit", "completed" if s["S6"]["pass"] else "not completed", "completed", tick(s["S6"]["pass"])],
            ["S7 Krippendorff α", "n/m" if s["S7"]["alpha"] is None else f"{s['S7']['alpha']:.3f}", "≥ .667", tick(s["S7"]["pass"])],
            ["Verdict", s["verdict"], "", ""]]
    return ("table", ["Condition", "Value", "Threshold", "Pass"], rows, None)


def build(inputs):
    return Model(inputs).build()


def median(xs):
    return statistics.median(xs)
