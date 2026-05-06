import logging
from fpdf import FPDF
from datetime import datetime
import pandas as pd
from typing import List, Dict, Optional
import io

logger = logging.getLogger(__name__)

class ExecutiveReportPDF(FPDF):
    def header(self):
        # Logo placeholder
        self.set_font('Arial', 'B', 15)
        self.set_text_color(26, 26, 46)
        self.cell(0, 10, 'AI Customer Intelligence Engine - Executive Report', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(company_name: str, 
                        summary: str, 
                        sentiment_counts: Dict, 
                        aspects: List[Dict], 
                        alerts: List[Dict]) -> bytes:
    """Generates a PDF executive report and returns the bytes."""
    pdf = ExecutiveReportPDF()
    pdf.add_page()
    
    # 1. Overview Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Analysis Overview: {company_name}', 0, 1)
    pdf.ln(5)
    
    # 2. AI Summary
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'AI Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 11)
    # Convert markdown-like summary to plain text if needed, but FPDF handles simple strings
    pdf.multi_cell(0, 7, summary.replace('**', '').replace('#', ''))
    pdf.ln(10)
    
    # 3. Sentiment Distribution
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Sentiment Distribution', 0, 1)
    pdf.set_font('Arial', '', 11)
    total = sum(sentiment_counts.values())
    for label, count in sentiment_counts.items():
        pct = (count / total * 100) if total > 0 else 0
        pdf.cell(0, 7, f"- {label.capitalize()}: {count} ({pct:.1f}%)", 0, 1)
    pdf.ln(10)
    
    # 4. Key Aspects
    if aspects:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Top Business Aspects', 0, 1)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(50, 7, 'Aspect', 1)
        pdf.cell(30, 7, 'Score', 1)
        pdf.cell(110, 7, 'Notes', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 10)
        for a in aspects[:5]: # Top 5
            pdf.cell(50, 7, a.get('aspect', 'N/A'), 1)
            pdf.cell(30, 7, f"{a.get('score', 0):.2f}", 1)
            pdf.cell(110, 7, a.get('summary', 'N/A'), 1)
            pdf.ln()
        pdf.ln(10)
        
    # 5. Active Alerts
    if alerts:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(231, 76, 60) # Red for alerts
        pdf.cell(0, 10, 'CRITICAL ALERTS (Pressure Radar)', 0, 1)
        pdf.set_font('Arial', '', 11)
        for alert in alerts:
            pdf.multi_cell(0, 7, f"!!! {alert['keyword'].upper()} Surge: {alert['pressure_score']}x normal baseline")
        pdf.ln(10)

    # Return as bytes
    return pdf.output(dest='S')
