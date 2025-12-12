# SV - Struttura Completa Progetto

**Data analisi:** 02 Nov 2025 18:29  
**Totale size:** ~3.22 MB

---

## 📁 **ROOT DIRECTORY** (3 files, 45.5 KB)

```
H:\il mio drive\sv\
├── README.md (25.2 KB)       ⭐ Documentazione principale
├── DIARY.md (18.2 KB)        📓 Diario operazioni + troubleshooting
└── SV_Start.bat (2.1 KB)     🚀 Entry point sistema
```

---

## 🗂️ **DIRECTORY STRUCTURE**

### **1. modules/** (19 files, 0.98 MB = 461.9 KB)

**Core del sistema - Tutti i moduli Python attivi**

```
modules/
├── Core Generators (3 files, 253.9 KB)
│   ├── daily_generator.py (199.5 KB)    ⭐⭐⭐⭐⭐ CORE - 22 msgs/day
│   ├── weekly_generator.py (28.8 KB)    ⭐⭐⭐⭐ Weekly PDF
│   └── monthly_generator.py (25.6 KB)   ⭐⭐⭐⭐ Monthly PDF
│
├── Communication (3 files, 66.6 KB)
│   ├── telegram_handler.py (28.7 KB)    ⭐⭐⭐⭐⭐ CORE Telegram
│   ├── pdf_generator.py (26.8 KB)       ⭐⭐⭐ PDF creation
│   └── manual_sender.py (11.1 KB)       ⭐⭐⭐⭐ Manual testing
│
├── Data Sources (2 files, 38.6 KB)
│   ├── sv_news.py (20.3 KB)             ⭐⭐⭐⭐⭐ CORE News RSS
│   └── sv_calendar.py (18.3 KB)         ⭐⭐⭐⭐⭐ CORE Calendar
│
├── Scheduler (2 files, 24.4 KB)
│   ├── sv_scheduler.py (14.8 KB)        ⭐⭐⭐⭐⭐ CORE Timing
│   └── main.py (9.6 KB)                 ⭐⭐⭐⭐⭐ CORE Orchestrator
│
├── Triggers (5 files, 17.6 KB)
│   ├── trigger_press_review.py (3.4 KB) ⭐⭐⭐⭐⭐ 07:00
│   ├── trigger_morning.py (3.3 KB)      ⭐⭐⭐⭐⭐ 08:30
│   ├── trigger_noon.py (3.2 KB)         ⭐⭐⭐⭐⭐ 13:00
│   ├── trigger_evening.py (3.3 KB)      ⭐⭐⭐⭐⭐ 18:30
│   └── trigger_summary.py (4.4 KB)      ⭐⭐⭐⭐⭐ 20:00
│
├── Utilities (1 file, 4.8 KB)
│   └── sv_emoji.py (4.8 KB)             ⭐⭐⭐⭐⭐ CORE Windows emoji fix
│
└── Support (3 files, 56.2 KB)
    ├── api_fallback_config.py (21.6 KB)  🔄 Fallback logic (potenzialmente utile)
    ├── chart_generator.py (22.9 KB)      🔄 Grafici (feature futura)
    └── momentum_indicators.py (11.7 KB)  🔄 Calcoli tecnici (potenzialmente utile)
```

**Status:** 16 CORE attivi + 3 Support mantenuti

---

### **2. temp_test/** (5 files, 0.07 MB = 67.7 KB)

**Moduli future features v2.0 + documentazione**

```
temp_test/
├── ML/AI Modules (4 files, 56.7 KB)
│   ├── ml_analyzer.py (24.3 KB)         🔄 ML analysis avanzata
│   ├── brain.py (13.7 KB)               🔄 AI decision engine
│   ├── sv_ml.py (11 KB)                 🔄 ML wrapper
│   └── engine.py (7.7 KB)               🔄 Core engine legacy
│
└── Documentation (1 file, 11 KB)
    └── MODULES_STRUCTURE.md (11 KB)     📄 Analisi dettagliata moduli
```

**Scopo:** Moduli potenzialmente utili per v2.0, non attivi ora

---

### **3. temp_tests/** (10 files, 0.09 MB = 91.1 KB)

**Test scripts + moduli avanzati non integrati**

```
temp_tests/
├── Advanced Modules (4 files, 53.4 KB)
│   ├── narrative_continuity.py (16 KB)       🔄 Sistema continuità avanzato
│   ├── ml_coherence_analyzer.py (22.9 KB)   🔄 Analisi ML coerenza
│   ├── trigger_ml_analysis.py (11 KB)       🔄 Trigger ML analysis
│   └── log_handler.py (3.5 KB)              🔄 Console-safe logging
│
├── Test Scripts (5 files, 31.6 KB)
│   ├── test_rich_pdf.py (8.2 KB)            🧪 PDF testing
│   ├── test_complete_pdf_system.py (7.5 KB) 🧪 PDF + Telegram test
│   ├── test_pdf_reports.py (6.5 KB)         🧪 PDF reports test
│   ├── cleanup_reports.py (5.3 KB)          🧪 Utility cleanup
│   └── test_pdf_telegram.py (4.1 KB)        🧪 Telegram test
│
└── Documentation (1 file, 6.1 KB)
    └── MODULI_ANALISI.md (6.1 KB)           📄 Analisi costi-benefici
```

**Scopo:** Testing + moduli avanzati non integrati

---

### **4. reports/** (8 subdirs, 418 files, 1.96 MB)

**Output sistema - Tutti i report generati**

```
reports/
├── 1_daily/ (1 file, ~0 MB)
│   └── Archiviazione daily data
│
├── 2_weekly/ (1 file, 0.01 MB = 10 KB)
│   └── SV_Weekly_Report_*.pdf (1 PDF generato)
│
├── 3_monthly/ (0 files)
│   └── Ready per accumulo dati
│
├── 4_quarterly/ (0 files)
│   └── Future timeframe
│
├── 5_semiannual/ (0 files)
│   └── Future timeframe
│
├── 6_annual/ (0 files)
│   └── Future timeframe
│
├── 8_daily_content/ (14 files, 0.09 MB)
│   ├── day_connection_2025-11-02.json
│   ├── 2025-11-02_*_press_review.json
│   ├── 2025-11-02_*_morning_report.json
│   ├── 2025-11-02_*_noon_update.json
│   ├── 2025-11-02_*_evening_analysis.json
│   └── Content JSON files per ML analysis
│
└── 9_telegram_history/ (402 files, 1.86 MB)
    └── 2025-11-02_*_<content_type>.json
        ├── 185834_press_review.json (7 messages oggi)
        ├── 185859_morning.json (3 messages oggi)
        ├── 185914_noon.json (3 messages oggi)
        ├── 184628_evening.json (3 messages ieri)
        └── Historical archive tutti messaggi Telegram
```

**Dettaglio Telegram History:**
- **402 files totali** = ~20+ giorni operativi
- **1.86 MB** = ~4.6 KB/message medio
- **Oggi (02 Nov):** 13 messages inviati (press, morning, noon)
- **Funzione:** Cronologia completa + ML training data

---

### **5. config/** (state & ML analysis)

**Runtime state e session data**

```
config/
├── sv_flags.json (0.2 KB)                    📍 Scheduler flags (aggiornato 18:59)
├── daily_session.json (0.7 KB)               📊 Session tracking (31 Oct)
├── daily_contexts/                           🧠 ML contexts
└── ml_analysis/                              🔬 ML analysis results
```

**sv_flags.json attuale:**
```json
{
  "press_review_sent": true,
  "morning_sent": true,
  "noon_sent": true,
  "evening_sent": true,
  "summary_sent": false,  ← READY per 20:00
  "weekly_sent": false,
  "monthly_sent": false,
  "last_reset_date": "20251102"
}
```

---

### **6. config/** (6 files, 0.02 MB = 20 KB)

**Configurazione sistema**

```
config/
├── private.txt                  🔐 Telegram credentials
├── requirements.txt             📦 Python dependencies
└── [altri config files]
```

---

### **7. data/** (0 files)

**Directory per dati esterni (vuota)**

---

### **8. templates/** (3 files, 0.1 MB = 100 KB)

**Template configurazione**

```
templates/
├── private.txt.template         📄 Template credentials
└── [altri template]
```

---

## 📊 **STATISTICHE GLOBALI**

### **Size Distribution:**
| Directory | Size (MB) | % Total | Files | Status |
|-----------|-----------|---------|-------|--------|
| reports/ | 1.96 | 60.9% | 418 | ✅ Growing |
| modules/ | 0.98 | 30.4% | 19 | ✅ Active |
| temp_tests/ | 0.09 | 2.8% | 10 | 🔄 Testing |
| temp_test/ | 0.07 | 2.2% | 5 | 🔄 Future |
| templates/ | 0.10 | 3.1% | 3 | ✅ Static |
| config/ | 0.02 | 0.6% | 6 | ✅ Active |
| previews/ | ~0 | ~0% | 5 | ✅ Active |
| data/ | 0 | 0% | 0 | ⚠️ Empty |
| **TOTAL** | **3.22 MB** | **100%** | **465** | **✅ OPERATIONAL** |

### **Core System:**
- **Active modules:** 16 (100% operational)
- **Support modules:** 3 (potentially useful)
- **Future modules:** 9 (v2.0 features)
- **Daily messages:** 22/day (7 press, 3 morning, 3 noon, 3 evening, 6 summary)
- **Telegram history:** 402 messages archived
- **Weekly reports:** 1 PDF generated

---

## 🎯 **COSA SUCCEDE NEL SISTEMA**

### **📤 OUTPUT FLOW:**

```
1. SCHEDULER (sv_scheduler.py)
   ↓ Check every 30s
   
2. TRIGGERS (trigger_*.py)
   ↓ is_time_for(content_type)
   
3. GENERATORS (daily_generator.py)
   ↓ generate_<content_type>()
   
4. TELEGRAM (telegram_handler.py)
   ↓ send_message(msg, content_type)
   
5. DUAL SAVE:
   ├─→ 8_daily_content/ (JSON content per ML)
   └─→ 9_telegram_history/ (JSON sent messages)
```

### **📊 ACCUMULAZIONE DATI:**

**Oggi (02 Nov):**
- ✅ 07:00 Press Review → 7 messages inviati
- ✅ 08:30 Morning → 3 messages inviati
- ✅ 13:00 Noon → 3 messages inviati
- ✅ 18:30 Evening → 3 messages inviati (ieri)
- ⏰ 20:00 Summary → 6 messages schedulati

**Weekly Reports:**
- 1 PDF in `reports/2_weekly/`
- Prossimo: Domenica 20:05

**Telegram History:**
- 402 messaggi totali archiviati
- ~20+ giorni operativi
- Average: 4.6 KB/message

---

## 🔄 **DIFFERENZA temp_test vs temp_tests**

### **temp_test/** (67.7 KB, 5 files)
- **Scopo:** Moduli ML/AI futuri v2.0
- **Content:** ml_analyzer, brain, sv_ml, engine
- **Quando:** Creato oggi durante cleanup
- **Status:** Future features non integrate

### **temp_tests/** (91.1 KB, 10 files)
- **Scopo:** Test scripts + moduli avanzati
- **Content:** Test PDF, narrative_continuity, ml_coherence
- **Quando:** Esiste da prima
- **Status:** Test utilities + advanced features

**⚠️ NOTA:** Due cartelle simili ma scopi diversi - considerare consolidamento futuro

---

## ✅ **SALUTE SISTEMA**

### **OPERATIONAL:**
- ✅ 16/19 moduli core attivi (84%)
- ✅ Scheduler funzionante 100%
- ✅ Telegram integration OK
- ✅ Daily messages 21/21 puliti
- ✅ Weekly PDF generation OK
- ✅ Data accumulation in progress

### **TODO:**
- 🔄 Testare Daily Summary 20:00 (oggi)
- 🔄 Consolidare temp_test + temp_tests (opzionale)
- 🔄 Modularizzazione daily_generator.py (future)
- 🔄 Implementare monthly dopo accumulo dati

### **STORAGE:**
- 📊 Total: 3.22 MB (molto leggero)
- 📈 Growth rate: ~100 KB/day (Telegram history)
- 🎯 Healthy: Nessun problema spazio

---

**🚀 Sistema SV - FULLY OPERATIONAL - Ready for 20:00 Summary Test**
