"""
Builds the pitch deck from model.py and the charts.

    python charts.py && python build_deck.py
    soffice --headless --convert-to pdf Instamart_Densification_Plan.pptx
"""
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

import model

HERE = Path(__file__).resolve().parent
CH = HERE / "charts"
OUT = HERE / "Instamart_Densification_Plan.pptx"

AUTHOR = "Arnav Deshpande"
EMAIL = "arnavhpd@gmail.com"

DARK, ORANGE, INK, INK2, MUTED = "1F2430", "EB6834", "1D1D1B", "55544F", "8C8B85"
TINT, GREY, LINE, WHITE = "FDF0EA", "F3F3F1", "DDDCD7", "FFFFFF"
BLUE, RED, GREEN = "2A78D6", "C9442F", "2F8F5B"
FONT = "Calibri"

df, I, B, G = model.baseline()
P = model.plan(I)
S = P["store"]
GAP = model.per_order_gap(I, B)
TG = model.throughput_gap(I, B)
HALF = model.plan(I, plays=model.scaled_plays(0.5))
EBITDA_BE = (S["semi_fixed"] + S["fixed"]) / model.with_levers(S, 24.5) / 1e5

prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)   # exact 16:9
BLANK = prs.slide_layouts[6]
W = 13.333


def rgb(h):
    return RGBColor.from_string(h)


def box(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    st = s._element.find(qn("p:style"))
    if st is not None:                      # drop the theme style: no inherited shadow or outline
        s._element.remove(st)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.text_frame.text = ""
    return s


def text(slide, x, y, w, h, runs, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, bullets=False, space_after=6, line_spacing=1.05, margin=0.0, shape=None):
    """runs: str, or list of paragraphs; a paragraph is a str or a list of (text, {opts}) tuples."""
    tb = shape or slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(margin))
    paras = runs if isinstance(runs, list) else [runs]
    for k, para in enumerate(paras):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        if bullets:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Emu(Inches(0.22))))
            pPr.set("indent", str(-Emu(Inches(0.22))))
            bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
            pPr.append(bu)
        pieces = para if isinstance(para, list) else [(para, {})]
        for t, o in pieces:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def new_slide(dark=False):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(DARK if dark else WHITE)
    return s


PAGE = {"n": 0}


def frame(slide, kicker, title, source=None):
    PAGE["n"] += 1
    text(slide, 0.6, 0.38, 11, 0.3, kicker.upper(), size=11, color=ORANGE, bold=True)
    text(slide, 0.6, 0.66, 12.1, 1.0, title, size=25, bold=True, color=INK, line_spacing=0.95)
    if source:
        text(slide, 0.6, 6.66, 12.1, 0.38, source, size=9.5, color=MUTED, line_spacing=1.0, space_after=0)
    text(slide, 0.6, 7.06, 8, 0.25, f"{AUTHOR}  ·  Instamart densification plan", size=9, color=MUTED)
    text(slide, W - 1.4, 7.06, 0.8, 0.25, str(PAGE["n"] + 1), size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def pic(slide, name, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(CH / f"{name}.png"), Inches(x), Inches(y), **kw)


def dot(slide, x, y, label, d=0.42, fill=ORANGE, size=14):
    c = box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
    text(slide, 0, 0, 0, 0, label, size=size, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, shape=c, space_after=0)
    return c


def stat(slide, x, y, w, big, small, color=ORANGE, big_size=34):
    text(slide, x, y, w, 0.7, big, size=big_size, bold=True, color=color, space_after=0)
    text(slide, x, y + big_size / 72 + 0.08, w, 0.8, small, size=12.5, color=INK2, line_spacing=1.0)


def table(slide, x, y, w, rows, col_w, header_fill=DARK, size=12, row_h=0.42, first_bold=True, zebra=True):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # "No Style, Table Grid": no Office banding
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = rgb(header_fill)
            else:
                cell.fill.fore_color.rgb = rgb(GREY if (zebra and i % 2 == 0) else WHITE)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.color.rgb = rgb(WHITE if i == 0 else INK)
            r.font.bold = i == 0 or (first_bold and j == 0)
    return tbl


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


L = lambda v: f"₹{v / 1e5:.2f}L"  # noqa: E731


def pct(v):
    return f"{v:+.1f}%".replace("-", "−")

# ---------------------------------------------------------------- 1. title
s = new_slide(dark=True)
text(s, 0.8, 0.9, 6, 0.35, "STRATEGY CASE  ·  INDIA QUICK COMMERCE", size=12, color=ORANGE, bold=True)
text(s, 0.8, 1.5, 11.5, 2.2, "Fill the stores before you build more", size=50, bold=True, color=WHITE, line_spacing=0.92)
text(s, 0.8, 3.0, 10.5, 1.2,
     "A plan to add ₹1 lakh of daily sales to every Swiggy Instamart dark store, "
     "and why that is the cheapest way across break-even", size=21, color="D9D8D3", line_spacing=1.05)
text(s, 0.8, 5.35, 8, 0.4, AUTHOR, size=20, bold=True, color=WHITE, space_after=2)
text(s, 0.8, 5.8, 8, 0.35, EMAIL, size=14, color="D9D8D3")
text(s, 0.8, 6.55, 11.5, 0.5,
     "Independent analysis of public filings (Swiggy and Eternal shareholder letters, Zepto UDRHP). "
     "Baseline: Q1FY27, quarter to 30 June 2026. Not affiliated with any company.", size=11, color="A9A8A2")
for k, (v, lab) in enumerate([(L(S["nov"]), "NOV per store per day today"), (L(P["new_nov"]), "after the plan")]):
    text(s, 9.2 + k * 2.0, 5.3, 1.9, 0.6, v, size=26, bold=True, color=ORANGE if k else WHITE, space_after=0)
    text(s, 9.2 + k * 2.0, 5.85, 1.9, 0.6, lab, size=11, color="A9A8A2")
notes(s, "One-line pitch: Instamart doesn't need more stores yet, it needs fuller ones. "
         "This deck goes problem, root cause, plan, numbers, how I'd test it.")

# ---------------------------------------------------------------- 2. answer first
s = new_slide()
frame(s, "The answer, on one page",
      "₹1 lakh more per store per day takes Instamart across contribution break-even for good, without a single new store",
      "Q1FY27 filings; my model (model.py). Contribution-positive store share uses an assumed spread of store throughput, see appendix.")
rows = [
    ("Problem", "Instamart sells the same basket as Blinkit (₹508 vs ₹518 net) but each store sells ₹5.5L a day against ₹8.0L. "
                f"{GAP['_volume_share']:.0%} of the ₹71 per-order EBITDA gap to Blinkit is volume, not price."),
    ("Root cause", "Capacity was built ahead of habit. Users order 2.83 times a month vs 3.47 at Blinkit, which is "
                   f"{TG['freq_share']:.0%} of the throughput gap. Stores run at about 40% of capacity."),
    ("Plan", "Four habit plays on the existing 1,171 stores: Morning Ritual + fresh, a Swiggy-to-Mart bridge, "
             "winning back lapsed users, and a bigger basket. Together +₹1.04L per store per day."),
    ("Payoff", f"Contribution {pct(P['cm_pct_before'])} → {pct(P['cm_pct_after'])} of NOV. "
               f"About ₹{round(P['annual_nov_cr'], -2):,.0f} Cr more NOV a year, ~₹{round(P['annual_net_cr'], -1):,.0f} Cr net of programme cost, "
               f"and {P['stores_avoided']:,.0f} fewer stores needed to reach Swiggy's ₹60,000 Cr break-even scale."),
    ("Not solved", f"Company-level EBITDA break-even still needs ~₹{EBITDA_BE:.1f}L per store per day plus Swiggy's "
                   "own per-order levers (ads, mix, inventory model). This is the first, cheapest step."),
]
for k, (h, body) in enumerate(rows):
    y = 1.85 + k * 0.95
    text(s, 0.6, y, 1.6, 0.8, h, size=14, bold=True, color=ORANGE if k < 4 else INK2)
    text(s, 2.2, y, 6.2, 0.9, body, size=13, color=INK, line_spacing=1.0)
box(s, 8.85, 1.85, 3.9, 4.75, fill=TINT)
for k, (big, small) in enumerate([
        (f"+₹{P['add_nov']/1e5:.2f}L", "NOV per store per day,\nno new stores"),
        (f"{pct(P['cm_pct_before'])} → {pct(P['cm_pct_after'])}", "contribution margin, % of NOV"),
        (f"{P['share_cm_positive_before']:.0%} → {P['share_cm_positive_after']:.0%}", "stores contribution-positive"),
        (f"{P['stores_avoided']:,.0f}", f"fewer stores to reach ₹60k Cr\n(~₹{P['capex_avoided_cr']:,.0f} Cr capex)")]):
    stat(s, 9.15, 2.0 + k * 1.13, 3.4, big, small, big_size=28)
notes(s, "If I only get one minute, this is the slide. Lead with the problem in rupees per order, then the root cause, "
         "then the ask: fund a 60-store pilot.")

# ---------------------------------------------------------------- 3. situation
s = new_slide()
frame(s, "Situation",
      "Same basket, emptier stores: an Instamart store sells 31% less a day than a Blinkit one",
      "Swiggy and Eternal shareholder letters Q1FY25–Q1FY27. NOV per store-day computed as NOV ÷ average stores ÷ 91; "
      "tracks Blinkit's own published figure within ±4%.")
pic(s, "01_throughput", 0.55, 1.75, w=7.7)
facts = [
    ("₹508 vs ₹518", "net basket (AOV), Instamart vs Blinkit. Basically equal."),
    ("1,089 vs 1,552", "orders per store per day"),
    ("₹72k vs ₹38k", "HQ, tech and brand cost carried per store-day"),
    ("~40%", "Instamart store utilisation (Swiggy, Q1FY27)"),
    ("63% → 75%", "Blinkit's share of the two players' combined NOV, Q1FY25 → Q1FY27"),
]
for k, (big, small) in enumerate(facts):
    y = 1.85 + k * 0.95
    text(s, 8.7, y, 4.1, 0.45, big, size=22, bold=True, color=ORANGE if k != 4 else BLUE, space_after=0)
    text(s, 8.7, y + 0.43, 4.1, 0.5, small, size=12, color=INK2)
notes(s, "The point of this slide: it is not a pricing or basket problem. The basket is the same. The stores are emptier.")

# ---------------------------------------------------------------- 4. RCA 1: per-order gap
s = new_slide()
frame(s, "Root cause  ·  step 1 of 3: where the loss sits",
      f"Three-quarters of Instamart's ₹71 per-order gap to Blinkit comes from spreading costs over too few orders",
      "Q1FY27. HQ cost = contribution minus Adj. EBITDA. Store rent and staff assumed at ₹38k per store-day for both "
      "players (see appendix). The residual is everything else inside contribution.")
pic(s, "02_per_order_gap", 0.55, 1.75, w=7.7)
text(s, 8.7, 1.9, 4.1, 0.4, "How to read it", size=15, bold=True, color=INK)
text(s, 8.7, 2.35, 4.1, 4.2, [
    f"Blinkit makes +₹{GAP['Blinkit']:.0f} per order, Instamart loses ₹{-GAP['Instamart']:.0f}.",
    f"₹{-GAP['HQ costs over fewer orders']:.0f} of the gap: HQ, tech and brand costs are similar in rupees "
    "(₹762 Cr vs ₹805 Cr a quarter) but Instamart spreads them over a third of the orders.",
    f"₹{-GAP['Store costs over fewer orders']:.0f}: the same rent and staff, fewer orders through the door.",
    f"₹{-GAP['Variable margin (ads, 1P, pricing)']:.0f}: genuinely per-order. Ads, Blinkit's inventory-led margin, "
    "discounts. Swiggy's own plan already targets this.",
    "So the first question is not \"how do we earn more per order\" but \"why are there so few orders per store\".",
], size=13, bullets=True, space_after=8)
notes(s, "Waterfall from Blinkit to Instamart. Red bars are volume problems, grey is a margin problem. "
         "I split store cost using the same per-store-day cost for both, which is conservative for Blinkit.")

# ---------------------------------------------------------------- 5. RCA 2: issue tree
s = new_slide()
frame(s, "Root cause  ·  step 2 of 3: the issue tree",
      "Following the tree down, every branch that explains the gap ends at one thing: too few orders per user",
      "Q1FY27. Users per store = MTU ÷ stores. Orders/store/day = users per store × orders per user per month × 12 ÷ 365.")
# root
def node(x, y, w, h, title, sub, state):
    fill, col, tcol = {"hot": (ORANGE, WHITE, WHITE), "warm": (TINT, INK, INK2), "cold": (GREY, MUTED, MUTED)}[state]
    b = box(s, x, y, w, h, fill=fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    text(s, 0, 0, 0, 0, [[(title, {"bold": True, "size": 13.5, "color": col})], [(sub, {"size": 11, "color": tcol})]],
         shape=b, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=1, margin=0.06)
    return (x, y, w, h)


def link(a, b2):
    x1, y1 = a[0] + a[2] / 2, a[1] + a[3]
    x2, y2 = b2[0] + b2[2] / 2, b2[1]
    ym = (y1 + y2) / 2
    for (xa, ya, xb, yb) in [(x1, y1, x1, ym), (min(x1, x2), ym, max(x1, x2), ym), (x2, ym, x2, y2)]:
        if abs(xb - xa) < 1e-6 and abs(yb - ya) < 1e-6:
            continue
        ln = s.shapes.add_connector(1, Inches(xa), Inches(ya), Inches(xb), Inches(yb))
        ln.line.color.rgb = rgb(MUTED)
        ln.line.width = Pt(1.25)


root = node(4.67, 1.75, 4.0, 0.72, "Adj. EBITDA per store-day: −₹74k", "vs Blinkit +₹3k", "hot")
n_nov = node(0.6, 2.95, 3.9, 0.72, "NOV per store-day: ₹5.52L", "Blinkit ₹8.04L  (−31%)", "hot")
n_cm = node(4.72, 2.95, 3.9, 0.72, "Contribution: −0.3% of NOV", "Blinkit +5.3%", "warm")
n_fx = node(8.84, 2.95, 3.9, 0.72, "HQ cost per store-day: ₹72k", "same ₹ as Blinkit, half the sales", "warm")
n_us = node(0.6, 4.2, 1.22, 0.8, "Users / store", "11.5k vs 13.0k", "warm")
n_fr = node(1.94, 4.2, 1.22, 0.8, "Orders / user", "2.83 vs 3.47 /mo", "hot")
n_bk = node(3.28, 4.2, 1.22, 0.8, "Basket", "₹508 vs ₹518", "cold")
n_sf = node(4.72, 4.2, 1.85, 0.8, "Store costs / order", "₹35 vs ₹24", "warm")
n_vm = node(6.77, 4.2, 1.85, 0.8, "Ads, 1P, pricing", "~₹18/order gap", "cold")
n_sc = node(8.84, 4.2, 3.9, 0.8, "Fixed by scale, i.e. more orders", "on the same network", "warm")
for a, b2 in [(root, n_nov), (root, n_cm), (root, n_fx), (n_nov, n_us), (n_nov, n_fr), (n_nov, n_bk),
              (n_cm, n_sf), (n_cm, n_vm), (n_fx, n_sc)]:
    link(a, b2)
box(s, 0.6, 5.4, 12.15, 0.8, fill=GREY)
text(s, 0.8, 5.5, 11.8, 0.65, [
    [("Read across the tree. ", {"bold": True}),
     ("Orange = explains the gap, tint = a consequence of it, grey = ruled out or already being worked on. "
      "Store-cost and HQ-cost problems shrink by themselves once orders per store rise, "
      "so the branch to attack is orders per user.", {})]], size=12.5, color=INK, line_spacing=1.0)
notes(s, "MECE split: EBITDA = NOV × contribution% − HQ cost. Basket is ruled out. "
         "Two of the three branches are really the same volume problem seen from the cost side.")

# ---------------------------------------------------------------- 6. RCA 3: frequency + 5 whys
s = new_slide()
frame(s, "Root cause  ·  step 3 of 3: five whys",
      "The root cause: Instamart built stores faster than it built the habit of ordering from them",
      "Swiggy shareholder letters (Q4FY25 store additions, Q1FY26 on weaning off ~4M low-value users, Q1FY27 utilisation "
      "and M1 retention). The Q1FY26 user cut-off is the company's own explanation for the frequency drop.")
pic(s, "03_throughput_split", 0.55, 1.75, w=6.3)
whys = [
    ("Why do stores lose money?", "They sell ₹5.5L a day; costs are set for ₹8L+."),
    ("Why so little per store?", "1,089 orders a day against 1,552 at Blinkit, on the same basket."),
    ("Why so few orders?", "Each user orders 2.83×/month vs 3.47×. Frequency is "
                           f"{TG['freq_share']:.0%} of the gap, users per store {TG['users_share']:.0%}."),
    ("Why so infrequent?", "It's a top-up and stock-up app, not a daily one: milk, eggs and vegetables still come "
                           "from the kirana and the doodhwala. 39% of new users don't return in month one."),
    ("Why?", "316 stores opened in one quarter (Q4FY25) into catchments with no habit yet, then ~4M "
             "low-value users were cut. Capacity ran ahead of demand: ~40% utilisation."),
]
for k, (q, a) in enumerate(whys):
    y = 1.75 + k * 0.98
    dot(s, 7.15, y + 0.02, str(k + 1), d=0.4, fill=ORANGE if k == 4 else DARK, size=13)
    text(s, 7.72, y - 0.02, 5.1, 0.3, q, size=13, bold=True, color=INK, space_after=0)
    text(s, 7.72, y + 0.28, 5.1, 0.7, a, size=11.5, color=INK2, line_spacing=1.0)
box(s, 0.6, 5.55, 6.2, 1.05, fill=TINT)
text(s, 0.8, 5.63, 5.9, 0.95, [[("So the fix is a habit fix. ", {"bold": True, "color": ORANGE}),
                               ("Get the users already inside each store's radius to order one more time a month, "
                                "and pull in the Swiggy users who live there but don't use Instamart.", {})]],
     size=13, color=INK, line_spacing=1.0)
notes(s, "Log split of orders per store per day into users per store and orders per user. "
         "The fifth why is where strategy comes in: it's a sequencing mistake, not a bad store.")

# ---------------------------------------------------------------- 7. three floors
s = new_slide()
frame(s, "What 'break-even' means here",
      "Break-even has three floors. ₹1 lakh more per store clears the first two; the third needs Swiggy's per-order levers too",
      f"My model. Store variable margin {S['var_margin']:.1%} of NOV; store rent and staff ₹38k/day; HQ cost ₹72.4k/store-day "
      "held flat (no new stores). Per-order levers from Swiggy's Q1FY27 bridge: ads ₹10, mix ₹10, inventory model ₹4.5.")
pic(s, "04_breakeven_floors", 0.55, 1.75, w=8.0)
floors = [
    ("1", "Network contribution ≥ 0", f"Average store clears ₹{S['breakeven_nov_contribution']/1e5:.2f}L. Swiggy touched this in May-26 "
                                      f"for one month. The plan holds it at {pct(P['cm_pct_after'])}.", ORANGE, "Cleared"),
    ("2", "Most stores in the black", f"Contribution-positive stores go from {P['share_cm_positive_before']:.0%} to "
                                           f"{P['share_cm_positive_after']:.0%}.", ORANGE, "Cleared"),
    ("3", "Company Adj. EBITDA ≥ 0", f"Needs ~₹{EBITDA_BE:.1f}L per store per day once ads, mix and the inventory model land. "
                                    "Blinkit's own steady-state target is ₹11L.", DARK, "Next"),
]
for k, (n, h, body, col, tag) in enumerate(floors):
    y = 1.85 + k * 1.55
    dot(s, 8.95, y, n, d=0.44, fill=col)
    text(s, 9.55, y - 0.02, 2.4, 0.35, h, size=13.5, bold=True, color=INK, space_after=0)
    t = box(s, 11.95, y + 0.02, 0.8, 0.3, fill=TINT if col == ORANGE else GREY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    text(s, 0, 0, 0, 0, tag, size=10, bold=True, color=col if col == ORANGE else INK2, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, shape=t, space_after=0)
    text(s, 9.55, y + 0.38, 3.2, 1.1, body, size=11.5, color=INK2, line_spacing=1.0)
notes(s, "Be upfront in an interview: ₹1 lakh alone does not make Swiggy profitable. "
         "It crosses the contribution line durably and it's the first quarter of the climb to EBITDA break-even.")

# ---------------------------------------------------------------- 8. store view
s = new_slide()
frame(s, "What it does to the network",
      "Moving every store ₹1 lakh to the right turns two out of three stores contribution-positive, up from fewer than half",
      "Swiggy reported >45% of stores CM-positive in Q1FY27. The spread (normal, σ = ₹1.8L) is my assumption, chosen so the "
      "break-even line from the cost split reproduces that 45%. Store-level data would replace it.")
pic(s, "05_store_distribution", 0.55, 1.75, w=8.2)
text(s, 9.15, 1.9, 3.6, 4.6, [
    [("Why this matters more than the average. ", {"bold": True})],
    "A store that covers its own rent and staff can be left alone. A store that doesn't has to be fixed, moved or shut, "
    "and every one of those costs management time.",
    [("Not every store moves equally. ", {"bold": True})],
    "The plays work best where there are many households in the radius and the store is under-used. "
    "The pilot picks those first (slide 15).",
    [("Stores still below the line ", {"bold": True}),
     ("after a year are candidates for consolidation, not more spend.", {})],
], size=12.5, color=INK, space_after=9, line_spacing=1.02)
notes(s, "45% to about two-thirds. If asked about the distribution: it's an assumption, calibrated to the one store-level "
         "number Swiggy discloses. I'd replace it with the store P&L table on day one.")

# ---------------------------------------------------------------- 9. CIRCLES
s = new_slide()
frame(s, "Designing the fix  ·  CIRCLES",
      "Working through CIRCLES from one store's catchment, the answer is a daily habit rather than a discount",
      "CIRCLES: Comprehend, Identify customers, Report needs, Cut through prioritisation, List solutions, Evaluate trade-offs, "
      "Summarise. Average store catchment = 13.5M MTU ÷ 1,171 stores ≈ 11.5k monthly users.")
circ = [
    ("C", "Comprehend", "Add ₹1L NOV per store per day on the 1,171 stores open today, inside four quarters. No new stores in "
                        "the same micro-markets. Every added order must earn positive contribution. Speed is off the table: "
                        "platforms were asked to drop the 10-minute promise in Jan-26."),
    ("I", "Identify customers", "Five people in one catchment: the daily-essentials household, the monthly stock-up planner, "
                                "the late-night impulse buyer, the Swiggy food user who has never opened Instamart, and "
                                "the one-time user who never came back."),
    ("R", "Report needs", "Milk before 7 am and vegetables they trust. Prices close to DMart for the big basket. No reason "
                          "to open a second app. A first order that didn't disappoint (stock-outs, bruised fruit)."),
    ("C", "Cut", "Rank by orders added per store-day × how habit-forming the behaviour is ÷ cost to margin. "
                 "Frequency first: it is 63% of the gap."),
    ("L", "List", "Nine candidates, from a morning subscription slot to blanket free delivery (next slide)."),
    ("E", "Evaluate", "Contribution per added order, cannibalisation of existing orders, peak-hour SLA risk, how easily "
                      "Blinkit or Zepto can copy it."),
    ("S", "Summarise", "Four plays, +₹1.04L per store per day, contribution to +0.8% of NOV."),
]
for k, (ltr, h, body) in enumerate(circ):
    y = 1.78 + k * 0.7
    dot(s, 0.6, y + 0.02, ltr, d=0.44, fill=ORANGE if k in (1, 2, 3) else DARK, size=15)
    text(s, 1.2, y + 0.06, 2.2, 0.4, h, size=13.5, bold=True, color=INK, space_after=0)
    text(s, 3.4, y + 0.02, 9.35, 0.7, body, size=12, color=INK2, line_spacing=1.0)
notes(s, "I used CIRCLES because the root cause is behavioural, so the fix has to start from the customer, "
         "not the P&L. The P&L tells you where to look; CIRCLES tells you what to build.")

# ---------------------------------------------------------------- 10. prioritisation
s = new_slide()
frame(s, "Cut through: what goes in, what stays out",
      "Four plays make the cut. Blanket discounts would add more orders, but they rent demand instead of building it",
      "Impact = NOV per store per day from the sizing on slide 12; ease = my judgement of build time and operational risk. "
      "Blanket free delivery sized at Q2FY27-style pricing investments (~100 bps of CM).")
pic(s, "07_prioritisation", 0.55, 1.72, w=8.1)
text(s, 9.05, 1.9, 3.7, 4.7, [
    [("Parked, not killed", {"bold": True, "color": INK})],
    [("Radius retune. ", {"bold": True}), ("With the 10-minute promise gone, an under-used store could serve a wider "
                                            "radius in 15–20 minutes. Big lever, but it needs rider and SLA work. Phase 2.", {})],
    [("Afternoon fee holiday. ", {"bold": True}), ("Small on its own; folded into the morning-slot test as a variant.", {})],
    [("Rejected", {"bold": True, "color": INK})],
    [("Blanket free delivery: ", {"bold": True}), ("margin-negative, and Blinkit can match it the next day.", {})],
    [("Faster promise: ", {"bold": True}), ("regulatory headwind and no frequency evidence.", {})],
    [("New stores in served micro-markets: ", {"bold": True}), ("splits existing demand and lowers throughput.", {})],
], size=12, color=INK2, space_after=7, line_spacing=1.0)
notes(s, "The interesting rejection is blanket free delivery: it's the easiest and adds orders, "
         "but it doesn't change who the customer is, and it's the first thing a competitor copies.")

# ---------------------------------------------------------------- 11. four plays
s = new_slide()
frame(s, "List solutions: the four plays",
      "Each play attacks a different reason a household inside the radius isn't ordering more",
      "Swiggy platform MTU 26.2M vs Instamart MTU 13.5M (Q1FY27). M1 retention 61% (Q1FY27). Nectr and No!ce from Swiggy's "
      "Q2FY27 letter. Per-store figures are averages; sizing on the next slide.")
plays = [
    ("Morning Ritual + fresh", f"+₹{P['stack'][0][1]/1e3:.0f}k  ·  +{P['stack'][0][2]:.0f} orders/day",
     "Subscribe once to milk, bread, eggs, curd and a fruit-and-veg box, delivered 6–9 am on batched routes. "
     "Mornings are the quietest hours for a dark store, so this uses capacity that is already paid for. "
     "Scale Nectr (curated fresh produce, live in Bengaluru) to the top metros with a no-questions replacement promise.",
     "Orders per user per month 2.83 → 3.08"),
    ("Swiggy-to-Mart bridge", f"+₹{P['stack'][1][1]/1e3:.0f}k  ·  +{P['stack'][1][2]:.0f} orders/day",
     "About 12.7M people use Swiggy every month but not Instamart (26.2M platform users vs 13.5M). Offer tomorrow's milk on the "
     "food-tracking screen: one cart, one delivery fee, Swiggy One on both. Near-zero acquisition cost.", "8% of food-only users in a radius try Instamart"),
    ("Win back the lapsed", f"+₹{P['stack'][2][1]/1e3:.0f}k  ·  +{P['stack'][2][2]:.0f} orders/day",
     "Roughly 4 in 10 new users don't come back in month one. Find out why per user (a stock-out on the first order, a "
     "late delivery, a price shock) and send the fix, not a blanket coupon. Capped cohort pricing, like the ₹9 store.",
     "~580 users per store back at 2 orders/month"),
    ("Bigger basket", f"+₹{P['stack'][3][1]/1e3:.0f}k  ·  +₹15 net AOV",
     "Private label (No!ce is already in more than 1 in 8 orders and is margin-accretive), 'finish the recipe' "
     "add-ons, and Maxxsaver thresholds set per store from its own basket data rather than one national number.",
     "Net AOV ₹508 → ₹523"),
]
for k, (h, size_line, body, kpi) in enumerate(plays):
    x = 0.6 + (k % 2) * 6.15
    y = 1.78 + (k // 2) * 2.5
    box(s, x, y, 5.95, 2.32, fill=GREY)
    dot(s, x + 0.2, y + 0.2, str(k + 1), d=0.42)
    text(s, x + 0.78, y + 0.17, 3.2, 0.4, h, size=15, bold=True, color=INK, space_after=0)
    text(s, x + 3.6, y + 0.22, 2.2, 0.35, size_line, size=11.5, bold=True, color=ORANGE, align=PP_ALIGN.RIGHT)
    text(s, x + 0.25, y + 0.72, 5.5, 1.2, body, size=11.5, color=INK2, line_spacing=1.0)
    text(s, x + 0.25, y + 1.93, 5.5, 0.3, [[("Target: ", {"bold": True, "color": INK}), (kpi, {})]], size=11.5, color=INK2)
notes(s, "Morning Ritual is the anchor because it creates a daily reason to open the app and fills off-peak hours. "
         "The bridge is the cheapest acquisition Swiggy has: its own food users.")

# ---------------------------------------------------------------- 12. lever stack
s = new_slide()
frame(s, "Sizing",
      f"Added up for an average store, the four plays take NOV from ₹5.52L to ₹{P['new_nov']/1e5:.2f}L a day",
      f"Per-store catchment = {I.mtu_mn:.1f}M MTU ÷ {int(I.stores_end):,} stores. Orders × ₹{I.value_per_order:.0f} net AOV. "
      "Basket play applied to all orders after the other three. Utilisation scaled from Swiggy's ~40%.")
pic(s, "06_lever_stack", 0.55, 1.72, w=8.0)
table(s, 8.95, 1.85, 3.8, [
    ["Assumption", "Value"],
    ["Users per store", f"{I.mtu_mn*1e6/I.stores_end/1e3:.1f}k"],
    ["Frequency uplift", "+0.25 /month"],
    ["Bridge converts", "520 users"],
    ["Lapsed won back", "580 users"],
    ["New users' frequency", "2.0 /month"],
    ["Basket uplift", "+₹15"],
    ["Orders added", f"+{P['add_orders']:.0f} /day"],
    ["Utilisation after", f"~{P['utilisation_after']:.0f}%"],
], [2.2, 1.6], size=11.5, row_h=0.4)
text(s, 8.95, 5.65, 3.8, 1.0, "Even after the plan, stores run under half capacity. "
     "There is room to do this twice before a new store is needed.", size=12, color=INK, bold=True, line_spacing=1.0)
notes(s, "Every input is in model.py. If someone challenges one, change it there and the deck rebuilds.")

# ---------------------------------------------------------------- 13. HEART
s = new_slide()
frame(s, "Measuring it  ·  HEART",
      "One north star, five HEART signals and three guardrails, so the habit is measured rather than assumed",
      "HEART: Happiness, Engagement, Adoption, Retention, Task success (Google's UX metrics framework). Targets are for "
      "pilot stores at day 120; baselines from Q1FY27 filings where public.")
table(s, 0.6, 1.8, 12.15, [
    ["", "Goal", "Signal", "Metric", "Target"],
    ["Happiness", "People trust the morning and fresh orders", "Fewer complaints on fresh", "Fresh complaints per 1,000 orders; slot CSAT", "Below today; CSAT ≥ 4.5"],
    ["Engagement", "Instamart becomes a daily app", "More orders, more categories per user", "Orders per MTU per month", "2.83 → 3.08"],
    ["Adoption", "The new behaviours get picked up", "Sign-ups and first orders", "% MTU on Morning Ritual; % food-only users trying Mart", "8–10%; 8%"],
    ["Retention", "First-timers stay", "Users still ordering after a month", "M1 retention; day-60 survival of won-back users", "61% → 65%; ≥ 40%"],
    ["Task success", "The order arrives complete and on time", "Fewer substitutions and misses", "Fill rate on top-200 SKUs; on-time % in 6–9 am slot", "≥ 98%; ≥ 95%"],
], [1.6, 2.9, 2.55, 3.35, 1.75], size=11.5, row_h=0.58)
box(s, 0.6, 5.42, 3.85, 1.05, fill=DARK)
text(s, 0.8, 5.48, 3.5, 1.0, [[("North star", {"bold": True, "color": ORANGE, "size": 12})],
                              [("NOV per store per day", {"bold": True, "color": WHITE, "size": 16})],
                              [("₹5.52L → ₹6.52L+", {"color": "D9D8D3", "size": 12.5})]], space_after=2)
box(s, 4.6, 5.42, 8.15, 1.05, fill=TINT)
text(s, 4.8, 5.5, 7.8, 0.95, [[("Guardrails (stop if breached)", {"bold": True, "color": INK, "size": 12.5})],
                              "Contribution per added order ≥ ₹20  ·  peak-hour on-time % no worse than control  ·  "
                              "rider earnings per hour no lower than before"], size=13, color=INK2, space_after=3)
notes(s, "HEART keeps the plays honest. A morning slot that shows good adoption but bad task success "
         "(late milk) will kill the habit, so task success is the metric I'd watch first.")

# ---------------------------------------------------------------- 14. economics
s = new_slide()
frame(s, "The money",
      f"About ₹{round(P['annual_net_cr'], -1):,.0f} Cr a year of net contribution, and ~{round(P['stores_avoided'], -1):,.0f} fewer stores to build",
      f"Annualised on {P['stores']:,} stores. Marginal contribution = store variable margin ({S['var_margin']:.1%}); "
      "store rent and staff are already paid. Capex at ₹2.5 Cr per store is Blinkit's guided figure; Instamart doesn't disclose its own.")
table(s, 0.6, 1.85, 5.6, [
    ["Per year, whole network", "₹ Cr"],
    ["Added NOV", f"+{P['annual_nov_cr']:,.0f}"],
    [f"Contribution on it ({S['var_margin']:.1%})", f"+{P['annual_contribution_cr']:,.0f}"],
    ["Programme spend (₹10 per added order)", f"−{P['annual_play_cost_cr']:,.0f}"],
    ["Net contribution", f"+{P['annual_net_cr']:,.0f}"],
    ["Today's annualised Adj. EBITDA loss", f"−{P['annual_ebitda_loss_cr']:,.0f}"],
    ["Net, if the plays deliver only half", f"+{HALF['annual_net_cr']:,.0f}"],
], [4.1, 1.5], size=12.5, row_h=0.46)
text(s, 0.6, 5.25, 5.6, 1.4, [
    f"₹{P['annual_net_cr']:,.0f} Cr closes about {P['annual_net_cr']/P['annual_ebitda_loss_cr']:.0%} of the EBITDA loss. "
    "That's honest, not heroic.",
    f"The bigger prize is on the right: the same ₹60,000 Cr of break-even NOV with {P['stores_avoided']:,.0f} fewer stores, "
    f"about ₹{P['capex_avoided_cr']:,.0f} Cr of capex not spent.",
], size=12.5, color=INK, bullets=True, space_after=6, line_spacing=1.0)
pic(s, "08_expand_vs_densify", 6.55, 1.85, w=6.2)
stat(s, 6.75, 4.75, 2.8, f"{P['stores_avoided']:,.0f}", "fewer dark stores to reach\n₹60,000 Cr of annual NOV", big_size=30)
stat(s, 9.75, 4.75, 3.0, f"₹{P['capex_avoided_cr']:,.0f} Cr", "capex not spent, at ₹2.5 Cr\nper store", big_size=30)
notes(s, "Two kinds of value: the P&L uplift (small but immediate) and the capital it saves on the way to break-even scale "
         "(large). The second is the strategic argument.")

# ---------------------------------------------------------------- 15. roadmap + test
s = new_slide()
frame(s, "How I'd roll it out",
      "Prove it in 60 stores, scale it in the metros, then make it the default, with a stop rule at every gate",
      "Store-level randomisation because the plays change store capacity, not just one user's experience. "
      "Messaging variants inside pilot stores are user-level A/B tests.")
phases = [
    ("Days 0–30", "Set up", ["Weekly store league table: NOV/store/day, utilisation by hour, fill rate",
                             "Pick 60 pilot + 60 matched control stores (same city, vintage, throughput band)",
                             "Freeze new stores where utilisation < 60%"]),
    ("Days 30–120", "Pilot", ["Morning Ritual + bridge in Bengaluru and Pune pilot stores",
                              "Win-back and basket tests at user level inside them",
                              "Read difference-in-differences on NOV/store/day, CUPED on pre-period"]),
    ("Days 120–240", "Scale metros", ["Gate: ≥ +₹40k/store/day vs control, ≥ ₹20 contribution per added order",
                                      "Roll out to the top 8 metros (most of the network's NOV)",
                                      "Start radius-retune trial in the weakest stores"]),
    ("Days 240–365", "Default", ["Whole network; morning slot and bridge become standard",
                                 "Stores still below break-even: consolidate or relocate",
                                 "Re-open expansion only where stores pass ~60% utilisation"]),
]
for k, (when, what, items) in enumerate(phases):
    x = 0.6 + k * 3.07
    box(s, x, 1.8, 2.92, 0.75, fill=ORANGE if k == 1 else DARK)
    text(s, x + 0.15, 1.84, 2.7, 0.7, [[(when, {"bold": True, "size": 12, "color": "F6C9B5" if k == 1 else ORANGE})],
                                      [(what, {"bold": True, "size": 16, "color": WHITE})]], space_after=0)
    box(s, x, 2.6, 2.92, 2.35, fill=GREY)
    text(s, x + 0.15, 2.72, 2.65, 2.2, items, size=11.5, color=INK2, bullets=True, space_after=7, line_spacing=1.0)
box(s, 0.6, 5.2, 12.15, 0.95, fill=TINT)
text(s, 0.8, 5.3, 11.8, 0.8, [
    [("Stop rule. ", {"bold": True, "color": ORANGE}),
     ("If pilot stores are less than ₹20k a day ahead of control at day 120, or the added orders earn under ₹10 of "
      "contribution each, stop scaling and move the budget to radius retuning and store consolidation. "
      "A plan that can't say when it's wrong isn't a plan.", {})]], size=12.5, color=INK, line_spacing=1.0)
notes(s, "Sixty stores per arm is enough: stores are big units with stable daily sales, and CUPED on the 8-week pre-period "
         "removes most of the store-to-store noise.")

# ---------------------------------------------------------------- 16. risks
s = new_slide()
frame(s, "Risks",
      "What could go wrong, and what would change my mind",
      "Labour-code social security: 1–2% of turnover, capped at 5% of payouts (Nov-25). Competitor store counts: Business Standard, Aug-26.")
risks = [
    ("Competitors match it", "Blinkit (2,443 stores), Zepto, Flipkart Minutes (1,000+) and Amazon Now can copy a discount "
                             "overnight. A subscription habit and the food-app bridge are much harder to copy.", "Medium"),
    ("Orders move rather than grow", "The morning slot could just shift orders users would have placed anyway. "
                                     "Measure orders per user per month, never slot orders alone.", "High"),
    ("Morning ops are hard", "Cold chain for milk, a 5:30 am shift, riders at dawn. Start with stores near dairy "
                             "partners; batching raises rider earnings per hour.", "Medium"),
    ("Gig-worker cost rises", "The new labour codes add 1–2% of turnover. Plays that raise drops per trip "
                              "absorb it; plays that add single-item trips don't.", "Medium"),
    ("My cost split is off", "The ₹38k store cost is an estimate. At ₹30k–45k, and even at half delivery, "
                             "contribution still ends positive.", "Low"),
]
for k, (h, body, lvl) in enumerate(risks):
    y = 1.8 + k * 0.96
    tag = box(s, 0.6, y + 0.05, 1.0, 0.34, fill={"High": RED, "Medium": ORANGE, "Low": GREEN}[lvl],
              shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    text(s, 0, 0, 0, 0, lvl, size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
         shape=tag, space_after=0)
    text(s, 1.85, y, 3.0, 0.5, h, size=14, bold=True, color=INK)
    text(s, 4.9, y, 7.85, 0.9, body, size=12.5, color=INK2, line_spacing=1.0)
notes(s, "The biggest risk is the second one. It's the most common way frequency programmes fool themselves.")

# ---------------------------------------------------------------- 17. postscript
ps_note = ("Swiggy Q2FY27 shareholder letter (Oct-26): orders per store per day 1,089 → 1,192; 69 stores added; "
           "CM bridge as disclosed by the company. NOV per store-day computed the same way as slide 3.")
s = new_slide()
frame(s, "Postscript: Q2FY27 came out while I was writing this",
      "The next quarter shows both halves of the argument: fuller stores paid off, discounts and new stores gave it back",
      ps_note)
pic(s, "09_q2fy27_postscript", 0.55, 1.75, w=7.9)
text(s, 8.9, 1.9, 3.85, 4.7, [
    [("Density worked. ", {"bold": True, "color": GREEN}),
     ("Orders per store rose 9.5% and Swiggy credits that with +60 bps of contribution. NOV per store per day reached "
      "about ₹6.0L, half of this plan's target in a single quarter.", {})],
    [("Then it was spent. ", {"bold": True, "color": RED}),
     ("100 bps went on habit and reactivation pricing, 40 bps on mix, and 69 new stores (as many as the previous three "
      "quarters together) carried start-up losses. Contribution fell to −1.0%.", {})],
    [("Reading for this plan: ", {"bold": True}),
     ("the throughput lever is real and roughly the size I assumed (the 60 bps is one of the two ways I sized store cost). "
      "Buy the habit with product, not price, and hold the store count.", {})],
], size=12.5, color=INK, space_after=10, line_spacing=1.02)
notes(s, "I kept Q1FY27 as the baseline so it matches the rest of the repo. Q2 is the out-of-sample check.")

# ---------------------------------------------------------------- 18. appendix
s = new_slide()
frame(s, "Appendix: assumptions and sources", "Everything I had to assume, and where every number comes from")
table(s, 0.6, 1.55, 6.6, [
    ["Assumption", "Value", "Basis"],
    ["Store rent + staff", "₹38k/day", "4,200 sq ft × ~₹100/sq ft/month + ~30 staff; cross-checked on Q2FY27's 60 bps"],
    ["Store variable margin", f"{S['var_margin']:.1%}", "Implied by contribution and the line above"],
    ["Spread of store sales", "σ ₹1.8L", "Reproduces '45% of stores CM-positive'"],
    ["Programme spend", "₹10/order", "About a third of marginal contribution"],
    ["Capex per store", "₹2.5 Cr", "Blinkit guidance; Instamart not disclosed"],
    ["Per-order levers", "₹24.5", "Swiggy: ads ₹10, mix ₹10, inventory ₹4–5"],
    ["Play inputs", "slide 12", "Set in model.py; tests pin every headline number"],
], [1.8, 1.0, 3.8], size=10.5, row_h=0.5)
text(s, 7.6, 1.55, 5.15, 5.2, [
    [("Sources", {"bold": True, "color": INK, "size": 13})],
    "Swiggy shareholder letters Q1FY26, Q4FY26, Q1FY27, Q2FY27 (swiggy.com/corporate)",
    "Eternal shareholder letters Q3FY25, Q4FY25, Q1FY27, Q2FY27 (eternal.com/investor-relations)",
    "Zepto abridged UDRHP, June 2026 (sebi.gov.in)",
    "Business Standard on dark-store additions, Aug-26; TechCrunch on the 10-minute directive, Jan-26; "
    "Fisher Phillips on India's labour codes",
    "Consulting structure: IIM Ahmedabad Consult Prep Book 2025–26 (profitability trees, phased recommendations)",
    [("Model, charts and this deck are rebuilt from code: ", {"bold": True}),
     ("densification-strategy/ in the case-study repo.", {})],
], size=11.5, color=INK2, bullets=False, space_after=7, line_spacing=1.0)

# ---------------------------------------------------------------- 19. close
s = new_slide(dark=True)
text(s, 0.8, 1.6, 11.5, 1.6, "Instamart doesn't need more stores yet. It needs a reason to order every morning.",
     size=36, bold=True, color=WHITE, line_spacing=0.95)
text(s, 0.8, 3.45, 11, 1.2, f"Fund a 60-store pilot of Morning Ritual and the Swiggy-to-Mart bridge. If it clears "
     f"+₹40k per store per day by day 120, scale it. If it doesn't, the stop rule says so.", size=18, color="D9D8D3")
text(s, 0.8, 5.35, 8, 0.4, AUTHOR, size=20, bold=True, color=WHITE, space_after=2)
text(s, 0.8, 5.8, 8, 0.35, EMAIL, size=14, color="D9D8D3")

# ---------------------------------------------------------------- metadata
cp = prs.core_properties
cp.author = AUTHOR
cp.last_modified_by = AUTHOR
cp.title = "Fill the stores before you build more: a densification plan for Swiggy Instamart"
cp.subject = "Instamart densification strategy"
cp.keywords = "quick commerce, Instamart, densification, unit economics, India"
cp.comments = ""
cp.category = ""
cp.revision = 1
now = datetime.now().replace(microsecond=0)
cp.created = now
cp.modified = now
prs.save(OUT)


def fix_app_props(path):
    """python-pptx ships a 4:3 template's app.xml; make it describe this deck."""
    import re
    import shutil
    import zipfile
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/app.xml":
                x = data.decode("utf-8")
                x = re.sub(r"<PresentationFormat>.*?</PresentationFormat>", "<PresentationFormat>Widescreen</PresentationFormat>", x)
                x = re.sub(r"<Application>.*?</Application>", "<Application>Microsoft Office PowerPoint</Application>", x)
                x = re.sub(r"<Slides>\d+</Slides>", f"<Slides>{len(prs.slides)}</Slides>", x)
                data = x.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


fix_app_props(OUT)
print("wrote", OUT.name, len(prs.slides), "slides")
