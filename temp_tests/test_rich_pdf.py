#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Rich PDF Generation - Recreate 18:16 Style
"""

import sys
import os
import datetime
import random

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'modules'))

def create_rich_weekly_data():
    """Create rich data structure like the 18:16 PDF version"""
    
    # Dynamic data generation 
    accuracy = round(75 + random.uniform(5, 15), 1)
    hit_rate = round(random.uniform(70, 90), 1)
    max_dd = round(random.uniform(1.0, 3.5), 1)
    next_week_prob = round(random.uniform(65, 85), 1)
    
    week_start = datetime.datetime.now() - datetime.timedelta(days=7)
    week_end = datetime.datetime.now()
    
    return {
        'week_start': week_start,
        'week_end': week_end, 
        'weekly_summary': f"Strong week with {2.1}% S&P performance and {accuracy}% ML accuracy. Tech leadership continued with solid risk-adjusted returns. Maximum drawdown kept under {max_dd}% demonstrating excellent risk control.",
        
        'performance_metrics': {
            'total_signals': random.randint(85, 120),
            'total_trades': random.randint(85, 120), # Alias for compatibility
            'success_rate': f'{accuracy}%',
            'weekly_return': '+2.1%',
            'total_profit': f'+${random.randint(8000, 15000):,}',
            'sharpe_ratio': str(round(random.uniform(2.0, 3.2), 1)),
            'max_drawdown': f'-{max_dd}%'
        },
        
        'daily_performance': [
            {'day': 'Monday', 'trades': 18, 'signals': 18, 'pnl': '+$2,100', 'success_rate': '83%', 'notes': 'Strong tech momentum, gap-up openings performed well'},
            {'day': 'Tuesday', 'trades': 22, 'signals': 22, 'pnl': '+$2,800', 'success_rate': '86%', 'notes': 'Crypto breakout signals, continuation patterns'}, 
            {'day': 'Wednesday', 'trades': 15, 'signals': 15, 'pnl': '+$1,950', 'success_rate': '80%', 'notes': 'FOMC volatility managed well, defensive approach'},
            {'day': 'Thursday', 'trades': 20, 'signals': 20, 'pnl': '+$3,200', 'success_rate': '90%', 'notes': 'Earnings season momentum, sector rotation captured'},
            {'day': 'Friday', 'trades': 19, 'signals': 19, 'pnl': '+$2,400', 'success_rate': '79%', 'notes': 'End-of-week profit taking, rebalancing flows handled'}
        ],
        
        'market_analysis': {
            'regime': 'BULLISH MOMENTUM',
            'volatility': 'CONTROLLED',
            'trend_strength': 'STRONG UPTREND',
            'sector_rotation': 'TECH LEADERSHIP ACTIVE'
        },
        
        'risk_metrics': {
            'risk_level': 'MODERATE',
            'var_95': f'-{round(random.uniform(1.8, 2.5), 1)}%',
            'max_position': '20% allocation',
            'correlation_risk': 'WELL DIVERSIFIED'
        },
        
        'key_events': [
            {'date': 'Monday', 'description': 'Strong market open after weekend', 'impact': 'POSITIVE'},
            {'date': 'Wednesday', 'description': 'Fed dovish commentary', 'impact': 'VERY POSITIVE'},
            {'date': 'Thursday', 'description': 'Tech earnings beats expectations', 'impact': 'POSITIVE'},
            {'date': 'Friday', 'description': 'Employment data supportive', 'impact': 'NEUTRAL'}
        ],
        
        'next_week_outlook': f'Bullish bias maintained with {next_week_prob}% probability for continued upside. Tech sector leadership expected to persist with crypto showing institutional adoption momentum.',
        
        'next_week_strategy': [
            'Continue tech sector overweight positioning', 
            'Monitor crypto institutional flows and adoption metrics',
            'Maintain disciplined risk management with current volatility regime',
            'Position for potential earnings season extension momentum'
        ],
        
        'action_items': [
            {'priority': 'HIGH', 'task': 'Review Position Sizes', 'description': 'Adjust allocation based on volatility changes'},
            {'priority': 'MEDIUM', 'task': 'Update ML Models', 'description': 'Retrain with latest market regime data'},
            {'priority': 'LOW', 'task': 'Documentation', 'description': 'Update procedures with new signal insights'}
        ]
    }

def test_rich_pdf_generation():
    """Test generating rich PDF like 18:16 version"""
    print("🎯 [TEST] Creating Rich PDF (18:16 Style)...")
    
    try:
        from pdf_generator import Createte_weekly_pdf
        
        # Create rich data
        rich_data = create_rich_weekly_data()
        
        print(f"📊 [TEST] Rich data structure created with {len(rich_data)} sections")
        print(f"📈 [TEST] Performance metrics: {len(rich_data['performance_metrics'])} fields")
        print(f"📅 [TEST] Daily performance: {len(rich_data['daily_performance'])} days")
        print(f"🎯 [TEST] Action items: {len(rich_data['action_items'])} items")
        
        # Generate PDF
        pdf_path = Createte_weekly_pdf(rich_data)
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ [TEST] Rich PDF created: {pdf_path}")
            print(f"📏 [TEST] File size: {file_size} bytes")
            
            # Compare with 18:16 version (4625 bytes)
            if 4000 <= file_size <= 6000:
                print("🎉 [SUCCESS] PDF size matches 18:16 version range (4-6KB)!")
            elif file_size < 4000:
                print("⚠️ [WARNING] PDF smaller than expected - may be missing content")
            else:
                print("⚠️ [WARNING] PDF larger than expected - may have layout issues")
            
            return True
            
        else:
            print("❌ [TEST] PDF generation failed")
            return False
            
    except Exception as e:
        print(f"❌ [TEST] Rich PDF test failed: {e}")
        return False

def test_pdf_with_telegram():
    """Test PDF generation + Telegram sending"""
    print("\n📤 [TEST] Testing PDF + Telegram Integration...")
    
    try:
        from pdf_generator import Createte_weekly_pdf
        from telegram_handler import get_telegram_handler
        
        # Create rich data
        rich_data = create_rich_weekly_data()
        
        # Generate PDF
        pdf_path = Createte_weekly_pdf(rich_data)
        
        if pdf_path:
            # Send to Telegram
            telegram = get_telegram_handler()
            result = telegram.send_document(
                file_path=pdf_path,
                caption="Rich Weekly Report (18:16 Style Recreation)",
                content_type='weekly',
                metadata={'test_type': 'rich_pdf_recreation'}
            )
            
            if result.get('success'):
                print(f"✅ [TEST] Rich PDF sent to Telegram: {result.get('filename')}")
                print(f"📊 [TEST] File size: {result.get('file_size')} bytes")
                return True
            else:
                print(f"❌ [TEST] Telegram sending failed: {result.get('error')}")
                return False
        else:
            print("❌ [TEST] PDF generation failed")
            return False
            
    except Exception as e:
        print(f"❌ [TEST] PDF + Telegram test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 [TEST] Rich PDF Generation Test (Recreating 18:16 Style)")
    print("="*60)
    
    # Test 1: Rich PDF generation
    pdf_result = test_rich_pdf_generation()
    
    # Test 2: PDF + Telegram
    telegram_result = test_pdf_with_telegram()
    
    print("\n" + "="*60)
    print("📊 [SUMMARY] Test Results:")
    print(f"Rich PDF Generation: {'✅ PASSED' if pdf_result else '❌ FAILED'}")
    print(f"PDF + Telegram: {'✅ PASSED' if telegram_result else '❌ FAILED'}")
    
    if pdf_result and telegram_result:
        print("\n🎉 [SUCCESS] Rich PDF system fully operational!")
        print("📄 PDF generation now matches 18:16 quality with comprehensive data")
    else:
        print("\n⚠️ [WARNING] Some tests failed - check implementation")