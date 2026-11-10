@echo off
cd /d "%~dp0"
if not exist build\classes mkdir build\classes
javac -encoding UTF-8 -d build\classes src\KbdxServer.java
if errorlevel 1 exit /b 1
echo built: %~dp0build\classes
