# 📋 **SV MODULES - COMPLETE DESCRIPTION & INTERCONNECTIONS**

## 🏗️ **ARCHITECTURE OVERVIEW**

Il sistema SV è costruito con un'architettura modulare dove ogni componente ha responsabilità specifiche e comunica con gli altri attraverso interfacce ben definite. La struttura segue il pattern **Producer → Processor → Consumer** con layer di supporto trasversali.

---

## 📊 **CONTENT GENERATORS (Core Production Layer)**

### **1. daily_generator.py** 
**🎯 Funzione**: Motore principale per la generazione di contenuti giornalieri (22 messaggi/giorno)

**📋 Responsabilità**:
|- Genera 5 tipi di contenuto: Press Review (7 msgs), Morning (3 msgs), Noon (3 msgs), Evening (3 msgs), Summary (6 pages/msg)
|- La Summary ora include **Page 6 - Daily Journal & Notes** + salvataggio `journal_YYYY-MM-DD.json` strutturato.
|- Coordina ML predictions con dati live di mercato (BTC/SPX/EURUSD) e calcola `accuracy_pct` giornaliera.
|- Usa `get_live_crypto_prices()` + `calculate_crypto_support_resistance()` per generare livelli BTC dinamici (supporti/resistenze/range/breakout) in Morning/Noon/Evening e Summary Page 5, eliminando livelli fissi tipo 110–115K.
|- Implementa narrative continuity tra messaggi e tracking del sentiment intraday (Press→Morning→Noon→Evening→Summary).
|- Gestisce formattazione ASCII-safe per Telegram

**🔗 Interconnessioni**:
- **Input**: `sv_news.py` (notizie), `sv_calendar.py` (eventi), `ml_analyzer.py` (predizioni)
- **Output**: `telegram_handler.py` (invio messaggi), `reports/8_daily_content/` (backup)
- **Support**: `sv_emoji.py` (emoji Windows-safe), `brain.py` (decisioni trading)

**⚡ Trigger**: Chiamato da `trigger_*.py` agli orari programmati

---

### **2. weekly_generator.py**
**🎯 Funzione**: Genera report settimanali comprensivi con PDF automatico + invio Telegram

**📋 Responsabilità**:
|- Analisi performance 7 giorni con 11 sezioni dettagliate
|- Breakdown giornaliero con note specifiche per ogni day
|- Market analysis e risk metrics settimanali
|- Weekend Crypto Focus con prezzi BTC/ETH live e supporti/resistenze dinamici (nessun livello fisso 117K/115K/110K).
|- Generazione PDF professionale (6.1KB) + invio automatico Telegram

**🔗 Interconnessioni**:
- **Input**: Dati aggregati da `reports/8_daily_content/`, `ml_analyzer.py`
- **Output**: `pdf_generator.py` → PDF, `telegram_handler.py` → invio documento
- **Storage**: `reports/2_weekly/` per archivio PDF

**⚡ Trigger**: `sv_scheduler.py` ogni domenica 20:05

---

### **3. monthly_generator.py**
**🎯 Funzione**: Report mensili estesi (in sviluppo, foundation pronta)

**📋 Responsabilità**:
- Analisi completa 30 giorni con 8+ sezioni
- ML models performance evolution
- Strategic outlook trimestrale
- PDF generation + Telegram integration (quando attivato)

**🔗 Interconnessioni**:
- **Input**: `weekly_generator.py` (dati settimanali), `ml_analyzer.py` (performance models)
- **Output**: `pdf_generator.py`, `telegram_handler.py`
- **Storage**: `reports/3_monthly/`

**🔄 Status**: Foundation completa, attivazione dopo accumulo dati sufficienti

---

## 🤖 **ML & ANALYSIS (Intelligence Layer)**

### **4. coherence_manager.py**
**🎯 Funzione**: Valutare la coerenza giornaliera tra previsioni, risultati reali e narrativa dei 21+ messaggi.

**📋 Responsabilità**:
- Leggere il `journal_YYYY-MM-DD.json` generato da `daily_generator.py` (Page 6 + metadata).
- Leggere il file `reports/1_daily/predictions_YYYY-MM-DD.json` con le previsioni BTC/SPX/EURUSD.
- Calcolare metriche strutturate:
  - `daily_accuracy` (hits, misses, pending, accuracy_pct).
  - `coherence_score` Press→Morning→Noon→Evening→Summary.
  - `sentiment_evolution` e `news_volume`.
- Salvare:
  - `config/ml_analysis/coherence_YYYY-MM-DD.json` (metriche per day).
  - `config/daily_contexts/context_YYYY-MM-DD.json` (snapshot narrativo).
  - `config/ml_analysis/coherence_history.json` (storico multi‑giorno).

**🔗 Interconnessioni**:
- **Input**: `reports/8_daily_content/10_daily_journal/`, `reports/1_daily/predictions_*.json`.
- **Output**: File JSON in `config/` usati da Engine/Brain per decisioni informate su più giorni.

---

### **5. ml_analyzer.py**
**🎯 Funzione**: Sistema ML avanzato per predizioni di mercato e analisi pattern

**📋 Responsabilità**:
- Implementa 6+ algoritmi ML (Random Forest, XGBoost, Neural Networks, etc.)
- Real-time market predictions con confidence scoring
- Performance tracking e accuracy verification
- Feature engineering da dati multi-source

**🔗 Interconnessioni**:
- **Input**: `sv_news.py` (sentiment), `momentum_indicators.py` (technical signals), live market data
- **Output**: Predizioni per `daily_generator.py`, performance data per `weekly_generator.py`
- **Feedback Loop**: `brain.py` per decision making, `reports/` per historical analysis

**💾 Data Flow**: Salva predizioni in `data/ml_predictions/` per tracking accuracy

---

### **5. sv_ml.py**
**🎯 Funzione**: Core ML framework e model management

**📋 Responsabilità**:
- Gestione lifecycle dei modelli ML
- Training, validation, deployment pipeline
- Model versioning e performance comparison
- Hyperparameter optimization

**🔗 Interconnessioni**:
- **Collabora**: Con `ml_analyzer.py` per execution, `brain.py` per strategy
- **Input**: Historical data da `data/`, news sentiment
- **Output**: Trained models, performance metrics

---

### **6. momentum_indicators.py**
**🎯 Funzione**: Calcolo indicatori tecnici avanzati per analysis ML

**📋 Responsabilità**:
- RSI, MACD, Bollinger Bands, custom indicators
- Multi-timeframe analysis (1m, 5m, 1h, 1d)
- Signal strength scoring
- Trend detection algorithms

**🔗 Interconnessioni**:
- **Input**: Live market data via `api_fallback_config.py`
- **Output**: Technical signals per `ml_analyzer.py`, `brain.py`
- **Storage**: Cache in `data/market_data/`

---

### **7. brain.py**
**🎯 Funzione**: Strategic decision engine e trading signal generation

**📋 Responsabilità**:
- Combina ML predictions + technical indicators + news sentiment
- Risk management e position sizing
- Strategy selection basata su market regime
- Trading signals con confidence levels

**🔗 Interconnessioni**:
- **Input**: `ml_analyzer.py` (predizioni), `momentum_indicators.py` (technical), `sv_news.py` (sentiment)
- **Output**: Trading decisions per `daily_generator.py`, risk metrics per `weekly_generator.py`
- **Storage**: Decisions log in `config/daily_session.json`

---

## 📡 **DATA & NEWS (Information Layer)**

### **8. sv_news.py**
**🎯 Funzione**: Sistema news aggregation da 88+ fonti con AI sentiment analysis

**📋 Responsabilità**:
- RSS feeds monitoring da 28 fonti internazionali
- Critical news detection con ML
- Sentiment analysis e impact scoring
- News categorization (Finance, Crypto, Geopolitics, Tech)

**🔗 Interconnessioni**:
- **Output**: News feed per `daily_generator.py`, sentiment per `ml_analyzer.py`
- **Cache**: `data/news_cache/` per performance
- **Web UI**: Integrato in `sv_dashboard.py`

**⚡ Update Frequency**: Real-time polling con intelligent refresh rates

---

### **9. sv_calendar.py**
**🎯 Funzione**: Smart calendar system per eventi economici e market-moving events

**📋 Responsabilità**:
- 31+ economic events tracking (Fed, ECB, earnings, data releases)
- Impact categorization (HIGH/MEDIUM/LOW)
- Market hours awareness e timezone management
- Event correlation con market volatility

**🔗 Interconnessioni**:
- **Output**: Event data per `daily_generator.py`, market intelligence per `sv_scheduler.py`
- **Integration**: `sv_dashboard.py` per calendar view
- **Cache**: Event data in `data/calendar/`

---

### **10. api_fallback_config.py**
**🎯 Funzione**: Failover system per garantire continuous data flow

**📋 Responsabilità**:
- Primary/Secondary/Tertiary API endpoint management
- Automatic failover quando primary API non disponibile
- Rate limiting e error handling
- Data quality validation

**🔗 Interconnessioni**:
- **Serves**: `momentum_indicators.py`, `ml_analyzer.py`, market data consumers
- **Fallback Chain**: Yahoo Finance → Alpha Vantage → Backup sources
- **Monitoring**: Status logging per reliability tracking

---

### **11. bt_integration_real.py**
**🎯 Funzione**: Real Backtrader integration per backtesting e live trading simulation

**📋 Responsabilità**:
- Backtest strategies con historical data
- Performance metrics calculation
- Risk-adjusted returns analysis
- Strategy validation pre-deployment

**🔗 Interconnessioni**:
- **Input**: Strategies da `brain.py`, historical data
- **Output**: Backtest results per `weekly_generator.py`, validation per `ml_analyzer.py`
- **Storage**: Results in `data/backtest_results/`

---

## 📨 **COMMUNICATION & MESSAGE DELIVERY**

### **12. telegram_handler.py**
**🎯 Funzione**: Sistema messaging Telegram con ASCII-safe formatting + document sending

**📋 Responsabilità**:
- Multi-message sending (rispetta 4096 char limit Telegram)
- PDF document sending con retry logic
- Message history tracking per ML analysis
- Professional formatting con SV branding

**🔗 Interconnessioni**:
- **Input**: Content da `daily_generator.py`, PDF da `pdf_generator.py`
- **Config**: Credentials da `config/private.txt`
- **Logging**: Message history in `reports/9_telegram_history/`
- **Support**: `sv_emoji.py` per Windows emoji compatibility

**📊 Features**: Batch sending, error handling, rate limiting compliance

---

### **13. sv_emoji.py**
**🎯 Funzione**: Emoji handling system per Windows compatibility

**📋 Responsabilità**:
- Unicode emoji definitions per evitare corruption
- Windows PowerShell encoding fix
- Cross-platform emoji rendering
- ASCII fallback per sistemi legacy

**🔗 Interconnessioni**:
- **Used by**: `telegram_handler.py`, `daily_generator.py`, tutti i content generators
- **Purpose**: Risolve corruption emoji su Windows (ðŸ"Š → 📊)

---

### **14. manual_sender.py**
**🎯 Funzione**: Manual control system per bypass scheduler (NEW v1.4.0)

**📋 Responsabilità**:
- Manual message sending con `--force` flag
- Content preview con `--preview` mode
- Bypass scheduler restrictions
- Testing e debugging support

**🔗 Interconnessioni**:
- **Calls**: `daily_generator.py` methods, `telegram_handler.py` per sending
- **Control**: Override `sv_scheduler.py` flags
- **Usage**: `python modules/manual_sender.py press_review --force`

**🛠️ Commands**: 
- `--list` (available types)
- `--preview` (show content without sending)  
- `--force` (bypass scheduler)

---

### **15. sv_dashboard.py**
**🎯 Funzione**: Web dashboard system (localhost:5000) per monitoring real-time

**📋 Responsabilità**:
- Real-time calendar view con economic events
- News feed display con 88+ sources
- System status monitoring
- Market data visualization

**🔗 Interconnessioni**:
- **Data Sources**: `sv_calendar.py`, `sv_news.py`, `sv_scheduler.py` status
- **Templates**: HTML templates da `templates/`
- **Port**: 5000 (Flask app)
- **Access**: http://localhost:5000

---

## ⚙️ **SYSTEM CONTROL (Orchestration Layer)**

### **16. main.py**
**🎯 Funzione**: Main orchestrator che coordina tutti i moduli

**📋 Responsabilità**:
- System startup e initialization
- Module coordination e dependency management
- Error handling e recovery
- Graceful shutdown procedures

**🔗 Interconnessioni**:
- **Controls**: `sv_scheduler.py`, `sv_dashboard.py`, tutti i core modules
- **Entry Point**: Chiamato da `SV_Start.bat`
- **Config**: Loads da `config/sv_config.py`

---

### **17. engine.py**
**🎯 Funzione**: Core SV engine per business logic centrale

**📋 Responsabilità**:
- Business rules enforcement
- Data flow coordination
- Performance monitoring
- System health checks

**🔗 Interconnessioni**:
- **Interface**: Tra `main.py` e tutti i processing modules
- **Monitor**: System performance, memory usage, API quotas

---

### **18. sv_scheduler.py**
**🎯 Funzione**: Intelligent scheduling con calendar integration e market awareness

**📋 Responsabilità**:
- Fixed schedule: 07:00→20:10 con 7 content types
- Market-aware timing (pre-market, session, after-hours)
- Flag management per evitare duplicate sending
- Weekend/holiday handling

**🔗 Interconnessioni**:
- **Triggers**: Calls all `trigger_*.py` scripts
- **Intelligence**: `sv_calendar.py` per market hours awareness
- **Flags**: Prevents duplicate content generation
- **Schedule**: 
  - 07:00 Press Review
  - 08:30 Morning Report  
  - 13:00 Noon Update
  - 18:30 Evening Analysis
  - 20:00 Daily Summary
  - 20:05 Weekly Report (Sunday)
  - 20:10 Monthly Report (Last day of month)

---

## 🎯 **TRIGGERS & AUTOMATION**

### **19-23. trigger_*.py (5 files)**
**🎯 Funzione**: Trigger specifici per ogni content type agli orari programmati

**📋 Files**:
- `trigger_press_review.py` (07:00)
- `trigger_morning.py` (08:30)  
- `trigger_noon.py` (13:00)
- `trigger_evening.py` (18:30)
- `trigger_summary.py` (20:00)

**🔗 Interconnessioni**:
- **Called by**: `sv_scheduler.py` at scheduled times
- **Execute**: Specific `daily_generator.py` methods
- **Flow**: Check scheduler flags → Generate content → Send via `telegram_handler.py` → Mark as sent

---

## 📊 **OUTPUT GENERATION**

### **24. pdf_generator.py**
**🎯 Funzione**: Professional PDF reports system (ENHANCED) con ReportLab

**📋 Responsabilità**:
- Weekly PDF generation (6.1KB rich content)
- Professional styling con SV branding
- Multi-section reports (Executive Summary, Performance, Analysis, Outlook)
- Clean text-based layout (no complex tables)

**🔗 Interconnessioni**:
- **Input**: Rich data da `weekly_generator.py`, `monthly_generator.py`
- **Output**: PDF files in `reports/2_weekly/`, `reports/3_monthly/`
- **Integration**: `telegram_handler.py` per automatic PDF sending
- **Technology**: ReportLab library con custom SVPDFGenerator class

---

### **25. chart_generator.py**
**🎯 Funzione**: Charts e visualizations system

**📋 Responsabilità**:
- Performance charts per PDF reports
- ML model comparison visualizations  
- Technical indicator plots
- Market data charts

**🔗 Interconnessioni**:
- **Input**: Data da `ml_analyzer.py`, performance metrics
- **Output**: Charts per `pdf_generator.py` integration
- **Formats**: PNG, SVG per embedding in PDFs

---

## 🔄 **DATA FLOW SUMMARY**

```
📊 COMPLETE DATA FLOW:

1. DATA COLLECTION:
   sv_news.py + sv_calendar.py + api_fallback_config.py
   ↓
2. ML PROCESSING:
   momentum_indicators.py → ml_analyzer.py + sv_ml.py → brain.py
   ↓
3. CONTENT GENERATION:
   daily_generator.py (triggered by sv_scheduler.py via trigger_*.py)
   ↓
4. MESSAGE DELIVERY:
   telegram_handler.py (with sv_emoji.py support)
   ↓
5. REPORTING:
   weekly_generator.py → pdf_generator.py → telegram_handler.py (PDF sending)
   ↓
6. STORAGE & MONITORING:
   reports/ directories + sv_dashboard.py monitoring

MANUAL CONTROLS:
manual_sender.py (bypass automation)
main.py + engine.py (system orchestration)
```

---

## 💾 **STORAGE INTERACTIONS**

- **`data/`**: Cache tecnica (ricreabile) - news_cache, ml_predictions, market_data
- **`config/`**: Business memory (critica) - daily_session.json, contexts
- **`reports/`**: Output finale - 1_daily, 2_weekly, 3_monthly, 8_daily_content, 9_telegram_history  
- **`config/`**: System configuration - private.txt, sv_config.py

---

## ⚡ **CRITICAL DEPENDENCIES**

1. **High Priority**: `sv_scheduler.py` → All triggers → `daily_generator.py` → `telegram_handler.py`
2. **ML Chain**: `api_fallback_config.py` → `momentum_indicators.py` → `ml_analyzer.py` → `brain.py`
3. **Reporting Chain**: `weekly_generator.py` → `pdf_generator.py` → `telegram_handler.py`
4. **Monitoring**: `sv_dashboard.py` ← Multiple data sources

**🎯 System designed for 24/7 operation with failover mechanisms and intelligent scheduling**