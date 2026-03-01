#!/usr/bin/env python3
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def create_notice(output_path, info_dict, sections_dict):
    """
    Generate an examiner's notice PDF.
    sections_dict is { "SECTION Title": [ ("Code", "Title", "Text"), ... ] }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    city_blue = colors.HexColor("#003F72")
    city_red  = colors.HexColor("#C8102E")

    header_style = ParagraphStyle("header", fontSize=18, textColor=city_blue, fontName="Helvetica-Bold", spaceAfter=2)
    sub_style = ParagraphStyle("sub", fontSize=10, textColor=city_blue, fontName="Helvetica", spaceAfter=2)
    title_style = ParagraphStyle("title", fontSize=14, textColor=colors.black, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
    body_style = ParagraphStyle("body", fontSize=9, leading=14, fontName="Helvetica", spaceAfter=6)
    deficiency_title_style = ParagraphStyle("def_title", fontSize=10, fontName="Helvetica-Bold", textColor=city_red, spaceAfter=2, spaceBefore=8)
    def_body_style = ParagraphStyle("def_body", fontSize=9, leading=13, fontName="Helvetica", leftIndent=12, spaceAfter=4)
    label_style = ParagraphStyle("label", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)

    story.append(Paragraph("City of Toronto", header_style))
    story.append(Paragraph("Toronto Building — Plans Examination Branch", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=city_blue, spaceAfter=10))

    story.append(Paragraph("EXAMINER'S NOTICE", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceAfter=10))

    info_data = [
        [Paragraph("<b>Application Number:</b>", body_style), Paragraph(info_dict.get('app_num', '12345'), body_style), Paragraph("<b>Notice Date:</b>", body_style), Paragraph(info_dict.get('date', 'Today'), body_style)],
        [Paragraph("<b>Property Address:</b>", body_style), Paragraph(info_dict.get('address', '123 Fake St'), body_style), Paragraph("<b>Ward:</b>", body_style), Paragraph("Ward 9 — Davenport", body_style)],
        [Paragraph("<b>Application Type:</b>", body_style), Paragraph(info_dict.get('type', 'Building Permit'), body_style), Paragraph("<b>Examiner File:</b>", body_style), Paragraph("BP-202X", body_style)],
        [Paragraph("<b>Owner/Agent:</b>", body_style), Paragraph(info_dict.get('agent', 'Jane Doe'), body_style), Paragraph("<b>Zoning:</b>", body_style), Paragraph("RD", body_style)],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 2.6*inch, 1.3*inch, 2.1*inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("TO: The Above-Named Owner/Authorized Agent", label_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("This notice is issued pursuant to Section 11 of the <i>Building Code Act, 1992</i> and Section 2.3.5 of the <i>Ontario Building Code (OBC) 2012</i>. The plans and documents submitted in support of the above-referenced building permit application have been reviewed and found to contain the following deficiencies.", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceAfter=6))

    for sec_title, items in sections_dict.items():
        story.append(Paragraph(sec_title, deficiency_title_style))
        for code, title, text in items:
            story.append(Paragraph(f"<b>{code} — {title}</b>", def_body_style))
            story.append(Paragraph(text, def_body_style))
            story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4))

    doc.build(story)
    print(f"Generated: {os.path.abspath(output_path)}")

def generate_all():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "realworld_examples")
    
    # 1. Laneway Suite Zoning Example
    create_notice(
        os.path.join(docs_dir, "ex1_laneway_zoning_issues.pdf"),
        {
            "app_num": "24 159932 BLD 00 LS",
            "date": "February 28, 2026",
            "address": "45 Parkdale Ave, Toronto, ON",
            "type": "New Laneway Suite",
            "agent": "BuildCo Group"
        },
        {
            "SECTION A — ZONING BY-LAW DEFICIENCIES": [
                (
                    "A-1", "Maximum Building Height — Section 150.8.20(1)",
                    "For an ancillary building containing a laneway suite, the maximum permitted building height is 6.3 metres if the suite is located more than 5.0 metres from the residential building. The proposed design height is 6.8m, exceeding the limit by 0.5m. Revise design to comply with By-law 569-2013."
                ),
                (
                    "A-2", "Laneway Abutment Length — Section 150.8.20(3)",
                    "A lot may have an ancillary building containing a laneway suite if it has a rear lot line or side lot line abutting a lane for at least 3.5 metres. The submitted survey shows the rear lot line abuts the lane for only 3.2 metres. A minor variance is required."
                )
            ],
            "SECTION B — TREE PROTECTION": [
                (
                    "B-1", "Tree Protection Zone — Chapter 813",
                    "A City of Toronto tree having a diameter of 35cm exists adjacent to the proposed excavation. Chapter 813 requires a permit to injure or destroy any tree >30cm DBH. Provide an Urban Forestry approved Tree Protection Plan."
                )
            ]
        }
    )

    # 2. Garden Suite OBC & Fire Example
    create_notice(
        os.path.join(docs_dir, "ex2_garden_suite_obc_fire.pdf"),
        {
            "app_num": "24 238122 BLD 00 GS",
            "date": "March 1, 2026",
            "address": "888 Bathurst St, Toronto, ON",
            "type": "New Garden Suite",
            "agent": "DesignStudio Inc."
        },
        {
            "SECTION A — ONTARIO BUILDING CODE (OBC)": [
                (
                    "A-1", "Spatial Separation / Limiting Distance — OBC Article 9.10.14.3",
                    "Ontario Building Code 3.2.3.1 requires calculating unprotected openings in an exposing building face. The proposed garden suite east wall is located 0.8 metres from the property line, thus requiring a 45-minute fire-resistance rating with no unprotected openings. Drawing A-202 shows two large windows. Provide non-combustible construction details or remove windows."
                )
            ],
            "SECTION B — FIRE ACCESS": [
                (
                    "B-1", "Distance to Hydrant and Fire Route",
                    "Fire access route must provide uninterrupted access from the principle street face of the dwelling unit to the entry of the garden suite. The principal path of travel is shown as 0.7m width. It must be a minimum 0.9m width without overhanging obstructions lower than 2.1m. Revise site plan to show compliant access path."
                )
            ],
            "SECTION C — LANDSCAPING": [
                (
                    "C-1", "Soft Landscaping Requirements",
                    "If the lot area is greater than 100 square metres, a minimum of 85% of the rear yard area not covered by the ancillary building must be maintained as soft landscaping. The submitted plan shows an extensive concrete patio reducing soft landscaping to 55%. Revise plans to decrease hardscape footprint."
                )
            ]
        }
    )

    # 3. Comprehensive Refusal Example
    create_notice(
        os.path.join(docs_dir, "ex3_comprehensive_deficiency_report.pdf"),
        {
            "app_num": "25 101010 BLD 00 RS",
            "date": "March 2, 2026",
            "address": "100 King St W, Toronto, ON",
            "type": "Residential Addition",
            "agent": "Homeowners"
        },
        {
             "SECTION A — ZONING BY-LAW DEFICIENCIES": [
                (
                    "Z-1", "Rear Yard Setback",
                    "An ancillary building containing a laneway suite must be set back from a rear lot line abutting a street or a lane 1.5 metres. The proposed building is located right on the lot line (0.0m setback). This violates By-law 569-2013."
                )
             ],
            "SECTION B — FIRE ACCESS & OBC": [
                 (
                    "F-1", "Fire Access Route",
                    "The principal path of travel must be a minimum 0.9m width without overhanging obstructions lower than 2.1m. The proposed side yard pathway is obstructed by the HVAC unit."
                 ),
                 (
                    "OBC-1", "Spatial Separation",
                    "The percentage of unprotected openings in an exposing building face shall be determined in conformance with Table 3.2.3.1.B for the limiting distance. Submit required OBC matrix."
                 )
             ]
        }
    )

if __name__ == "__main__":
    generate_all()
