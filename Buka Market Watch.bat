@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo   Market Watch AJN ^| Sync ^& Buka Infografis
echo ================================================
echo.

:: [1] Git pull
echo [1/2] Sinkronisasi data terbaru dari GitHub...
git pull origin main
if %errorlevel% neq 0 (
    echo.
    echo [WARN] git pull gagal. Mungkin tidak ada koneksi internet.
    echo        Melanjutkan dengan file lokal yang tersedia...
)
echo.

:: [2] Cari file HTML terbaru di folder output
echo [2/2] Mencari infografis HTML terbaru...
set "LATEST="
for /f "delims=" %%f in ('dir /b /od /a-d "output\MarketWatch_AJN_*.html" 2^>nul') do (
    set "LATEST=%%f"
)

if defined LATEST (
    echo Membuka: output\%LATEST%
    echo.
    start "" "%~dp0output\%LATEST%"
) else (
    echo.
    echo [INFO] File HTML belum tersedia di folder output\
    echo        Trigger workflow GitHub Actions untuk generate infografis,
    echo        atau jalankan: python buat_infografis.py --test-html
    echo.
    pause
)
