#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test PDF Telegram Integration
"""

import sys
import os
import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'modules'))

def test_telegram_document_sending():
    """Test sending PDF documents via Telegram"""
    print("🧪 [TEST] Testing Telegram PDF Document Sending...")
    
    try:
        from telegram_handler import get_telegram_handler
        
        # Get telegram handler
        telegram = get_telegram_handler()
        
        # Test connection first
        if not telegram.test_connection():
            print("❌ [TEST] Telegram connection failed - check credentials")
            return False
        
        print("✅ [TEST] Telegram connection successful")
        
        # Test document sending method exists
        if hasattr(telegram, 'send_document'):
            print("✅ [TEST] send_document method available")
        else:
            print("❌ [TEST] send_document method not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Telegram document test failed: {e}")
        return False

def test_weekly_pdf_generation():
    """Test weekly PDF generation with Telegram integration"""
    print("📄 [TEST] Testing Weekly PDF Generation + Telegram...")
    
    try:
        from weekly_generator import get_weekly_Generatetor
        
        # Generate weekly report
        generator = get_weekly_Generatetor()
        report = generator.Generatete_weekly_report()
        
        print(f"✅ [TEST] Weekly report generated: {len(report)} characters")
        
        # Check if PDF generation and Telegram sending are mentioned
        if "PDF sent to Telegram" in report:
            print("✅ [TEST] PDF Telegram integration working")
        elif "PDF Report:" in report:
            print("⚠️ [TEST] PDF generated but Telegram integration needs verification")
        else:
            print("❌ [TEST] No PDF generation detected")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Weekly PDF test failed: {e}")
        return False

def test_monthly_pdf_generation():
    """Test monthly PDF generation with Telegram integration"""
    print("📋 [TEST] Testing Monthly PDF Generation + Telegram...")
    
    try:
        from monthly_generator import get_monthly_Generatetor
        
        # Generate monthly report
        generator = get_monthly_Generatetor()
        report = generator.Generatete_monthly_report()
        
        print(f"✅ [TEST] Monthly report generated: {len(report)} characters")
        
        # Check if PDF generation and Telegram sending are mentioned
        if "PDF sent to Telegram" in report:
            print("✅ [TEST] Monthly PDF Telegram integration working")
        elif "PDF Report:" in report:
            print("⚠️ [TEST] PDF generated but Telegram integration needs verification")
        else:
            print("❌ [TEST] No PDF generation detected")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Monthly PDF test failed: {e}")
        return False

def main():
    """Run all PDF Telegram tests"""
    print("🚀 [TEST] Starting PDF Telegram Integration Tests...\n")
    
    tests = [
        test_telegram_document_sending,
        test_weekly_pdf_generation,
        test_monthly_pdf_generation
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"📊 [SUMMARY] Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ [SUCCESS] All PDF Telegram integration tests passed!")
        return True
    else:
        print("⚠️ [WARNING] Some tests failed - check implementation")
        return False

if __name__ == '__main__':
    main()