#!/usr/bin/env python3
"""
Create mock daily metrics files to demonstrate improved weekly report
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'modules'))

def create_mock_daily_metrics():
    """Create mock daily metrics files for Monday-Thursday of this week"""
    
    metrics_dir = project_root / "reports" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Base date: get Monday of this week
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    
    # Mock data for Monday to Thursday (Friday already exists)
    daily_templates = {
        0: {  # Monday
            "predictions": {
                "hits": 2,
                "misses": 1,
                "pending": 0,
                "total_tracked": 3,
                "accuracy_pct": 66.7
            },
            "market_summary": "Strong opening with tech leading gains. Volatility remained low as markets consolidated recent moves."
        },
        1: {  # Tuesday
            "predictions": {
                "hits": 1,
                "misses": 2,
                "pending": 0,
                "total_tracked": 3,
                "accuracy_pct": 33.3
            },
            "market_summary": "Mixed session with Fed minutes causing rotation into defensive sectors. Energy outperformed."
        },
        2: {  # Wednesday
            "predictions": {
                "hits": 3,
                "misses": 0,
                "pending": 1,
                "total_tracked": 3,
                "accuracy_pct": 100.0
            },
            "market_summary": "Exceptional day with all major predictions hitting targets. Crypto showed particular strength."
        },
        3: {  # Thursday
            "predictions": {
                "hits": 2,
                "misses": 1,
                "pending": 0,
                "total_tracked": 3,
                "accuracy_pct": 66.7
            },
            "market_summary": "Solid performance continued with breakouts in several key technical levels."
        }
    }
    
    created_files = []
    
    for day_offset, template in daily_templates.items():
        target_date = monday + timedelta(days=day_offset)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Skip if file already exists
        metrics_file = metrics_dir / f"daily_metrics_{date_str}.json"
        if metrics_file.exists():
            print(f"📄 [MOCK] File already exists: {metrics_file.name}")
            continue
            
        # Create mock daily metrics
        mock_data = {
            "date": date_str,
            "timestamp": target_date.isoformat() + "+01:00",
            "predictions": template["predictions"],
            "market_summary": template["market_summary"],
            "market_snapshot": {
                "SPX": {
                    "price": 5400 + (day_offset * 10),  # Mock progressive price
                    "change_pct": 0.5 + (day_offset * 0.2),
                    "unit": "USD"
                },
                "BTC": {
                    "price": 84000 + (day_offset * 200),
                    "change_pct": 1.0 + (day_offset * 0.5),
                    "unit": "USD"
                }
            }
        }
        
        # Write mock file
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=2)
        
        created_files.append(metrics_file.name)
        print(f"✅ [MOCK] Created: {metrics_file.name}")
    
    return created_files

def create_mock_journal_entries():
    """Create mock journal entries for the week"""
    
    journals_dir = project_root / "reports" / "journals"
    journals_dir.mkdir(parents=True, exist_ok=True)
    
    # Base date: get Monday of this week
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    
    journal_templates = {
        0: """# Trading Journal - Monday

## Market Overview
Strong opening with tech sector leading gains. S&P 500 broke above key resistance.

## Key Trades
- **BTC Long**: Entry at 84000, target hit at 86000 (+2.4%)  
- **SPX Long**: Entry at 5400, stopped out at 5375 (-0.5%)
- **AAPL**: Volatility play worked well, +1.2%

## Lessons Learned
Tech earnings season providing good momentum signals.
""",
        1: """# Trading Journal - Tuesday

## Market Overview  
Fed minutes caused sector rotation. Energy outperformed while tech consolidated.

## Key Trades
- **Oil Long**: WTI breakout above $78, target at $80 (+2.6%)
- **EUR/USD Short**: Failed to hold 1.085 support, hit target at 1.075 (+90 pips)

## Market Events
- Fed minutes showed dovish tone
- Energy earnings better than expected

## Risk Management
Position sizing kept conservative ahead of volatility.
""",
        2: """# Trading Journal - Wednesday

## Market Overview
Exceptional trading day with all major setups working perfectly.

## Key Trades  
- **BTC**: Massive breakout above 85000, held positions overnight
- **NASDAQ**: Trend following signals all triggered
- **Gold**: Safe haven flows reversed, short positions profitable

## Notes
Best trading day of the month. Risk/reward ratios optimal.
Market sentiment clearly bullish with strong volume confirmation.
""",
        3: """# Trading Journal - Thursday

## Market Overview
Continuation of positive momentum with breakouts in key levels.

## Key Trades
- **SPX**: Clean breakout above 5420 resistance  
- **Crypto**: BTC holding gains, altcoins following
- **FX**: USD strength persisting

## Technical Analysis
Multiple timeframe alignment working well.
Support/resistance levels holding as expected.
"""
    }
    
    created_files = []
    
    for day_offset, content in journal_templates.items():
        target_date = monday + timedelta(days=day_offset)
        date_str = target_date.strftime('%Y-%m-%d')
        
        journal_file = journals_dir / f"trading_journal_{date_str}_session.md"
        
        # Skip if file already exists
        if journal_file.exists():
            print(f"📄 [MOCK] Journal already exists: {journal_file.name}")
            continue
            
        # Write mock journal
        with open(journal_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        created_files.append(journal_file.name)
        print(f"✅ [MOCK] Created: {journal_file.name}")
    
    return created_files

def main():
    """Main function to create mock data"""
    try:
        print("🧪 [MOCK] Creating mock weekly data for demonstration...")
        
        # Create mock daily metrics
        metrics_files = create_mock_daily_metrics()
        
        # Create mock journal entries
        journal_files = create_mock_journal_entries()
        
        print(f"\n📊 [MOCK] Summary:")
        print(f"  - Created {len(metrics_files)} daily metrics files")
        print(f"  - Created {len(journal_files)} journal entries")
        print(f"\n🔄 Now run the weekly report to see improved data aggregation!")
        
        return True
        
    except Exception as e:
        print(f"❌ [MOCK] Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    print(f"🏁 [MOCK] Exit status: {'SUCCESS' if success else 'FAILED'}")