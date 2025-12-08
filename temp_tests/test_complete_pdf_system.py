#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete End-to-End Test for PDF + Telegram System
"""

import sys
import os
import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'modules'))

def test_complete_weekly_flow():
    """Test complete weekly PDF generation + Telegram sending"""
    print("📊 [E2E] Testing Complete Weekly Flow...")
    
    try:
        # Step 1: Generate weekly report with PDF
        from weekly_generator import Generatete_weekly_report
        
        print("🔄 [E2E] Generating weekly report...")
        report = Generatete_weekly_report()
        
        print(f"✅ [E2E] Weekly report generated: {len(report)} chars")
        
        # Step 2: Check if PDF was mentioned in output
        if "PDF Report:" in report:
            print("✅ [E2E] PDF generation detected in report")
            
            if "PDF sent to Telegram" in report:
                print("✅ [E2E] Telegram integration successful")
                return True
            elif "PDF Telegram sending failed" in report or "Telegram sending error" in report:
                print("⚠️ [E2E] PDF generated but Telegram sending failed")
                return False
            else:
                print("⚠️ [E2E] PDF generated but no Telegram status found")
                return False
        else:
            print("❌ [E2E] No PDF generation detected")
            return False
            
    except Exception as e:
        print(f"❌ [E2E] Complete weekly flow failed: {e}")
        return False

def test_complete_monthly_flow():
    """Test complete monthly PDF generation + Telegram sending"""
    print("📋 [E2E] Testing Complete Monthly Flow...")
    
    try:
        # Step 1: Generate monthly report with PDF
        from monthly_generator import Generatete_monthly_report
        
        print("🔄 [E2E] Generating monthly report...")
        report = Generatete_monthly_report()
        
        print(f"✅ [E2E] Monthly report generated: {len(report)} chars")
        
        # Step 2: Check if PDF was mentioned in output
        if "PDF Report:" in report:
            print("✅ [E2E] PDF generation detected in report")
            
            if "PDF sent to Telegram" in report:
                print("✅ [E2E] Telegram integration successful")
                return True
            elif "PDF Telegram sending failed" in report or "Telegram sending error" in report:
                print("⚠️ [E2E] PDF generated but Telegram sending failed")
                return False
            else:
                print("⚠️ [E2E] PDF generated but no Telegram status found")
                return False
        else:
            print("❌ [E2E] No PDF generation detected")
            return False
            
    except Exception as e:
        print(f"❌ [E2E] Complete monthly flow failed: {e}")
        return False

def test_manual_pdf_telegram():
    """Test manual PDF creation and Telegram sending"""
    print("🔧 [MANUAL] Testing Manual PDF + Telegram...")
    
    try:
        # Create a test PDF
        from pdf_generator import Createte_weekly_pdf
        import datetime
        
        test_data = {
            'week_start': datetime.datetime.now(),
            'week_end': datetime.datetime.now(),
            'weekly_summary': 'End-to-End Test PDF Report',
            'performance_metrics': {
                'weekly_return': '+2.1%',
                'ml_accuracy': '82%',
                'max_drawdown': '-1.8%'
            }
        }
        
        pdf_path = Createte_weekly_pdf(test_data)
        if not pdf_path:
            print("❌ [MANUAL] PDF creation failed")
            return False
        
        print(f"✅ [MANUAL] PDF created: {pdf_path}")
        
        # Send to Telegram
        from telegram_handler import get_telegram_handler
        telegram = get_telegram_handler()
        
        result = telegram.send_document(
            file_path=pdf_path,
            caption="E2E Test - Weekly Report PDF",
            content_type='weekly',
            metadata={'test': True}
        )
        
        if result.get('success'):
            print(f"✅ [MANUAL] PDF sent to Telegram: {result.get('filename')}")
            print(f"📊 [MANUAL] File size: {result.get('file_size')} bytes")
            return True
        else:
            print(f"❌ [MANUAL] Telegram sending failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ [MANUAL] Manual test failed: {e}")
        return False

def check_file_structure():
    """Check if PDF file structure is correct"""
    print("📁 [STRUCTURE] Checking PDF file structure...")
    
    try:
        import os
        
        # Check if directories exist
        weekly_dir = os.path.join(project_root, 'reports', '2_weekly')
        monthly_dir = os.path.join(project_root, 'reports', '3_monthly')
        
        if os.path.exists(weekly_dir):
            print("✅ [STRUCTURE] Weekly directory exists")
            files = os.listdir(weekly_dir)
            pdf_files = [f for f in files if f.endswith('.pdf')]
            print(f"📄 [STRUCTURE] {len(pdf_files)} weekly PDF files found")
        else:
            print("⚠️ [STRUCTURE] Weekly directory missing")
        
        if os.path.exists(monthly_dir):
            print("✅ [STRUCTURE] Monthly directory exists")
            files = os.listdir(monthly_dir)
            pdf_files = [f for f in files if f.endswith('.pdf')]
            print(f"📄 [STRUCTURE] {len(pdf_files)} monthly PDF files found")
        else:
            print("⚠️ [STRUCTURE] Monthly directory missing")
        
        return True
        
    except Exception as e:
        print(f"❌ [STRUCTURE] Structure check failed: {e}")
        return False

def main():
    """Run complete system tests"""
    print("🚀 [E2E] Starting Complete PDF + Telegram System Tests...\n")
    
    tests = [
        ("File Structure Check", check_file_structure),
        ("Manual PDF + Telegram", test_manual_pdf_telegram),
        ("Complete Weekly Flow", test_complete_weekly_flow),
        ("Complete Monthly Flow", test_complete_monthly_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Running: {test_name}")
        print('='*50)
        
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 FINAL TEST SUMMARY")
    print('='*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 SUCCESS: All PDF + Telegram integration tests passed!")
        print("🚀 System is fully operational and ready for production!")
        return True
    else:
        print("⚠️ WARNING: Some tests failed - review implementation")
        return False

if __name__ == '__main__':
    main()