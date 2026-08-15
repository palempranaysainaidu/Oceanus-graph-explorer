"""
Generate a professional PDF document introducing the Oceanus Agentic RAG Project.
"""

import os
import sys

def build_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    except ImportError:
        print("ReportLab is not installed yet.")
        return False

    pdf_filename = os.path.join(os.path.dirname(__file__), "Oceanus_Project_Overview.pdf")
    doc = SimpleDocTemplate(
        pdf_filename,
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
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        alignment=TA_CENTER,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        alignment=TA_LEFT,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeCustom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#090D16'),
        spaceAfter=4
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("🌊 Oceanus Agentic RAG Platform", title_style))
    story.append(Paragraph("Oceanographic Data Intelligence & Multi-Agent RAG Architecture Overview", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    exec_summary_text = (
        "<b>Oceanus</b> is an enterprise-grade AI platform designed for marine researchers, oceanographers, "
        "and climate scientists to explore, query, and visualize global <b>Argo Float ocean measurement datasets</b>. "
        "By replacing complex SQL and GIS workflows with natural language conversation, users can instantly "
        "analyze sea surface temperature anomalies, salinity profiles, and underwater pressure depth metrics across the world's oceans."
    )
    story.append(Paragraph(exec_summary_text, body_style))

    # 2. Core Features & Capabilities
    story.append(Paragraph("2. Key Features & Capabilities", h1_style))
    features = [
        "<b>Natural Language Ocean Querying:</b> Ask plain-English questions about float measurements, regional thermal patterns, or depth profiles.",
        "<b>Multi-Agent RAG Intelligence:</b> Coordinated suite of specialized LLM agents (Router, DB Tool Agent, Vector RAG Agent, Quality Evaluator).",
        "<b>Conversational Session Memory:</b> Remembers float IDs (e.g. <i>7902073</i>), regions discussed (<i>Arabian Sea</i>), and detail level preferences across multi-turn chats.",
        "<b>Interactive Geospatial Mapping:</b> Real-time Leaflet map displaying active float locations, pulsating markers, and depth trajectory popups.",
        "<b>Depth Profile Visualization:</b> Recharts graphics rendering Temperature (°C), Salinity (PSS), and Pressure (dbar) vs. depth and time.",
        "<b>Resilient Fallback Mode:</b> Operates with zero downtime by automatically loading local CSV datasets (88 floats, 460,000+ data rows) when offline."
    ]
    for feat in features:
        story.append(Paragraph(f"• {feat}", bullet_style))

    story.append(Spacer(1, 10))

    # 3. Technical Architecture
    story.append(Paragraph("3. Technical Architecture", h1_style))
    
    arch_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology / Framework</b>", body_style), Paragraph("<b>Role / Functionality</b>", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("Next.js 15, React 19, TailwindCSS", body_style), Paragraph("Interactive Dashboard, AI Chat Sidebar, Glassmorphism UI", body_style)],
        [Paragraph("Geospatial Map", body_style), Paragraph("Leaflet.js, Recharts, Three.js", body_style), Paragraph("Float cluster markers, trajectory popups, depth graphs", body_style)],
        [Paragraph("Backend Server", body_style), Paragraph("FastAPI, Uvicorn, Python 3.13", body_style), Paragraph("Unified REST API for Chat, Sessions, Metrics & Float Data", body_style)],
        [Paragraph("Multi-Agent Core", body_style), Paragraph("LangChain, Groq, OpenAI LLMs", body_style), Paragraph("Multi-cycle reasoning, quality evaluation, agent orchestration", body_style)],
        [Paragraph("Database / RAG", body_style), Paragraph("CockroachDB, Neo4j, Pinecone, CSV", body_style), Paragraph("Time-series measurements, graph relations, vector RAG", body_style)]
    ]
    
    t = Table(arch_data, colWidths=[110, 160, 240])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 12))

    # 4. System Endpoints & Verification
    story.append(Paragraph("4. System Endpoints & Quick Start", h1_style))
    endpoints = [
        "<b>Web Application Interface:</b> http://localhost:9002",
        "<b>Unified FastAPI Server:</b> http://localhost:8000",
        "<b>ReDoc Interactive API Specs:</b> http://localhost:8000/redoc",
        "<b>Float Map Data Stream:</b> http://localhost:8000/api/floats",
        "<b>System Health Check:</b> http://localhost:8000/health"
    ]
    for ep in endpoints:
        story.append(Paragraph(f"• {ep}", bullet_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Unified Start Command:</b>", body_style))
    story.append(Paragraph("<font name='Courier'>python start_app.py</font> &nbsp;&nbsp;(or double click <b>start_oceanus.bat</b>)", bullet_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94A3B8'), spaceAfter=8))
    story.append(Paragraph("Generated by Antigravity AI Assistant | Oceanus Agentic RAG Platform v1.0.0", ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#64748B'), alignment=TA_CENTER)))

    doc.build(story)
    print(f"PDF successfully generated at: {pdf_filename}")
    return True

if __name__ == "__main__":
    build_pdf()
