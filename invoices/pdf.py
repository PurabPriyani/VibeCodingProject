"""
Builds the invoice as a PDF so it can be attached to emails.

ReportLab draws the PDF directly in Python, so there's nothing extra to
install on Windows (no browser engine or system libraries). The layout
follows the invoice page in the app: business on the left, invoice
number on the right, then the client, the line items and the totals.
"""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK = colors.HexColor("#1d2129")
MUTED = colors.HexColor("#8a909c")
SOFT = colors.HexColor("#5b6270")
LINE = colors.HexColor("#e6e3dc")
MINT = colors.HexColor("#0f8a6a")
PANEL = colors.HexColor("#f2f0ea")

body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=14, textColor=SOFT)
strong = ParagraphStyle("strong", parent=body, fontName="Helvetica-Bold", textColor=INK)
label = ParagraphStyle("label", parent=body, fontName="Helvetica-Bold", fontSize=7.5, textColor=MUTED)
business_name = ParagraphStyle("business", parent=body, fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=INK)
title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=MINT, alignment=TA_RIGHT)
right = ParagraphStyle("right", parent=body, alignment=TA_RIGHT)


def _money(value):
    return f"${value:,.2f}"


def _text(value):
    # Paragraphs read a little markup, so a name like "Pine & Co." has to be
    # escaped or ReportLab treats the & as the start of a tag.
    return escape(str(value))


def _lines(*parts):
    """Join the non-empty parts with line breaks, for addresses and contact details."""
    kept = []
    for part in parts:
        if part:
            kept.append(_text(part).replace("\n", "<br/>"))
    return "<br/>".join(kept)


def build_invoice_pdf(invoice, business):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {invoice.number}",
        author=business.name,
    )
    width = doc.width
    story = []

    # Header: who it's from, and the invoice number.
    header = Table(
        [[
            [Paragraph(_text(business.name), business_name), Paragraph(_lines(business.address, business.email, business.phone), body)],
            [Paragraph("Invoice", title), Paragraph(invoice.number, right)],
        ]],
        colWidths=[width * 0.6, width * 0.4],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, LINE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header)
    story.append(Spacer(1, 16))

    # Who it's for, and the dates.
    client = invoice.client
    bill_to = [
        Paragraph("BILL TO", label),
        Spacer(1, 4),
        Paragraph(_text(client.company or client.name), strong),
        Paragraph(_lines(client.name if client.company else "", client.address, client.email), body),
    ]
    dates = Table(
        [
            [Paragraph("Issued", body), Paragraph(invoice.issue_date.strftime("%b %d, %Y"), right)],
            [Paragraph("Due", body), Paragraph(invoice.due_date.strftime("%b %d, %Y"), right)],
            [Paragraph("Terms", body), Paragraph(invoice.get_terms_display(), right)],
        ],
        colWidths=[width * 0.14, width * 0.22],
    )
    dates.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    meta = Table([[bill_to, dates]], colWidths=[width * 0.64, width * 0.36])
    meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(meta)
    story.append(Spacer(1, 20))

    # Line items.
    rows = [[
        Paragraph("DESCRIPTION", label),
        Paragraph("QTY", ParagraphStyle("lr", parent=label, alignment=TA_RIGHT)),
        Paragraph("PRICE", ParagraphStyle("lr", parent=label, alignment=TA_RIGHT)),
        Paragraph("AMOUNT", ParagraphStyle("lr", parent=label, alignment=TA_RIGHT)),
    ]]
    for item in invoice.items.all():
        rows.append([
            Paragraph(_text(item.description), ParagraphStyle("d", parent=body, textColor=INK)),
            Paragraph(f"{item.quantity.normalize():f}", right),
            Paragraph(_money(item.unit_price), right),
            Paragraph(_money(item.line_total), right),
        ])
    items = Table(rows, colWidths=[width * 0.52, width * 0.12, width * 0.18, width * 0.18], repeatRows=1)
    items.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, LINE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#efece6")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(items)
    story.append(Spacer(1, 12))

    # Totals, lined up on the right.
    tax_label = "HST"
    if invoice.tax_rate:
        tax_label = f"HST ({invoice.tax_rate.normalize():f}%)"
    grand = ParagraphStyle("grand", parent=strong, fontSize=11.5)
    grand_right = ParagraphStyle("grand_r", parent=grand, alignment=TA_RIGHT)
    totals = Table(
        [
            [Paragraph("Subtotal", body), Paragraph(_money(invoice.subtotal), right)],
            [Paragraph(tax_label, body), Paragraph(_money(invoice.tax_amount), right)],
            [Paragraph("Total due", grand), Paragraph(f"{_money(invoice.total)} CAD", grand_right)],
        ],
        colWidths=[width * 0.2, width * 0.24],
        hAlign="RIGHT",
    )
    totals.setStyle(TableStyle([
        ("LINEABOVE", (0, 2), (-1, 2), 1.4, INK),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 2), (-1, 2), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(totals)

    if invoice.notes:
        story.append(Spacer(1, 22))
        notes = Table(
            [[[Paragraph("NOTES", label), Spacer(1, 3), Paragraph(_lines(invoice.notes), body)]]],
            colWidths=[width],
        )
        notes.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(notes)

    def footer(canvas, document):
        if business.hst_number:
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(MUTED)
            canvas.drawCentredString(LETTER[0] / 2, 12 * mm, f"HST registration {business.hst_number}")
            canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
