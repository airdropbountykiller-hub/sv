# Audit moduli

Riscontro sui contenuti della cartella `modules` per individuare file duplicati, obsoleti o non più referenziati.

## Elementi obsoleti o duplicati
- Nessun duplicato individuato all'interno della cartella `modules`.
- Le directory `__pycache__` generate automaticamente (es. in `modules/brain`, `modules/engine`, `modules/generators`) non sono necessarie al versionamento e possono restare ignorate.

## Moduli non referenziati
- `legacy_daily_generator_helpers.py`: nessun riferimento nei sorgenti o nella documentazione corrente. Contiene helper estratti dal vecchio `daily_generator` e già marcati come "Legacy" nel docstring; al momento è tenuto solo per riferimento storico.

## Esito test rapido sui moduli
- Script eseguito: `python temp_tests/test_all_modules.py`.
- Import principali e generator funzionanti, ma il test fallisce su `modules.narrative_continuity` perché il modulo non è presente nel repository (il daily generator opera comunque con narrativa disabilitata).

## Moduli principali attivi
- I trigger giornalieri e scheduler (`main.py`, `trigger_*`, `sv_scheduler.py`) sono ancora i punti di ingresso elencati nei file di struttura e nei test interni; non risultano duplicati degli stessi moduli con nomi differenti.
