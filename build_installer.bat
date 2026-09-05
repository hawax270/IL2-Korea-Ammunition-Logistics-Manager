@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo IL2 Korea Ammunition Logistics Manager v1.0.2
echo Installer build
echo ============================================================
echo.

if not exist "dist\IL2_Korea_Ammunition_Logistics_Manager\IL2_Korea_Ammunition_Logistics_Manager.exe" (
    echo ERROR:
    echo The compiled application was not found.
    echo.
    echo First run:
    echo     build_windows.bat
    echo.
    echo Then run this file again.
    echo.
    pause
    exit /b 1
)

set "ISCC="

if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
)

if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
)

if not defined ISCC if exist "%LocalAppData%\Programs\Inno Setup 7\ISCC.exe" (
    set "ISCC=%LocalAppData%\Programs\Inno Setup 7\ISCC.exe"
)

if not defined ISCC (
    echo ERROR:
    echo Inno Setup 7 / ISCC.exe was not found automatically.
    echo.
    echo Open Inno Setup manually and compile:
    echo     installer.iss
    echo.
    pause
    exit /b 1
)

echo Inno Setup:
echo "%ISCC%"
echo.

if exist "installer_output" rmdir /s /q "installer_output"

"%ISCC%" "installer.iss"
if errorlevel 1 goto :error

echo.
echo ============================================================
echo INSTALLER BUILD COMPLETE
echo ============================================================
echo.
echo Output:
echo installer_output\IL2_Korea_ALM_Setupv1.0.2.exe
echo.
pause
exit /b 0

:error
echo.
echo ============================================================
echo INSTALLER BUILD FAILED
echo ============================================================
echo.
echo Check the error messages above.
echo.
pause
exit /b 1
