@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
REM ========================================================================
REM 人景合一 逐镜评审 Gallery 智能启动脚本（拷进 <项目>/10_镜头图/ 使用）
REM 功能：检查 Python -> 生成/校验 shot-manifest -> 端口占用检测 -> 启动服务器 -> 开浏览器
REM 本脚本不调用任何生图 API；融合候选由 fuse_shots.py 在授权后单独生成。
REM ========================================================================
cd /d "%~dp0"

set PORT=8792
set MANIFEST=shot-manifest.json
set STATE=selection-state.json

echo [1/4] 检查 Python...
where python >nul 2>nul
if errorlevel 1 (
  echo   [错误] 未找到 python，请先安装 Python 3.9+ 并加入 PATH。
  pause & exit /b 1
)

echo [2/4] 检查 shot-manifest...
if not exist "%MANIFEST%" (
  echo   [提示] 未找到 %MANIFEST%。请先运行：
  echo         python build_shot_manifest.py --project-root .. --episode 01
  echo   或手动指定 --out 路径。
  pause & exit /b 1
)

echo [3/4] 检查端口 %PORT% 占用...
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo   [警告] 端口 %PORT% 已被占用。选择：
  echo     [K] 杀掉占用进程   [C] 换端口 8793   [X] 取消
  set /p CHOICE="   输入 K / C / X： "
  if /i "!CHOICE!"=="K" (
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
      echo   杀掉 PID %%P ... & taskkill /f /pid %%P >nul 2>nul
    )
  ) else if /i "!CHOICE!"=="C" (
    set PORT=8793
  ) else (
    echo   已取消。& pause & exit /b 0
  )
)

echo [4/4] 启动服务器 http://127.0.0.1:%PORT%/ ...
start "" "http://127.0.0.1:%PORT%/"
python fusion_gallery_server.py --manifest "%MANIFEST%" --out "%STATE%" --port %PORT%

endlocal
pause
