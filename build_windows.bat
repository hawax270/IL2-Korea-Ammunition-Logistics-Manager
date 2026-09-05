@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo IL-2 Korea Ammunition Logistics Manager v1.0.2
echo Windows build
echo ================================================
echo.

py -m pip install --upgrade pip
if errorlevel 1 goto :error

py -m pip install -r requirements.txt
if errorlevel 1 goto :error

py -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

py -m PyInstaller --noconfirm IL2_Korea_Ammunition_Logistics_Manager.spec
if errorlevel 1 goto :error

echo.
echo Build complete.
echo Output:
echo dist\IL2_Korea_Ammunition_Logistics_Manager\
echo.
pause
exit /b 0

:error
echo.
echo BUILD FAILED.
echo Check the messages above.
echo.
pause
exit /b 1
