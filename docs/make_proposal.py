"""Reproduce the two-page Iteration-1 proposal (all nine proposed A-I modules).

    python docs/make_proposal.py proposal.pdf

ReportLab's built-in Helvetica fonts require no Windows, macOS or Linux font paths.
Page 1 contains one module-selection table; page 2 one contribution table.
The existing title rows are intentionally retained per the group's preference.
"""
from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak

CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=7.7, leading=9.5,
                      spaceAfter=0, spaceBefore=0, splitLongWords=1)
HEAD = ParagraphStyle("head", parent=CELL, fontName="Helvetica-Bold", fontSize=8.0,
                      leading=9.8, textColor=colors.white)
TITLE = ParagraphStyle("title", parent=CELL, fontName="Helvetica-Bold", fontSize=9.2,
                       leading=11.5, alignment=TA_CENTER)
BIG = ParagraphStyle("big", parent=CELL, fontSize=9.1, leading=11.5)
GROUP = ("LIFELINE: Algorithm-selection report (proposal), Iteration 1. Group 18: "
         "Saneed Ullah (23i-2568), Hasnat Ahmed (23i-2652), "
         "Hussain Muhammad Ibrahim (23i-2626), AI-B")


def P(s, style=CELL):
    return Paragraph(s, style)


# Problem, two or more algorithm candidates with asymptotic running time,
# primary/baseline, data-dependent reason + assumption + failure condition.
# All numbers and operations here come from cases.xlsx or ProjectPhase1.pdf.
MODULES = [
    (
        "<b>A. Relief inventory</b>",
        "n indivisible crates with integer weights w in [1,20], stored values v in [10,100], "
        "capacity W. Maximise sum(v) with sum(w) &lt;= W (0/1 knapsack).",
        "Capacity DP O(nW) time, O(W) value memory (+ choices to rebuild); "
        "exhaustive O(n2<super>n</super>); ratio-greedy O(n log n).",
        "<b>Primary:</b> exact capacity DP + reconstruction. <b>Baseline:</b> ratio-greedy; "
        "brute force verifies S claims.",
        "Small integer weights and seed-18 W &lt;= 3,388 keep DP practical "
        "(max nW ~ 4.2m). Assumes integral kg. Large W makes reconstruction memory costly; "
        "trap 47 gives greedy only 55% of optimum. No day multiplier in data."
    ),
    (
        "<b>B. Route planning</b>",
        "G=(V,E), blocked wave roads, HQ 0, targets. Find reachable sites, fewest-road BFS "
        "path, and minimum-cost route using c(u,v)=minutes+penalty(v).",
        "BFS O(V+E); binary-heap Dijkstra O((V+E) log V); "
        "array Dijkstra O(V<super>2</super>); Bellman-Ford O(VE).",
        "<b>Primary:</b> Dijkstra for cost; BFS for hops/reachability. "
        "<b>Baseline:</b> BFS-cost path and Bellman-Ford check.",
        "E &lt;= 3V and strictly positive step costs suit heap Dijkstra. "
        "Destination penalties make travel direction cost asymmetric. Must remove closed edges; "
        "return no route if disconnected. Negative edge weights would invalidate Dijkstra; "
        "trap 48 defeats fewest roads by &gt;=1.5x. No storm multiplier."
    ),
    (
        "<b>C. Rescue scheduling</b>",
        "n windows [start, finish), values 1..100. Select compatible windows (touching "
        "allowed) to maximise count or total value.",
        "Earliest-finish greedy O(n log n) (count); weighted interval DP O(n log n) "
        "(value); exhaustive O(n2<super>n</super>); value-greedy O(n log n).",
        "<b>Primary:</b> finish-time greedy / weighted DP with predecessor search. "
        "<b>Baseline:</b> value-greedy; brute on S.",
        "Up to 3,000 windows and study-3 heavy overlap favour interval algorithms. "
        "Compatibility uses start &gt;= previous finish; strict &gt; is incorrect. "
        "Assumes one team, no travel or setup time; extra teams invalidate the model."
    ),
    (
        "<b>D. Emergency queue</b>",
        "m alarms (tick, priority 1..10, id). At each tick release at most one arrived "
        "alarm, highest priority first (tie: earlier tick/id).",
        "Binary max-heap O(m log m); priority buckets O(m+10T); "
        "sorted-array insert O(m<super>2</super>); scanned list O(m<super>2</super>).",
        "<b>Primary:</b> stable heap keyed (-priority,tick,id). "
        "<b>Baseline:</b> sorted array and bucket queue.",
        "M/L/X arrival rate 1.2..1.8 per tick exceeds one service/tick; "
        "backlog can be large (1,826 in 18-47). Ten fixed priorities may make buckets "
        "faster. Priority aging needs a different update strategy."
    ),
    (
        "<b>E. Radio logs</b>",
        "Log length N, pattern P, reports lengths a,b, alphabet size sigma=38. "
        "Return all overlapping matches, minimum edits + script, and optimal prefix-free code.",
        "KMP O(N+P) vs naive O(NP); edit DP O(ab) vs recursive exponential; "
        "Huffman O(N+sigma log sigma) vs fixed-length encoding O(N).",
        "<b>Primary:</b> KMP, edit DP with backtrace, Huffman heap. "
        "<b>Baselines:</b> naive scan, recursive edits (small), fixed-length code.",
        "Long logs (trap 49: 50k..100k) and frequent repeated prefixes punish naive search. "
        "Edit script needs O(ab) traceback storage. Huffman minimises expected bit length "
        "for observed symbol frequencies, assuming static, lossless binary coding."
    ),
    (
        "<b>F. Network planning</b>",
        "Undirected active roads carry integer cable costs. Connect all sites reachable "
        "from HQ with minimum total cable cost (MST of active component).",
        "Kruskal+DSU O(E log E); heap Prim O(E log V); "
        "naive scan Prim O(V<super>2</super>).",
        "<b>Primary:</b> Kruskal+DSU. <b>Baseline:</b> Prim heap (same optimum).",
        "Roads are sparse and cable weights positive (1..100). Exclude closed roads and "
        "isolate the HQ component before MST; do not confuse road travel minutes/penalties "
        "with cable cost. Disconnected graphs need a forest or explicit infeasibility."
    ),
    (
        "<b>G. Chains and cuts</b>",
        "n stage dimensions d0..dn: minimise matrix-chain scalar products. "
        "Drum prices p[1..L]: maximise revenue from exact cut lengths summing to L.",
        "Matrix-chain DP O(n<super>3</super>), O(n<super>2</super>) space vs brute exponential; "
        "drum DP O(L<super>2</super>) vs all cuts O(2<super>L-1</super>).",
        "<b>Primary:</b> interval DP + split reconstruction; rod-cut DP + cuts. "
        "<b>Baselines:</b> left-fold matrices and uncut drum.",
        "Dimensions 2..100 and non-proportional prices mean greedy choices are unsafe. "
        "L reaches 2,000: quadratic drum DP is feasible; cubic chain DP may be slow "
        "for 300 stages. Requires compatible adjacent matrix dimensions."
    ),
    (
        "<b>H. Hard planning</b>",
        "Find satisfying 3-SAT safety assignment; exact ration subset target; "
        "shortest closed <i>Manhattan</i> tour; vertex cover of size &lt;= k.",
        "DPLL worst O(2<super>b</super>); subset-sum DP O(nT); Held-Karp "
        "O(n<super>2</super>2<super>n</super>); k-cover branching O(2<super>k</super>(n+E)).",
        "<b>Primary:</b> DPLL, subset DP, exact S-tour/cover; heuristic tour &amp; "
        "cover on large cases. <b>Baseline:</b> brute force (S), NN/greedy (L).",
        "Planted feasibility gives checkable safety/rations/cover; it does not prove cover "
        "minimum. Exact TSP is feasible for S sites (5..9) but not 200..500 L sites. "
        "For larger instances heuristics lose optimality guarantees; report gaps explicitly."
    ),
    (
        "<b>I. Nearest sites and checksums</b>",
        "Find closest pair among n distinct (x,y) integer sites using squared Euclidean "
        "distance; multiply two decimal integers formed from 8-digit crate serials.",
        "Closest pair divide-and-conquer O(n log n) vs brute O(n<super>2</super>); "
        "Karatsuba O(d<super>log<sub>2</sub>3</super>) vs schoolbook O(d<super>2</super>).",
        "<b>Primary:</b> closest-pair D&amp;C and digit-array Karatsuba. "
        "<b>Baselines:</b> pair scan and schoolbook multiply.",
        "Sites lie in [0,999]<super>2</super>, up to 500, so brute checks correctness. "
        "Concatenated serials can yield thousands of digits, favouring Karatsuba. "
        "D&amp;C assumes planar squared Euclidean distance; small-digit inputs favour schoolbook."
    ),
]

MEMBERS = [
    ("<b>Saneed Ullah</b><br/>23i-2568<br/>AI-B",
     "<b>Iteration 1 generator:</b> locations, roads, waves, sites, planted tour; "
     "trap 48 and variety-2 construction. <b>Validator:</b> V5 radio pattern/edit checks; "
     "V8 traps 46/49. <b>Exact claim:</b> tour_opt. "
     "<b>Approach:</b> story-to-numbers network/tour discussion. "
     "<b>Iteration 2 proposals:</b> B (routes), F (minimum cable network), I (closest pair and long-product)."),
    ("<b>Hasnat Ahmed</b><br/>23i-2652<br/>AI-B",
     "<b>Iteration 1 generator:</b> crates/capacity, windows, incidents, pipeline/drum; "
     "traps 46/47 and variety-1 construction. <b>Validator:</b> V4 network; "
     "V6 planted tour; V7 signatures; V8 trap 48. <b>Exact claims:</b> "
     "cargo_opt, window_count_opt, window_value_opt, drum_opt. "
     "<b>Approach:</b> trap rationale. <b>Iteration 2 proposals:</b> A (inventory), "
     "C (rescue scheduling), G (matrix chains and drum cuts)."),
    ("<b>Hussain Muhammad Ibrahim</b><br/>23i-2626<br/>AI-B",
     "<b>Iteration 1 generator:</b> cases/writer, radio, sensor cover, 3-SAT safety, rations; "
     "trap 49, variety-3/4 construction. <b>Validator:</b> loader/framework, "
     "V1–V3, V5 claim recheck, V6 cover/assignment/rations, V8 trap 47; broken tests/report. "
     "<b>Exact claim:</b> cover_min. <b>Approach:</b> planted objects/claims and "
     "the cross-scenario hard-decision summary. <b>Iteration 2 proposals:</b> D (queue), "
     "E (radio), H (hard planning)."),
]

BLUE = colors.HexColor("#1F3A5F")
GRID = colors.HexColor("#8A94A6")
SHADE = colors.HexColor("#EEF2F7")


def table_style():
    return TableStyle([
        ("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 1), (-1, 1), BLUE),
        ("BACKGROUND", (0, 2), (0, -1), SHADE),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ])


def module_table():
    head = [P(h, HEAD) for h in ("Module", "Problem (n, m, V, E, W)",
                                 "Candidates (time complexity)", "Selection",
                                 "Justification (property, assumption, failure case)")]
    rows = [[P(GROUP, TITLE), "", "", "", ""], head] + [[P(c) for c in m] for m in MODULES]
    t = Table(rows, colWidths=[23*mm, 59*mm, 58*mm, 51*mm, 86*mm], repeatRows=0)
    t.setStyle(table_style())
    return t


def member_table():
    title = GROUP.replace("Algorithm-selection report (proposal)", "Work division") + \
        ". Every member can explain the whole submission."
    rows = [[P(title, TITLE), ""],
            [P("Member (name, roll number, section)", HEAD),
             P("Contribution in Iteration 1 and decision modules proposed for Iteration 2", HEAD)]]
    rows += [[P(a, BIG), P(b, BIG)] for a, b in MEMBERS]
    t = Table(rows, colWidths=[52*mm, 225*mm])
    t.setStyle(table_style())
    return t


def main(out="proposal.pdf"):
    doc = SimpleDocTemplate(str(Path(out)), pagesize=landscape(A4),
                            leftMargin=10*mm, rightMargin=10*mm,
                            topMargin=7.5*mm, bottomMargin=7.5*mm,
                            title="LIFELINE proposal: all modules A-I, group 18",
                            author="Saneed Ullah, Hasnat Ahmed, Hussain Muhammad Ibrahim")
    doc.build([module_table(), PageBreak(), member_table()])
    print(f"wrote {out}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
