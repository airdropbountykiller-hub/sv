#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Manual Content Sender
Sistema per invio manuale dei contenuti - bypassa scheduler e recovery
"""

import sys
import os
import argparse
import logging
from typing import List, Optional
import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'modules'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class ManualContentSender:
    """Manual content generation and sending system"""
    
    def __init__(self, force_send: bool = False):
        """Initialize manual sender
        
        Args:
            force_send: If True, bypass all scheduler checks and send immediately
        """
        self.force_send = force_send
        self.available_contents = {
            'press_review': {
                'name': 'Press Review',
                'function': 'generate_press_review_wrapper',
                'scheduled_time': '07:00',
                'description': '7 messages with market intelligence'
            },
            'morning': {
                'name': 'Morning Report', 
                'function': 'generate_morning',
                'scheduled_time': '08:30',
                'description': '3 messages with market pulse and ML analysis'
            },
            'noon': {
                'name': 'Noon Update',
                'function': 'generate_noon',
                'scheduled_time': '13:00', 
                'description': '3 messages with intraday tracking'
            },
            'evening': {
                'name': 'Evening Analysis',
                'function': 'generate_evening',
                'scheduled_time': '18:30',
                'description': '3 messages with session wrap and performance review'
            },
            'summary': {
                'name': 'Daily Summary',
                'function': 'generate_summary', 
                'scheduled_time': '20:00',
                'description': '5-page comprehensive daily analysis'
            }
        }
        
    def list_available_contents(self):
        """Display all available content types"""
        print("\n[SV] MANUAL CONTENT SENDER")
        print("=" * 60)
        print("\nAVAILABLE CONTENT TYPES:")
        
        for key, info in self.available_contents.items():
            status = self._get_content_status(key)
            print(f"\n[{key.upper()}]: {info['name']}")
            print(f"   Scheduled: {info['scheduled_time']}")
            print(f"   Content: {info['description']}")
            print(f"   Status: {status}")
        
        print(f"\nUsage: python manual_sender.py <content_type> [--force]")
        print(f"   Example: python manual_sender.py press_review --force")
        
    def _get_content_status(self, content_type: str) -> str:
        """Get current status of content type"""
        try:
            from sv_scheduler import is_time_for, get_status
            
            # Get scheduler status
            status = get_status()
            
            if is_time_for(content_type):
                return "[READY] Ready to send (scheduled time)"
            elif content_type in status.get('pending_content', []):
                return "[PENDING] Pending in queue"
            else:
                return "[DONE] Not scheduled or already sent"
                
        except Exception as e:
            return f"[UNKNOWN] Status unknown ({str(e)[:30]}...)"
    
    def generate_and_send(self, content_type: str, preview_only: bool = False) -> bool:
        """Generate and send content manually
        
        Args:
            content_type: Type of content to generate
            preview_only: If True, only show preview without sending
            
        Returns:
            True if successful, False otherwise
        """
        if content_type not in self.available_contents:
            print(f"[ERR] Unknown content type: {content_type}")
            print(f"Available: {', '.join(self.available_contents.keys())}")
            return False
        
        content_info = self.available_contents[content_type]
        
        print(f"\n[SV] MANUAL {content_info['name'].upper()}")
        print("=" * 50)
        
        try:
            # Import required modules
            from daily_generator import (
                generate_press_review_wrapper, generate_morning, 
                generate_noon, generate_evening, generate_summary
            )
            from telegram_handler import TelegramHandler
            
            # Get generation function
            generation_functions = {
                'generate_press_review_wrapper': generate_press_review_wrapper,
                'generate_morning': generate_morning,
                'generate_noon': generate_noon, 
                'generate_evening': generate_evening,
                'generate_summary': generate_summary
            }
            
            generate_func = generation_functions[content_info['function']]
            
            # Generate content
            print(f"[GEN] Generating {content_info['name'].lower()}...")
            content = generate_func()
            
            if not content:
                print(f"[ERR] Failed to generate {content_info['name'].lower()}")
                return False
            
            # All content types now return list of messages
            messages = content if isinstance(content, list) else [content]
            
            print(f"[OK] Generated {len(messages)} message(s)")
            
            # Preview mode
            if preview_only:
                print(f"\n[PREVIEW] - {content_info['name'].upper()}:")
                print("-" * 50)
                for i, msg in enumerate(messages, 1):
                    print(f"\nMessage {i}/{len(messages)}:")
                    preview = msg[:300] + "..." if len(msg) > 300 else msg
                    print(preview)
                print(f"\nUse --send to actually send to Telegram")
                return True
            
            # Sending mode
            if not self.force_send:
                # Check scheduler status
                status = self._get_content_status(content_type)
                if "[DONE]" in status and "already sent" in status:
                    print(f"[WARN] {content_info['name']} appears to already be sent today")
                    response = input("Continue anyway? (y/N): ").lower().strip()
                    if response != 'y':
                        print("[CANCEL] Cancelled by user")
                        return False
            
            # Initialize Telegram handler
            telegram = TelegramHandler()
            
            # Send to Telegram
            print(f"[SEND] Sending to Telegram...")
            
            # Format messages for TelegramHandler
            content_list = []
            for i, msg in enumerate(messages):
                content_list.append({
                    'content': msg,
                    'type': content_type,
                    'metadata': {'sequence': i+1, 'total': len(messages)}
                })
            
            # Send using correct method
            results = telegram.send_sv_content_batch(content_list)
            success = all(result.get('success', False) for result in results)
            
            if success:
                print(f"[OK] {content_info['name']} sent successfully to Telegram!")
                
                # Optionally mark as sent in scheduler (if not forcing)
                if not self.force_send:
                    try:
                        from sv_scheduler import mark_sent
                        mark_sent(content_type)
                        print(f"[SCHEDULER] Marked as sent in scheduler")
                    except Exception as e:
                        print(f"[WARN] Could not mark as sent: {e}")
                
                return True
            else:
                print(f"[ERR] Failed to send {content_info['name']} to Telegram")
                return False
                
        except ImportError as e:
            print(f"[ERR] Missing dependencies: {e}")
            return False
        except Exception as e:
            log.error(f"[ERR] Error in manual sender: {e}")
            print(f"[ERR] Manual sending failed: {e}")
            return False
    


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description='SV Manual Content Sender')
    parser.add_argument('content_type', nargs='?', help='Content type to generate and send')
    parser.add_argument('--force', action='store_true', help='Force send bypassing scheduler checks')
    parser.add_argument('--preview', action='store_true', help='Show preview without sending')
    parser.add_argument('--list', action='store_true', help='List available content types')
    
    args = parser.parse_args()
    
    sender = ManualContentSender(force_send=args.force)
    
    if args.list or not args.content_type:
        sender.list_available_contents()
        return
    
    # Generate and send content
    success = sender.generate_and_send(args.content_type, preview_only=args.preview)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()