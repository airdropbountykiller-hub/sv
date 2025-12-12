#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Press Review
Script individuale per generare press review (07:00)
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
    """Main function for press_review generation trigger"""
    print("📰 SV - TRIGGER PRESS REVIEW")
    print("=" * 50)
    
    try:
        # Import modules
        from sv_scheduler import is_time_for, mark_sent, get_status
        from daily_generator import generate_press_review_wrapper
        from telegram_handler import TelegramHandler
        
        # Check scheduler
        status = get_status()
        print(f"ðŸ• Current time: {status['current_time']}")
        print(f"ðŸ“… Date: {status['current_date']} ({status['day_of_week']})")
        
        # Check if it's time for press_review
        if is_time_for('press_review'):
            print("âœ… Time for press_review - generating content...")
            
            # Initialize telegram handler
            telegram = TelegramHandler()
            
            # Generate press review content
            messages = generate_press_review_wrapper()
            
            if messages:
                print(f"ðŸ“ Generated {len(messages)} press_review sections")
                
                # Send to Telegram - send each message individually
                all_success = True
                for i, msg in enumerate(messages, 1):
                    result = telegram.send_message(msg, content_type="press_review")
                    if result.get('success'):
                        print(f"✅ Press review message {i}/{len(messages)} sent")
                    else:
                        print(f"❌ Press review message {i}/{len(messages)} failed")
                        all_success = False
                
                if all_success:
                    # Mark as sent
                    mark_sent('press_review')
                    print("✅ Press review sent successfully and marked as complete")
                else:
                    print("❌ Failed to send some press review messages to Telegram")
                    return False
            else:
                print("âŒ Failed to generate press_review content")
                return False
        else:
            print("â° Not time for press_review yet")
            pending = status['pending_content']
            if 'press_review' in pending:
                print("ðŸ“‹ press_review is in pending queue")
            else:
                print("ðŸ“‹ press_review not scheduled or already sent")
        
        return True
        
    except ImportError as e:
        print(f"âŒ Missing dependencies: {e}")
        return False
    except Exception as e:
        log.error(f"âŒ Error in press_review trigger: {e}")
        print(f"âŒ press_review trigger failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)


