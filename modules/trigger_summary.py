#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Daily Summary
Script individuale per generare daily summary (21:00)
"""

from pathlib import Path
import sys
import os
import logging

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'config' / 'modules'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def main():
    """Main function for daily summary trigger"""
    print("📊 SV - TRIGGER DAILY SUMMARY")
    print("=" * 50)
    
    try:
        # Import modules
        from sv_scheduler import is_time_for, mark_sent, get_status
        from daily_generator import generate_summary
        from telegram_handler import TelegramHandler
        
        # Check scheduler
        status = get_status()
        print(f"🕐 Current time: {status['current_time']}")
        print(f"📅 Date: {status['current_date']} ({status['day_of_week']})")
        
        # Check if it's time for daily summary
        if is_time_for('summary'):
            print("✅ Time for daily summary - generating content...")
            
            # Initialize telegram handler
            telegram = TelegramHandler()
            
            # Generate summary content (returns list of 6 pages/messages)
            messages = generate_summary()
            
            if messages:
                print(f"📝 Generated daily summary: {len(messages)} messages")
                for i, msg in enumerate(messages, 1):
                    print(f"  Message {i}: {len(msg)} chars")
                
                # Send to Telegram - send each message individually
                all_success = True
                for i, msg in enumerate(messages, 1):
                    result = telegram.send_message(msg, content_type="summary")
                    if result.get('success'):
                        print(f"✅ Summary message {i}/{len(messages)} sent")
                    else:
                        print(f"❌ Summary message {i}/{len(messages)} failed")
                        all_success = False
                
                if all_success:
                    # Mark as sent
                    mark_sent('summary')
                    print("✅ Daily summary sent successfully and marked as complete")
                else:
                    print("❌ Failed to send some summary messages to Telegram")
                    return False
            else:
                print("❌ Failed to generate daily summary content")
                return False
        else:
            print("⏰ Not time for daily summary yet")
            pending = status['pending_content']
            if 'summary' in pending:
                print("📋 Daily summary is in pending queue")
            else:
                print("📋 Daily summary not scheduled or already sent")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        return False
    except Exception as e:
        log.error(f"❌ Error in summary trigger: {e}")
        print(f"❌ Summary trigger failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)