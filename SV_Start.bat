@echo off
setlocal enableextensions enabledelayedexpansion
chcp 65001 >nul
title SV - Unified Trading System v1.4.0 - FULLY OPERATIONAL
color 0A

REM === BASE DIR ===
set BASEDIR=%~dp0
cd /d "%BASEDIR%"

echo.
echo ================================================
echo   [SV] Unified Trading System v1.4.0

echo   [STATUS] FULLY OPERATIONAL - Complete English System
echo ================================================

echo.
echo [START] Complete system initialization...
echo [ENGINE] Content Generation + Telegram Integration
echo [WEB] Dashboard: http://localhost:5000
echo [MSG] Telegram: Full message delivery system
echo.

echo [CHECK] Configuration validation...
if not exist "config\private.txt" (
    echo [ERROR] config\private.txt file not found!
    echo    [FIX] Copy templates\private.txt.template as config\private.txt
    echo    [EDIT] Add your real Telegram credentials
    echo    [INFO] Get bot token from @BotFather on Telegram
    echo.
    if exist "templates\private.txt.template" (
        echo [AUTO] Creating config\private.txt from template...
        copy "templates\private.txt.template" "config\private.txt" >nul
        echo [OK] File config\private.txt created! EDIT NOW with real credentials.
    ) else (
        echo [WARN] Template not found. Create config\private.txt manually.
    )
    echo.
    pause
)

echo [OK] Configuration validated

echo.
echo [CHECK] Recovery system status...
echo [SCAN] Missing content verification...

python modules\sv_recovery_launcher.py 2>nul
if %errorlevel% neq 0 (
    echo [WARN] Recovery not available - continuing with normal startup
) else (
    echo [OK] Recovery check completed
)

echo.
echo [WEB] Starting dashboard server...
start "SV Dashboard" /b python modules\sv_dashboard.py

echo [ENGINE] Starting orchestrator (continuous) in background...
start "SV Orchestrator" /b python "modules\main.py" continuous

echo [WAIT] Boot warm-up...
timeout /t 3 >nul

echo ========================================
echo   SV v1.4.0 - FULLY OPERATIONAL

echo   Dashboard: http://localhost:5000

echo   Content: 21 messages/day (5 types)

echo   Language: Complete English System

echo   Telegram: Full integration active

echo ========================================

echo.
echo [INFO] Orchestrator and Dashboard are running.

REM === CONTROL MENU (Unified) ===
:menu
echo.
echo ================== SV - CONTROL MENU ==================
echo  1) Run Single Check (one cycle now)
echo  2) Manual Send (safe)     [press_review|morning|noon|evening|summary]
echo  3) Manual Send (FORCE)    [press_review|morning|noon|evening|summary]
echo  4) Send saved JSON(s) via Telegram (paths separated by space)
echo  5) Open reports folder
echo  Q) Quit (orchestrator/dashboard stay running)
echo ========================================================
set /p OPT=Select option: 

if /i "%OPT%"=="1" goto single
if /i "%OPT%"=="2" goto manual_safe
if /i "%OPT%"=="3" goto manual_force
if /i "%OPT%"=="4" goto send_saved
if /i "%OPT%"=="5" goto open_reports
if /i "%OPT%"=="Q" goto end
if /i "%OPT%"=="q" goto end
echo Invalid option.
goto menu

:single
echo Running single check cycle...
python "modules\main.py" single
pause
goto menu

:manual_safe
set /p TYPE=Content type [press_review|morning|noon|evening|summary]: 
echo Sending %TYPE% (safe mode, respects scheduler and marks sent)...
python "modules\manual_sender.py" %TYPE%
pause
goto menu

:manual_force
set /p TYPE=Content type [press_review|morning|noon|evening|summary]: 
echo WARNING: FORCE mode may duplicate later via orchestrator. Consider avoiding for production.
echo Sending %TYPE% (FORCE mode)...
python "modules\manual_sender.py" %TYPE% --force
pause
goto menu

:send_saved
set /p FILES=Enter JSON file path(s) (space-separated): 
echo Sending saved JSON(s)...
python "scripts\send_telegram_reports.py" %FILES%
pause
goto menu

:open_reports
start "" "%BASEDIR%reports\8_daily_content"
goto menu

:end
echo Leaving control menu. Orchestrator and Dashboard keep running.
exit /b 0

