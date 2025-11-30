#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Trigger Monthly
Gestisce l'avvio automatico dei report mensili
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'modules'))

# Setup logging
log = logging.getLogger(__name__)

def main() -> bool:
    """
    Main function per trigger monthly report
    
    Returns:
        bool: True se esecuzione successful, False otherwise
    """
    try:
        log.info("📊 [TRIGGER-MONTHLY] Starting monthly report generation...")
        
        # Import monthly generator
        from monthly_generator import main as generate_monthly
        
        # Generate monthly report
        success = generate_monthly()
        
        if success:
            log.info("✅ [TRIGGER-MONTHLY] Monthly report generated successfully")
            return True
        else:
            log.error("❌ [TRIGGER-MONTHLY] Monthly report generation failed")
            return False
            
    except ImportError as e:
        log.error(f"❌ [TRIGGER-MONTHLY] Import error: {e}")
        return False
    except Exception as e:
        log.error(f"❌ [TRIGGER-MONTHLY] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)