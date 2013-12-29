@echo off
:loop
python kancolle_echor.py
set /p SLEEP_TIME= < sleep_time
timeout /NOBREAK %SLEEP_TIME%
goto loop