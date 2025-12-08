#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script per generare report PDF settimanali e mensili
"""

import sys
import os
from datetime import datetime, timedelta

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modules'))

from pdf_generator import SVPDFGeneratetor

def test_weekly_report():
    """Test generazione report settimanale"""
    print("🧪 Testing weekly PDF report generation...")
    
    # Create PDF generator for weekly reports
    weekly_generator = SVPDFGeneratetor(timeframe='weekly')
    
    # Enhanced test data for weekly report with all new sections
    weekly_test_data = {
        'week_start': '2025-10-26',
        'week_end': '2025-11-01',
        'weekly_summary': 'Settimana caratterizzata da forte volatilità sui mercati ma con performance complessivamente positive. Il sistema SV ha dimostrato resilienza nelle condizioni di mercato turbolente, mantenendo un alto tasso di successo nei segnali generati.',
        'performance_metrics': {
            'total_trades': 45,
            'successful_trades': 34,
            'success_rate': '75.6%',
            'total_profit': '+12.5%',
            'max_drawdown': '-2.3%',
            'sharpe_ratio': 1.85,
            'best_day': 'Martedì (+3.2%)',
            'worst_day': 'Giovedì (-1.1%)'
        },
        'daily_performance': [
            {'day': 'Lunedì', 'trades': 8, 'pnl': '+1.8%', 'success_rate': '75%', 'notes': 'Apertura positiva'},
            {'day': 'Martedì', 'trades': 10, 'pnl': '+3.2%', 'success_rate': '80%', 'notes': 'Migliore giornata'},
            {'day': 'Mercoledì', 'trades': 12, 'pnl': '+2.1%', 'success_rate': '67%', 'notes': 'Volatilità elevata'},
            {'day': 'Giovedì', 'trades': 9, 'pnl': '-1.1%', 'success_rate': '56%', 'notes': 'Correzione mercato'},
            {'day': 'Venerdì', 'trades': 6, 'pnl': '+6.5%', 'success_rate': '100%', 'notes': 'Recupero forte'}
        ],
        'market_analysis': {
            'regime': 'BULL MARKET with HIGH VOLATILITY',
            'volatility': 'ELEVATED (VIX: 28)',
            'trend_strength': 'STRONG UPWARD',
            'sector_rotation': 'TECH LEADING, ENERGY LAGGING'
        },
        'risk_metrics': {
            'risk_level': 'MODERATE',
            'var_95': '-2.8%',
            'max_position': '15% per trade',
            'correlation_risk': 'LOW'
        },
        'key_events': [
            {'date': '26/10', 'description': 'Fed Meeting Minutes Release', 'impact': 'POSITIVE'},
            {'date': '28/10', 'description': 'Big Tech Earnings Season', 'impact': 'STRONG POSITIVE'},
            {'date': '30/10', 'description': 'GDP Data Release', 'impact': 'NEUTRAL'},
            {'date': '01/11', 'description': 'Employment Report', 'impact': 'POSITIVE'}
        ],
        'next_week_outlook': 'La prossima settimana si prevede continui la tendenza positiva supportata da dati macro solidi. Focus particolare sui titoli tecnologici che stanno guidando il mercato.',
        'next_week_strategy': [
            'Mantenere posizioni long sui titoli tech di qualità',
            'Monitorare attentamente i livelli di volatilità',
            'Preparare strategie difensive per eventuali correzioni',
            'Sfruttare opportunità nel settore energetico'
        ],
        'action_items': [
            {'priority': 'HIGH', 'task': 'Review Risk Parameters', 'description': 'Aggiornare i parametri di rischio per gestire meglio la volatilità'},
            {'priority': 'MEDIUM', 'task': 'Sector Analysis', 'description': 'Analisi approfondita rotazione settoriale'},
            {'priority': 'LOW', 'task': 'Model Optimization', 'description': 'Ottimizzazione algoritmi per mercati volatili'}
        ]
    }
    
    # Generate weekly PDF
    pdf_path = weekly_generator.Createte_weekly_report_pdf(weekly_test_data)
    
    if pdf_path and os.path.exists(pdf_path):
        print(f"✅ Weekly PDF created successfully: {pdf_path}")
        return True
    else:
        print("❌ Weekly PDF creation failed")
        return False

def test_monthly_report():
    """Test generazione report mensile (da implementare)"""
    print("🧪 Testing monthly PDF report generation...")
    
    # Create PDF generator for monthly reports
    monthly_generator = SVPDFGeneratetor(timeframe='monthly')
    
    # Test data for monthly report
    monthly_test_data = {
        'month': 'Ottobre 2025',
        'month_start': '2025-10-01',
        'month_end': '2025-10-31',
        'monthly_summary': 'Ottobre si è rivelato un mese positivo per le strategie SV. Mercati in crescita con performance superiori alle aspettative.',
        'performance_metrics': {
            'total_trades': 180,
            'successful_trades': 135,
            'success_rate': '75.0%',
            'monthly_return': '+8.7%',
            'volatility': '14.5%',
            'max_drawdown': '-3.2%',
            'sharpe_ratio': 2.1,
            'best_week': 'Settimana 3 (+4.1%)',
            'worst_week': 'Settimana 1 (-0.8%)',
            'sectors_performance': {
                'Technology': '+12.3%',
                'Finance': '+6.8%',
                'Healthcare': '+5.2%',
                'Energy': '+3.1%'
            }
        },
        'market_analysis': {
            'dominant_trend': 'BULLISH',
            'market_regime': 'RISK-ON',
            'volatility_level': 'NORMAL',
            'correlation': 'MODERATE'
        },
        'next_month_outlook': 'Novembre dovrebbe continuare con sentiment positivo. Attenzione agli eventi geopolitici e ai dati inflazione.'
    }
    
    # Try to generate monthly PDF
    try:
        pdf_path = monthly_generator.create_monthly_report_pdf(monthly_test_data)
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ Monthly PDF created successfully: {pdf_path}")
            return True
        else:
            print("❌ Monthly PDF creation failed")
            return False
    except AttributeError:
        print("⚠️ Monthly PDF function not implemented yet - will implement it")
        return False

if __name__ == '__main__':
    print("🚀 Starting PDF reports test...\n")
    
    # Test weekly report
    weekly_success = test_weekly_report()
    print()
    
    # Test monthly report  
    monthly_success = test_monthly_report()
    print()
    
    print(f"📊 Test Results:")
    print(f"Weekly Report: {'✅' if weekly_success else '❌'}")
    print(f"Monthly Report: {'✅' if monthly_success else '❌'}")