#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Evening Analysis
Script individuale per generare evening analysis (18:30)
"""

import sys
import os
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'config', 'modules'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def main():
    """Main function for evening analysis trigger"""
    print("🌆 SV - TRIGGER EVENING ANALYSIS")
    print("=" * 50)
    
    try:
        # Import modules
        from sv_scheduler import is_time_for, mark_sent, get_status
        from daily_generator import generate_evening
        from telegram_handler import TelegramHandler
        
        # Check scheduler
        status = get_status()
        print(f"🕐 Current time: {status['current_time']}")
        print(f"📅 Date: {status['current_date']} ({status['day_of_week']})")
        
        # Check if it's time for evening analysis
        if is_time_for('evening'):
            print("✅ Time for evening analysis - generating content...")
            
            # Initialize telegram handler
            telegram = TelegramHandler()
            
            # Generate evening content
            messages = generate_evening()
            
            if messages:
                print(f"📝 Generated {len(messages)} evening analysis messages")
                
                # Send to Telegram - send each message individually
                all_success = True
                for i, msg in enumerate(messages, 1):
                    result = telegram.send_message(msg, content_type="evening")
                    if result.get('success'):
                        print(f"✅ Evening message {i}/{len(messages)} sent")
                    else:
                        print(f"❌ Evening message {i}/{len(messages)} failed")
                        all_success = False
                
                if all_success:
                    # Mark as sent
                    mark_sent('evening')
                    print("✅ Evening analysis sent successfully and marked as complete")
                else:
                    print("❌ Failed to send some evening messages to Telegram")
                    return False
            else:
                print("❌ Failed to generate evening analysis content")
                return False
        else:
            print("⏰ Not time for evening analysis yet")
            pending = status['pending_content']
            if 'evening' in pending:
                print("📋 Evening analysis is in pending queue")
            else:
                print("📋 Evening analysis not scheduled or already sent")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        return False
    except Exception as e:
        log.error(f"❌ Error in evening trigger: {e}")
        print(f"❌ Evening trigger failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)