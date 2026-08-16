@echo off
setlocal enabledelayedexpansion
title PC Remote Control - by Ruaaln
cls

cd /d "%~dp0"

call .venv\Scripts\activate.bat

color 0A

echo.
echo  ===================================================================
echo.
echo    ########   ######     ######   #######  ##    ## ######## 
echo    ##     ## ##    ##   ##    ## ##     ## ###   ##    ##    
echo    ##     ## ##         ##       ##     ## ####  ##    ##    
echo    ########  ##         ##       ##     ## ## ## ##    ##    
echo    ##        ##         ##       ##     ## ##  ####    ##    
echo    ##        ##    ##   ##    ## ##     ## ##   ###    ##    
echo    ##         ######     ######   #######  ##    ##    ##    
echo.
echo  ===================================================================
echo               DEVELOPED BY RUAALN  ^|  v2.0
echo  ===================================================================
echo.

echo  [+] Local IP unvanlari teyin olunur...
echo.

for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr "IPv4"') do (
    set "RAW_IP=%%A"
    rem Basindaki ve sonundaki bosluqlari temizleyirik
    for /f "tokens=*" %%B in ("!RAW_IP!") do set "MY_IP=%%B"
    
    echo  [>] IP Tapildi: http://!MY_IP!:9050
    echo  -------------------------------------------------------------------
    
    python -c "import qrcode; qr = qrcode.QRCode(border=1); qr.add_data('http://!MY_IP!:9050'); qr.make(); qr.print_ascii(invert=True)" 2>nul
    
    echo  -------------------------------------------------------------------
)

echo.
echo  [!] Telefonunuzla yuxaridaki QR kodu skan edin ve ya brauzerde acin.
echo  [*] Server baslayir (0.0.0.0:9050)...
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 9050

pause