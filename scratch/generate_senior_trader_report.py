import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report():
    pdf_filename = r"c:\Users\RANAY\Desktop\FO TRADING BOT\Senior_Trader_Quant_Analysis_Report_v3.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=10,
        spaceAfter=3
    )

    story = []

    story.append(Paragraph("INSTITUTIONAL QUANTITATIVE TRADING OPTIMIZATION REPORT", title_style))
    story.append(Paragraph("Post-Optimization Validation: Flipping Bot 1 Positive (+15.16%) & Zerodha Rate Alignment", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=10))

    story.append(Paragraph("1. Executive Overview & Post-Optimization Breakthrough", h2_style))
    story.append(Paragraph(
        "Following recommendations from the quantitative audit, the 5-step optimization blueprint was implemented on <b>Bot 1 (Intraday Equity Cash Engine)</b>. "
        "By introducing <b>5x SEBI MIS intraday margin leverage</b>, a <b>2.0:1 asymmetric reward-to-risk ratio</b>, a <b>liquidity time-of-day filter</b>, "
        "and strict <b>Relative Strength (RS) outperformance gates</b>, Bot 1 successfully flipped from a negative return (-10.02%) to a <b>net-profitable +15.16% return (+INR 15,162.61)</b> "
        "after accounting for all official Zerodha brokerage and tax frictions.",
        body_style
    ))

    story.append(Paragraph("2. Updated Side-by-Side Performance Scorecard (Post-Optimization)", h2_style))
    scorecard_data = [
        ["Performance Metric", "Bot 1: Intraday Cash (Post-Optimization)", "Bot 2: Shadow Traders F&O Quant Engine"],
        ["Initial Capital Allocation", "INR 100,000.00", "INR 500,000.00 (INR 5 Lakhs)"],
        ["Asset Class & Leverage", "NIFTY Cash Stocks (5x MIS Margin)", "NIFTY & BANKNIFTY Options + Futures"],
        ["Timeframe & Signals", "15m Candles (09:30-11:30 & 14:00-15:00)", "1m / 5m / 15m Multi-Timeframe"],
        ["Total Trades Executed", "770 Trades", "101 Trades"],
        ["Win / Loss Ratio", "347 Wins / 423 Losses (45.06% WR)", "46 Wins / 55 Losses (45.54% WR)"],
        ["Reward-to-Risk Ratio", "1.30 : 1 (Shifted to 2.0:1 Target)", "1.42 : 1"],
        ["Profit Factor", "1.07x (Net Profitable Engine)", "1.19x (Net Profitable Engine)"],
        ["Avg Winning Trade", "+INR 668.42", "+INR 43,829.88 (+25.0% Premium Move)"],
        ["Avg Losing Trade", "-INR 512.48", "-INR 30,928.92 (-10.0% Premium Drop)"],
        ["Total Zerodha Charges", "INR 56,293.27 (Calculated via Zerodha Rate)", "INR 4,040.00 (Flat INR 20 Model)"],
        ["Net Realized Return", "+INR 15,162.61 (+15.16% NET PROFIT)", "+INR 315,083.93 (+63.02% Net Return)"],
        ["Final Portfolio Value", "INR 115,162.48", "INR 815,083.98"],
        ["Walk-Forward Verdict", "PASS (Flipped to Net Profitable)", "PASS (Profitable Options Delta Leverage)"]
    ]
    stable = Table(scorecard_data, colWidths=[140, 200, 200])
    stable.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('TEXTCOLOR', (1,11), (1,11), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (2,11), (2,11), colors.HexColor('#16a34a')),
        ('FONTNAME', (0,11), (-1,11), 'Helvetica-Bold'),
    ]))
    story.append(stable)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Summary of 5-Step Optimization Enhancements Applied", h2_style))
    steps = [
        "<b>1. Activated 5x SEBI MIS Intraday Margin Leverage:</b> Intraday cash moves of 1-1.5% were scaled 5x on margin, enabling gross gains to easily overcome fixed friction.",
        "<b>2. Implemented 2.0:1 Asymmetric Reward-to-Risk Ratio:</b> Shifted target floor to +2.5x ATR and initial SL to -1.25x ATR, boosting average win payout to +INR 668 vs average loss of -INR 512.",
        "<b>3. Filtered Out Mid-Day Chop (11:30 AM – 01:30 PM IST):</b> Restricted trade entries to high-volume morning (09:30-11:30 AM) and afternoon power hours (02:00-03:00 PM).",
        "<b>4. Applied Relative Strength (RS) Outperformance Filter:</b> Only entered long trades on stocks outperforming NIFTY 50 (RS > 1.0) and short trades on underperforming stocks (RS < 1.0).",
        "<b>5. Enforced Zerodha Cost-Gate Floor:</b> Rejected trade candidates where expected gross gain was less than 3x total Zerodha friction charges."
    ]
    for step in steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=6))
    story.append(Paragraph("<b>Report Prepared by:</b> AlphaDesk Quantitative Research Team • <b>Date:</b> August 07, 2026", ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=colors.HexColor('#64748b'))))

    doc.build(story)
    print(f"PDF Report v3 generated successfully: {pdf_filename}")

if __name__ == "__main__":
    generate_pdf_report()
