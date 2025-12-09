#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Morning Report  
Script individuale to generate morning report (08:30)
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
    """Main function for morning report trigger"""
    print("ðŸŒ… SV - TRIGGER MORNING REPORT")
    print("=" * 50)
    
    try:
        # Import modules
        from sv_scheduler import is_time_for, mark_sent, get_status
        from daily_generator import generate_morning
        from telegram_handler import TelegramHandler
        
        # Check scheduler
        status = get_status()
        print(f"ðŸ• Current time: {status['current_time']}")
        print(f"ðŸ“… Date: {status['current_date']} ({status['day_of_week']})")
        
        # Check if it's time for morning report
        if is_time_for('morning'):
            print("✅ Time for morning report - generating content...")
            
            # Initialize telegram handler
            telegram = TelegramHandler()
            
            # Generate morning content
            messages = generate_morning()
            
            if messages:
                print(f"📝 Generated {len(messages)} morning messages")
                
                # Send to Telegram - send each message individually
                all_success = True
                for i, msg in enumerate(messages, 1):
                    result = telegram.send_message(msg, content_type="morning")
                    if result.get('success'):
                        print(f"✅ Morning message {i}/{len(messages)} sent")
                    else:
                        print(f"❌ Morning message {i}/{len(messages)} failed")
                        all_success = False
                
                if all_success:
                    # Mark as sent
                    mark_sent('morning')
                    print("✅ Morning report sent successfully and marked as complete")
                else:
                    print("❌ Failed to send some morning messages to Telegram")
                    return False
            else:
                print("❌ Failed to generate morning content")
                return False
        else:
            print("â° Not time for morning report yet")
            pending = status['pending_content']
            if 'morning' in pending:
                print("ðŸ“‹ Morning report is in pending queue")
            else:
                print("ðŸ“‹ Morning report not scheduled or already sent")
        
        return True
        
    except ImportError as e:
        print(f"âŒ Missing dependencies: {e}")
        return False
    except Exception as e:
        log.error(f"âŒ Error in morning trigger: {e}")
        print(f"âŒ Morning trigger failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)



