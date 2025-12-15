#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SV - Trigger Afternoon Update
Script individuale per generare Afternoon Update (15:00)
"""

from pathlib import Path
import sys
import logging

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'config' / 'modules'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def main():
    """Main function for afternoon update trigger"""
    print("🌤 SV - TRIGGER AFTERNOON UPDATE")
    print("=" * 50)

    try:
        from sv_scheduler import is_time_for, mark_sent, get_status
        from daily_generator import generate_afternoon
        from telegram_handler import TelegramHandler

        status = get_status()
        print(f"🕐 Current time: {status['current_time']}")
        print(f"📅 Date: {status['current_date']} ({status['day_of_week']})")

        if is_time_for('afternoon'):
            print("✅ Time for afternoon update - generating content...")

            telegram = TelegramHandler()
            messages = generate_afternoon()

            if messages:
                print(f"📝 Generated {len(messages)} afternoon message(s)")

                all_success = True
                for i, msg in enumerate(messages, 1):
                    result = telegram.send_message(msg, content_type="afternoon")
                    if result.get('success'):
                        print(f"✅ Afternoon message {i}/{len(messages)} sent")
                    else:
                        print(f"❌ Afternoon message {i}/{len(messages)} failed")
                        all_success = False

                if all_success:
                    mark_sent('afternoon')
                    print("✅ Afternoon update sent successfully and marked as complete")
                else:
                    print("❌ Failed to send some afternoon messages to Telegram")
                    return False
            else:
                print("❌ Failed to generate afternoon content")
                return False
        else:
            print("⏰ Not time for afternoon update yet")
            pending = status.get('pending_content', [])
            if 'afternoon' in pending:
                print("📋 Afternoon update is in pending queue")
            else:
                print("📋 Afternoon update not scheduled or already sent")

        return True

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        return False
    except Exception as e:
        log.error(f"❌ Error in afternoon trigger: {e}")
        print(f"❌ Afternoon trigger failed: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
