@echo off
title GitHub Actions Runner - Market Watch AJN

echo ==========================================
echo  Self-Hosted Runner - Market Watch AJN
echo ==========================================
echo.

:: Coba folder yang sama dengan bat ini
set "RUNNER_DIR=%~dp0"
if exist "%RUNNER_DIR%run.cmd" goto :start_runner

:: Fallback ke C:\actions-runner
set "RUNNER_DIR=C:\actions-runner\"
if exist "%RUNNER_DIR%run.cmd" goto :start_runner

echo [ERROR] run.cmd tidak ditemukan.
echo.
echo Pastikan runner sudah di-install di C:\actions-runner
echo atau copy file ini ke folder runner.
echo Lihat panduan: RUNNER_SETUP.md
echo.
pause
exit /b 1

:start_runner
echo Runner: %RUNNER_DIR%
echo Tekan Ctrl+C untuk menghentikan.
echo.
cd /d "%RUNNER_DIR%"
run.cmd
pause
