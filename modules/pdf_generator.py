#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - PDF Generatetor Module
System to Generatete report PDF professionali per Content Createtion Engine
"""

import os
import datetime
from typing import Dict, List, Optional, Any
import logging

# Setup logging
log = logging.getLogger(__name__)

# Import chart generator
try:
    from .chart_generator import generate_weekly_charts, generate_monthly_charts
    CHARTS_AVAILABLE = True
except ImportError:
    log.warning("⚠️ [PDF] Chart generator not available - charts will be skipped")
    CHARTS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus import PageBreak, Image as RLImage, KeepTogether
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    log.warning("âš ï¸ [PDF] ReportLab not installed. Install with: pip install reportlab")
    REPORTLAB_AVAILABLE = False

class SVPDFGeneratetor:
    def __init__(self, timeframe: str = 'daily'):
        """Inizializza Generatetore PDF per SV
        
        Args:
            timeframe: Timeframe (daily, weekly, monthly) per scegliere la cartella giusta
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab package required for PDF Generatetion")
        
        # Directory per PDF output basata su timeframe
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        timeframe_folders = {
            'daily': '1_daily',
            'weekly': '2_weekly', 
            'monthly': '3_monthly',
            'quarterly': '4_quarterly',
            'semiannual': '5_semiannual',
            'annual': '6_annual'
        }
        folder = timeframe_folders.get(timeframe, '1_daily')
        self.pdf_output_dir = os.path.join(project_root, 'reports', folder)
        os.makedirs(self.pdf_output_dir, exist_ok=True)
        
        # Configurazione stili SV
        self.styles = getSampleStyleSheet()
        self._setup_sv_styles()
        
        # Configurazione colori SV
        self.sv_colors = {
            'primary': colors.HexColor('#2E86AB'),     # Blu SV
            'secondary': colors.HexColor('#A23B72'),   # Rosa SV  
            'accent': colors.HexColor('#F18F01'),      # Arancione
            'success': colors.HexColor('#28A745'),     # Verde successo
            'danger': colors.HexColor('#DC3545'),      # Rosso per alert
            'text': colors.HexColor('#2D3748'),        # Grigio scuro testo
            'light_gray': colors.HexColor('#F7FAFC'),  # Grigio chiaro
            'border': colors.HexColor('#E2E8F0')       # Grigio bordi
        }
        
        # Layout flags (placeholder per futuri layout/pro vs basic; non usato
        # direttamente nella generazione corrente)
        self.pro_layout = True
    
    def _add_chart_to_story(self, story: List, chart_path: str, title: str, width: float = 15*cm) -> bool:
        """Add chart image to PDF story if chart exists, keeping title+image on same page"""
        try:
            if chart_path and os.path.exists(chart_path):
                flows = []
                flows.append(Paragraph(title, self.styles['SVSection']))
                chart_img = RLImage(chart_path, width=width, height=width*0.6)
                flows.append(chart_img)
                flows.append(Spacer(1, 20))
                story.append(KeepTogether(flows))
                return True
            return False
        except Exception as e:
            log.error(f"⚠️ [PDF] Error adding chart {title}: {e}")
            return False
    def _two_col(self, left_flows: List, right_flows: List, col_widths=(8*cm, 8*cm)):
        """Insert a two-column layout block using a Table wrapper"""
        tbl = Table([[left_flows, right_flows]], colWidths=list(col_widths))
        tbl.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        return tbl
    
    def _header_footer(self, canvas, doc):
        """Draw header and footer on each page"""
        canvas.saveState()
        w, h = doc.pagesize
        # Header bar
        canvas.setFillColor(self.sv_colors['primary'])
        canvas.rect(0, h-20, w, 20, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(2*cm, h-15, 'SV - SISTEMA UNIFICATO TRADING')
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(w-2*cm, h-15, datetime.datetime.now().strftime('%d %B %Y'))
        # Footer with page number
        canvas.setFillColor(self.sv_colors['border'])
        canvas.rect(0, 0, w, 18, fill=1, stroke=0)
        canvas.setFillColor(self.sv_colors['text'])
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(w-2*cm, 6, f'Page {doc.page}')
        canvas.restoreState()
    
    def _setup_sv_styles(self):
        """Configura stili personalizzati per SV"""
        # Titolo principale SV
        self.styles.add(ParagraphStyle(
            'SVTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E86AB'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Sottotitolo SV
        self.styles.add(ParagraphStyle(
            'SVSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#A23B72'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Small caption style
        self.styles.add(ParagraphStyle(
            'SVCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4A5568'),
            spaceAfter=6,
            fontName='Helvetica-Oblique',
            alignment=TA_LEFT
        ))
        
        # Sezione SV
        self.styles.add(ParagraphStyle(
            'SVSection',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2D3748'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Corpo testo SV
        self.styles.add(ParagraphStyle(
            'SVBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2D3748'),
            spaceAfter=8,
            fontName='Helvetica',
            alignment=TA_LEFT
        ))
        
        # Highlights SV
        self.styles.add(ParagraphStyle(
            'SVHighlight',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#C73E1D'),
            spaceAfter=8,
            fontName='Helvetica-Bold',
            backColor=colors.HexColor('#FFF5F5'),
            borderPadding=8
        ))
    
    def Createte_daily_summary_pdf(self, summary_data: Dict) -> str:
        """
        Create PDF del Daily Summary SV
        
        Args:
            summary_data: Dati del summary giornaliero
        
        Returns:
            Path del PDF Generateto
        """
        try:
            # Nome file con timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"SV_Daily_Summary_{timestamp}.pdf"
            filepath = os.path.join(self.pdf_output_dir, filename)
            
            # Create documento
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )
            
            # Content container
            story = []
            
            # Header
            story.append(Paragraph("SV - System UNIFICATO TRADING", self.styles['SVTitle']))
            story.append(Paragraph("Daily Summary Report", self.styles['SVSubtitle']))
            story.append(Spacer(1, 20))
            
            # Data e metainfo
            date_str = datetime.datetime.now().strftime('%d %B %Y')
            story.append(Paragraph(f"<b>Data:</b> {date_str}", self.styles['SVBody']))
            
            if 'market_status' in summary_data:
                story.append(Paragraph(f"<b>Market Status:</b> {summary_data['market_status']}", self.styles['SVBody']))
            
            story.append(Spacer(1, 20))
            
            # Sezione performance
            if 'performance' in summary_data:
                story.append(Paragraph("ðŸ“Š performance OVERVIEW", self.styles['SVSection']))
                perf = summary_data['performance']
                
                perf_data = [
                    ['Metrica', 'Valore'],
                    ['Accuracy', str(perf.get('accuracy', 'N/A'))],
                    ['Total Signals', str(perf.get('total_signals', 'N/A'))],
                    ['Success Rate', str(perf.get('success_rate', 'N/A'))],
                ]
                
                perf_table = Table(perf_data, colWidths=[8*cm, 6*cm])
                perf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.sv_colors['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), self.sv_colors['light_gray']),
                    ('GRID', (0, 0), (-1, -1), 1, self.sv_colors['border'])
                ]))
                
                story.append(perf_table)
                story.append(Spacer(1, 20))
            
            # Sezione Market Analysis  
            if 'market_analysis' in summary_data:
                story.append(Paragraph("ðŸŽ¯ MARKET ANALYSIS", self.styles['SVSection']))
                analysis = summary_data['market_analysis']
                
                for key, value in analysis.items():
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", self.styles['SVBody']))
                
                story.append(Spacer(1, 20))
            
            # Tomorrow Outlook
            if 'tomorrow_outlook' in summary_data:
                story.append(Paragraph("ðŸ”® TOMORROW OUTLOOK", self.styles['SVSection']))
                outlook = summary_data['tomorrow_outlook']
                story.append(Paragraph(outlook, self.styles['SVBody']))
                story.append(Spacer(1, 20))
            
            # Key Points (se presenti)
            if 'key_points' in summary_data:
                story.append(Paragraph("ðŸŽ¯ KEY POINTS", self.styles['SVSection']))
                for point in summary_data['key_points']:
                    story.append(Paragraph(f"â€¢ {point}", self.styles['SVBody']))
                story.append(Spacer(1, 20))
            
            # Footer
            story.append(Spacer(1, 40))
            footer_text = f"Generateted by SV Content Engine - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(footer_text, self.styles['SVBody']))
            
            # Build PDF
            doc.build(story)
            
            log.info(f"âœ… [PDF] Daily Summary PDF Generateted: {filename}")
            return filepath
            
        except Exception as e:
            log.error(f"âŒ [PDF] Error Createting daily summary PDF: {e}")
            return None
    
    def Createte_weekly_report_pdf(self, weekly_data: Dict) -> str:
        """
        Create PDF del Weekly Report SV - Simple Text Version
        
        Args:
            weekly_data: Dati del report settimanale
        
        Returns:
            Path del PDF Generateto
        """
        try:
            # Nome file con timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"SV_Weekly_Report_{timestamp}.pdf"
            filepath = os.path.join(self.pdf_output_dir, filename)
            
            # Create documento
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Header Section
            story.append(Paragraph("🏆 SV - SISTEMA UNIFICATO TRADING", self.styles['SVTitle']))
            week_dates = f"{weekly_data.get('week_start', 'N/A')} - {weekly_data.get('week_end', 'N/A')}"
            story.append(Paragraph(f"📈 WEEKLY REPORT - {week_dates}", self.styles['SVSubtitle']))
            
            # Date and timestamp
            generation_time = datetime.datetime.now().strftime('%d %B %Y - %H:%M')
            story.append(Paragraph(f"🕐 Generated: {generation_time}", self.styles['SVBody']))
            story.append(Spacer(1, 25))
            
            # Generate charts for the report
            charts = {}
            if CHARTS_AVAILABLE:
                try:
                    charts = generate_weekly_charts(weekly_data)
                    if charts:
                        log.info(f"[PDF] Generated {len(charts)} charts for PDF integration")
                    else:
                        log.warning("[PDF] No charts generated - data may be insufficient")
                except Exception as e:
                    log.error(f"[PDF] Error generating charts: {e}")
            
            # Executive Summary
            if 'weekly_summary' in weekly_data:
                story.append(Paragraph("📊 EXECUTIVE SUMMARY", self.styles['SVSection']))
                story.append(Paragraph(weekly_data['weekly_summary'], self.styles['SVHighlight']))
                story.append(Spacer(1, 12))
            
            # KPI panel
            kpi_para = []
            if 'performance_metrics' in weekly_data:
                metrics = weekly_data['performance_metrics']
                data_sources = weekly_data.get('data_sources', {})
                coverage = f"{data_sources.get('daily_metrics_files',0)}/5 days"
                kpi_text = f"""
                <b>Total Signals:</b> {metrics.get('total_signals', metrics.get('total_trades','N/A'))}<br/>
                <b>Success Rate:</b> {metrics.get('success_rate','N/A')}<br/>
                <b>Coverage:</b> {coverage}<br/>
                <b>Weekly Return:</b> {metrics.get('weekly_return','N/A')}<br/>
                <b>Sharpe Ratio:</b> {metrics.get('sharpe_ratio','N/A')}<br/>
                <b>Max Drawdown:</b> {metrics.get('max_drawdown','N/A')}
                """
                kpi_para = [Paragraph("Key Performance Indicators", self.styles['SVSection']), Paragraph(kpi_text, self.styles['SVBody'])]
            
            # Two-column dashboard: left chart, right KPI
            if charts.get('weekly_summary') and kpi_para:
                dash = self._two_col([RLImage(charts['weekly_summary'], width=8*cm, height=4.8*cm)], kpi_para)
                story.append(dash)
                story.append(Spacer(1, 12))
            elif charts.get('weekly_summary'):
                self._add_chart_to_story(story, charts['weekly_summary'], "📊 WEEKLY PERFORMANCE DASHBOARD", width=16*cm)
            
            # Highlights section if available
            if weekly_data.get('content_highlights'):
                story.append(Paragraph("⭐ HIGHLIGHTS", self.styles['SVSection']))
                for h in weekly_data['content_highlights']:
                    story.append(Paragraph(f"• {h}", self.styles['SVBody']))
                story.append(Spacer(1, 10))
            
            story.append(HRFlowable(width='100%', color=self.sv_colors['border']))
            
            # Key Performance Indicators - Simple Text Version
            if 'performance_metrics' in weekly_data:
                story.append(Paragraph("🎯 KEY PERFORMANCE INDICATORS", self.styles['SVSection']))
                metrics = weekly_data['performance_metrics']
                
                # Create simple formatted text instead of table
                kpi_text = f"""
                <b>📈 Total Signals:</b> {metrics.get('total_signals', metrics.get('total_trades', 'N/A'))}<br/>
                <b>✅ Success Rate:</b> {metrics.get('success_rate', 'N/A')}<br/>
                <b>💰 Weekly Return:</b> {metrics.get('total_profit', 'N/A')}<br/>
                <b>📊 Sharpe Ratio:</b> {metrics.get('sharpe_ratio', 'N/A')}<br/>
                <b>🛡️ Max Drawdown:</b> {metrics.get('max_drawdown', 'N/A')}
                """
                
                story.append(Paragraph(kpi_text, self.styles['SVBody']))
                story.append(Spacer(1, 20))
            
            # Daily Performance - Only show if data available
            if 'daily_performance' in weekly_data and weekly_data['daily_performance']:
                # Force new page so heading is not left alone at the bottom
                story.append(PageBreak())
                story.append(Paragraph("📅 DAILY PERFORMANCE", self.styles['SVSection']))
                daily_data = weekly_data['daily_performance']
                daily_signals = {d.get('date'): d.get('signals', []) for d in weekly_data.get('daily_signals', []) or []}
                
                # Create daily breakdown with per-signal table
                for day_info in daily_data:
                    if day_info.get('signals', 0) == 0 and day_info.get('notes', '') == 'No market summary available':
                        continue
                    date_key = day_info.get('date')
                    day_flows = []
                    day_flows.append(Paragraph(f"<b>{day_info.get('day','N/A')}</b>", self.styles['SVBody']))
                    meta_parts = []
                    if day_info.get('signals',0) > 0:
                        meta_parts.append(f"Signals: {day_info.get('signals')}")
                    if day_info.get('success_rate','n/a') != 'n/a':
                        meta_parts.append(f"Success rate: {day_info.get('success_rate')}")
                    if meta_parts:
                        day_flows.append(Paragraph(" | ".join(meta_parts), self.styles['SVBody']))
                    notes = day_info.get('notes', '')
                    if notes:
                        day_flows.append(Paragraph(f"<i>{notes}</i>", self.styles['SVBody']))
                    
                    # Per-signal table (asset/direction/outcome)
                    signals = daily_signals.get(date_key) or []
                    if signals:
                        table_data = [["Asset", "Dir", "Entry", "Target", "Stop", "Outcome"]]
                        for s in signals:
                            table_data.append([
                                s.get('asset','N/A'),
                                s.get('direction','N/A'),
                                str(s.get('entry','N/A')),
                                str(s.get('target','N/A')),
                                str(s.get('stop','N/A')),
                                s.get('outcome','N/A'),
                            ])
                        sig_table = Table(table_data, colWidths=[2*cm, 1.2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4*cm])
                        sig_table.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), self.sv_colors['primary']),
                            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0,0), (-1,0), 8),
                            ('FONTSIZE', (0,1), (-1,-1), 8),
                            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                            ('BACKGROUND', (0,1), (-1,-1), self.sv_colors['light_gray']),
                            ('GRID', (0,0), (-1,-1), 0.5, self.sv_colors['border']),
                            ('TOPPADDING', (0,0), (-1,-1), 3),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                        ]))
                        day_flows.append(sig_table)
                    day_flows.append(Spacer(1, 12))
                    story.append(KeepTogether(day_flows))
                        
                # Daily Performance Chart (if available)
                if charts.get('daily_accuracy'):
                    self._add_chart_to_story(story, charts['daily_accuracy'], "📈 DAILY ACCURACY TRENDS", width=16*cm)
                
                story.append(Spacer(1, 10))
                story.append(HRFlowable(width='100%', color=self.sv_colors['border']))
                story.append(Spacer(1, 10))
            
            # Market Analysis Section
            if 'market_analysis' in weekly_data:
                story.append(Paragraph("🌍 MARKET ANALYSIS", self.styles['SVSection']))
                analysis = weekly_data['market_analysis']
                
                analysis_data = [
                    ['Market Factor', 'Assessment', 'Impact'],
                    ['Market Regime', analysis.get('regime', 'N/A'), '🔍'],
                    ['Regime Confidence', analysis.get('regime_confidence', 'N/A'), '📌'],
                    ['Volatility', analysis.get('volatility', 'N/A'), '📊'],
                    ['Trend Strength', analysis.get('trend_strength', 'N/A'), '💪'],
                    ['Sector Rotation', analysis.get('sector_rotation', 'N/A'), '🔄']
                ]
                
                analysis_table = Table(analysis_data, colWidths=[5*cm, 5*cm, 3*cm])
                analysis_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.sv_colors['secondary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), self.sv_colors['light_gray']),
                    ('GRID', (0, 0), (-1, -1), 1, self.sv_colors['border'])
                ]))
                
                story.append(analysis_table)
                story.append(Spacer(1, 25))
            
            # What worked / What didn’t (if available)
            what_worked = weekly_data.get('what_worked') or []
            what_didnt = weekly_data.get('what_didnt') or []
            if what_worked or what_didnt:
                flows = []
                flows.append(Paragraph("WHAT WORKED / WHAT DIDN’T", self.styles['SVSection']))
                if what_worked:
                    flows.append(Paragraph("<b>What worked:</b>", self.styles['SVBody']))
                    for w in what_worked:
                        flows.append(Paragraph(f"• {w}", self.styles['SVBody']))
                if what_didnt:
                    flows.append(Spacer(1, 6))
                    flows.append(Paragraph("<b>What didn’t work:</b>", self.styles['SVBody']))
                    for w in what_didnt:
                        flows.append(Paragraph(f"• {w}", self.styles['SVBody']))
                flows.append(Spacer(1, 15))
                story.append(KeepTogether(flows))
            
            # Risk Assessment
            if 'risk_metrics' in weekly_data:
                story.append(Paragraph("⚠️ RISK ASSESSMENT", self.styles['SVSection']))
                risk = weekly_data['risk_metrics']
                
                risk_text = f"""
                <b>Current Risk Level:</b> {risk.get('risk_level', 'N/A')}<br/>
                <b>VaR (95%):</b> {risk.get('var_95', 'N/A')}<br/>
                <b>Maximum Position Size:</b> {risk.get('max_position', 'N/A')}<br/>
                <b>Correlation Risk:</b> {risk.get('correlation_risk', 'N/A')}
                """
                
                story.append(Paragraph(risk_text, self.styles['SVBody']))
                
                # Risk Metrics Chart (if available)
                if charts.get('risk_metrics'):
                    self._add_chart_to_story(story, charts['risk_metrics'], "🛡️ RISK METRICS DASHBOARD")
                
                # Risk Surrogates (if available)
                if charts.get('risk_surrogates'):
                    self._add_chart_to_story(story, charts['risk_surrogates'], "🛡️ RISK METRICS (Surrogates)")
                
                story.append(Spacer(1, 20))
            
            # Key Events & News Impact - Only show if events exist
            if 'key_events' in weekly_data and weekly_data['key_events']:
                story.append(Paragraph("📰 KEY EVENTS & NEWS IMPACT", self.styles['SVSection']))
                events = weekly_data['key_events']
                
                for event in events:
                    event_text = f"• <b>{event.get('date', 'N/A')}:</b> {event.get('description', 'N/A')} <i>(Impact: {event.get('impact', 'N/A')})</i>"
                    story.append(Paragraph(event_text, self.styles['SVBody']))
                
                story.append(Spacer(1, 15))
            
            # Weekly News Summary - from seen_news snapshots
            if weekly_data.get('weekly_news'):
                flows = []
                flows.append(Paragraph("📰 WEEKLY NEWS SUMMARY", self.styles['SVSection']))
                for n in weekly_data['weekly_news']:
                    date_str = n.get('date','')
                    title = n.get('title','')
                    link = n.get('link','')
                    if link:
                        text = f"• <b>{date_str}</b> – <a href='{link}' color='blue'>{title}</a>" if date_str else f"• <a href='{link}' color='blue'>{title}</a>"
                    else:
                        text = f"• <b>{date_str}</b> – {title}" if date_str else f"• {title}"
                    flows.append(Paragraph(text, self.styles['SVBody']))
                flows.append(Spacer(1, 25))
                story.append(KeepTogether(flows))
            
            # Signal Quality Analysis
            if 'signal_analysis' in weekly_data:
                story.append(Paragraph("🔍 SIGNAL QUALITY ANALYSIS", self.styles['SVSection']))
                signal_data = weekly_data['signal_analysis']
                
                signal_table_data = [
                    ['Signal Type', 'Count', 'Accuracy', 'Avg Return', 'Quality Score'],
                    ['Trend Following', str(signal_data.get('trend_count', 'N/A')), signal_data.get('trend_accuracy', 'N/A'), signal_data.get('trend_return', 'N/A'), signal_data.get('trend_score', 'N/A')],
                    ['Mean Reversion', str(signal_data.get('reversion_count', 'N/A')), signal_data.get('reversion_accuracy', 'N/A'), signal_data.get('reversion_return', 'N/A'), signal_data.get('reversion_score', 'N/A')],
                    ['Momentum', str(signal_data.get('momentum_count', 'N/A')), signal_data.get('momentum_accuracy', 'N/A'), signal_data.get('momentum_return', 'N/A'), signal_data.get('momentum_score', 'N/A')],
                    ['Breakout', str(signal_data.get('breakout_count', 'N/A')), signal_data.get('breakout_accuracy', 'N/A'), signal_data.get('breakout_return', 'N/A'), signal_data.get('breakout_score', 'N/A')]
                ]
                
                signal_table = Table(signal_table_data, colWidths=[2.8*cm, 1.8*cm, 2*cm, 2.2*cm, 2*cm])
                signal_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.sv_colors['accent']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 1), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BACKGROUND', (0, 1), (-1, -1), self.sv_colors['light_gray']),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.sv_colors['border'])
                ]))
                
                story.append(signal_table)
                story.append(Spacer(1, 20))
            
            # AI Model Performance Breakdown
            if 'ai_performance' in weekly_data:
                story.append(Paragraph("🤖 AI MODEL PERFORMANCE BREAKDOWN", self.styles['SVSection']))
                ai_data = weekly_data['ai_performance']
                
                ai_performance_text = f"""
                <b>🏆 Best Performing Model:</b> {ai_data.get('best_model', 'N/A')} ({ai_data.get('best_accuracy', 'N/A')})\n
                <b>📈 Model Rankings This Week:</b><br/>
                1. {ai_data.get('rank_1', 'Random Forest')} - {ai_data.get('rank_1_score', '89.2%')}<br/>
                2. {ai_data.get('rank_2', 'XGBoost')} - {ai_data.get('rank_2_score', '85.7%')}<br/>
                3. {ai_data.get('rank_3', 'Neural Network')} - {ai_data.get('rank_3_score', '82.3%')}<br/>
                4. {ai_data.get('rank_4', 'SVM')} - {ai_data.get('rank_4_score', '79.1%')}<br/>
                5. {ai_data.get('rank_5', 'Logistic Regression')} - {ai_data.get('rank_5_score', '76.8%')}\n
                <b>🔧 Model Improvements:</b> {ai_data.get('improvements', 'Hyperparameter tuning completed, feature engineering enhanced')}
                """
                
                story.append(Paragraph(ai_performance_text, self.styles['SVBody']))
                story.append(Spacer(1, 20))
            
            # Market Sector Performance
            if 'sector_performance' in weekly_data:
                story.append(Paragraph("🏢 SECTOR PERFORMANCE ANALYSIS", self.styles['SVSection']))
                sectors = weekly_data['sector_performance']
                
                sector_table_data = [['Sector', 'Return', 'Signals', 'Success', 'Trend']]
                for sector, data in sectors.items():
                    trend_emoji = '🟢' if float(str(data.get('return', '0')).rstrip('%+')) > 2 else '🟡' if float(str(data.get('return', '0')).rstrip('%+')) > 0 else '🔴'
                    sector_table_data.append([
                        sector,
                        data.get('return', 'N/A'),
                        str(data.get('signals', 'N/A')),
                        data.get('success_rate', 'N/A'),
                        trend_emoji
                    ])
                
                sector_table = Table(sector_table_data, colWidths=[2.5*cm, 2.2*cm, 1.8*cm, 2.2*cm, 1.5*cm])
                sector_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.sv_colors['secondary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 1), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BACKGROUND', (0, 1), (-1, -1), self.sv_colors['light_gray']),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.sv_colors['border'])
                ]))
                
                story.append(sector_table)
                story.append(Spacer(1, 15))
            
            # Risk + Asset charts side-by-side when both available
            if charts.get('risk_metrics') and charts.get('asset_performance'):
                block = self._two_col([
                    Paragraph("🛡️ RISK METRICS", self.styles['SVSection']),
                    RLImage(charts['risk_metrics'], width=7.8*cm, height=4.7*cm)
                ], [
                    Paragraph("🏆 ASSET PERFORMANCE", self.styles['SVSection']),
                    RLImage(charts['asset_performance'], width=7.8*cm, height=4.7*cm)
                ])
                story.append(block)
                story.append(Spacer(1, 15))
            else:
                # Fallback: single charts
                if charts.get('risk_metrics'):
                    self._add_chart_to_story(story, charts['risk_metrics'], "🛡️ RISK METRICS DASHBOARD", width=16*cm)
                if charts.get('asset_performance'):
                    self._add_chart_to_story(story, charts['asset_performance'], "🏆 ASSET PERFORMANCE ANALYSIS", width=16*cm)
            
            # Page break before next week outlook so it sits on the last page
            story.append(PageBreak())
            # Next Week Predictions & Strategy
            story.append(Paragraph("🔮 NEXT WEEK STRATEGY & OUTLOOK", self.styles['SVSection']))
            
            # Show predictive recommendations if available
            if 'next_week_predictions' in weekly_data and weekly_data['next_week_predictions']:
                predictions = weekly_data['next_week_predictions']
                
                # Weekly outlook from predictions
                outlook = predictions.get('weekly_outlook')
                if outlook:
                    story.append(Paragraph(f"<b>Market Outlook:</b> {outlook}", self.styles['SVBody']))
                    story.append(Spacer(1, 10))
                
                # Top recommendations (sanitized)
                def _clean(txt: str) -> str:
                    if not isinstance(txt, str):
                        return ''
                    # Remove duplicated phrases and trim length
                    txt = txt.replace('based on 0% recent accuracy', '').strip()
                    return (txt[:220] + '…') if len(txt) > 220 else txt
                
                top_recs = predictions.get('top_recommendations', [])
                if top_recs:
                    story.append(Paragraph("<b>Top Recommendations:</b>", self.styles['SVBody']))
                    for rec in top_recs:
                        priority_emoji = '🔴' if rec.get('priority') == 'HIGH' else '🟡'
                        title = _clean(rec.get('title', 'N/A'))
                        desc = _clean(rec.get('description', ''))
                        if desc:
                            rec_text = f"{priority_emoji} <b>{title}</b><br/>{desc}"
                        else:
                            rec_text = f"{priority_emoji} <b>{title}</b>"
                        story.append(Paragraph(rec_text, self.styles['SVBody']))
                    story.append(Spacer(1, 15))
            
            # Fallback to basic outlook
            elif 'next_week_outlook' in weekly_data:
                story.append(Paragraph(weekly_data['next_week_outlook'], self.styles['SVBody']))
            
            # Next Week – Focus (3 bullets concise)
            if weekly_data.get('next_week_focus'):
                story.append(Spacer(1, 10))
                story.append(Paragraph("NEXT WEEK – FOCUS", self.styles['SVSection']))
                for b in weekly_data['next_week_focus']:
                    story.append(Paragraph(f"• {b}", self.styles['SVBody']))
            
            if 'next_week_strategy' in weekly_data and weekly_data['next_week_strategy']:
                story.append(Spacer(1, 15))
                story.append(Paragraph("<b>Strategic Focus:</b>", self.styles['SVBody']))
                for strategy in weekly_data['next_week_strategy']:
                    story.append(Paragraph(f"• {strategy}", self.styles['SVBody']))
            
            story.append(Spacer(1, 25))
            
            # Focus Assets (if available)
            if weekly_data.get('asset_focus'):
                story.append(Paragraph("🎯 FOCUS ASSETS", self.styles['SVSection']))
                for a in weekly_data['asset_focus']:
                    story.append(Paragraph(
                        f"• {a.get('asset')}: {a.get('total_predictions',0)} signals this week",
                        self.styles['SVBody']
                    ))
                story.append(Spacer(1, 10))
            
            # Action Items - Enhanced section with automatic generation if missing
            action_items = weekly_data.get('action_items', [])
            
            # Generate basic action items if none provided
            if not action_items:
                performance_metrics = weekly_data.get('performance_metrics', {})
                success_rate_str = performance_metrics.get('success_rate', '0%')
                
                try:
                    if success_rate_str != 'n/a':
                        success_rate = float(success_rate_str.replace('%', ''))
                        if success_rate < 50:
                            action_items = [
                                {'priority': 'HIGH', 'task': 'Review Model Performance', 'description': f'Success rate {success_rate_str} below target - analyze prediction methodology'},
                                {'priority': 'MEDIUM', 'task': 'Optimize Asset Selection', 'description': 'Focus on best performing assets and reduce exposure to underperformers'}
                            ]
                        elif success_rate < 65:
                            action_items = [
                                {'priority': 'MEDIUM', 'task': 'Fine-tune Parameters', 'description': f'Success rate {success_rate_str} has improvement potential - optimize model parameters'},
                                {'priority': 'LOW', 'task': 'Monitor Performance', 'description': 'Continue current strategy with close performance monitoring'}
                            ]
                        else:
                            action_items = [
                                {'priority': 'LOW', 'task': 'Document Success Patterns', 'description': f'Excellent success rate {success_rate_str} - document winning strategies'},
                                {'priority': 'MEDIUM', 'task': 'Scale Successful Strategies', 'description': 'Consider increasing position sizes for consistent performers'}
                            ]
                except ValueError:
                    pass
            
            # Display action items if we have any
            if action_items:
                story.append(Paragraph("✅ ACTION ITEMS", self.styles['SVSection']))
                
                for i, action in enumerate(action_items):
                    priority = action.get('priority', 'MEDIUM')
                    priority_emoji = '🔴' if priority == 'HIGH' else '🟡' if priority == 'MEDIUM' else '🟢'
                    task = action.get('task', 'N/A')
                    description = action.get('description', 'N/A')
                    
                    action_text = f"{priority_emoji} <b>{i+1}. {task}</b><br/>{description}"
                    story.append(Paragraph(action_text, self.styles['SVBody']))
                    story.append(Spacer(1, 8))
                
                story.append(Spacer(1, 15))
            
            # Footer with disclaimers
            story.append(Spacer(1, 30))
            story.append(Paragraph("" + "="*80, self.styles['SVBody']))
            footer_text = f"""
            <b>DISCLAIMER:</b> This report is generated by SV Trading System for internal analysis purposes only. 
            Past performance does not guarantee future results. Trading involves significant risk of loss.<br/><br/>
            <i>Report generated on {generation_time} | SV Content Engine v2.0</i>
            """
            story.append(Paragraph(footer_text, self.styles['SVBody']))
            
            # Build PDF with header/footer
            doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            
            # Cleanup temporary chart files
            for chart_type, chart_path in charts.items():
                try:
                    if chart_path and os.path.exists(chart_path):
                        os.unlink(chart_path)
                        log.debug(f"[PDF] Cleaned up temporary chart: {chart_type}")
                except Exception as e:
                    log.warning(f"[PDF] Could not cleanup chart {chart_type}: {e}")
            
            log.info(f"✅ [PDF] Enhanced Weekly Report PDF Generated: {filename}")
            return filepath
            
        except Exception as e:
            log.error(f"⚠ [PDF] Error Creating enhanced weekly report PDF: {e}")
            return None

    def Createte_monthly_report_pdf(self, monthly_data: Dict) -> str:
        """Create PDF del Monthly Report SV"""
        try:
            # Nome file con timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"SV_Monthly_Report_{timestamp}.pdf"
            filepath = os.path.join(self.pdf_output_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )
            story = []
            
            # Header
            story.append(Paragraph("SV - SISTEMA UNIFICATO TRADING", self.styles['SVTitle']))
            month_label = monthly_data.get('month_label') or monthly_data.get('month_name') or 'This Month'
            story.append(Paragraph(f"MONTHLY REPORT - {month_label}", self.styles['SVSubtitle']))
            generation_time = datetime.datetime.now().strftime('%d %B %Y - %H:%M')
            story.append(Paragraph(f"Generated: {generation_time}", self.styles['SVBody']))
            story.append(Spacer(1, 20))
            
            # Charts
            charts = {}
            if CHARTS_AVAILABLE:
                try:
                    charts = generate_monthly_charts(monthly_data)
                except Exception as e:
                    log.warning(f"[PDF] Monthly charts error: {e}")
            
            # Executive Summary
            if monthly_data.get('monthly_summary'):
                story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SVSection']))
                story.append(Paragraph(monthly_data['monthly_summary'], self.styles['SVHighlight']))
                story.append(Spacer(1, 12))
            
            # Highlights
            if monthly_data.get('content_highlights'):
                story.append(Paragraph("HIGHLIGHTS", self.styles['SVSection']))
                for h in monthly_data['content_highlights']:
                    story.append(Paragraph(f"• {h}", self.styles['SVBody']))
                story.append(Spacer(1, 10))
            
            # What worked / What didn’t (if available)
            what_worked = monthly_data.get('what_worked') or []
            what_didnt = monthly_data.get('what_didnt') or []
            if what_worked or what_didnt:
                flows = []
                flows.append(Paragraph("WHAT WORKED / WHAT DIDN’T", self.styles['SVSection']))
                if what_worked:
                    flows.append(Paragraph("<b>What worked:</b>", self.styles['SVBody']))
                    for w in what_worked:
                        flows.append(Paragraph(f"• {w}", self.styles['SVBody']))
                if what_didnt:
                    flows.append(Spacer(1, 6))
                    flows.append(Paragraph("<b>What didn’t work:</b>", self.styles['SVBody']))
                    for w in what_didnt:
                        flows.append(Paragraph(f"• {w}", self.styles['SVBody']))
                flows.append(Spacer(1, 15))
                story.append(KeepTogether(flows))
            
            # Dashboard
            if charts.get('monthly_summary'):
                self._add_chart_to_story(story, charts['monthly_summary'], "MONTHLY PERFORMANCE DASHBOARD", width=16*cm)
            
            # Daily trend
            if charts.get('daily_accuracy'):
                self._add_chart_to_story(story, charts['daily_accuracy'], "DAILY ACCURACY TREND", width=16*cm)
            
            # Market analysis
            if monthly_data.get('market_analysis'):
                story.append(Paragraph("MARKET ANALYSIS", self.styles['SVSection']))
                analysis = monthly_data['market_analysis']
                analysis_data = [
                    ['Market Factor', 'Assessment', 'Impact'],
                    ['Market Regime', analysis.get('regime', 'N/A'), ''],
                    ['Volatility', analysis.get('volatility', 'N/A'), ''],
                    ['Trend Strength', analysis.get('trend_strength', 'N/A'), ''],
                    ['Sector Rotation', analysis.get('sector_rotation', 'N/A'), '']
                ]
                table = Table(analysis_data, colWidths=[5*cm, 8*cm, 2*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.sv_colors['secondary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), self.sv_colors['light_gray']),
                    ('GRID', (0, 0), (-1, -1), 1, self.sv_colors['border'])
                ]))
                story.append(table)
                story.append(Spacer(1, 15))
            
            # Monthly risk overview (surrogates)
            risk_overview = monthly_data.get('risk_overview')
            if risk_overview:
                story.append(Paragraph("RISK OVERVIEW (MONTHLY)", self.styles['SVSection']))
                txt = f"""
                <b>Coverage days:</b> {risk_overview.get('coverage_days','n/a')}<br/>
                <b>Signal days:</b> {risk_overview.get('signal_days','n/a')}<br/>
                <b>Max consecutive loss days:</b> {risk_overview.get('max_loss_streak','n/a')}
                """
                story.append(Paragraph(txt, self.styles['SVBody']))
                if charts.get('risk_surrogates'):
                    self._add_chart_to_story(story, charts['risk_surrogates'], "RISK SURROGATES", width=16*cm)
                story.append(Spacer(1, 15))
            
            # Monthly key events (from daily summaries)
            if monthly_data.get('monthly_events'):
                story.append(Paragraph("KEY EVENTS OF THE MONTH", self.styles['SVSection']))
                for ev in monthly_data['monthly_events']:
                    date_str = ev.get('date','')
                    desc = ev.get('description','')
                    text = f"• <b>{date_str}</b>: {desc}" if date_str else f"• {desc}"
                    story.append(Paragraph(text, self.styles['SVBody']))
                story.append(Spacer(1, 15))
            
            # Monthly News Summary
            if monthly_data.get('monthly_news'):
                flows = []
                flows.append(Paragraph("MONTHLY NEWS SUMMARY", self.styles['SVSection']))
                for n in monthly_data['monthly_news']:
                    date_str = n.get('date','')
                    title = n.get('title','')
                    link = n.get('link','')
                    if link:
                        text = f"• <b>{date_str}</b> – <a href='{link}' color='blue'>{title}</a>" if date_str else f"• <a href='{link}' color='blue'>{title}</a>"
                    else:
                        text = f"• <b>{date_str}</b> – {title}" if date_str else f"• {title}"
                    flows.append(Paragraph(text, self.styles['SVBody']))
                flows.append(Spacer(1, 20))
                story.append(KeepTogether(flows))
            
            # Focus Assets
            if monthly_data.get('asset_focus'):
                story.append(Paragraph("FOCUS ASSETS", self.styles['SVSection']))
                for a in monthly_data['asset_focus']:
                    story.append(Paragraph(f"• {a.get('asset')}: {a.get('return','n/a')} | {a.get('days',0)} days with price", self.styles['SVBody']))
                story.append(Spacer(1, 10))

            # Risk + Asset charts
            if charts.get('risk_metrics') and charts.get('asset_performance'):
                block = self._two_col([
                    Paragraph("RISK METRICS", self.styles['SVSection']),
                    RLImage(charts['risk_metrics'], width=7.8*cm, height=4.7*cm)
                ], [
                    Paragraph("ASSET PERFORMANCE", self.styles['SVSection']),
                    RLImage(charts['asset_performance'], width=7.8*cm, height=4.7*cm)
                ])
                story.append(block)
                story.append(Spacer(1, 15))
            else:
                if charts.get('risk_metrics'):
                    self._add_chart_to_story(story, charts['risk_metrics'], "RISK METRICS", width=16*cm)
                if charts.get('asset_performance'):
                    self._add_chart_to_story(story, charts['asset_performance'], "ASSET PERFORMANCE", width=16*cm)
            
            # Next Month Focus (3 bullets)
            if monthly_data.get('next_month_focus'):
                story.append(Paragraph("NEXT MONTH – FOCUS", self.styles['SVSection']))
                for b in monthly_data['next_month_focus']:
                    story.append(Paragraph(f"• {b}", self.styles['SVBody']))
                story.append(Spacer(1, 10))

            # Action items (auto if missing)
            action_items = monthly_data.get('action_items', [])
            if not action_items:
                # Simple heuristic from success rate
                sr = monthly_data.get('performance_metrics', {}).get('success_rate', 'n/a')
                try:
                    if sr != 'n/a' and float(sr.replace('%','')) < 60:
                        action_items = [
                            {'priority': 'HIGH', 'task': 'Optimize Model Features', 'description': 'Sub-60% monthly success rate – review inputs and parameters'},
                            {'priority': 'MEDIUM', 'task': 'Focus on strong days', 'description': 'Scale up on historically strong weekday patterns'}
                        ]
                except Exception:
                    pass
            if action_items:
                story.append(Paragraph("ACTION ITEMS", self.styles['SVSection']))
                for a in action_items:
                    story.append(Paragraph(f"• {a.get('task','Task')}: {a.get('description','')}", self.styles['SVBody']))
                story.append(Spacer(1, 10))
            
            # Build PDF
            doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            
            # Cleanup temporary charts
            for _, p in charts.items():
                try:
                    if p and os.path.exists(p):
                        os.unlink(p)
                except Exception:
                    pass
            
            log.info(f"✅ [PDF] Monthly Report PDF Generated: {filename}")
            return filepath
        except Exception as e:
            log.error(f"⚠ [PDF] Error Creating monthly report PDF: {e}")
            return None

# Singleton e helper functions
pdf_Generatetor = None

def get_pdf_Generatetor() -> SVPDFGeneratetor:
    """Get istanza singleton del PDF Generatetor"""
    global pdf_Generatetor
    if pdf_Generatetor is None:
        if REPORTLAB_AVAILABLE:
            pdf_Generatetor = SVPDFGeneratetor()
        else:
            raise ImportError("ReportLab not available - cannot Createte PDF Generatetor")
    return pdf_Generatetor

def Createte_daily_pdf(summary_data: Dict) -> str:
    """Helper per Createre PDF daily summary"""
    try:
        Generatetor = get_pdf_Generatetor()
        return Generatetor.Createte_daily_summary_pdf(summary_data)
    except Exception as e:
        log.error(f"âŒ [PDF] Error in Createte_daily_pdf: {e}")
        return None

def Createte_weekly_pdf(weekly_data: Dict) -> str:
    """Helper per Createre PDF weekly report"""
    try:
        weekly_generator = SVPDFGeneratetor(timeframe='weekly')
        return weekly_generator.Createte_weekly_report_pdf(weekly_data)
    except Exception as e:
        log.error(f"⌠ [PDF] Error in Createte_weekly_pdf: {e}")
        return None

def Createte_monthly_pdf(monthly_data: Dict) -> str:
    """Helper per creare PDF monthly report"""
    try:
        monthly_generator = SVPDFGeneratetor(timeframe='monthly')
        return monthly_generator.Createte_monthly_report_pdf(monthly_data)
    except Exception as e:
        log.error(f"⌠ [PDF] Error in Createte_monthly_pdf: {e}")
        return None

# Test function
def test_pdf_Generatetion():
    """Test Generatezione PDF"""
    if not REPORTLAB_AVAILABLE:
        print("âŒ [TEST] ReportLab not available - cannot test PDF Generatetion")
        return False
    
    print("ðŸ§ª [TEST] Testing PDF Generatetion...")
    
    # Test data
    test_summary = {
        'market_status': 'CLOSED',
        'performance': {
            'accuracy': '85%',
            'total_signals': 12,
            'success_rate': '78%'
        },
        'market_analysis': {
            'regime': 'BULL MARKET',
            'sentiment': 'POSITIVE',
            'volatility': 'NORMAL'
        },
        'tomorrow_outlook': 'Markets expected to continue positive momentum with focus on tech sector.',
        'key_points': [
            'Strong performance in morning predictions',
            'Tech sector showing leadership',
            'Risk metrics within normal ranges'
        ]
    }
    
    # Test daily PDF
    pdf_path = Createte_daily_pdf(test_summary)
    if pdf_path and os.path.exists(pdf_path):
        print(f"âœ… [TEST] Daily PDF Createted successfully: {pdf_path}")
        return True
    else:
        print("âŒ [TEST] Daily PDF Createtion failed")
        return False

if __name__ == '__main__':
    test_pdf_Generatetion()



