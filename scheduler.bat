@echo off
:loop
python kancolle_echor.py
set /p SLEEP_TIME= < sleep_time
sleep %SLEEP_TIME%
goto loop