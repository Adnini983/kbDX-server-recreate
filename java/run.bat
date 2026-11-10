@echo off
cd /d "%~dp0"
if not exist build\classes\KbdxServer.class call build.bat
java -cp "%~dp0build\classes" KbdxServer
