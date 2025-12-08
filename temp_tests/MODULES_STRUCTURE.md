# SV - Struttura Dettagliata Moduli

**Totale:** 25 moduli | **Size:** 520 KB | **Linee:** 9,739

---

## 🎯 **CORE GENERATORS** (278.7 KB, 4,803 linee) - 53.6%

### 1. **`daily_generator.py`** ⭐⭐⭐⭐⭐
- **Size:** 199.5 KB | **Lines:** 3,279 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Core del sistema
- **Funzioni principali:**
  - `generate_press_review()` - 7 messaggi Press Review (07:00)
  - `generate_morning()` - 3 messaggi Morning Report (08:30)
  - `generate_noon()` - 3 messaggi Noon Update (13:00)
  - `generate_evening()` - 3 messaggi Evening Analysis (18:30)
  - `generate_summary()` - 5 pagine Daily Summary (20:00)
  - `get_live_crypto_prices()` - Prezzi crypto live
  - `get_fallback_data()` - Dati fallback integrati
  - `_load_yesterday_connection()` - Continuità tra giorni
  - `_prepare_next_day_connection()` - Setup giorno successivo
  - `_perform_coherence_check()` - Verifica coerenza messaggi
- **Import:** `sv_emoji`, `sv_news`, `sv_calendar`
- **Dipendenze:** CORE - Usato da tutti i triggers

---

### 2. **`weekly_generator.py`** ⭐⭐⭐⭐
- **Size:** 28.8 KB | **Lines:** 493 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Report settimanale
- **Funzioni principali:**
  - `generate_weekly_report()` - Report settimanale (20:05 Domenica)
  - PDF + messaggio Telegram
- **Import:** Standard libraries
- **Dipendenze:** Chiamato da scheduler Domenica 20:05

---

### 3. **`monthly_generator.py`** ⭐⭐⭐⭐
- **Size:** 25.6 KB | **Lines:** 460 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Report mensile
- **Funzioni principali:**
  - `generate_monthly_report()` - Report mensile (20:10 ultimo giorno)
  - PDF + messaggio Telegram
- **Import:** Standard libraries
- **Dipendenze:** Chiamato da scheduler ultimo giorno mese 20:10

---

## 📱 **TELEGRAM & COMMUNICATION** (40.9 KB, 1,039 linee) - 7.9%

### 4. **`telegram_handler.py`** ⭐⭐⭐⭐⭐
- **Size:** 28.7 KB | **Lines:** 691 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Core comunicazione
- **Funzioni principali:**
  - `send_message()` - Invio singolo messaggio
  - `send_document()` - Invio PDF
  - `_save_message_history()` - Salva cronologia messaggi
- **Import:** `requests`, `pathlib`
- **Dipendenze:** Usato da: triggers, manual_sender

---

### 5. **`manual_sender.py`** ⭐⭐⭐⭐
- **Size:** 11.1 KB | **Lines:** 277 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Invio manuale
- **Classe:** `ManualContentSender`
- **Funzioni principali:**
  - `send_press_review()` - Invio manuale press review
  - `send_morning()`, `send_noon()`, `send_evening()`, `send_summary()`
- **Import:** `daily_generator`, `telegram_handler`
- **Dipendenze:** CLI tool per testing

---

### 6. **`pdf_generator.py`** ⭐⭐⭐
- **Size:** 26.8 KB | **Lines:** 571 | **Modified:** 11-02
- **Status:** ⚠️ USED - Solo weekly/monthly
- **Classe:** `SVPDFGenerator` (typo: Generatetor)
- **Funzioni principali:**
  - `generate_weekly_pdf()` - PDF report settimanale
  - `generate_monthly_pdf()` - PDF report mensile
- **Import:** Standard libraries (no external PDF libs)
- **Dipendenze:** Usato da: weekly_generator, monthly_generator
- **Note:** ⚠️ Typo nel nome classe

---

## 📊 **DATA SOURCES** (38.6 KB, 885 linee) - 7.4%

### 7. **`sv_news.py`** ⭐⭐⭐⭐⭐
- **Size:** 20.3 KB | **Lines:** 473 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Sistema news
- **Classe:** `SVNewsSystem`
- **Funzioni principali:**
  - `get_news_for_content()` - Fetch news per tipo contenuto
  - `analyze_news_sentiment()` - Sentiment analysis
  - `_fetch_rss_feeds()` - Parsing RSS feeds
- **Import:** `feedparser`, `requests`, `pytz`
- **Dipendenze:** Usato da: daily_generator

---

### 8. **`sv_calendar.py`** ⭐⭐⭐⭐⭐
- **Size:** 18.3 KB | **Lines:** 412 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Sistema calendario
- **Classe:** `SVCalendarSystem`
- **Funzioni principali:**
  - `get_calendar_events()` - Eventi economici
  - `analyze_calendar_impact()` - Impatto mercato
  - `get_day_context()` - Contesto giornaliero
- **Import:** `pytz`, `json`
- **Dipendenze:** Usato da: daily_generator, sv_scheduler

---

## ⚙️ **SCHEDULER & ORCHESTRATION** (24.4 KB, 618 linee) - 4.7%

### 9. **`sv_scheduler.py`** ⭐⭐⭐⭐⭐
- **Size:** 14.8 KB | **Lines:** 361 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Scheduler principale
- **Funzioni principali:**
  - `is_time_for_content()` - Check timing con catch-up logic
  - `get_pending_content()` - Contenuti in attesa
  - `mark_sent()` - Marca contenuto inviato
  - `reset_daily_flags()` - Reset giornaliero flags
- **Schedule:**
  - 07:00 - Press Review
  - 08:30 - Morning Report
  - 13:00 - Noon Update
  - 18:30 - Evening Analysis
  - 20:00 - Daily Summary
  - 20:05 - Weekly Report (Domenica)
  - 20:10 - Monthly Report (ultimo giorno mese)
- **Import:** `sv_calendar`, `pytz`, `json`
- **Dipendenze:** Usato da: main.py, triggers

---

### 10. **`main.py`** ⭐⭐⭐⭐
- **Size:** 9.6 KB | **Lines:** 257 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Orchestratore
- **Classe:** `SVOrchestrator`
- **Funzioni principali:**
  - `run()` - Loop principale monitoring
  - `_check_and_send_content()` - Verifica e invio contenuti
  - Monitoring ogni 30 secondi
- **Import:** `sv_scheduler`, triggers
- **Dipendenze:** Entry point SV_Start.bat

---

## 🎬 **TRIGGERS** (17.6 KB, 449 linee) - 3.4%

### 11-15. **Trigger Scripts** ⭐⭐⭐⭐⭐
**Status:** ✅ ACTIVE - Tutti fixati con send_message() loop

| File | Size | Lines | Funzione | Schedule |
|------|------|-------|----------|----------|
| `trigger_press_review.py` | 3.4 KB | 85 | Press Review | 07:00 |
| `trigger_morning.py` | 3.3 KB | 85 | Morning Report | 08:30 |
| `trigger_noon.py` | 3.2 KB | 85 | Noon Update | 13:00 |
| `trigger_evening.py` | 3.3 KB | 85 | Evening Analysis | 18:30 |
| `trigger_summary.py` | 4.4 KB | 109 | Daily Summary | 20:00 |

**Struttura comune:**
- Import: `sv_scheduler`, `daily_generator`, `telegram_handler`
- Check: `is_time_for(content_type)`
- Generate: `generate_X()`
- Send: Loop `telegram.send_message()` per ogni messaggio
- Mark: `mark_sent(content_type)`

---

## 🛠️ **UTILITIES** (4.8 KB, 125 linee) - 0.9%

### 16. **`sv_emoji.py`** ⭐⭐⭐⭐⭐
- **Size:** 4.8 KB | **Lines:** 125 | **Modified:** 11-02
- **Status:** ✅ ACTIVE - Sistema emoji Windows-safe
- **Content:** Dictionary `EMOJI` con 50+ emoji puliti
- **Funzioni:**
  - `get_emoji(name)` - Recupera emoji by name
  - `render_emoji(name)` - Render safe per Windows
- **Import:** Nessuna dipendenza
- **Dipendenze:** Usato da: daily_generator, weekly_generator, monthly_generator
- **Soluzione:** Emoji corruption fix Windows PowerShell

---

## ❌ **OBSOLETI - DA ELIMINARE** (72.2 KB, 1,675 linee) - 13.9%

### 17. **`api_fallback_config.py`** ❌
- **Size:** 21.6 KB | **Lines:** 536 | **Modified:** 11-01
- **Status:** ❌ OBSOLETO - Funzioni integrate in daily_generator.py
- **Classe:** `APIFallbackManager`
- **Motivo:** `get_fallback_data()` già definita in daily_generator.py (linea 196)

### 18. **`momentum_indicators.py`** ❌
- **Size:** 11.7 KB | **Lines:** 259 | **Modified:** 11-01
- **Status:** ❌ OBSOLETO - NON importato
- **Funzione:** `calculate_news_momentum()`
- **Motivo:** Calcoli momentum integrati in daily_generator.py

### 19. **`bt_integration_real.py`** ❌
- **Size:** 10.9 KB | **Lines:** 244 | **Modified:** 11-01
- **Status:** ❌ OBSOLETO - Feature non attiva
- **Classe:** `SVAnalysisEngine`
- **Motivo:** Backtest integration mai implementata

### 20. **`chart_generator.py`** ❌
- **Size:** 22.9 KB | **Lines:** 495 | **Modified:** 11-01
- **Status:** ❌ OBSOLETO - NON usato
- **Motivo:** Generazione grafici non utilizzata

### 21. **`sv_dashboard.py`** ❌
- **Size:** 5.1 KB | **Lines:** 141 | **Modified:** 11-01
- **Status:** ❌ OBSOLETO - Feature non attiva
- **Import:** `Flask`, `sv_news`, `sv_calendar`, `sv_ml`
- **Motivo:** Dashboard web mai implementata
- **Note:** ⚠️ Importa `sv_ml` che è anch'esso obsoleto

---

## 🔄 **TEMP_TEST - FEATURES V2.0** (56.4 KB, 1,447 linee) - 10.8%

### 22. **`ml_analyzer.py`** 🔄
- **Size:** 24.3 KB | **Lines:** 603 | **Modified:** 11-01
- **Status:** 🔄 FUTURE - Sistema ML avanzato
- **Import:** `numpy`, `pandas`
- **Motivo:** ML analysis non integrato, utile v2.0

### 23. **`sv_ml.py`** 🔄
- **Size:** 11 KB | **Lines:** 290 | **Modified:** 11-01
- **Status:** 🔄 FUTURE - ML wrapper
- **Classe:** `SVMLSystem`
- **Motivo:** Sistema ML non attivo, utile v2.0

### 24. **`brain.py`** 🔄
- **Size:** 13.7 KB | **Lines:** 354 | **Modified:** 11-01
- **Status:** 🔄 FUTURE - AI decision engine
- **Classe:** `SVBrain`
- **Import:** `pandas`, `numpy`
- **Motivo:** AI engine avanzato per v2.0

### 25. **`engine.py`** 🔄
- **Size:** 7.7 KB | **Lines:** 220 | **Modified:** 11-01
- **Status:** 🔄 FUTURE - Core engine
- **Import:** `yfinance`, `matplotlib`, `seaborn`, `feedparser`
- **Motivo:** Engine legacy, potenzialmente utile v2.0

---

## 📈 **STATISTICHE FINALI**

### **Per Categoria:**
| Categoria | Files | Size | Lines | % |
|-----------|-------|------|-------|---|
| Core Generators | 3 | 278.7 KB | 4,803 | 53.6% |
| Telegram & Comm | 3 | 40.9 KB | 1,039 | 7.9% |
| Data Sources | 2 | 38.6 KB | 885 | 7.4% |
| Scheduler | 2 | 24.4 KB | 618 | 4.7% |
| Triggers | 5 | 17.6 KB | 449 | 3.4% |
| Utilities | 1 | 4.8 KB | 125 | 0.9% |
| **ACTIVE TOTAL** | **16** | **405 KB** | **7,919** | **77.9%** |
| Obsoleti | 5 | 72.2 KB | 1,675 | 13.9% |
| Future/Temp | 4 | 56.4 KB | 1,447 | 10.8% |
| **INACTIVE TOTAL** | **9** | **128.6 KB** | **3,122** | **24.7%** |
| **GRAND TOTAL** | **25** | **520 KB** | **9,739** | **100%** |

---

## 🎯 **AZIONI CONSIGLIATE**

### **IMMEDIATE (oggi):**
1. ❌ **ELIMINA 5 obsoleti** → Libera 72.2 KB (13.9%)
   - `api_fallback_config.py`
   - `momentum_indicators.py`
   - `bt_integration_real.py`
   - `chart_generator.py`
   - `sv_dashboard.py`

2. 🔄 **SPOSTA 4 in temp_test** → Libera 56.4 KB (10.8%)
   - `ml_analyzer.py`
   - `sv_ml.py`
   - `brain.py`
   - `engine.py`

### **Risultato post-cleanup:**
- **Moduli attivi:** 16 files (405 KB, 7,919 linee)
- **Riduzione:** -24.7% size, -3,122 linee
- **Struttura:** Snella, modulare, mantenibile

### **PRIORITY FIX (opzionale):**
- ⚠️ Rinomina classe `SVPDFGeneratetor` → `SVPDFGenerator` in `pdf_generator.py`

---

## 📋 **DIPENDENZE ATTIVE**

```
main.py (orchestrator)
  └─> sv_scheduler.py
      ├─> sv_calendar.py
      └─> triggers/*.py
          ├─> daily_generator.py
          │   ├─> sv_emoji.py
          │   ├─> sv_news.py
          │   └─> sv_calendar.py
          ├─> weekly_generator.py
          │   └─> pdf_generator.py
          ├─> monthly_generator.py
          │   └─> pdf_generator.py
          └─> telegram_handler.py
```

### **Nessuna dipendenza circolare** ✅
### **Struttura pulita e gerarchica** ✅
