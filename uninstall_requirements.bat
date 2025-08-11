@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Uninstall Pillow / NumPy / OpenCV everywhere (with 3.11 fallback)

echo.
echo === Phase 1: Try all interpreters from "py -0p" ===
where py >nul 2>&1
if %errorlevel%==0 (
  for /f "usebackq tokens=* delims=" %%L in (`py -0p 2^>nul`) do (
    REM Grab the last token on the line (should be the python.exe path)
    set "LINE=%%L"
    set "PYEXE="
    for %%T in (!LINE!) do set "PYEXE=%%T"
    if defined PYEXE (
      if exist "!PYEXE!" (
        echo.
        echo --- Using interpreter: "!PYEXE!" ---
        call :UNINSTALL_ONE "!PYEXE!"
      ) else (
        REM Some lines are version labels or markers, ignore
        REM echo Skipping non-path line: !LINE!
      )
    )
  )
) else (
  echo Python launcher 'py' not found; skipping this phase.
)

echo.
echo === Phase 2: Try PATH-discovered pythons (where python/python3) ===
for /f "usebackq delims=" %%P in (`where python 2^>nul`) do call :UNINSTALL_ONE "%%P"
for /f "usebackq delims=" %%P in (`where python3 2^>nul`) do call :UNINSTALL_ONE "%%P"

echo.
echo === Phase 3 (Targeted): Force-uninstall from Python 3.11 user site ===
where py >nul 2>&1
if %errorlevel%==0 (
  echo Trying: py -3.11 -m pip uninstall -y ...
  py -3.11 -m pip --version 1>nul 2>nul
  if not errorlevel 1 (
    py -3.11 -m pip uninstall -y opencv-contrib-python opencv-python-headless opencv-python numpy pillow
    echo.
    echo Purging pip cache for 3.11...
    py -3.11 -m pip cache purge
  ) else (
    echo pip not available via py -3.11 -m pip (yet). Will try manual removal.
  )
  for /f "usebackq tokens=* delims=" %%S in (`py -3.11 -c "import site,sys;print(site.getusersitepackages())"`) do (
    set "USR=%%S"
  )
  if defined USR (
    echo User site for 3.11: "%USR%"
    call :MANUAL_DELETE "%USR%"
  ) else (
    echo Could not resolve Python 3.11 user site path.
  )
) else (
  echo 'py' launcher still not available; skipping 3.11-targeted phase.
)

echo.
echo === Done. Re-run your installer to confirm fresh installs. ===
echo If it still says "Requirement already satisfied", paste that output here.
pause
goto :eof


:UNINSTALL_ONE
set "PYEXE=%~1"
echo.
echo [Inspect] "%PYEXE%" -m pip --version
"%PYEXE%" -m pip --version 1>nul 2>nul
if errorlevel 1 (
  echo pip missing for this interpreter; skipping pip uninstall here.
  goto :EOF
)

echo [Show] Installed versions (if present):
"%PYEXE%" -m pip show pillow 2>nul
"%PYEXE%" -m pip show numpy 2>nul
"%PYEXE%" -m pip show opencv-python 2>nul
"%PYEXE%" -m pip show opencv-python-headless 2>nul
"%PYEXE%" -m pip show opencv-contrib-python 2>nul

echo [Uninstall] Attempting via pip...
"%PYEXE%" -m pip uninstall -y opencv-contrib-python opencv-python-headless opencv-python numpy pillow

echo [Purge] pip cache...
"%PYEXE%" -m pip cache purge

echo [Path] User site folder:
for /f "usebackq tokens=* delims=" %%S in (`"%PYEXE%" -c "import site,sys;print(site.getusersitepackages())"`) do (
  echo   %%S
  call :MANUAL_DELETE "%%S"
)
goto :EOF


:MANUAL_DELETE
set "SITE=%~1"
if not exist "%SITE%" goto :EOF

echo [Manual] Removing leftover package folders under:
echo   %SITE%
set "CAND=pillow* numpy* opencv_python* opencv_contrib_python* cv2*"
for %%D in (%CAND%) do (
  if exist "%SITE%\%%D" (
    echo   Deleting "%SITE%\%%D"
    rmdir /s /q "%SITE%\%%D" 2>nul
    del /s /q "%SITE%\%%D" 2>nul
  )
)
goto :EOF
