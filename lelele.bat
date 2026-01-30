@echo off
rem --- Batch File to Start Server and Clients (Windows 10/11) ---

rem Set a specific title for this script's window for easy identification
title Python Script Launcher (Server/Clients)

echo.
echo [1/4] Attempting to close previous Python server/client processes...
rem /f forces the termination
rem /im specifies the image name (executable)
rem /t terminates the process and any child processes started by it
taskkill /f /im python.exe /t >nul 2>&1

echo [2/4] Starting server.py in a new window (Will now stay open)...
rem The 'cmd /k' command forces the new window to stay open after python.exe finishes.
start "Server Window" cmd /k "python server.py"

echo [3/4] Waiting for 1 second to allow server to initialize...
rem /t 1 waits for 1 second. /nobreak prevents Ctrl+C from interrupting the wait.
timeout /t 1 /nobreak >nul

echo [4/4] Starting MK.py (Client 1) and MK.py (Client 2) in separate windows (Will now stay open)...
rem Running MK.py twice, each in its own new window, forced to stay open by 'cmd /k'
start "Client 1 Window" cmd /k "python MK.py"
start "Client 2 Window" cmd /k "python MK.py"

echo.
echo All server and client scripts have been launched in separate windows.
echo The three new windows will stay open, even if the Python scripts finished.
rem The PAUSE command keeps this window open until you press a key.
pause