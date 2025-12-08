#!/usr/bin/env python3
"""
Preview script for improved weekly report using WeeklyDataAssembler
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'modules'))

# Set environment variable to skip Telegram
os.environ['SV_SKIP_TELEGRAM'] = '1'

def main():
    try:
        print("🧪 [PREVIEW] Testing improved weekly report generation...")
        
        # Import weekly generator 
        from weekly_generator import main as weekly_main
        
        # Run weekly main function
        success = weekly_main()
        
        if success:
            print("✅ [PREVIEW] Weekly report generated successfully!")
            print("📄 Check reports/2_weekly/ for the new PDF")
        else:
            print("❌ [PREVIEW] Weekly report generation failed")
        
        return success
        
    except Exception as e:
        print(f"❌ [PREVIEW] Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    print(f"🏁 [PREVIEW] Exit status: {'SUCCESS' if success else 'FAILED'}")