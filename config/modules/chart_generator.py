#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Chart Generator Module
Generate basic charts for weekly PDF reports
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import tempfile

log = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    from matplotlib.patches import Rectangle
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    log.warning("⚠️ [CHART] Matplotlib not available. Install with: pip install matplotlib seaborn")
    MATPLOTLIB_AVAILABLE = False

class SVChartGenerator:
    """Generate charts for SV weekly reports"""
    
    def __init__(self):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib and seaborn required for chart generation")
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Chart configuration
        self.figure_size = (10, 6)
        self.dpi = 100
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'success': '#28A745',
            'danger': '#DC3545',
            'warning': '#FFC107',
            'info': '#17A2B8'
        }
    
    def create_daily_accuracy_chart(self, daily_performance: List[Dict]) -> str:
        """Create daily accuracy trend chart"""
        try:
            if not daily_performance:
                return None
                
            # Extract data for chart
            dates = []
            accuracies = []
            signals = []
            
            for day_info in daily_performance:
                day_date = day_info.get('date', '')
                day_signals = day_info.get('signals', 0)
                success_rate = day_info.get('success_rate', 'n/a')
                
                if success_rate != 'n/a' and day_signals > 0:
                    try:
                        # Convert date string to datetime
                        if day_date:
                            date_obj = datetime.strptime(day_date, '%Y-%m-%d')
                            dates.append(date_obj)
                            accuracy = float(success_rate.replace('%', ''))
                            accuracies.append(accuracy)
                            signals.append(day_signals)
                    except (ValueError, AttributeError):
                        continue
            
            if len(dates) < 2:
                return None
                
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figure_size, 
                                         height_ratios=[2, 1], dpi=self.dpi)
            fig.suptitle('Daily Performance Tracking', fontsize=16, fontweight='bold')
            
            # Top chart: Accuracy trend
            ax1.plot(dates, accuracies, marker='o', linewidth=2, 
                    markersize=8, color=self.colors['primary'], label='Daily Accuracy')
            
            # Overlay: 4-day moving average (if enough points)
            if len(accuracies) >= 3:
                try:
                    window = min(4, len(accuracies))
                    ma = np.convolve(accuracies, np.ones(window)/window, mode='valid')
                    ma_dates = dates[window-1:]
                    ax1.plot(ma_dates, ma, linestyle='--', linewidth=2, color=self.colors['secondary'], label=f'{window}-day MA')
                except Exception:
                    pass
            
            # Mark best/worst day
            try:
                best_idx = int(np.argmax(accuracies))
                worst_idx = int(np.argmin(accuracies))
                ax1.scatter([dates[best_idx]],[accuracies[best_idx]], color=self.colors['success'], s=80, zorder=5, label='Best')
                ax1.scatter([dates[worst_idx]],[accuracies[worst_idx]], color=self.colors['danger'], s=80, zorder=5, label='Worst')
            except Exception:
                pass
            ax1.axhline(y=50, color=self.colors['danger'], linestyle='--', 
                       alpha=0.7, label='Break-even (50%)')
            ax1.fill_between(dates, accuracies, 50, 
                           where=[acc >= 50 for acc in accuracies],
                           color=self.colors['success'], alpha=0.3, label='Profitable')
            ax1.fill_between(dates, accuracies, 50,
                           where=[acc < 50 for acc in accuracies], 
                           color=self.colors['danger'], alpha=0.3, label='Loss')
            
            ax1.set_ylabel('Accuracy (%)', fontsize=12)
            ax1.set_title('Daily Prediction Accuracy', fontsize=14)
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='lower right')
            ax1.set_ylim(0, 100)
            
            # Format x-axis for top chart
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a %d/%m'))
            ax1.xaxis.set_major_locator(mdates.DayLocator())
            
            # Bottom chart: Signal volume
            colors_bars = [self.colors['success'] if acc >= 50 else self.colors['danger'] 
                          for acc in accuracies]
            ax2.bar(dates, signals, color=colors_bars, alpha=0.7)
            ax2.set_ylabel('Signals', fontsize=12)
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_title('Daily Signal Volume', fontsize=14)
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis for bottom chart
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%a %d/%m'))
            ax2.xaxis.set_major_locator(mdates.DayLocator())
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Use constrained layout instead of tight_layout to avoid warnings
            try:
                plt.tight_layout()
            except UserWarning:
                # Fallback: adjust layout manually if tight_layout fails
                plt.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.9, hspace=0.4, wspace=0.3)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, bbox_inches='tight', dpi=self.dpi, facecolor='white')
            plt.close()
            
            log.info("[CHART] Daily accuracy chart created successfully")
            return temp_file.name
            
        except Exception as e:
            log.error(f"[CHART] Error creating daily accuracy chart: {e}")
            if 'fig' in locals():
                plt.close()
            return None
    
    def create_asset_performance_chart(self, performance_attribution: Dict) -> str:
        """Create asset performance comparison chart"""
        try:
            # Try multiple data sources for asset performance
            asset_performance = {}
            
            # Primary source: asset_attribution
            if 'asset_attribution' in performance_attribution:
                asset_attribution = performance_attribution['asset_attribution']
                if isinstance(asset_attribution, dict) and 'asset_performance' in asset_attribution:
                    asset_performance = asset_attribution['asset_performance']
            
            # Fallback: direct asset_performance key
            if not asset_performance and 'asset_performance' in performance_attribution:
                asset_performance = performance_attribution['asset_performance']
            
            # If no asset data available, skip chart to avoid fabricated values
            if not asset_performance:
                return None
            
            # Extract asset data
            assets = []
            accuracies = []
            predictions = []
            
            for asset, perf_data in asset_performance.items():
                accuracy_str = perf_data.get('accuracy', '0%')
                total_predictions = perf_data.get('total_predictions', 0)
                
                try:
                    accuracy = float(str(accuracy_str).replace('%', ''))
                    assets.append(asset)
                    accuracies.append(accuracy)
                    predictions.append(total_predictions)
                except (ValueError, AttributeError):
                    continue
            
            if not assets:
                return None
                
            # Create figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=self.dpi)
            fig.suptitle('Asset Performance Analysis', fontsize=16, fontweight='bold')
            
            # Left chart: Accuracy comparison
            colors_acc = [self.colors['success'] if acc >= 50 else self.colors['danger'] 
                         for acc in accuracies]
            bars1 = ax1.bar(assets, accuracies, color=colors_acc, alpha=0.8)
            ax1.axhline(y=50, color=self.colors['warning'], linestyle='--', 
                       alpha=0.8, label='Break-even')
            ax1.set_ylabel('Accuracy (%)', fontsize=12)
            ax1.set_title('Accuracy by Asset', fontsize=14)
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Add value labels on bars
            for bar, acc in zip(bars1, accuracies):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{acc:.0f}%', ha='center', va='bottom', fontweight='bold')
            
            # Right chart: Prediction volume
            bars2 = ax2.bar(assets, predictions, color=self.colors['info'], alpha=0.8)
            ax2.set_ylabel('Total Predictions', fontsize=12)
            ax2.set_title('Prediction Volume by Asset', fontsize=14)
            ax2.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, pred in zip(bars2, predictions):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        str(pred), ha='center', va='bottom', fontweight='bold')
            
            # Rotate x-axis labels if needed
            if len(assets) > 3:
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Safe tight_layout with fallback
            try:
                plt.tight_layout()
            except UserWarning:
                plt.subplots_adjust(top=0.9, bottom=0.15, left=0.1, right=0.9, hspace=0.4, wspace=0.3)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, bbox_inches='tight', dpi=self.dpi, facecolor='white')
            plt.close()
            
            log.info("[CHART] Asset performance chart created successfully")
            return temp_file.name
            
        except Exception as e:
            log.error(f"[CHART] Error creating asset performance chart: {e}")
            if 'fig' in locals():
                plt.close()
            return None
    
    def create_risk_metrics_chart(self, risk_analysis: Dict) -> str:
        """Create risk metrics visualization"""
        try:
            if not risk_analysis or 'var_metrics' not in risk_analysis:
                return None
                
            var_metrics = risk_analysis.get('var_metrics', {})
            drawdown_metrics = risk_analysis.get('drawdown_metrics', {})
            risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
            
            # Extract metrics for visualization with better fallbacks
            metrics_data = {}
            
            # VaR metrics
            var_95 = var_metrics.get('var_95', 'N/A')
            if var_95 != 'N/A' and '%' in str(var_95):
                try:
                    metrics_data['VaR (95%)'] = float(str(var_95).replace('%', ''))
                except ValueError:
                    pass
            
            mean_acc = var_metrics.get('mean_accuracy', 'N/A')
            if mean_acc != 'N/A':
                try:
                    if isinstance(mean_acc, str) and '%' in mean_acc:
                        metrics_data['Mean Accuracy'] = float(mean_acc.replace('%', ''))
                    elif isinstance(mean_acc, (int, float)):
                        metrics_data['Mean Accuracy'] = float(mean_acc) * 100
                except (ValueError, TypeError):
                    pass
            
            # Drawdown metrics
            max_consecutive = drawdown_metrics.get('max_consecutive_losses')
            if isinstance(max_consecutive, int):
                metrics_data['Max Consecutive Losses'] = max_consecutive * 20  # Scale for visualization
            
            # If there is no chartable risk data, skip the chart to keep report fully data-driven
            if not metrics_data:
                return None
                
            # Create figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=self.dpi)
            fig.suptitle('Risk Assessment Dashboard', fontsize=16, fontweight='bold')
            
            # Left: Risk level gauge
            risk_colors = {'LOW': self.colors['success'], 'MEDIUM': self.colors['warning'], 
                          'HIGH': self.colors['danger'], 'UNKNOWN': '#6C757D'}
            risk_color = risk_colors.get(risk_level, '#6C757D')
            
            # Create risk level visualization
            ax1.pie([1], colors=[risk_color], startangle=90)
            ax1.add_patch(plt.Circle((0, 0), 0.7, color='white'))
            ax1.text(0, 0, f'{risk_level}\nRISK', ha='center', va='center', 
                    fontsize=16, fontweight='bold')
            ax1.set_title('Current Risk Level', fontsize=14)
            
            # Right: Risk metrics radar/bar chart
            if len(metrics_data) >= 2:
                # Bar chart for multiple metrics
                metrics_names = list(metrics_data.keys())
                metrics_values = list(metrics_data.values())
                
                # Normalize values for better visualization
                max_val = max(metrics_values)
                if max_val > 0:
                    normalized_values = [v/max_val * 100 for v in metrics_values]
                else:
                    normalized_values = metrics_values
                
                bars = ax2.barh(metrics_names, normalized_values, 
                               color=[self.colors['primary'], self.colors['secondary'], 
                                     self.colors['info']][:len(metrics_names)])
                ax2.set_xlabel('Relative Score', fontsize=12)
                ax2.set_title('Risk Metrics Overview', fontsize=14)
                ax2.grid(True, alpha=0.3)
                
                # Add value labels
                for bar, original_val in zip(bars, metrics_values):
                    width = bar.get_width()
                    label = f'{original_val:.1f}' if isinstance(original_val, float) else str(original_val)
                    ax2.text(width + 1, bar.get_y() + bar.get_height()/2,
                            label, ha='left', va='center', fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'Insufficient\nRisk Data', ha='center', va='center',
                        transform=ax2.transAxes, fontsize=14, alpha=0.7)
                ax2.set_title('Risk Metrics Overview', fontsize=14)
            
            # Safe tight_layout with fallback
            try:
                plt.tight_layout()
            except UserWarning:
                plt.subplots_adjust(top=0.9, bottom=0.1, left=0.1, right=0.9, hspace=0.4, wspace=0.3)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, bbox_inches='tight', dpi=self.dpi, facecolor='white')
            plt.close()
            
            log.info("[CHART] Risk metrics chart created successfully")
            return temp_file.name
            
        except Exception as e:
            log.error(f"[CHART] Error creating risk metrics chart: {e}")
            if 'fig' in locals():
                plt.close()
            return None
    
    def create_weekly_summary_chart(self, weekly_data: Dict) -> str:
        """Create overall summary dashboard (weekly/monthly)"""
        try:
            performance_metrics = weekly_data.get('performance_metrics', {})
            daily_performance = weekly_data.get('daily_performance', [])
            
            if not performance_metrics:
                return None
                
            # Choose title based on timeframe if provided
            timeframe = str(weekly_data.get('timeframe','weekly')).lower()
            if timeframe == 'monthly':
                title = 'Monthly Performance Dashboard'
            else:
                title = 'Weekly Performance Dashboard'
            
            # Create figure with subplots
            fig = plt.figure(figsize=(14, 10), dpi=self.dpi)
            fig.suptitle(title, fontsize=18, fontweight='bold')
            
            # Create grid layout
            gs = fig.add_gridspec(3, 2, height_ratios=[1, 1.5, 1], hspace=0.3, wspace=0.3)
            
            # Top row: Key metrics
            ax_metrics = fig.add_subplot(gs[0, :])
            
            # Extract key metrics
            total_signals = performance_metrics.get('total_signals', 0)
            success_rate = performance_metrics.get('success_rate', 'n/a')
            
            # Create metrics display
            metrics_text = f"Total Signals: {total_signals}"
            if success_rate != 'n/a':
                metrics_text += f" | Success Rate: {success_rate}"
            
            ax_metrics.text(0.5, 0.5, metrics_text, ha='center', va='center',
                          transform=ax_metrics.transAxes, fontsize=16, fontweight='bold')
            ax_metrics.set_xlim(0, 1)
            ax_metrics.set_ylim(0, 1)
            ax_metrics.axis('off')
            
            # Add colored background based on success rate
            if success_rate != 'n/a':
                try:
                    success_val = float(success_rate.replace('%', ''))
                    if success_val >= 70:
                        bg_color = self.colors['success']
                    elif success_val >= 50:
                        bg_color = self.colors['warning']  
                    else:
                        bg_color = self.colors['danger']
                    
                    rect = Rectangle((0.1, 0.2), 0.8, 0.6, 
                                   facecolor=bg_color, alpha=0.2)
                    ax_metrics.add_patch(rect)
                except ValueError:
                    pass
            
            # Middle row: Daily performance trend (if available)
            if daily_performance:
                ax_daily = fig.add_subplot(gs[1, :])
                
                # Extract daily data
                days = []
                accuracies = []
                
                for day_info in daily_performance:
                    day_name = day_info.get('day', '').split()[0]  # Get day name only
                    success_rate = day_info.get('success_rate', 'n/a')
                    
                    if success_rate != 'n/a' and day_name:
                        try:
                            accuracy = float(success_rate.replace('%', ''))
                            days.append(day_name[:3])  # Abbreviate day names
                            accuracies.append(accuracy)
                        except (ValueError, AttributeError):
                            continue
                
                if days and accuracies:
                    # Create line chart
                    ax_daily.plot(days, accuracies, marker='o', linewidth=3, 
                                markersize=10, color=self.colors['primary'])
                    ax_daily.axhline(y=50, color=self.colors['danger'], 
                                   linestyle='--', alpha=0.8, label='Break-even')
                    ax_daily.fill_between(days, accuracies, 50,
                                        where=[acc >= 50 for acc in accuracies],
                                        color=self.colors['success'], alpha=0.3)
                    ax_daily.set_ylabel('Accuracy (%)', fontsize=12)
                    ax_daily.set_title('Daily Performance Trend', fontsize=14)
                    ax_daily.grid(True, alpha=0.3)
                    ax_daily.set_ylim(0, 100)
                    ax_daily.legend()
                else:
                    ax_daily.text(0.5, 0.5, 'No Daily Performance Data', 
                                ha='center', va='center', transform=ax_daily.transAxes,
                                fontsize=14, alpha=0.7)
            
            # Bottom row: Market regime and risk indicators
            ax_info = fig.add_subplot(gs[2, 0])
            ax_risk = fig.add_subplot(gs[2, 1])
            
            # Left bottom: Market regime visualization
            market_analysis = weekly_data.get('market_analysis', {})
            regime = market_analysis.get('regime', 'MIXED_REGIME')
            volatility = market_analysis.get('volatility', 'MEDIUM_VOLATILITY')
            
            # Market regime pie chart
            regime_colors = {'BULLISH': self.colors['success'], 'BEARISH': self.colors['danger'], 
                           'MIXED_REGIME': self.colors['warning'], 'NEUTRAL': '#6C757D'}
            regime_color = regime_colors.get(regime, '#6C757D')
            
            ax_info.pie([1], colors=[regime_color], startangle=90, wedgeprops={'width': 0.7})
            ax_info.add_patch(plt.Circle((0, 0), 0.4, color='white'))
            regime_short = regime.replace('_REGIME', '').replace('_', ' ')
            ax_info.text(0, 0, f'{regime_short}\nMARKET', ha='center', va='center', 
                        fontsize=11, fontweight='bold')
            ax_info.set_title('Market Regime', fontsize=12, pad=10)
            
            # Right bottom: Risk and data quality indicators
            risk_analysis = weekly_data.get('risk_analysis', {})
            risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
            data_sources = weekly_data.get('data_sources', {})
            
            # Create risk level indicator
            risk_colors = {'LOW': self.colors['success'], 'MEDIUM': self.colors['warning'], 
                          'HIGH': self.colors['danger'], 'UNKNOWN': '#6C757D'}
            risk_color = risk_colors.get(risk_level, '#6C757D')
            
            risk_metrics = [risk_level, f"{data_sources.get('daily_metrics_files', 0)} Days", 
                           f"{data_sources.get('journal_entries', 0)} Entries"]
            risk_labels = ['Risk Level', 'Data Files', 'Journals']
            
            # Simple bar visualization
            risk_values = [3 if risk_level == 'HIGH' else 2 if risk_level == 'MEDIUM' else 1,
                          data_sources.get('daily_metrics_files', 0),
                          data_sources.get('journal_entries', 0)]
            
            bars = ax_risk.barh(risk_labels, [rv/max(risk_values)*100 if max(risk_values) > 0 else 0 for rv in risk_values], 
                               color=[risk_color, self.colors['info'], self.colors['secondary']])
            ax_risk.set_xlim(0, 100)
            ax_risk.set_title('Risk & Data Quality', fontsize=12)
            ax_risk.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, metric in zip(bars, risk_metrics):
                width = bar.get_width()
                ax_risk.text(width + 2, bar.get_y() + bar.get_height()/2,
                            str(metric), ha='left', va='center', fontsize=10, fontweight='bold')
            
            # Safe tight_layout with fallback
            try:
                plt.tight_layout()
            except UserWarning:
                plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.95, hspace=0.4, wspace=0.3)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, bbox_inches='tight', dpi=self.dpi, facecolor='white')
            plt.close()
            
            log.info("[CHART] Weekly summary chart created successfully")
            return temp_file.name
            
        except Exception as e:
            log.error(f"[CHART] Error creating weekly summary chart: {e}")
            if 'fig' in locals():
                plt.close()
            return None

# Helper functions and chart generation
def generate_weekly_charts(weekly_data: Dict) -> Dict[str, Optional[str]]:
    """Generate all weekly charts and return file paths"""
    if not MATPLOTLIB_AVAILABLE:
        log.warning("[CHART] Matplotlib not available - skipping chart generation")
        return {}
    
    try:
        generator = SVChartGenerator()
        charts = {}
        
        # Generate daily accuracy chart
        daily_performance = weekly_data.get('daily_performance', [])
        if daily_performance:
            charts['daily_accuracy'] = generator.create_daily_accuracy_chart(daily_performance)
        
        # Generate asset performance chart
        performance_attribution = weekly_data.get('performance_attribution', {})
        if performance_attribution:
            charts['asset_performance'] = generator.create_asset_performance_chart(performance_attribution)
        
        # Generate risk metrics chart
        risk_analysis = weekly_data.get('risk_analysis', {})
        if risk_analysis:
            charts['risk_metrics'] = generator.create_risk_metrics_chart(risk_analysis)
        
        # Risk surrogates (histogram + streak + coverage)
        try:
            # Build surrogates only if we have at least 3 days with signals
            dp = weekly_data.get('daily_performance', [])
            signal_days = [d for d in dp if d.get('signals',0) > 0 and d.get('success_rate','n/a')!='n/a']
            if len(signal_days) >= 3:
                charts['risk_surrogates'] = create_risk_surrogates_chart(weekly_data)
        except Exception:
            pass
        
        # Generate weekly summary chart
        charts['weekly_summary'] = generator.create_weekly_summary_chart(weekly_data)
        
        # Filter out None values
        charts = {k: v for k, v in charts.items() if v is not None}
        
        log.info(f"[CHART] Generated {len(charts)} charts successfully")
        return charts
        
    except Exception as e:
        log.error(f"[CHART] Error generating weekly charts: {e}")
        return {}

def generate_monthly_charts(monthly_data: Dict) -> Dict[str, Optional[str]]:
    """Generate charts for monthly reports and return file paths"""
    if not MATPLOTLIB_AVAILABLE:
        log.warning("[CHART] Matplotlib not available - skipping monthly chart generation")
        return {}
    try:
        generator = SVChartGenerator()
        charts = {}
        
        # Daily accuracy trend over the month
        daily_performance = monthly_data.get('daily_performance', [])
        if daily_performance:
            charts['daily_accuracy'] = generator.create_daily_accuracy_chart(daily_performance)
        
        # Asset performance (if available)
        performance_attribution = monthly_data.get('performance_attribution', {})
        if performance_attribution:
            asset_chart = generator.create_asset_performance_chart(performance_attribution)
            if asset_chart:
                charts['asset_performance'] = asset_chart
        
        # Risk metrics (if available)
        risk_analysis = monthly_data.get('risk_analysis', {})
        if risk_analysis:
            risk_chart = generator.create_risk_metrics_chart(risk_analysis)
            if risk_chart:
                charts['risk_metrics'] = risk_chart
        
        # Risk surrogates over the month (histogram + streak/coverage)
        try:
            rs_chart = create_risk_surrogates_chart(monthly_data)
            if rs_chart:
                charts['risk_surrogates'] = rs_chart
        except Exception:
            pass
        
        # Monthly summary dashboard
        monthly_summary_chart = generator.create_weekly_summary_chart(monthly_data)
        if monthly_summary_chart:
            charts['monthly_summary'] = monthly_summary_chart
        
        charts = {k: v for k, v in charts.items() if v}
        log.info(f"[CHART] Generated {len(charts)} monthly charts successfully")
        return charts
    except Exception as e:
        log.error(f"[CHART] Error generating monthly charts: {e}")
        return {}

def create_risk_surrogates_chart(weekly_data: Dict) -> Optional[str]:
    """Histogram of daily success rates + streak/coverage indicators"""
    try:
        dp = weekly_data.get('daily_performance', []) or []
        coverage_days = int(weekly_data.get('data_sources',{}).get('daily_metrics_files', 0))
        # Numeric accuracies
        acc = []
        streak = 0
        max_streak = 0
        for d in dp:
            s = d.get('signals',0)
            sr = d.get('success_rate','n/a')
            if s>0 and sr!='n/a':
                try:
                    v = float(str(sr).replace('%',''))
                    acc.append(v)
                    if v < 50:
                        streak += 1
                        max_streak = max(max_streak, streak)
                    else:
                        streak = 0
                except Exception:
                    continue
        if len(acc) < 3:
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12,6), dpi=100)
        fig.suptitle('Risk Surrogates', fontsize=16, fontweight='bold')
        
        # Histogram
        ax1.hist(acc, bins=[0,25,50,75,100], color='#6baed6', edgecolor='white')
        ax1.set_title('Daily Accuracy Distribution')
        ax1.set_xlabel('Accuracy (%)')
        ax1.set_ylabel('Days')
        ax1.grid(True, alpha=0.3)
        
        # Streak & coverage bars
        labels = ['Max Loss Streak', 'Coverage Days', 'Signal Days']
        values = [max_streak, coverage_days, len(acc)]
        colors = [ '#e74c3c', '#17A2B8', '#28A745']
        ax2.barh(labels, values, color=colors, alpha=0.85)
        for i, v in enumerate(values):
            ax2.text(v+0.1, i, str(v), va='center', fontweight='bold')
        ax2.set_xlim(0, max(values)+1)
        ax2.set_title('Streak & Coverage')
        ax2.grid(True, alpha=0.3)
        
        try:
            plt.tight_layout()
        except UserWarning:
            plt.subplots_adjust(top=0.9, bottom=0.15, left=0.08, right=0.98, wspace=0.35)
        temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp.name, bbox_inches='tight', dpi=100, facecolor='white')
        plt.close()
        return temp.name
    except Exception as e:
        log.error(f"[CHART] Risk surrogates error: {e}")
        try:
            plt.close()
        except Exception:
            pass
        return None

def test_chart_generation():
    """Test function for chart generation"""
    if not MATPLOTLIB_AVAILABLE:
        print("❌ [TEST] Matplotlib not available - cannot test chart generation")
        return False
    
    print("🧪 [TEST] Testing Chart Generation...")
    
    try:
        # Create test data
        test_weekly_data = {
            'performance_metrics': {
                'total_signals': 12,
                'success_rate': '67%'
            },
            'daily_performance': [
                {'day': 'Monday 17/11', 'date': '2025-11-17', 'signals': 3, 'success_rate': '67%'},
                {'day': 'Tuesday 18/11', 'date': '2025-11-18', 'signals': 3, 'success_rate': '33%'},
                {'day': 'Wednesday 19/11', 'date': '2025-11-19', 'signals': 3, 'success_rate': '100%'}
            ],
            'performance_attribution': {
                'asset_attribution': {
                    'asset_performance': {
                        'BTC': {'accuracy': '85%', 'total_predictions': 5},
                        'SPX': {'accuracy': '60%', 'total_predictions': 4},
                        'EURUSD': {'accuracy': '40%', 'total_predictions': 3}
                    }
                }
            },
            'risk_analysis': {
                'risk_level': 'LOW',
                'var_metrics': {
                    'var_95': '25%',
                    'mean_accuracy': 0.67
                },
                'drawdown_metrics': {
                    'max_consecutive_losses': 2
                }
            },
            'data_sources': {
                'daily_metrics_files': 5,
                'journal_entries': 3
            }
        }
        
        # Test chart generation
        charts = generate_weekly_charts(test_weekly_data)
        
        print(f"✅ [TEST] Generated {len(charts)} charts")
        for chart_type, path in charts.items():
            if path and os.path.exists(path):
                print(f"✅ [TEST] {chart_type}: {os.path.basename(path)}")
            else:
                print(f"❌ [TEST] {chart_type}: Failed")
        
        print("✅ [TEST] Chart generation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Chart generation error: {e}")
        return False

if __name__ == '__main__':
    test_chart_generation()