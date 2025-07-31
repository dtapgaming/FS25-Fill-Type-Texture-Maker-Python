@echo off
title 🧪 FS25 DiffuseMakerPython - Launch Tool
color 0B

:: Get the directory of this .bat file (assumes it's in the top-level folder)
set "ROOTDIR=%~dp0"
cd /d "%ROOTDIR%"

echo 💡 Launching FS25 Texture Generator...
echo.

:: Run the main script once
python generate_all_texture_types.py

echo.
echo ✅ Script finished. You may close this window or re-run the tool again.
pause
