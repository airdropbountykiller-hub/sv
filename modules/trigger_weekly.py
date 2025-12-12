#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Weekly
Gestisce l'avvio automatico dei report settimanali
"""

from pathlib import Path
import sys
import os
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'config' / 'modules'))

# Setup logging
log = logging.getLogger(__name__)

def main() -> bool:
    """
    Main function per trigger weekly report
    
    Returns:
        bool: True se esecuzione successful, False otherwise
    """
    try:
        log.info("🗓️ [TRIGGER-WEEKLY] Starting weekly report generation...")
        
        # Import scheduler and weekly generator
        from sv_scheduler import mark_sent
        from weekly_generator import main as generate_weekly
        
        # Generate weekly report
        success = generate_weekly()
        
        if success:
            # Mark weekly as sent to prevent loop
            mark_sent('weekly')
            log.info("✅ [TRIGGER-WEEKLY] Weekly report generated successfully and marked as sent")
            return True
        else:
            log.error("❌ [TRIGGER-WEEKLY] Weekly report generation failed")
            return False
            
    except ImportError as e:
        log.error(f"❌ [TRIGGER-WEEKLY] Import error: {e}")
        return False
    except Exception as e:
        log.error(f"❌ [TRIGGER-WEEKLY] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)