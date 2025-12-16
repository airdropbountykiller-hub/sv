#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Noon Update  
Script individuale to generate noon update (12:00)
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
    """Main function for noon update trigger"""
    print("ðŸŒž SV - TRIGGER NOON UPDATE")
    print("=" * 50)
    
    try:
        # Import modules
        from sv_scheduler import is_time_for, mark_sent, get_status
        from daily_generator import generate_noon
        from telegram_handler import TelegramHandler
        
        # Check scheduler
        status = get_status()
        print(f"ðŸ• Current time: {status['current_time']}")
        print(f"ðŸ“… Date: {status['current_date']} ({status['day_of_week']})")
        
        # Check if it's time for noon update
        if is_time_for('noon'):
            print("✅ Time for noon update - generating content...")
            
            # Initialize telegram handler
            telegram = TelegramHandler()
            
            # Generate noon content
            messages = generate_noon()
            
            if messages:
                print(f"📝 Generated {len(messages)} noon messages")
                
                # Send to Telegram - send each message individually
                all_success = True
                for i, msg in enumerate(messages, 1):
                    result = telegram.send_message(msg, content_type="noon")
                    if result.get('success'):
                        print(f"✅ Noon message {i}/{len(messages)} sent")
                    else:
                        print(f"❌ Noon message {i}/{len(messages)} failed")
                        all_success = False
                
                if all_success:
                    # Mark as sent
                    mark_sent('noon')
                    print("✅ Noon update sent successfully and marked as complete")
                else:
                    print("❌ Failed to send some noon messages to Telegram")
                    return False
            else:
                print("❌ Failed to generate noon content")
                return False
        else:
            print("â° Not time for noon update yet")
            pending = status['pending_content']
            if 'noon' in pending:
                print("ðŸ“‹ Noon update is in pending queue")
            else:
                print("ðŸ“‹ Noon update not scheduled or already sent")
        
        return True
        
    except ImportError as e:
        print(f"âŒ Missing dependencies: {e}")
        return False
    except Exception as e:
        log.error(f"âŒ Error in noon trigger: {e}")
        print(f"âŒ Noon trigger failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)


