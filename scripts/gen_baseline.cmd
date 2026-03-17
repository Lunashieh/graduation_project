@echo off
setlocal EnableExtensions

REM ============================================================
REM gen_baseline.cmd
REM Usage:
REM   gen_baseline.cmd NeedhamSchroederPK
REM   gen_baseline.cmd NeedhamSchroederSK
REM   gen_baseline.cmd DenningSacco
REM ============================================================

REM ---- Fixed paths (edit once) ----
set "ROOT=D:\graduation project\project_root"
set "PROVERIF_EXE=D:\graduation project\proverif2.05\proverif.exe"
set "MAKE_VERDICT=%ROOT%\scripts\make_verdict.py"

REM ---- Args ----
if "%~1"=="" (
  echo [ERROR] Missing protocol name.
  echo Usage: %~nx0 ^<ProtocolFolderName^>
  exit /b 1
)
set "PROTOCOL=%~1"
set "BASE_DIR=%ROOT%\data_modified\%PROTOCOL%\baseline"

REM ---- Checks ----
if not exist "%PROVERIF_EXE%" (
  echo [ERROR] ProVerif not found: "%PROVERIF_EXE%"
  exit /b 1
)
if not exist "%MAKE_VERDICT%" (
  echo [ERROR] make_verdict.py not found: "%MAKE_VERDICT%"
  exit /b 1
)
if not exist "%BASE_DIR%\model.pv" (
  echo [ERROR] Missing model.pv: "%BASE_DIR%\model.pv"
  exit /b 1
)

echo.
echo ============================================================
echo Generating baseline artefacts: %PROTOCOL%
echo Folder: %BASE_DIR%
echo ============================================================

REM ---- 1) Run ProVerif ----
cd /d "%BASE_DIR%"
"%PROVERIF_EXE%" -in pitype model.pv > proverif.log 2>&1



REM ---- 3) verdict.json ----
python "%MAKE_VERDICT%" ^
  --protocol "%PROTOCOL%" ^
  --variant "baseline" ^
  --dir "%BASE_DIR%" ^
  --command "proverif -in pitype model.pv"

echo [OK] baseline artefacts generated for %PROTOCOL%
endlocal