"""
PDF Export Service — generates a professional resubmission package PDF.

The output PDF contains:
  1. Cover Letter (addressed to Toronto Building, referencing the permit application)
  2. Itemized Deficiency Responses (matching the order of the Examiner's Notice)
  3. Revision Summary Table
  4. Professional Liability Disclaimer

Design: clean, professional, two-column layout for deficiency items.
"""

import io
import textwrap
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colour palette ──────────────────────────────────────────────────────
CITY_BLUE = colors.HexColor("#003F72")
CITY_BLUE_LIGHT = colors.HexColor("#E8F0FE")
ACCENT_GREEN = colors.HexColor("#0D7C3F")
ACCENT_AMBER = colors.HexColor("#D97706")
ACCENT_RED = colors.HexColor("#C8102E")
ACCENT_PURPLE = colors.HexColor("#7C3AED")
GREY_LIGHT = colors.HexColor("#F3F4F6")
GREY_BORDER = colors.HexColor("#D1D5DB")
TEXT_DARK = colors.HexColor("#1F2937")
TEXT_MUTED = colors.HexColor("#6B7280")

STATUS_COLOURS = {
    "RESOLVED": ACCENT_GREEN,
    "DRAWING_REVISION_NEEDED": ACCENT_AMBER,
    "VARIANCE_REQUIRED": ACCENT_RED,
    "LDA_REQUIRED": ACCENT_PURPLE,
    "OUT_OF_SCOPE": TEXT_MUTED,
}

STATUS_LABELS = {
    "RESOLVED": "Resolved",
    "DRAWING_REVISION_NEEDED": "Drawing Revision Needed",
    "VARIANCE_REQUIRED": "Minor Variance Required",
    "LDA_REQUIRED": "LDA Required",
    "OUT_OF_SCOPE": "Out of Scope",
}

CATEGORY_LABELS = {
    "ZONING": "Zoning By-law",
    "OBC": "Ontario Building Code",
    "FIRE_ACCESS": "Fire Access",
    "TREE_PROTECTION": "Tree Protection",
    "LANDSCAPING": "Landscaping",
    "SERVICING": "Servicing",
    "OTHER": "Other",
}


def _styles():
    """Build the stylesheet for the PDF."""
    ss = getSampleStyleSheet()

    ss.add(ParagraphStyle(
        "CoverTitle", fontSize=22, fontName="Helvetica-Bold",
        textColor=CITY_BLUE, leading=28, spaceAfter=4,
    ))
    ss.add(ParagraphStyle(
        "CoverSubtitle", fontSize=11, fontName="Helvetica",
        textColor=TEXT_MUTED, leading=14, spaceAfter=16,
    ))
    ss.add(ParagraphStyle(
        "SectionTitle", fontSize=14, fontName="Helvetica-Bold",
        textColor=CITY_BLUE, leading=18, spaceBefore=16, spaceAfter=6,
    ))
    ss.add(ParagraphStyle(
        "ItemTitle", fontSize=10, fontName="Helvetica-Bold",
        textColor=TEXT_DARK, leading=14, spaceBefore=6, spaceAfter=2,
    ))
    ss.add(ParagraphStyle(
        "Body", fontSize=9, fontName="Helvetica",
        textColor=TEXT_DARK, leading=13, spaceAfter=4, alignment=TA_JUSTIFY,
    ))
    ss.add(ParagraphStyle(
        "BodySm", fontSize=8, fontName="Helvetica",
        textColor=TEXT_MUTED, leading=11, spaceAfter=2,
    ))
    ss.add(ParagraphStyle(
        "Citation", fontSize=8, fontName="Courier",
        textColor=CITY_BLUE, leading=11, spaceAfter=2,
    ))
    ss.add(ParagraphStyle(
        "Disclaimer", fontSize=7, fontName="Helvetica-Oblique",
        textColor=TEXT_MUTED, leading=10, spaceAfter=2, alignment=TA_JUSTIFY,
    ))
    ss.add(ParagraphStyle(
        "StatusBadge", fontSize=8, fontName="Helvetica-Bold",
        leading=11, spaceAfter=2,
    ))
    ss.add(ParagraphStyle(
        "TableHeader", fontSize=8, fontName="Helvetica-Bold",
        textColor=colors.white, leading=11,
    ))
    ss.add(ParagraphStyle(
        "TableCell", fontSize=8, fontName="Helvetica",
        textColor=TEXT_DARK, leading=11,
    ))
    ss.add(ParagraphStyle(
        "FooterText", fontSize=7, fontName="Helvetica",
        textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10,
    ))
    return ss


def _footer(canvas, doc):
    """Draw persistent footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawCentredString(
        letter[0] / 2, 0.5 * inch,
        f"PermitPulse Toronto — Resubmission Package — Page {doc.page}"
    )
    canvas.drawCentredString(
        letter[0] / 2, 0.38 * inch,
        "AI-generated document. Professional review required before submission to Toronto Building."
    )
    # Thin blue rule
    canvas.setStrokeColor(CITY_BLUE)
    canvas.setLineWidth(0.5)
    canvas.line(0.75 * inch, 0.62 * inch, letter[0] - 0.75 * inch, 0.62 * inch)
    canvas.restoreState()


class ResubmissionPackageGenerator:
    """Generates a PDF resubmission package from pipeline results."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.styles = _styles()
        self.now = datetime.utcnow()

    def generate(self) -> bytes:
        """Returns the PDF as bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.85 * inch,
        )

        story = []
        story += self._cover_letter()
        story.append(PageBreak())
        story += self._deficiency_responses()
        story.append(PageBreak())
        story += self._revision_summary()
        story += self._disclaimer()

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return buffer.getvalue()

    # ── Cover Letter ────────────────────────────────────────────────────
    def _cover_letter(self) -> list:
        s = self.styles
        addr = self.data.get("property_address", "Property Address")
        suite = self.data.get("suite_type", "Suite").replace("_", " ")
        session_id = self.data.get("session_id", "N/A")
        summary = self.data.get("summary", {})
        total = summary.get("total_deficiencies", 0)

        elements = []

        # Letterhead
        elements.append(Paragraph("PermitPulse Toronto", s["CoverTitle"]))
        elements.append(Paragraph(
            "AI-Powered Permit Correction Response System",
            s["CoverSubtitle"],
        ))
        elements.append(HRFlowable(
            width="100%", thickness=2, color=CITY_BLUE, spaceAfter=16,
        ))

        # Date & reference
        info_data = [
            [Paragraph("<b>Date:</b>", s["Body"]),
             Paragraph(self.now.strftime("%B %d, %Y"), s["Body"]),
             Paragraph("<b>Reference:</b>", s["Body"]),
             Paragraph(f"Session {session_id[:8]}…", s["Body"])],
            [Paragraph("<b>Property:</b>", s["Body"]),
             Paragraph(addr, s["Body"]),
             Paragraph("<b>Suite Type:</b>", s["Body"]),
             Paragraph(f"{suite} Suite", s["Body"])],
            [Paragraph("<b>Total Items:</b>", s["Body"]),
             Paragraph(str(total), s["Body"]),
             Paragraph("<b>Status:</b>", s["Body"]),
             Paragraph(self.data.get("status", "COMPLETE"), s["Body"])],
        ]
        info_table = Table(info_data, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 2.1 * inch])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CITY_BLUE_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, GREY_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, GREY_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 16))

        # Body text
        elements.append(Paragraph(
            "Plans Examination Branch<br/>"
            "Toronto Building<br/>"
            "Metro Hall, 55 John Street<br/>"
            "Toronto, ON M5V 3C6",
            s["Body"],
        ))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"<b>Re: Response to Examiner's Notice — {addr}</b>",
            s["ItemTitle"],
        ))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            f"Dear Plans Examiner,",
            s["Body"],
        ))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"Please find enclosed our response to the {total} deficiency item(s) "
            f"identified in the Examiner's Notice for the proposed {suite} "
            f"Suite at <b>{addr}</b>. Each item has been reviewed against the "
            f"applicable provisions of By-law 569-2013, the Ontario Building Code "
            f"(O. Reg. 332/12), Toronto Municipal Code Chapter 813, and related "
            f"regulatory standards.",
            s["Body"],
        ))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "This response document includes:",
            s["Body"],
        ))
        elements.append(Paragraph(
            "• Itemized responses to each deficiency, in the order listed in the Examiner's Notice<br/>"
            "• Regulatory citations supporting each response<br/>"
            "• Resolution classification for each item (Resolved / Drawing Revision / Variance Required)<br/>"
            "• A revision summary identifying drawing pages requiring resubmission",
            s["Body"],
        ))
        elements.append(Spacer(1, 6))

        # Category breakdown mini-table
        by_cat = summary.get("by_category", {})
        if by_cat:
            elements.append(Paragraph("<b>Deficiency Summary by Category:</b>", s["ItemTitle"]))
            cat_data = [[
                Paragraph("Category", s["TableHeader"]),
                Paragraph("Count", s["TableHeader"]),
            ]]
            for cat, count in by_cat.items():
                cat_data.append([
                    Paragraph(CATEGORY_LABELS.get(cat, cat), s["TableCell"]),
                    Paragraph(str(count), s["TableCell"]),
                ])
            cat_table = Table(cat_data, colWidths=[4.0 * inch, 1.0 * inch])
            cat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), CITY_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), GREY_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, GREY_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, GREY_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(cat_table)
            elements.append(Spacer(1, 12))

        elements.append(Paragraph(
            "We trust these revisions address the identified deficiencies and "
            "respectfully request the continuation of the permit review process.",
            s["Body"],
        ))
        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Respectfully submitted,", s["Body"]))
        elements.append(Spacer(1, 24))
        elements.append(Paragraph(
            "<i>PermitPulse Toronto — AI-Assisted Response</i>",
            s["BodySm"],
        ))

        return elements

    # ── Itemized Deficiency Responses ───────────────────────────────────
    def _deficiency_responses(self) -> list:
        s = self.styles
        elements = []

        elements.append(Paragraph(
            "ITEMIZED DEFICIENCY RESPONSES", s["SectionTitle"],
        ))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=CITY_BLUE, spaceAfter=8,
        ))

        results = self.data.get("results", [])
        for idx, result in enumerate(results, 1):
            deficiency = result.get("deficiency", {})
            response = result.get("response", {})
            agent = result.get("agent", "AI Agent")
            error = result.get("error")

            category = deficiency.get("category", "OTHER")
            cat_label = CATEGORY_LABELS.get(category, category)
            status = response.get("resolution_status", "OUT_OF_SCOPE") if response else "OUT_OF_SCOPE"
            status_label = STATUS_LABELS.get(status, status)
            status_color = STATUS_COLOURS.get(status, TEXT_MUTED)

            # Item header
            elements.append(Paragraph(
                f"<b>Item {idx} — {cat_label}</b>",
                ParagraphStyle(
                    f"ItemHead{idx}", parent=s["ItemTitle"],
                    textColor=CITY_BLUE, spaceBefore=12,
                ),
            ))

            # Status badge line
            elements.append(Paragraph(
                f'<font color="{status_color.hexval()}">'
                f'■ {status_label}</font>'
                f'  ·  <font color="{TEXT_MUTED.hexval()}">Agent: {agent}</font>',
                s["BodySm"],
            ))

            # Original notice text
            raw = deficiency.get("raw_notice_text", "")
            if raw:
                elements.append(Paragraph(
                    f"<b>Examiner's Notice:</b>", s["BodySm"],
                ))
                # Wrap long text
                wrapped = raw[:600] + ("…" if len(raw) > 600 else "")
                elements.append(Paragraph(
                    f"<i>\"{wrapped}\"</i>", s["Body"],
                ))

            # Extracted action
            action = deficiency.get("extracted_action", "")
            if action:
                elements.append(Paragraph(
                    f"<b>Required Action:</b> {action}", s["Body"],
                ))

            # Draft response
            if response and response.get("draft_text"):
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(
                    "<b>Response:</b>", s["BodySm"],
                ))

                # Response in a subtle box
                resp_text = response["draft_text"]
                resp_data = [[Paragraph(resp_text, s["Body"])]]
                resp_table = Table(resp_data, colWidths=[6.5 * inch])
                resp_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), GREY_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, GREY_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]))
                elements.append(resp_table)

            # Citations
            citations = response.get("citations", []) if response else []
            if citations:
                cite_strs = []
                for c in citations:
                    bylaw = c.get("bylaw", "")
                    section = c.get("section", "")
                    cite_strs.append(f"{bylaw} §{section}")
                elements.append(Paragraph(
                    "<b>Citations:</b> " + " | ".join(cite_strs),
                    s["Citation"],
                ))

            # Variance magnitude
            variance = response.get("variance_magnitude") if response else None
            if variance:
                elements.append(Paragraph(
                    f'<font color="{ACCENT_RED.hexval()}">'
                    f"<b>Variance Magnitude:</b> {variance}</font>",
                    s["BodySm"],
                ))

            # Error state
            if error:
                elements.append(Paragraph(
                    f'<font color="{ACCENT_RED.hexval()}">'
                    f"<b>Processing Error:</b> {error}</font>",
                    s["BodySm"],
                ))

            # Separator
            elements.append(Spacer(1, 4))
            elements.append(HRFlowable(
                width="100%", thickness=0.5, color=GREY_BORDER, spaceAfter=4,
            ))

        # Unhandled items
        unhandled = self.data.get("unhandled", [])
        if unhandled:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(
                f"UNHANDLED ITEMS ({len(unhandled)})", s["SectionTitle"],
            ))
            for item in unhandled:
                d = item.get("deficiency", {})
                elements.append(Paragraph(
                    f"• [{d.get('category', 'OTHER')}] {d.get('raw_notice_text', '')[:200]}",
                    s["Body"],
                ))
                elements.append(Paragraph(
                    f"  Reason: {item.get('reason', 'N/A')}", s["BodySm"],
                ))

        return elements

    # ── Revision Summary ────────────────────────────────────────────────
    def _revision_summary(self) -> list:
        s = self.styles
        elements = []

        elements.append(Paragraph(
            "REVISION SUMMARY", s["SectionTitle"],
        ))
        elements.append(HRFlowable(
            width="100%", thickness=1, color=CITY_BLUE, spaceAfter=8,
        ))
        elements.append(Paragraph(
            "The following table summarizes the resolution status of each "
            "deficiency item identified in the Examiner's Notice.",
            s["Body"],
        ))
        elements.append(Spacer(1, 6))

        # Build summary table
        header = [
            Paragraph("#", s["TableHeader"]),
            Paragraph("Category", s["TableHeader"]),
            Paragraph("Action Required", s["TableHeader"]),
            Paragraph("Status", s["TableHeader"]),
        ]
        table_data = [header]

        results = self.data.get("results", [])
        for idx, result in enumerate(results, 1):
            d = result.get("deficiency", {})
            r = result.get("response", {})
            status = r.get("resolution_status", "OUT_OF_SCOPE") if r else "OUT_OF_SCOPE"
            status_label = STATUS_LABELS.get(status, status)
            status_color = STATUS_COLOURS.get(status, TEXT_MUTED)
            category = CATEGORY_LABELS.get(d.get("category", "OTHER"), "Other")
            action = d.get("extracted_action", "N/A")
            # Truncate action for table
            if len(action) > 80:
                action = action[:77] + "…"

            table_data.append([
                Paragraph(str(idx), s["TableCell"]),
                Paragraph(category, s["TableCell"]),
                Paragraph(action, s["TableCell"]),
                Paragraph(
                    f'<font color="{status_color.hexval()}">'
                    f"<b>{status_label}</b></font>",
                    s["TableCell"],
                ),
            ])

        summary_table = Table(
            table_data,
            colWidths=[0.4 * inch, 1.2 * inch, 3.5 * inch, 1.9 * inch],
        )
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CITY_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GREY_LIGHT]),
            ("BOX", (0, 0), (-1, -1), 0.75, GREY_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, GREY_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 16))

        # Stats
        summary_data = self.data.get("summary", {})
        processed = summary_data.get("processed", 0)
        total = summary_data.get("total_deficiencies", 0)
        elements.append(Paragraph(
            f"<b>{processed}</b> of <b>{total}</b> deficiency items have been "
            f"addressed in this response package.",
            s["Body"],
        ))

        return elements

    # ── Disclaimer ──────────────────────────────────────────────────────
    def _disclaimer(self) -> list:
        s = self.styles
        elements = []

        elements.append(Spacer(1, 24))
        elements.append(HRFlowable(
            width="100%", thickness=1.5, color=ACCENT_RED, spaceAfter=8,
        ))
        elements.append(Paragraph(
            "PROFESSIONAL LIABILITY DISCLAIMER", s["SectionTitle"],
        ))
        elements.append(Paragraph(
            "This document was generated by PermitPulse Toronto, an AI-powered "
            "permit correction response system. The responses, citations, and "
            "analysis contained herein were produced by artificial intelligence "
            "and have NOT been reviewed by a licensed architect, professional "
            "engineer, or Ontario Land Surveyor.",
            s["Disclaimer"],
        ))
        elements.append(Paragraph(
            "This document is provided for INFORMATIONAL PURPOSES ONLY and does "
            "not constitute professional advice. Before submitting any response "
            "to the City of Toronto Plans Examination Branch, the applicant must "
            "have all proposed revisions reviewed and stamped by the appropriate "
            "licensed professional(s) as required by the Ontario Building Code "
            "Act, 1992 and the Professional Engineers Act.",
            s["Disclaimer"],
        ))
        elements.append(Paragraph(
            "PermitPulse Toronto, its developers, and affiliates accept no "
            "liability for any decisions made or actions taken based on the "
            "content of this document. Regulatory requirements are subject to "
            "change; always verify against the current applicable by-laws and "
            "codes.",
            s["Disclaimer"],
        ))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            f"Document generated: {self.now.strftime('%B %d, %Y at %H:%M UTC')}",
            s["BodySm"],
        ))

        return elements
