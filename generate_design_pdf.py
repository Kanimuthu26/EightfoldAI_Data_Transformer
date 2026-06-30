import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf():
    # File Path
    pdf_filename = "Surya_Sekhar_surya@example.com_Eightfold.pdf"
    
    # Setup document: letter size, 0.5 inch margins to ensure it fits exactly on 1 page
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    # Theme colors
    primary_color = colors.HexColor("#1e293b")   # Slate 800
    secondary_color = colors.HexColor("#4f46e5") # Indigo 600
    text_color = colors.HexColor("#334155")      # Slate 700
    
    # Base modifications
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=secondary_color,
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=12,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=5,
        borderPadding=(0, 0, 1, 0),
        borderColor=secondary_color,
        borderWidth=0.5
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=text_color,
        spaceAfter=5
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Candidate Data Unification Pipeline — Design Specification", title_style))
    story.append(Paragraph("Author: Surya Sekhar  |  Email: surya@example.com  |  Eightfold Engineering Intern Assignment", meta_style))

    # Section 1: Architecture
    story.append(Paragraph("1. Three-Layer Extensible Architecture", h2_style))
    story.append(Paragraph(
        "<b>Layer 1 — Ingestion:</b> Built on a dynamic adapter registry pattern. The abstract <i>SourceAdapter</i> exposes <i>detect()</i> and <i>extract() -> list[RawRecord]</i>. "
        "Adapters for Recruiter CSV, ATS JSON, PDF/Docx Resume (using <i>pypdf/docx</i>), notes, LinkedIn/GitHub URLs run isolated. A failure in an adapter returns an empty list, allowing other sources to merge without crashing the engine. New sources require zero changes to core engine logic.", body_style))
    story.append(Paragraph(
        "<b>Layer 2 — Engine:</b> Orchestrates data through a sequential, decoupled stage pipeline: <i>Normalize -> Match -> Merge -> Confidence</i>. "
        "Identity matching executes in <b>linear O(N) time complexity</b> by building indexes of emails and normalized phones, eliminating nested pairwise comparison.", body_style))
    story.append(Paragraph(
        "<b>Layer 3 — Output/Projection:</b> Completely decoupled presentation layer. Resolves nested data paths (e.g. <i>skills[].name</i>, <i>emails[0]</i>), renames fields, applies inline normalizers, and validates the output against configuration schemas. Prevents server crashes on invalid data by replacing failing types with <i>null</i>.", body_style))

    # Section 2: Canonical Schema & Normalization
    story.append(Paragraph("2. Canonical Schema & Field Normalization Rules", h2_style))
    story.append(Paragraph(
        "Ingested fields are normalized into uniform formats before resolving conflicts:", body_style))
    
    schema_data = [
        [
            Paragraph("<b>Field Name</b>", body_style),
            Paragraph("<b>Canonical Type</b>", body_style),
            Paragraph("<b>Normalization Rules / Formats</b>", body_style)
        ],
        [
            Paragraph("emails / phones", body_style),
            Paragraph("string[]", body_style),
            Paragraph("Emails: case-insensitive. Phones: E.164 (+[Country][Digits]) with US fallback (+1).", body_style)
        ],
        [
            Paragraph("location / links", body_style),
            Paragraph("object", body_style),
            Paragraph("Location: {city, region, country: ISO-3166 alpha-2}. Links: {linkedin, github, portfolio, other}.", body_style)
        ],
        [
            Paragraph("experience / education", body_style),
            Paragraph("object[]", body_style),
            Paragraph("Experience: start/end as YYYY-MM or 'Present'. Education: end_year as YYYY integer.", body_style)
        ],
        [
            Paragraph("skills", body_style),
            Paragraph("object[]", body_style),
            Paragraph("Canonicalized name via synonym lookup table (e.g., js/javascript -> JavaScript). Confidence score attached.", body_style)
        ]
    ]
    t = Table(schema_data, colWidths=[1.3*inch, 1.1*inch, 4.6*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

    # Section 3: Match & Merge Conflict Resolution
    story.append(Paragraph("3. Identity Matching & Merge Rules", h2_style))
    story.append(Paragraph(
        "• <b>Identity Resolution:</b> Case-insensitive email is the primary key. If email is absent on either side, matching falls back to normalized phone. Names are never used as a sole key. If neither email nor phone is present, profiles stand alone.", bullet_style))
    story.append(Paragraph(
        "• <b>Priority-Based Conflict Resolution:</b> Fully configurable source precedence (default: <i>ATS JSON > Recruiter CSV > Resume > Notes</i>). "
        "A missing field in a higher-priority source never blocks lower-priority data from merging.", bullet_style))
    story.append(Paragraph(
        "• <b>Confidence Scoring:</b> Calculated as a weighted average across populated fields, weighted toward identity fields. Individual field confidence increases with corroboration (multiple agreeing sources) and source authority weights.", bullet_style))
    story.append(Paragraph(
        "• <b>Provenance:</b> Tracks origin metadata for every field (supplied source and extraction method), persisting independently of confidence.", bullet_style))

    # Section 4: Runtime Config & Edge Cases
    story.append(Paragraph("4. Runtime Projection Config & Handled Edge Cases", h2_style))
    story.append(Paragraph(
        "<b>Projection Config:</b> Users pass a JSON configuration mapping output keys to canonical paths (e.g. <i>\"primary_email\": \"emails[0]\"</i>), setting missing policies (<i>null / omit / error</i>), and toggling confidence/provenance visibility.", body_style))
    
    story.append(Paragraph(
        "• <b>Duplicate Names:</b> Two candidates sharing a name with no email/phone will not match; they are kept separate.", bullet_style))
    story.append(Paragraph(
        "• <b>Empty Identifiers:</b> Sources with no email/phone are still ingested and stored as separate candidate profiles, rather than skipped.", bullet_style))
    story.append(Paragraph(
        "• <b>Inconsistent Spellings:</b> Skills like 'JS' and 'java script' normalize to 'JavaScript' before merging to prevent duplicate entries.", bullet_style))
    story.append(Paragraph(
        "• <b>Conflicting Emails:</b> Different emails with no shared phone will not auto-merge, creating separate profiles to prevent bad data blending.", bullet_style))
    story.append(Paragraph(
        "• <b>Out of Scope:</b> Fuzzy name matching, ML-based matching, and web scraping bypassing credentials are descope-declared for reliability.", bullet_style))

    doc.build(story)
    print(f"Successfully generated technical design PDF: {pdf_filename}")

if __name__ == "__main__":
    generate_pdf()
