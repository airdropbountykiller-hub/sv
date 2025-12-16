#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Main Orchestrator
Coordina tutti i piccoli script modulari del sistema SV
"""

from pathlib import Path
import sys
import os
import time
import logging
import threading
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'config' / 'modules'))

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

class SVOrchestrator:
    """
    Orchestratore principale del sistema SV
    Coordina tutti i moduli in piccoli script indipendenti
    """
    
    def __init__(self):
        """Initialize SV Orchestrator"""
        self.running = False
        self.check_interval = 30  # Base poll every 30 seconds (lightweight)
        # Throttle attempts: run each pending content at most once every 30 minutes
        self.pending_retry_interval = 30 * 60  # seconds
        self._last_attempt = {}  # content_type -> epoch seconds
        # ENGINE/BRAIN heartbeat every ~30 minutes (metrics-only, no messages)
        self.heartbeat_interval = 30 * 60  # seconds
        self._last_heartbeat = 0.0
        
        # Content trigger modules
        self.triggers = {
            'night': 'trigger_night',
            'late_night': 'trigger_late_night',
            'press_review': 'trigger_press_review',
            'morning': 'trigger_morning',
            'noon': 'trigger_noon',
            'afternoon': 'trigger_afternoon',
            'evening': 'trigger_evening',
            'summary': 'trigger_summary',
            'weekly': 'trigger_weekly',
            'monthly': 'trigger_monthly'
        }
        
    def run_single_check(self):
        """Run a single check cycle"""
        try:
            # Import scheduler
            from sv_scheduler import get_status, get_pending
            
            # Get current status
            status = get_status()
            pending_content = get_pending()
            
            log.info(f"[CHECK] Check cycle - Time: {status['current_time']}, Pending: {pending_content}")
            
            # Process each pending content type (throttled)
            now_epoch = time.time()
            for content_type in pending_content:
                if content_type not in self.triggers:
                    log.warning(f"[WARN] No trigger available for content type: {content_type}")
                    continue
                last = self._last_attempt.get(content_type, 0)
                if (now_epoch - last) < self.pending_retry_interval:
                    remaining = int(self.pending_retry_interval - (now_epoch - last))
                    log.info(f"[DEFER] {content_type} pending but deferred: retry in ~{remaining//60} min")
                    continue
                self.run_trigger(content_type)
                self._last_attempt[content_type] = time.time()

            # ENGINE/BRAIN heartbeat (metrics-only, no messages)
            if (now_epoch - self._last_heartbeat) >= self.heartbeat_interval:
                self.run_engine_brain_heartbeat()
                self._last_heartbeat = time.time()
            
            # Log status if no pending content
            if not pending_content:
                log.debug(f"[DEBUG] No pending content at {status['current_time']}")
                
        except Exception as e:
            log.error(f"[ERROR] Error in check cycle: {e}")
    
    def run_trigger(self, content_type: str):
        """Run specific content trigger"""
        try:
            trigger_module = self.triggers[content_type]
            log.info(f"[RUN] Running trigger: {trigger_module} for {content_type}")
            
            # Import and run trigger module
            module = __import__(trigger_module)
            if hasattr(module, 'main'):
                success = module.main()
                if success:
                    log.info(f"[OK] {content_type} trigger completed successfully")
                else:
                    log.error(f"âŒ {content_type} trigger failed")
            else:
                log.error(f"âŒ Trigger module {trigger_module} has no main() function")
                
        except ImportError as e:
            log.error(f"âŒ Cannot import trigger {trigger_module}: {e}")
        except Exception as e:
            log.error(f"âŒ Error running trigger {content_type}: {e}")

    def run_engine_brain_heartbeat(self):
        """Run a lightweight ENGINE+BRAIN heartbeat snapshot (no message generation)."""
        try:
            from modules.engine.heartbeat import run_heartbeat
        except ImportError as e:
            log.warning(f"[HEARTBEAT] Cannot import engine.heartbeat: {e}")
            return

        try:
            log.info("[HEARTBEAT] Running ENGINE+BRAIN heartbeat snapshot")
            run_heartbeat()
        except Exception as e:
            log.warning(f"[HEARTBEAT] Error during ENGINE/BRAIN heartbeat: {e}")
    
    def run_continuous(self):
        """Run continuous monitoring loop"""
        log.info("[START] SV Orchestrator starting continuous monitoring...")
        self.running = True
        
        try:
            while self.running:
                self.run_single_check()
                
                # Sleep for check interval
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            log.info("â¹ï¸ Received keyboard interrupt, stopping...")
        except Exception as e:
            log.error(f"âŒ Error in continuous monitoring: {e}")
        finally:
            self.running = False
            log.info("ðŸ›‘ SV Orchestrator stopped")
    
    def stop(self):
        """Stop continuous monitoring"""
        self.running = False
    
    def run_daemon(self):
        """Run as background daemon"""
        log.info("ðŸ‘» SV Orchestrator starting as daemon...")
        
        # Run in background thread
        daemon_thread = threading.Thread(target=self.run_continuous, daemon=True)
        daemon_thread.start()
        
        return daemon_thread
    
    def test_all_modules(self):
        """Test all SV modules connectivity"""
        print("ðŸ§ª SV ORCHESTRATOR - MODULE TESTING")
        print("=" * 50)
        
        modules_to_test = [
            'sv_scheduler',
            'daily_generator',
            'weekly_generator',
            'monthly_generator',
            'telegram_handler',
            'pdf_generator',
            'momentum_indicators',
            'sv_news',
            'sv_calendar',
            'sv_emoji',
            'manual_sender'
        ]
        
        results = {}
        
        for module_name in modules_to_test:
            try:
                module = __import__(module_name)
                
                # Try to run test function if available
                if hasattr(module, 'test_' + module_name.split('_')[0]) or hasattr(module, 'test'):
                    test_func = getattr(module, 'test_' + module_name.split('_')[0], None) or getattr(module, 'test', None)
                    if test_func:
                        test_result = test_func()
                        results[module_name] = test_result
                        print(f"âœ… {module_name}: {'PASSED' if test_result else 'FAILED'}")
                    else:
                        results[module_name] = True
                        print(f"âœ… {module_name}: IMPORTED (no test function)")
                else:
                    results[module_name] = True
                    print(f"âœ… {module_name}: IMPORTED")
                    
            except ImportError as e:
                results[module_name] = False
                print(f"âŒ {module_name}: IMPORT FAILED - {e}")
            except Exception as e:
                results[module_name] = False
                print(f"âŒ {module_name}: TEST FAILED - {e}")
        
        # Summary
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        print(f"\nðŸ“Š MODULE TEST RESULTS: {passed}/{total} modules working")
        
        return results

# Global orchestrator instance
orchestrator = None

def get_orchestrator() -> SVOrchestrator:
    """Get singleton orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = SVOrchestrator()
    return orchestrator

# Main execution modes
def run_single():
    """Run single check cycle"""
    orchestrator = get_orchestrator()
    orchestrator.run_single_check()

def run_continuous():
    """Run continuous monitoring"""
    orchestrator = get_orchestrator()
    orchestrator.run_continuous()

def run_daemon():
    """Run as daemon"""
    orchestrator = get_orchestrator()
    return orchestrator.run_daemon()

def test_modules():
    """Test all modules"""
    orchestrator = get_orchestrator()
    return orchestrator.test_all_modules()

def main():
    """Main entry point with command line options"""
    print("[SV] SV - UNIFIED TRADING SYSTEM")
    print("Content Creation Engine - Main Orchestrator")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'single':
            print("[RUN] Running single check cycle...")
            run_single()
        elif mode == 'continuous':
            print("[MONITOR] Running continuous monitoring...")
            run_continuous()
        elif mode == 'daemon':
            print("[DAEMON] Running as daemon...")
            daemon_thread = run_daemon()
            print("âœ… Daemon started, press Ctrl+C to stop")
            try:
                daemon_thread.join()
            except KeyboardInterrupt:
                print("\nâ¹ï¸ Stopping daemon...")
        elif mode == 'test':
            print("ðŸ§ª Testing all modules...")
            test_modules()
        else:
            print(f"âŒ Unknown mode: {mode}")
            print("Available modes: single, continuous, daemon, test")
    else:
        # Default: show status and run test
        print("ðŸ“Š Getting current status...")
        
        try:
            from sv_scheduler import get_status
            status = get_status()
            
            print(f"ðŸ• Current time: {status['current_time']}")
            print(f"ðŸ“… Date: {status['current_date']} ({status['day_of_week']})")
            print(f"ðŸ“‹ Pending content: {status['pending_content']}")
            print(f"âš ï¸ Weekend mode: {status['is_weekend']}")
            print(f"ðŸ“… Last day of month: {status['is_last_day_of_month']}")
            
        except Exception as e:
            print(f"âŒ Error getting status: {e}")
        
        print("\nðŸ§ª Running module tests...")
        test_modules()
        
        print("\nðŸ’¡ Usage:")
        print("  python main.py single      - Run single check")  
        print("  python main.py continuous  - Run continuous monitoring")
        print("  python main.py daemon      - Run as background daemon")
        print("  python main.py test        - Test all modules")

if __name__ == '__main__':
    main()


