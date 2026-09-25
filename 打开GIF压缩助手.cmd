@echo off
setlocal
set "APP=%~dp0GIF压缩助手.py"
set "PYTHON=C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%PYTHON%" (
  start "" "%PYTHON%" "%APP%"
) else (
  start "" pyw -3 "%APP%"
)
