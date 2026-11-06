"""Builds proposal.pdf: the two-page algorithm-selection report of Iteration 1 (Section 6).
Page 1: one table, one row per chosen module. Page 2: one table, one row per member.

    python docs/make_proposal.py proposal.pdf
"""
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak

pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")

CELL = ParagraphStyle("cell", fontName="Arial", fontSize=8.3, leading=10.1)
HEAD = ParagraphStyle("head", parent=CELL, fontName="Arial-Bold", fontSize=8, textColor=colors.white)
TITLE = ParagraphStyle("title", parent=CELL, fontName="Arial-Bold", fontSize=9.5, leading=12,
                       alignment=TA_CENTER)
BIG = ParagraphStyle("big", parent=CELL, fontSize=10, leading=13)

GROUP = ("LIFELINE: Algorithm-selection report (proposal), Iteration 1. Group 18: "
         "Saneed Ullah (23i-2568), Hasnat Ahmed (23i-2652), Hussain Muhammad Ibrahim (23i-2626), AI-B")


def P(text, style=CELL):
    return Paragraph(text, style)


MODULES = [
    ("<b>A. Relief inventory</b>",
     "<b>In:</b> n crates (weight w<sub>i</sub> 1..20 kg, value v<sub>i</sub> = floor(base &times; day "
     "multiplier)), capacity W. <b>Out:</b> a set S of whole crates with &Sigma;w<sub>i</sub> &le; W. "
     "<b>Objective:</b> maximise &Sigma;v<sub>i</sub>. This is the 0/1 knapsack problem (NP-hard in general, "
     "pseudo-polynomial in W).",
     "1. Exhaustive search over all subsets: O(2<super>n</super> &middot; n).<br/>"
     "2. DP over capacity: O(n &middot; W) time, O(n &middot; W) bits to rebuild the load.<br/>"
     "3. Greedy by value/weight, exact fractions: O(n log n), no guarantee.<br/>"
     "4. Branch &amp; bound with a fractional bound: O(2<super>n</super>) worst case.",
     "<b>Primary:</b> DP over capacity with a keep-table to rebuild the chosen crates.<br/>"
     "<b>Baseline:</b> greedy by value/weight (ties by crate_id). Exhaustive search is the exactness "
     "reference on tier S against cargo_opt.",
     "<b>Data property:</b> weights are small integers and W &le; 70% of the total weight. In our cases "
     "W &le; 3,388 and n&middot;W &le; 4.2&times;10<super>6</super> cells (case 18-45), so the DP is cheap. Day "
     "multipliers change values, not weights, so the table size stays the same every day. "
     "<b>Assumption:</b> integer weights. <b>Fails when:</b> W is very large (master data with n = 3,000 and "
     "W of about 40,000 gives 1.2&times;10<super>8</super> cells), so the memory needed to rebuild the load "
     "becomes the bottleneck; branch &amp; bound is the fallback. Greedy fails on trap 47 (55% of optimum)."),
    ("<b>B. Route planning</b>",
     "<b>In:</b> map G = (V, E), source HQ = 0, today's closed roads (waves). Directed step cost "
     "c(u&rarr;v) = minutes(u,v) + penalty(v). <b>Out:</b> a cheapest route to the target and its cost, or "
     "&ldquo;no route&rdquo;; the set of reachable locations; the fewest-roads route (BFS, neighbours in "
     "ascending id). <b>Objective:</b> minimise the route cost.",
     "1. BFS: O(V + E) (reachability, fewest roads).<br/>"
     "2. Dijkstra with a binary heap: O((V + E) log V).<br/>"
     "3. Dijkstra with an array: O(V<super>2</super>).<br/>"
     "4. Bellman-Ford: O(V &middot; E).",
     "<b>Primary:</b> Dijkstra with a binary heap (lazy deletion) for cost; BFS for reachable locations and "
     "the fewest-roads route.<br/><b>Baseline:</b> Bellman-Ford (exact, slower), plus the BFS route used "
     "as if it were the cheapest (the naive choice).",
     "<b>Data property:</b> every step costs at least 1 (minutes &ge; 1, penalty &ge; 0, and both the storm "
     "&times;1.5 rounded up and the doubled penalties keep it positive), so Dijkstra is correct. Maps are "
     "sparse (E &le; 3V; ours have V &le; 2,140 and E &le; 2,867), so the heap beats the O(V<super>2</super>) "
     "array. <b>Assumption:</b> no negative costs, and the penalty belongs to the destination (costs are "
     "directed). <b>Fails when:</b> a negative cost appears (then Bellman-Ford is needed). The BFS route "
     "fails on trap 48 (&ge; 1.5&times; the cheapest cost)."),
    ("<b>C. Rescue scheduling</b>",
     "<b>In:</b> n windows [s<sub>i</sub>, f<sub>i</sub>) in minutes 0..1440, value v<sub>i</sub>. "
     "Windows i and j are compatible if f<sub>i</sub> &le; s<sub>j</sub> or f<sub>j</sub> &le; s<sub>i</sub> "
     "(touching is allowed). <b>Out:</b> a set of pairwise compatible windows. <b>Objective:</b> (a) the most "
     "windows; (b) the most total value.",
     "1. Exhaustive search: O(2<super>n</super> &middot; n).<br/>"
     "2. Earliest-finish greedy: O(n log n).<br/>"
     "3. Greedy by highest value: O(n log n), no guarantee.<br/>"
     "4. Weighted interval DP + binary search: O(n log n); with a linear scan: O(n<super>2</super>).",
     "<b>Primary:</b> (a) earliest-finish greedy (provably optimal for the count); (b) weighted interval DP "
     "with binary search on finish times.<br/><b>Baseline:</b> greedy by highest value, and the "
     "O(n<super>2</super>) DP.",
     "<b>Data property:</b> windows lie in one day with integer ends; n &le; 3,000 (ours &le; 2,875). Study 3 "
     "is dense (&ge; 2 overlaps per window), which is where greedy-by-value does badly. "
     "<b>Assumption:</b> one rescue team (one window at a time), and touching windows are compatible, so "
     "the test is s<sub>j</sub> &ge; f<sub>i</sub> (not &gt;). Ties go by finish, then window_id. "
     "<b>Fails when:</b> several teams can work at once (this becomes k-machine scheduling), or windows "
     "need set-up or travel time between them."),
    ("<b>D. Emergency queue</b>",
     "<b>In:</b> m alarms (tick t<sub>i</sub>, priority p<sub>i</sub> 1..10, alarm_id). "
     "<b>Out:</b> the release order. At each tick, every alarm that has arrived joins the queue and exactly "
     "one is released. <b>Objective:</b> always release the most urgent alarm present (priority descending, "
     "then tick ascending, then alarm_id ascending).",
     "1. Binary max-heap: O(m log m).<br/>"
     "2. Sorted array with insertion: O(m<super>2</super>) shifts.<br/>"
     "3. Unsorted list, scanned for the max: O(m<super>2</super>).<br/>"
     "4. Bucket queue (one queue per priority): O(m + 10&middot;T).",
     "<b>Primary:</b> binary heap keyed on (&minus;p, t, id).<br/><b>Baseline:</b> sorted array with "
     "insertion (also measured: the unsorted scan and the bucket queue).",
     "<b>Data property:</b> alarms arrive at 1.2 to 1.8 per tick (ours 1.27 to 1.75) but only 1 is released "
     "per tick, so the queue grows linearly: in our data up to 1,826 alarms wait at once (case 18-47, "
     "m = 4,513). The list versions turn quadratic while the heap stays O(log m) per operation. <b>Assumption:</b> a priority "
     "never changes while an alarm waits. <b>Fails when:</b> priorities age, which needs decrease-key "
     "(an indexed heap). With only 10 priorities and arrivals already in (tick, id) order, the bucket "
     "queue may beat the heap; we will measure it."),
]

MEMBERS = [
    ("<b>Saneed Ullah</b><br/>23i-2568<br/>AI-B",
     "<b>Data modules (generator):</b> locations, roads and closure waves (spanning tree plus extra roads to "
     "each study's average degree, corridor bridges for study 5), sites and the planted tour (nearest "
     "neighbour + 2-opt). Trap 48 (shortest-looks-cheapest) and variety rule 2.<br/>"
     "<b>Validator checks:</b> V5 radio pattern counts (KMP) and edit_bound (DP); V8 traps 46 and 49.<br/>"
     "<b>Claims:</b> tour_opt (exhaustive search over tours).<br/>"
     "<b>Approach note:</b> part 1 (story to numbers) for the network and tour data.<br/>"
     "<b>Proposes for Iteration 2:</b> module B (route planning)."),
    ("<b>Hasnat Ahmed</b><br/>23i-2652<br/>AI-B",
     "<b>Data modules (generator):</b> crates and capacity (category quotas per study), rescue windows "
     "(planted touching pairs, clustered windows for study 3), incidents (arrival rate, aftershock bursts), "
     "pipeline_dims and drum_prices. Traps 46 (dock-order) and 47 (best-looking-crate), and variety rule 1.<br/>"
     "<b>Validator checks:</b> V4 connectivity and waves; V6 planted tour; V7 signature rules; V8 trap 48.<br/>"
     "<b>Claims:</b> cargo_opt, window_count_opt, window_value_opt, drum_opt.<br/>"
     "<b>Approach note:</b> part 3 (the traps).<br/>"
     "<b>Proposes for Iteration 2:</b> modules A (relief inventory) and C (rescue scheduling)."),
    ("<b>Hussain Muhammad Ibrahim</b><br/>23i-2626<br/>AI-B",
     "<b>Data modules (generator):</b> cases sheet and workbook writer, radio_log, radio_patterns and "
     "radio_reports, sensor graph with planted cover, safety rules with planted assignment, rations with "
     "planted selection. Trap 49 (near-miss), and variety rules 3 and 4.<br/>"
     "<b>Validator checks:</b> loader and framework; V1 structure, V2 ranges, V3 identifiers; V6 cover, "
     "assignment and rations; V5 claims re-check; V8 trap 47. The broken test copies and "
     "validation_report.txt.<br/>"
     "<b>Claims:</b> cover_min.<br/>"
     "<b>Approach note:</b> part 2 (planted objects and claims).<br/>"
     "<b>Proposes for Iteration 2:</b> module D (emergency queue)."),
]

BLUE = colors.HexColor("#1F3A5F")
GRID = colors.HexColor("#8A94A6")
SHADE = colors.HexColor("#EEF2F7")


def module_table():
    head = [P(h, HEAD) for h in ("Module", "Problem (n, m, V, E, W)", "Candidates (time complexity)",
                                  "Selection", "Justification (data property, assumption, failure case)")]
    rows = [[P(GROUP, TITLE), "", "", "", ""], head] + [[P(c) for c in m] for m in MODULES]
    widths = [22 * mm, 60 * mm, 55 * mm, 52 * mm, 88 * mm]
    t = Table(rows, colWidths=widths, repeatRows=0)
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 1), (-1, 1), BLUE),
        ("BACKGROUND", (0, 2), (0, -1), SHADE),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return t


def member_table():
    title = (GROUP.replace("Algorithm-selection report (proposal)", "Work division") +
             ". Every member can explain the whole submission.")
    head = [P("Member (name, roll number, section)", HEAD),
            P("Contribution in Iteration 1 and decision modules proposed for Iteration 2", HEAD)]
    rows = [[P(title, TITLE), ""], head] + [[P(a, BIG), P(b, BIG)] for a, b in MEMBERS]
    t = Table(rows, colWidths=[52 * mm, 225 * mm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 1), (-1, 1), BLUE),
        ("BACKGROUND", (0, 2), (0, -1), SHADE),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def main(out="proposal.pdf"):
    doc = SimpleDocTemplate(out, pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm,
                            topMargin=9 * mm, bottomMargin=9 * mm, title="LIFELINE proposal, group 18",
                            author="Saneed Ullah, Hasnat Ahmed, Hussain Muhammad Ibrahim")
    doc.build([module_table(), PageBreak(), member_table()])
    print(f"wrote {out}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
