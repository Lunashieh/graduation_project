@echo off
setlocal

REM ====== 1) Project paths (edit if needed) ======
set "ROOT=D:\graduation project\project_root"
set "PROTOCOL=Yahalom"
set "PROVERIF_EXE=D:\graduation project\proverif2.05\proverif.exe"
set "MAKE_VERDICT=%ROOT%\scripts\make_verdict.py"

REM ====== 2) Sanity checks ======
if not exist "%PROVERIF_EXE%" (
  echo [ERROR] ProVerif not found: "%PROVERIF_EXE%"
  exit /b 1
)

if not exist "%MAKE_VERDICT%" (
  echo [ERROR] make_verdict.py not found: "%MAKE_VERDICT%"
  exit /b 1
)

if not exist "%ROOT%\data_modified\%PROTOCOL%\baseline\model.pv" (
  echo [ERROR] baseline model not found: "%ROOT%\data_modified\%PROTOCOL%\baseline\model.pv"
  exit /b 1
)

REM ====== 3) Run all bugs ======
for %%V in (bug_01 bug_02 bug_03) do (
  echo.
  echo ==========================
  echo Running %%V
  echo ==========================

  REM ProVerif log
  "%PROVERIF_EXE%" -in pitype "%ROOT%\data_modified\%PROTOCOL%\bugs\%%V\model.pv" > "%ROOT%\data_modified\%PROTOCOL%\bugs\%%V\proverif.log" 2>&1

  REM patch.diff (fc returns errorlevel 1 when files differ; that's OK)
  fc /n "%ROOT%\data_modified\%PROTOCOL%\baseline\model.pv" "%ROOT%\data_modified\%PROTOCOL%\bugs\%%V\model.pv" > "%ROOT%\data_modified\%PROTOCOL%\bugs\%%V\patch.diff"

  
  python "%MAKE_VERDICT%" --protocol %PROTOCOL% --variant %%V --dir "%ROOT%\data_modified\%PROTOCOL%\bugs\%%V" --command "proverif -in pitype model.pv"

  echo [OK] %%V done.
)

echo.
echo All done.
endlocal