import streamlit as st
import pandas as pd
from datetime import datetime
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, NextPageTemplate, PageBreak, HRFlowable, Image as RLImage
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.pdfgen import canvas as pdfcanvas

st.set_page_config(page_title="Financial X-Ray Report", layout="wide")

# ================= BRAND =================
BRAND_NAME = "iArista Artha Pvt Ltd"
BRAND_TAGLINE = "Independent Financial Planning & Wealth Management"
NAVY = colors.HexColor("#0B2545")
GOLD = colors.HexColor("#C8A24A")
LIGHT_GREY = colors.HexColor("#F4F5F7")
MID_GREY = colors.HexColor("#8A93A6")
GREEN = colors.HexColor("#2E7D52")
AMBER = colors.HexColor("#C97A1A")
RED = colors.HexColor("#B23A48")
TEXT_DARK = colors.HexColor("#1B2430")

STATUS_COLOR = {"Strong": GREEN, "Partial": AMBER, "Needs Work": RED}

# ================= CONFIG =================

SECTIONS = {
    "Budget & Cash Flow": {
        "max_score": 6,
        "thresholds": [(2, "Needs Work"), (4, "Partial"), (6, "Strong")]
    },
    "Insurance": {
        "max_score": 5,
        "thresholds": [(2, "Needs Work"), (3, "Partial"), (5, "Strong")]
    },
    "Savings & Investments": {
        "max_score": 14,
        "thresholds": [(5, "Needs Work"), (9, "Partial"), (14, "Strong")]
    },
    "Debt Management": {
        "max_score": 3,
        "thresholds": [(1, "Needs Work"), (2, "Partial"), (3, "Strong")]
    },
    "Retirement & Estate": {
        "max_score": 7,
        "thresholds": [(2, "Needs Work"), (5, "Partial"), (7, "Strong")]
    }
}

NARRATIVES = {
    "Budget & Cash Flow": {
        "Needs Work": "Budgeting and emergency-fund planning show meaningful gaps. We recommend building a reserve covering at least six months of essential household expenses before increasing investment allocations.",
        "Partial": "A budgeting framework exists, but tracking discipline and emergency-reserve adequacy can be strengthened to improve resilience against income shocks.",
        "Strong": "Budgeting discipline and emergency preparedness are well established, providing a solid foundation for the wider financial plan."
    },
    "Insurance": {
        "Needs Work": "Current insurance coverage leaves material protection gaps. We recommend a full review of life and health cover relative to family income replacement needs.",
        "Partial": "Basic protection is in place, but asset and liability coverage (property, health top-up) should be reviewed to close remaining gaps.",
        "Strong": "Risk protection across life, health and asset insurance is comprehensive and well aligned to the family's needs."
    },
    "Savings & Investments": {
        "Needs Work": "Savings discipline and investment structuring require attention. Defining clear goals and increasing the systematic savings rate should be prioritised.",
        "Partial": "A savings and investment plan exists, but execution consistency, diversification and periodic review can be improved.",
        "Strong": "A strong wealth-creation framework is in place, supported by disciplined saving and well-diversified investments."
    },
    "Debt Management": {
        "Needs Work": "Current debt behaviour may create financial stress. We recommend reducing high-cost and speculative borrowing as a near-term priority.",
        "Partial": "Debt practices are broadly reasonable, though some habits — such as revolving credit card balances — should be improved.",
        "Strong": "Debt management is prudent, with disciplined repayment behaviour and minimal reliance on high-cost credit."
    },
    "Retirement & Estate": {
        "Needs Work": "Retirement and estate planning require immediate attention. We recommend quantifying the required retirement corpus and formalising nominations.",
        "Partial": "Some retirement planning is underway, but estate-readiness items such as nominations and Power of Attorney have gaps to close.",
        "Strong": "Future readiness is well structured, with retirement planning and estate documentation appropriately in place."
    }
}

def get_status(score, thresholds):
    for limit, label in thresholds:
        if score <= limit:
            return label
    return thresholds[-1][1]

# ================= PDF BUILDER =================

def header_footer(canvas_obj, doc, client_name, report_date):
    canvas_obj.saveState()
    page_w, page_h = A4

    # Top band
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, page_h - 18*mm, page_w, 18*mm, stroke=0, fill=1)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.drawString(18*mm, page_h - 11.5*mm, BRAND_NAME)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.drawRightString(page_w - 18*mm, page_h - 11.5*mm, "FINANCIAL X-RAY REPORT")

    # Footer
    canvas_obj.setStrokeColor(MID_GREY)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(18*mm, 14*mm, page_w - 18*mm, 14*mm)
    canvas_obj.setFont("Helvetica", 7.5)
    canvas_obj.setFillColor(MID_GREY)
    canvas_obj.drawString(18*mm, 10*mm, f"Prepared for {client_name}  |  {report_date}")
    canvas_obj.drawCentredString(page_w/2, 10*mm, BRAND_TAGLINE)
    canvas_obj.drawRightString(page_w - 18*mm, 10*mm, f"Page {doc.page}")
    canvas_obj.restoreState()


def cover_page(canvas_obj, doc, client_name, report_date, overall, total):
    page_w, page_h = A4
    canvas_obj.saveState()

    # Full navy background
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    # Gold accent line
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, page_h - 70*mm, page_w, 2.2*mm, stroke=0, fill=1)

    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawString(20*mm, page_h - 50*mm, BRAND_NAME.upper())
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawString(20*mm, page_h - 56*mm, BRAND_TAGLINE)

    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 30)
    canvas_obj.drawString(20*mm, page_h - 110*mm, "Financial X-Ray")
    canvas_obj.setFont("Helvetica-Bold", 30)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.drawString(20*mm, page_h - 122*mm, "Report")

    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica", 11)
    canvas_obj.drawString(20*mm, page_h - 140*mm, "A comprehensive assessment of personal financial health")

    # Client info card
    card_y = 55*mm
    canvas_obj.setFillColor(colors.HexColor("#102C54"))
    canvas_obj.roundRect(20*mm, card_y, page_w - 40*mm, 32*mm, 3*mm, stroke=0, fill=1)
    canvas_obj.setFillColor(MID_GREY)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(26*mm, card_y + 24*mm, "PREPARED FOR")
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(26*mm, card_y + 18*mm, client_name)

    canvas_obj.setFillColor(MID_GREY)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(26*mm, card_y + 10*mm, "REPORT DATE")
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawString(26*mm, card_y + 5*mm, report_date)

    canvas_obj.setFillColor(MID_GREY)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawRightString(page_w - 26*mm, card_y + 24*mm, "OVERALL SCORE")
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawRightString(page_w - 26*mm, card_y + 18*mm, f"{total}/35  ·  {overall}")

    canvas_obj.setFillColor(MID_GREY)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(20*mm, 20*mm, "Strictly private & confidential. For the named recipient only. Not a substitute for individualised regulated advice.")

    canvas_obj.restoreState()


def make_gauge_drawing(total, max_total=35):
    d = Drawing(170*mm, 26*mm)
    bar_x, bar_y, bar_w, bar_h = 0, 8*mm, 170*mm, 8*mm
    d.add(Rect(bar_x, bar_y, bar_w, bar_h, fillColor=LIGHT_GREY, strokeColor=None, rx=4, ry=4))

    seg_bounds = [0, 18, 28, max_total]
    seg_colors = [RED, AMBER, GREEN]
    for i in range(3):
        x0 = bar_x + (seg_bounds[i] / max_total) * bar_w
        x1 = bar_x + (seg_bounds[i+1] / max_total) * bar_w
        d.add(Rect(x0, bar_y, x1 - x0, bar_h, fillColor=seg_colors[i], strokeColor=colors.white, strokeWidth=1))

    marker_x = bar_x + (total / max_total) * bar_w
    d.add(Line(marker_x, bar_y - 2, marker_x, bar_y + bar_h + 2, strokeColor=NAVY, strokeWidth=2))
    d.add(Circle(marker_x, bar_y + bar_h + 4, 2.2, fillColor=NAVY, strokeColor=None))
    d.add(String(marker_x, bar_y + bar_h + 7, f"{total}", fillColor=NAVY, fontName="Helvetica-Bold", fontSize=9, textAnchor="middle"))

    labels = [("Needs Attention", 9), ("Moderate", 23), ("Strong", 31.5)]
    for text, pos in labels:
        x = bar_x + (pos / max_total) * bar_w
        d.add(String(x, bar_y - 7, text, fillColor=MID_GREY, fontName="Helvetica", fontSize=7, textAnchor="middle"))
    return d


def make_section_bar(sec, score, max_score):
    d = Drawing(110*mm, 6*mm)
    d.add(Rect(0, 0, 110*mm, 5*mm, fillColor=LIGHT_GREY, strokeColor=None, rx=2.5, ry=2.5))
    pct = score / max_score if max_score else 0
    status = get_status(score, SECTIONS[sec]["thresholds"])
    d.add(Rect(0, 0, 110*mm * pct, 5*mm, fillColor=STATUS_COLOR[status], strokeColor=None, rx=2.5, ry=2.5))
    return d


def build_pdf(client_name, report_date, scores_df, total, overall, answers_summary, recs):
    buf = io.BytesIO()
    styles = getSampleStyleSheet()

    style_h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=16, textColor=NAVY,
                               spaceAfter=4, fontName="Helvetica-Bold")
    style_h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12.5, textColor=NAVY,
                               spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold")
    style_body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=14,
                                 textColor=TEXT_DARK)
    style_small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8.5, leading=12,
                                  textColor=MID_GREY)
    style_section_label = ParagraphStyle("sec_label", parent=styles["BodyText"], fontSize=10,
                                          textColor=TEXT_DARK, fontName="Helvetica-Bold")
    style_score_label = ParagraphStyle("score_label", parent=styles["BodyText"], fontSize=9,
                                        textColor=MID_GREY, alignment=TA_LEFT)

    frame_normal = Frame(18*mm, 20*mm, A4[0]-36*mm, A4[1]-44*mm, id="normal")
    frame_cover = Frame(0, 0, A4[0], A4[1], id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def on_cover(c, d):
        cover_page(c, d, client_name, report_date, overall, total)

    def on_normal(c, d):
        header_footer(c, d, client_name, report_date)

    doc = BaseDocTemplate(buf, pagesize=A4,
                           topMargin=20*mm, bottomMargin=18*mm,
                           leftMargin=18*mm, rightMargin=18*mm)
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[frame_cover], onPage=on_cover),
        PageTemplate(id="Normal", frames=[frame_normal], onPage=on_normal),
    ])

    story = []
    story.append(NextPageTemplate("Normal"))
    story.append(PageBreak())

    # ---- Executive summary ----
    story.append(Paragraph("Executive Summary", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))
    story.append(Paragraph(
        f"This report presents an independent assessment of {client_name}'s financial position across five "
        f"core dimensions of personal financial health. The overall score of <b>{total} out of 35</b> places "
        f"the current position in the <b>{overall}</b> category. The sections below summarise findings and "
        f"set out prioritised recommendations to strengthen long-term financial resilience.",
        style_body))
    story.append(Spacer(1, 8))
    story.append(make_gauge_drawing(total))
    story.append(Spacer(1, 10))

    # ---- Score table ----
    story.append(Paragraph("Score Overview", style_h2))
    table_data = [["Dimension", "Score", "Max", "Status"]]
    for _, row in scores_df.iterrows():
        table_data.append([row["Dimension"], str(row["Score"]), str(SECTIONS[row["Dimension"]]["max_score"]), row["Status"]])

    t = Table(table_data, colWidths=[70*mm, 25*mm, 25*mm, 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D9DCE3")),
        ("ALIGN", (1,0), (2,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    for i, row in enumerate(table_data[1:], start=1):
        status = row[3]
        t.setStyle(TableStyle([("TEXTCOLOR", (3,i), (3,i), STATUS_COLOR.get(status, TEXT_DARK)),
                                ("FONTNAME", (3,i), (3,i), "Helvetica-Bold")]))
    story.append(t)
    story.append(Spacer(1, 12))

    # ---- Per-section detail ----
    story.append(Paragraph("Detailed Findings", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))

    for _, row in scores_df.iterrows():
        sec = row["Dimension"]
        score = row["Score"]
        max_score = SECTIONS[sec]["max_score"]
        status = row["Status"]
        story.append(Paragraph(sec, style_section_label))
        status_hex = "#%02x%02x%02x" % tuple(int(c*255) for c in STATUS_COLOR[status].rgb())
        bar_row = Table([[make_section_bar(sec, score, max_score), Paragraph(f"<b>{score}</b> / {max_score}  —  "
                          f"<font color='{status_hex}'>{status}</font>", style_score_label)]],
                         colWidths=[112*mm, 50*mm])
        bar_row.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),0)]))
        story.append(bar_row)
        story.append(Spacer(1, 3))
        story.append(Paragraph(NARRATIVES[sec][status], style_body))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # ---- Recommendations ----
    story.append(Paragraph("Key Recommendations", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))
    story.append(Paragraph(
        "The following actions are recommended in priority order, based on the assessment above. "
        "We suggest reviewing these with your relationship manager to build a structured implementation plan.",
        style_body))
    story.append(Spacer(1, 8))

    rec_data = [["Priority", "Recommended Action", "Suggested Timeline"]] + recs
    rt = Table(rec_data, colWidths=[28*mm, 95*mm, 32*mm])
    pr_colors = {"HIGH": RED, "MEDIUM": AMBER, "LOW": GREEN}
    rt_style = [
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D9DCE3")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]
    for i, row in enumerate(rec_data[1:], start=1):
        rt_style.append(("TEXTCOLOR", (0,i), (0,i), pr_colors.get(row[0], TEXT_DARK)))
        rt_style.append(("FONTNAME", (0,i), (0,i), "Helvetica-Bold"))
    rt.setStyle(TableStyle(rt_style))
    story.append(rt)
    story.append(Spacer(1, 14))

    # ---- Disclaimer ----
    story.append(Paragraph("Important Notes", style_h2))
    story.append(Paragraph(
        "This Financial X-Ray Report is a self-assessment tool intended to provide a high-level snapshot of "
        "financial wellbeing across budgeting, protection, savings, debt and retirement readiness. It is for "
        "general informational purposes only, is based solely on information provided by the client, and does "
        "not constitute personalised investment, tax or legal advice. We recommend a detailed consultation with "
        "your advisor before acting on any of the observations contained in this report.",
        style_small))

    doc.build(story)
    buf.seek(0)
    return buf


# ================= STREAMLIT UI =================

st.title("📊 Financial X-Ray Report Generator")

client = st.text_input("Client Name")

# ================= BUDGET =================
st.header("1. Budget & Cash Flow")

b1 = st.radio("Have you prepared a budget?", ["Yes","No"])
b2 = st.selectbox("Monthly household expenditure", ["< ₹30,000","₹30,000 – ₹50,000","> ₹50,000"])
b3 = st.radio("Do you know how much emergency cash is required?", ["Yes","No"])
b4 = st.radio("Do you have cash available for job/income loss?", ["Yes","No"])
b5 = st.radio("Do you follow your budgeting?", ["Yes","No"])

budget_score = 0
budget_score += 1 if b1=="Yes" else 0
budget_score += 1 if b2=="₹30,000 – ₹50,000" else 0
budget_score += 2 if b3=="Yes" else 0
budget_score += 1 if b4=="Yes" else 0
budget_score += 1 if b5=="Yes" else 0

# ================= INSURANCE =================
st.header("2. Insurance")

i1 = st.radio("Life Insurance Cover?", ["Yes","No"])
i2 = st.radio("Know required life cover?", ["Yes","No"])
i3 = st.radio("Family Health Insurance?", ["Yes","No"])
i4 = st.radio("Properties insured?", ["Yes","No"])

insurance_score = 0
insurance_score += 1 if i1=="Yes" else 0
insurance_score += 1 if i2=="Yes" else 0
insurance_score += 1 if i3=="Yes" else 0
insurance_score += 2 if i4=="Yes" else 0

# ================= SAVINGS =================
st.header("3. Savings & Investments")

s1 = st.radio("Financial goals identified?", ["Yes","No"])
s2 = st.radio("Investment plan exists?", ["Yes","No"])
s3 = st.selectbox("% income saved", ["<10%","10%-25%","At least 25% of take-home salary"])
s4 = st.radio("Follow investment plan?", ["Yes","No"])
s5 = st.radio("Review investments periodically?", ["Yes","No"])
s6 = st.radio("Diversified investments?", ["Yes","No"])
s7 = st.multiselect(
    "Asset Classes",
    ["Equity","Debt Mutual Funds","Real Estate","Gold","FD","International"]
)

savings_score = 0
savings_score += 2 if s1=="Yes" else 0
savings_score += 2 if s2=="Yes" else 0
savings_score += 3 if s3=="At least 25% of take-home salary" else 1
savings_score += 2 if s4=="Yes" else 0
savings_score += 2 if s5=="Yes" else 0
savings_score += 2 if s6=="Yes" else 0
savings_score += 1 if len(s7)>=3 else 0

# ================= DEBT =================
st.header("4. Debt Management")

d1 = st.radio("Speculative borrowing?", ["Yes","No"])
d2 = st.radio("Carry credit card balance?", ["Yes","No"])

debt_score = 0
debt_score += 2 if d1=="No" else 0
debt_score += 1 if d2=="No" else 0

# ================= RETIREMENT =================
st.header("5. Retirement & Estate")

r1 = st.radio("Retirement savings?", ["Yes","No"])
r2 = st.radio("Know retirement corpus required?", ["Yes","No"])
r3 = st.radio("Joint account holdings?", ["Yes","No"])
r4 = st.radio("Nominees assigned?", ["Yes","No"])
r5 = st.radio("Power of Attorney?", ["Yes","No"])

retirement_score = 0
retirement_score += 2 if r1=="Yes" else 0
retirement_score += 2 if r2=="Yes" else 0
retirement_score += 1 if r3=="Yes" else 0
retirement_score += 1 if r4=="Yes" else 0
retirement_score += 1 if r5=="Yes" else 0

# ================= REPORT =================

if st.button("Generate Financial X-Ray Report", type="primary"):

    scores = {
        "Budget & Cash Flow": budget_score,
        "Insurance": insurance_score,
        "Savings & Investments": savings_score,
        "Debt Management": debt_score,
        "Retirement & Estate": retirement_score
    }

    rows = []
    total = 0

    for sec, score in scores.items():
        total += score
        rows.append({
            "Dimension": sec,
            "Score": score,
            "Status": get_status(score, SECTIONS[sec]["thresholds"])
        })

    df = pd.DataFrame(rows)

    if total < 18:
        overall = "Needs Attention"
    elif total < 28:
        overall = "Moderate"
    else:
        overall = "Strong"

    st.success("Report Generated")

    c1,c2,c3 = st.columns(3)
    c1.metric("Client", client if client else "NA")
    c2.metric("Overall Score", f"{total}/35")
    c3.metric("Status", overall)

    st.subheader("Score Overview")
    st.dataframe(df, use_container_width=True)

    recs = [
        ["HIGH", "Build emergency fund", "30 Days"],
        ["HIGH", "Review insurance coverage", "30 Days"],
        ["MEDIUM", "Increase SIP investments", "60 Days"],
        ["MEDIUM", "Nominee & estate review", "60 Days"],
        ["LOW", "Portfolio optimization", "90 Days"],
    ]
    st.subheader("Key Recommendations")
    st.table(pd.DataFrame(recs, columns=["Priority","Action","Timeline"]))

    client_name = client.strip() if client and client.strip() else "Valued Client"
    report_date = datetime.now().strftime("%d %B %Y")

    pdf_buffer = build_pdf(client_name, report_date, df, total, overall, scores, recs)

    st.divider()
    st.subheader("📄 Client-Ready PDF Report")
    st.download_button(
        label="⬇️ Download Financial X-Ray Report (PDF)",
        data=pdf_buffer,
        file_name=f"Financial_X-Ray_Report_{client_name.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary"
    )
