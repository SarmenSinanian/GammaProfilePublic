@echo off
REM Start the python script in the background
start /min cmd /c python "gamma11.py"

REM Allow time for the server to start up
timeout /t 5

REM Open Chrome and go to the URL
start chrome http://127.0.0.1:8050/
