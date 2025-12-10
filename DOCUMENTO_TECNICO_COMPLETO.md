# DOCUMENTO TECNICO COMPLETO – Versione Integrale

## 1. Obiettivo del Sistema
Il sistema è progettato per:
- Raccogliere dati finanziari da API esterne (prezzi, volumi, news, sentiment).
- Applicare indicatori tecnici in tempo reale: RSI, MACD, ATR, Momentum, Trend, Volatilità, Bollinger Bands, Fibonacci Levels.
- Utilizzare modelli ML/AI per predizioni, classificazioni rischio e segnali intelligenti.
- Gestire un portafoglio multi-asset e multi-broker con operazioni consigliate e ribilanciamento automatico.
- Generare report settimanali, mensili, trimestrali, semestrali e annuali in PDF/HTML/JSON.
- Fornire una dashboard online per consultazione, alert e dati in tempo reale.
- Funzionare 24/7 grazie allo scheduler integrato.
- Inviare notifiche su Telegram tramite bot, con moduli dedicati per ogni tipo di messaggio/report.

Focus primario: fornire analisi decisionale di alto livello, integrando ENGINE (tecnica), BRAIN (AI), PORTFOLIO (decisioni) e PRODUCTION (output).

## 2. Panoramica dell'Architettura
Il sistema è suddiviso in quattro macro-moduli indipendenti:
- **ENGINE — Technical Market Layer**: raccolta dati, feature engineering, indicatori (RSI, MACD, ATR, Momentum, Trend, Volatilità).
- **BRAIN — Artificial Intelligence Layer**: predizioni tramite modelli ML/AI, rischio e classificazioni, generazione di segnali intelligenti.
- **PORTFOLIO — Decision & Allocation Layer**: gestione posizioni, simulazioni/backtesting, risk management, operazioni consigliate/automatiche.
- **PRODUCTION — Reporting Layer**: report giornalieri/settimanali/mensili, press review, dashboard data feed, storico analitico.

### Dashboard Web: 3 tabs principali
1. Calendario Task & Report
2. Notizie + Sentiment + correlazioni
3. Portfolio + Indicatori + Segnali Tecnici & AI

## 3. Struttura delle Directory
```
ROOT/
├── config/
│   └── config.txt # parametri principali
├── templates/ # template report e PDF
├── api/ # definizione API e token
├── diario.md # log di sviluppo
├── readme.md # documentazione
├── modules/
│   ├── engine/ # modulo 1
│   ├── brain/ # modulo 2
│   ├── portfolio/ # modulo 3
│   ├── production/ # modulo 4
│   ├── dashboard/ # backend API + frontend statico
│   ├── telegram/ # invio messaggi/report
│   ├── news/ # raccolta news e sentiment
│   ├── calendar/ # gestione eventi, task e report pianificati
├── cache/ # dati temporanei
├── scheduler.py # orchestrazione task
├── utils.py # helper condivisi
├── main.py # entry point principale
└── report/
    ├── daily/
    ├── weekly/
    ├── monthly/
    ├── quarterly/
    ├── semi_annual/
    └── yearly/
```

## 4. ENGINE — Modulo Tecnico Dettagliato
Funzione principale: acquisisce il flusso dati da API e lo trasforma in indicatori tecnici robusti.

**Pipeline** (30 minuti mercati tradizionali / 15 min crypto):
- `fetcher.py`: richiama API prezzi & volumi, controlla integrità dati, scrive `cache/raw/asset_timestamp.json`.
- `preprocessor.py`: normalizzazione, scaling (z-score/min-max), rimozione outlier.
- `indicators.py`: calcolo RSI, MACD, ATR, Momentum, Trend, Volatilità, Bollinger Bands, Fibonacci Levels (ultime 24h).
- `state_builder.py`: costruzione `engine_state.json`, aggiornamento `cache/processed`, invio segnali grezzi a BRAIN.

## 5. BRAIN — Modulo AI Dettagliato
Obiettivo: trasformare indicatori tecnici in predizioni, segnali intelligenti e classificazioni di rischio.

Moduli interni:
1. `analyzer.py`: pattern recognition, regression channels, anomalie.
2. `predictor.py`: modelli ML (LSTM, RNN, Gradient Boosting, Random Forest, Logistic Regression).
3. `signals.py`: genera segnali BUY/SELL/HOLD/STRONG BUY/STRONG SELL con punteggio confidenza 0–1.
4. `fusion.py`: combina ENGINE + ML per segnali finali (es. RSI < 30 + AI BUY → Strong BUY).

Output:
- `brain_predictions.json`.
- `brain_signals.json` → invio al modulo PORTFOLIO.

## 6. PORTFOLIO — Decision Layer
Obiettivo: gestione multi-asset e multi-broker, incluse posizioni, esposizione, rischio, segnali operativi, strategie, notifiche e rendicontazione costi.

Allocazione target (percentuale totale):

| Asset Class | Percentuale | Note |
| --- | --- | --- |
| Liquidità | 20% | Buffer per ordini e volatilità |
| Indici / Azioni / ETF oro | 40% | ETF azioni, indici e oro |
| Obbligazioni | 20% | Titoli o ETF obbligazionari |
| Crypto (derivati e spot) | 20% | Solo su Bybit, bot trading attivo |

**Distribuzione Broker**

| Broker | Tipo gestione | Asset principali | Note operative |
| --- | --- | --- | --- |
| Bybit | Bot trading | Derivati e spot crypto | Bot operativo, metà capitale broker attivo |
| IG Italia | Bot trading | Spot + derivati ETF/azioni/indici | Bot operativo, metà capitale broker |
| Directa | Medio-lungo | Azioni, ETF (oro), obbligazioni, liquidità | Riceve notifiche operative, nessun ordine automatico |
| Trade Republic | Medio-lungo | Azioni, ETF (oro), obbligazioni, liquidità | Riceve notifiche operative, nessun ordine automatico |

Tracciamento operazioni: ogni operazione registra broker, timestamp, asset, azione, quantità, prezzo unitario, totale, commissioni, tasse stimate e rationale decisionale. Ribilanciamento: mensile o straordinario ±10% target. Output JSON: `portfolio_state.json`, `portfolio_signals.json` per Telegram.

## 7. PRODUCTION — Reportistica
**Report giornalieri**

| Orario | Nome | Contenuto |
| --- | --- | --- |
| 06:00 | Press Review | Notizie chiave + sentiment |
| 09:00 | Morning | Indicatori + ML + scenario |
| 12:00 | Noon | Mid-day outlook |
| 15:00 | Afternoon | Segnali tecnici |
| 18:00 | Evening | Performance giornata |
| 21:00 | Summary | Riepilogo completo |
| 00:00 | Night | Analisi trend notturni |
| 03:00 | Late Night | Aggiornamento silenzioso |

Report settimanali/mensili/trimestrali/semestrali/annuali includono overview mercati, performance portafoglio, segnali ML ricorrenti, cambiamenti rilevanti.

Componenti: `report_builder.py`, `formatter.py`, `exporter.py`.

## 8. Dashboard Web
- Backend: FastAPI.
- Frontend: HTML/Tailwind/JS o React.

**Tabs**
1. Calendario → lista report, eventi scheduler, stato moduli.
2. Notizie → news da API, sentiment, correlazioni, press review automatica.
3. Portfolio + Segnali ML → posizioni, indicatori live, predizioni AI, segnali BUY/SELL, rischio.

API: `/api/calendar`, `/api/system_status`, `/api/news`, `/api/sentiment`, `/api/portfolio`, `/api/engine_state`, `/api/brain_state`, `/api/signals`.

## 9. Scheduler dei Task
- ENGINE: ogni 30 min (tradizionali), 15 min (crypto).
- BRAIN: ogni 60 min (tradizionali), 15–30 min (crypto).
- PORTFOLIO: ogni 60 min.
- PRODUCTION: weekly/monthly/quarterly/semi-annual/yearly.
- TELEGRAM: ad eventi (messaggi/retry/priorità).

## 10. Struttura Dati JSON
- `engine_state.json` → indicatori tecnici.
- `brain_signals.json` → segnali AI.
- `portfolio_state.json` → posizioni e operazioni consigliate.
- `report_metadata.json` → link PDF, orari, contenuti.

## 11. API Interne/Intermodulari
Flusso principale: ENGINE → BRAIN → PORTFOLIO → PRODUCTION → DASHBOARD → TELEGRAM.

## 12. Sicurezza, Logging e Error Handling
- Logging per modulo con livelli INFO/WARNING/ERROR/CRITICAL, rotazione giornaliera.
- API key encrypted, sanitizzazione input.
- Telegram bot con retry automatico.
- Fallback dati e notifiche errori critici.

## 13. Scalabilità, Deployment e Modularizzazione
- Massima modularizzazione per tutti i moduli.
- Microservizi indipendenti.
- Container Docker, Kubernetes.
- Load balancing API esterne, caching intelligente.
- Possibilità di sostituire singoli moduli senza impatto sugli altri.

## 14. Roadmap Evolutiva
- Bot Telegram completo per segnali e report.
- Strategie multiple + auto-trading.
- Backtesting automatico.
- API pubblica (read-only).
- Heatmap asset, auto-ottimizzazione ML.
- Espansione alert Telegram: push notifiche a gruppi multipli, prioritizzazione messaggi.

## 15. TELEGRAM – Integrazione Messaggistica
- Moduli dedicati per ogni tipo di messaggio/report: Weekly, Monthly, Quarterly, Semi-Annual, Yearly, Recommended Ops, Breaking News.
- Priorità invio: Breaking News > Operazioni consigliate > Yearly > Semi-Annual > Quarterly > Monthly > Weekly.
- Funzioni: invio messaggi PDF/Markdown/HTML, retry, scheduler prioritario.

## 16. Moduli Specifici di Messaggistica Telegram
- `telegram/weekly/` → invio report settimanale.
- `telegram/monthly/` → invio report mensile.
- `telegram/quarterly/` → invio report trimestrale.
- `telegram/semi_annual/` → invio report semestrale.
- `telegram/yearly/` → invio report annuale.
- `telegram/recommended_ops/` → operazioni consigliate.
- `telegram/breaking_news/` → breaking news immediate.

## 17. Moduli Aggiuntivi
- `news/` → raccolta news da API esterne, analisi sentiment, correlazioni.
- `calendar/` → gestione eventi e task, storico report generati.
- `dashboard/` → backend API + frontend HTML/Tailwind/React.

## Diagramma di Flusso Moduli
```
┌───────────────┐
│ ENGINE        │
│ Data collection│
│ Technical Ind. │
└───────┬───────┘
        │ JSON engine_state.json
        ▼
┌───────────────┐
│ BRAIN         │
│ ML/AI Signals │
└───────┬───────┘
        │ JSON brain_signals.json
        ▼
┌───────────────┐
│ PORTFOLIO     │
│ Asset Mgmt &  │
│ Recommendations│
└───────┬───────┘
        │ JSON portfolio_state.json
┌──────┼───────────────┐
▼      ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ PRODUCTION    │ │ TELEGRAM      │ │ DASHBOARD     │
│ Reports PDF/  │ │ Messaging     │ │ Frontend +    │
│ JSON/HTML     │ │ Modules       │ │ Backend APIs  │
└───────────────┘ └───────────────┘ └───────────────┘
        │ JSON report_metadata.json
        ▼
┌───────────────┐
│ NEWS          │
│ Sentiment     │
└───────┬───────┘
        ▼
┌───────────────┐
│ CALENDAR      │
│ Task Scheduling│
└───────────────┘
```
