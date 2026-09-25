@echo off
chcp 65001 >nul
setlocal
set "SCRIPT=%~dp0gif_frame_reducer.py"
set "PYTHON=C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo.
echo GIF 抽帧压缩工具
echo ----------------
echo 提示：将 GIF 文件直接拖到这个 .cmd 文件上，也可以在下面粘贴完整路径。
set "INPUT=%~1"
if "%INPUT%"=="" set /p "INPUT=GIF 文件路径："
if "%INPUT%"=="" (
  echo 未提供文件路径。
  pause
  exit /b 2
)
set /p "EVERY=每隔几帧保留 1 帧（建议 3 到 6）："
if "%EVERY%"=="" set "EVERY=4"

if exist "%PYTHON%" (
  "%PYTHON%" "%SCRIPT%" "%INPUT%" --every %EVERY%
) else (
  py -3 "%SCRIPT%" "%INPUT%" --every %EVERY%
)
echo.
pause
