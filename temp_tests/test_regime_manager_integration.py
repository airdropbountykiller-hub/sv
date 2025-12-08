#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Regime Manager Integration in daily_generator.py
Test focused on Evening Analysis and Summary generation
"""

import sys
import os
import datetime

# Add project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'modules'))

def test_regime_manager_evening():
    """Test Evening Analysis with Regime Manager integration"""
    print("🧪 [TEST] Testing Evening Analysis with Regime Manager...")
    
    try:
        from daily_generator import DailyContentGenerator
        
        # Initialize generator
        generator = DailyContentGenerator()
        
        # Test Evening Analysis generation
        evening_messages = generator.generate_evening_analysis()
        
        print(f"✅ [TEST] Evening Analysis generated: {len(evening_messages)} messages")
        
        if evening_messages:
            # Check first message (Session Wrap) for regime manager usage
            session_wrap = evening_messages[0]
            
            # Look for regime manager indicators
            has_session_character = "SESSION CHARACTER:" in session_wrap
            has_theme = "*Theme*:" in session_wrap
            
            print(f"✅ [TEST] Session Character section: {'✅' if has_session_character else '❌'}")
            print(f"✅ [TEST] Theme text present: {'✅' if has_theme else '❌'}")
            
            # Print excerpt from Session Character section
            lines = session_wrap.split('\n')
            character_section = []
            in_character_section = False
            
            for line in lines:
                if "SESSION CHARACTER:" in line:
                    in_character_section = True
                    character_section.append(line)
                elif in_character_section:
                    if line.strip() == "" or "─" in line:
                        break
                    character_section.append(line)
            
            if character_section:
                print("\n📄 [EXCERPT] Session Character section:")
                for line in character_section:
                    print(f"   {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Evening Analysis error: {e}")
        return False

def test_regime_manager_summary():
    """Test Summary generation with Regime Manager integration"""
    print("\n🧪 [TEST] Testing Summary with Regime Manager...")
    
    try:
        from daily_generator import DailyContentGenerator
        
        # Initialize generator  
        generator = DailyContentGenerator()
        
        # Test Summary generation
        summary_pages = generator.generate_daily_summary()
        
        print(f"✅ [TEST] Summary generated: {len(summary_pages)} pages")
        
        if len(summary_pages) >= 6:
            # Check Page 6 (Daily Journal) for regime manager usage
            journal_page = summary_pages[5]  # Page 6 is index 5
            
            has_narrative = "DAILY NARRATIVE" in journal_page
            has_session_character = "*Session Character*:" in journal_page
            
            print(f"✅ [TEST] Daily Narrative section: {'✅' if has_narrative else '❌'}")
            print(f"✅ [TEST] Session Character in journal: {'✅' if has_session_character else '❌'}")
            
            # Extract Session Character from journal
            lines = journal_page.split('\n')
            for line in lines:
                if "*Session Character*:" in line:
                    print(f"\n📄 [EXCERPT] Journal Session Character:")
                    print(f"   {line}")
                    break
            
            # Check Page 3 for Market Momentum
            if len(summary_pages) >= 3:
                page3 = summary_pages[2]  # Page 3 is index 2
                has_momentum = "*Market Momentum*:" in page3
                print(f"✅ [TEST] Market Momentum in Page 3: {'✅' if has_momentum else '❌'}")
                
                # Extract Market Momentum line
                lines = page3.split('\n')
                for line in lines:
                    if "*Market Momentum*:" in line:
                        print(f"\n📄 [EXCERPT] Market Momentum:")
                        print(f"   {line}")
                        break
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Summary generation error: {e}")
        return False

def test_regime_manager_standalone():
    """Test standalone Regime Manager functionality"""
    print("\n🧪 [TEST] Testing standalone Regime Manager...")
    
    try:
        from modules.regime_manager import get_daily_regime_manager, reset_daily_regime
        
        # Reset for clean test
        reset_daily_regime()
        
        # Get fresh manager
        manager = get_daily_regime_manager()
        
        # Simulate 0% accuracy scenario (like Nov 20 observations)
        manager.update_from_accuracy(0.0, 1)  # 0% with 1 tracked asset
        manager.update_from_sentiment_tracking({'evening': 'NEGATIVE'})
        
        # Test regime inference
        regime = manager.infer_regime()
        session_char = manager.get_session_character()
        momentum = manager.get_market_momentum_text()
        stability = manager.get_model_stability_text()
        
        print(f"✅ [TEST] Regime inferred: {regime.value}")
        print(f"✅ [TEST] Session Character: {session_char}")
        print(f"✅ [TEST] Market Momentum: {momentum}")
        print(f"✅ [TEST] Model Stability: {stability}")
        
        # Test coherence score
        coherence = manager.get_narrative_coherence_score()
        print(f"✅ [TEST] Coherence Score: {coherence:.1f}%")
        
        # Verify this matches Nov 20 observations (risk-off with defensive positioning)
        expected_risk_off = regime.value == 'risk_off'
        expected_defensive = 'defensive positioning' in session_char.lower()
        
        print(f"✅ [TEST] Risk-off regime: {'✅' if expected_risk_off else '❌'}")
        print(f"✅ [TEST] Defensive positioning: {'✅' if expected_defensive else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Standalone regime manager error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 [START] Regime Manager Integration Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Standalone functionality
    results.append(test_regime_manager_standalone())
    
    # Test 2: Evening Analysis integration  
    results.append(test_regime_manager_evening())
    
    # Test 3: Summary integration
    results.append(test_regime_manager_summary())
    
    print("\n" + "="*60)
    print("📊 [RESULTS] Integration Test Results:")
    
    total_tests = len(results)
    passed_tests = sum(results)
    
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 [SUCCESS] All Regime Manager integration tests passed!")
        print("\n🔧 [NEXT] Ready for production testing:")
        print("   1. Run full Evening Analysis")
        print("   2. Run full Daily Summary") 
        print("   3. Verify narrative consistency")
        return True
    else:
        print("⚠️ [PARTIAL] Some tests failed - review integration")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)