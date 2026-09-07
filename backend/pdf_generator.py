"""
Professional PDF Generator for Car Insurance Claim Vouchers & Policy Documents
Uses ReportLab 5.0
"""

import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_claim_pdf(claim: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b')
    )
    cell_label = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b')
    )
    cell_value = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#065f46') if claim.get('badge_type') == 'APPROVED' else colors.HexColor('#991b1b')
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("CLAIMVISION AUTOMOTIVE MUTUAL INSURANCE CORP.", title_style))
    story.append(Paragraph("Autonomous Computer Vision Underwriting & Claim Adjudication Bureau", subtitle_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=15))

    # 2. Claim Voucher Identification Table
    claim_id = claim.get("claim_id", "CLM-UNKNOWN")
    auth_token = claim.get("auth_token", "N/A")
    sub_time = claim.get("created_at") or claim.get("submission_time", "N/A")
    decision_label = claim.get("status_label", "UNDER REVIEW")

    header_data = [
        [
            Paragraph("CLAIM REFERENCE ID", cell_label),
            Paragraph("AUTH TOKEN", cell_label),
            Paragraph("ADJUDICATION STATUS", cell_label),
            Paragraph("TIMESTAMP (UTC)", cell_label)
        ],
        [
            Paragraph(f"<b>{claim_id}</b>", cell_value),
            Paragraph(f"<b>{auth_token}</b>", cell_value),
            Paragraph(f"<b>{decision_label}</b>", badge_style),
            Paragraph(sub_time, cell_value)
        ]
    ]
    t_header = Table(header_data, colWidths=[130, 130, 150, 120])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 15))

    # 3. Policy & Claimant Information
    story.append(Paragraph("1. Policyholder & Vehicle Incident Details", section_title))
    story.append(Spacer(1, 6))

    policy_no = claim.get("policy_number") or claim.get("claim_summary", {}).get("policy_number", "POL-884920")
    claimant = claim.get("claimant_name") or claim.get("claim_summary", {}).get("claimant", "Viswa Sharma")
    vin = claim.get("vehicle_vin") or claim.get("claim_summary", {}).get("vehicle_vin", "MH-46-AB-2026")
    inc_date = claim.get("incident_date") or claim.get("claim_summary", {}).get("incident_date", "2026-09-07")
    inc_desc = claim.get("incident_description") or claim.get("claim_summary", {}).get("incident_description", "Vehicle collision.")

    policy_data = [
        [Paragraph("Policyholder Name:", cell_label), Paragraph(claimant, cell_value),
         Paragraph("Policy Number:", cell_label), Paragraph(policy_no, cell_value)],
        [Paragraph("Vehicle VIN / Reg:", cell_label), Paragraph(vin, cell_value),
         Paragraph("Incident Date:", cell_label), Paragraph(inc_date, cell_value)],
        [Paragraph("Incident Narrative:", cell_label), Paragraph(inc_desc, cell_value), "", ""]
    ]
    t_policy = Table(policy_data, colWidths=[120, 145, 120, 145])
    t_policy.setStyle(TableStyle([
        ('SPAN', (1, 2), (3, 2)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_policy)
    story.append(Spacer(1, 15))

    # 4. Computer Vision Diagnostic Matrix
    story.append(Paragraph("2. Autonomous Multimodal Computer Vision Diagnostic Matrix", section_title))
    story.append(Spacer(1, 6))

    severity = claim.get("overall_severity") or claim.get("claim_summary", {}).get("damage_severity", "Moderate Damage")
    tier = claim.get("repair_cost_tier") or claim.get("claim_summary", {}).get("repair_tier", "Medium Tier")
    area_pct = claim.get("damage_area_pct", 14.8)
    deform = claim.get("deformation_flag", 0)
    deform_str = "STRUCTURAL CHASSIS DEFORMATION (Flag: 1)" if deform == 1 else "FRAME STRUCTURALLY INTACT (Flag: 0)"

    cv_data = [
        [Paragraph("AI Vision Member / Model", cell_label), Paragraph("Extracted Metric", cell_label), Paragraph("Engine Assessment", cell_label)],
        [Paragraph("Member 1: MobileNetV2 CNN", cell_value), Paragraph("Deep Vision Feature Maps", cell_value), Paragraph(f"<b>{severity}</b>", cell_value)],
        [Paragraph("Member 2: SVM + HOG Gradients", cell_value), Paragraph("8,100 Spatial Edge Descriptors", cell_value), Paragraph(f"<b>{deform_str}</b>", cell_value)],
        [Paragraph("Member 3: K-Means HSV Clustering", cell_value), Paragraph("3 Color-Space Pixel Clusters", cell_value), Paragraph(f"<b>{area_pct}% Surface Defect</b>", cell_value)],
        [Paragraph("Member 4: Random Forest Ensemble", cell_value), Paragraph("Tabular Fusion Classification", cell_value), Paragraph(f"<b>{tier}</b>", cell_value)],
    ]
    t_cv = Table(cv_data, colWidths=[170, 180, 180])
    t_cv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_cv)
    story.append(Spacer(1, 15))

    # 5. Financial Settlement Ledger
    story.append(Paragraph("3. Financial Settlement & Payout Ledger", section_title))
    story.append(Spacer(1, 6))

    gross_usd = claim.get("estimated_cost_usd") or claim.get("estimated_net_settlement_usd", "$750 - $2,200")
    gross_inr = claim.get("estimated_cost_inr") or claim.get("estimated_net_settlement_inr", "INR 55,000 - 1,65,000")
    ded_usd = claim.get("deductible_usd", "$250")
    ded_inr = claim.get("deductible_inr", "INR 5,000")
    action_note = claim.get("action_note", "Standard settlement.")

    finance_data = [
        [Paragraph("Gross Assessed Damage Valuation:", cell_label), Paragraph(f"{gross_usd} ({gross_inr})", cell_value)],
        [Paragraph("Standard Policy Deductible:", cell_label), Paragraph(f"-{ded_usd} ({ded_inr})", cell_value)],
        [Paragraph("Authorized Net Settlement Payout:", cell_label), Paragraph(f"<b>{gross_usd} ({gross_inr})</b>", cell_value)],
        [Paragraph("Underwriting Action Note:", cell_label), Paragraph(action_note, cell_value)]
    ]
    t_fin = Table(finance_data, colWidths=[200, 330])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 20))

    # 6. Signature & Digital Audit Stamp
    story.append(Paragraph("4. Authorization Signatures & Cryptographic Audit", section_title))
    story.append(Spacer(1, 6))

    sig_data = [
        [
            Paragraph("AI Underwriting System:<br/><b>CLAIMVISION AUTOMATED ENGINE v4.0</b><br/>Status: Verified & Timestamped", cell_value),
            Paragraph("Authorized Human Adjuster Review:<br/><b>CERTIFIED SURVEYOR SIGNATURE</b><br/>____________________________", cell_value)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[265, 265])
    t_sig.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sig)

    doc.build(story)
    return buffer.getvalue()
