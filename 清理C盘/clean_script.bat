@echo off
:: Batch Script for C Drive Cleanup
:: Checks for Admin rights and self-elevates if needed
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting Admin Privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

title C盘一键清理工具
color 0A
cls
echo ============================================================
echo                C盘一键清理工具 (详细日志版)
echo ============================================================
echo.
echo [1/5] 正在清理系统临时文件 (Windows\Temp)...
del /f /s /q "%windir%\temp\*.*"
rd /s /q "%windir%\temp" >nul 2>&1
md "%windir%\temp" >nul 2>&1

echo.
echo [2/5] 正在清理用户临时文件 (%TEMP%)...
del /f /s /q "%userprofile%\AppData\Local\Temp\*.*"
rd /s /q "%userprofile%\AppData\Local\Temp" >nul 2>&1
md "%userprofile%\AppData\Local\Temp" >nul 2>&1

echo.
echo [3/5] 正在清理系统预读取文件 (Prefetch)...
del /f /s /q "%windir%\Prefetch\*.*"

echo.
echo [4/5] 正在清理回收站...
echo 正在清空回收站...
rd /s /q %systemdrive%\$Recycle.Bin >nul 2>&1

echo.
echo [5/5] 正在清理系统更新缓存 (慎用)...
echo       跳过此步骤以保证稳定性。
:: del /f /s /q "%windir%\SoftwareDistribution\Download\*.*"

echo.
echo ============================================================
echo                     清理完成!
echo ============================================================
echo.
pause
