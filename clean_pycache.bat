@echo off
echo Cleaning __pycache__ folders in progress...

:: Delete all __pycache__ folders recursively
FOR /d /r . %%d in (__pycache__) DO @IF EXIST "%%d" rd /s /q "%%d"

:: Also delete all .pyc files
del /s /q *.pyc 2>nul

echo Cleaning completed!
pause 