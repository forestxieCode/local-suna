@echo off
REM Kortix CLI Windows 启动脚本

echo ========================================
echo   Kortix AI Agent CLI
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或未添加到 PATH
    echo 请安装 Python 3.8+ 并添加到系统环境变量
    pause
    exit /b 1
)

REM 检查依赖
echo [INFO] 检查依赖...
python -c "import dashscope" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 依赖未安装，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查 .env 文件
if not exist .env (
    echo [WARNING] .env 文件不存在
    echo [INFO] 正在创建 .env 文件...
    copy .env.example .env
    echo.
    echo ========================================
    echo   重要提示
    echo ========================================
    echo 请编辑 .env 文件，填入你的阿里云百炼 API Key
    echo API Key 获取地址: https://dashscope.console.aliyun.com/
    echo.
    echo 按任意键打开 .env 文件进行编辑...
    pause >nul
    notepad .env
    echo.
)

REM 检查 Docker
docker version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker 未运行或未安装
    echo 代码执行功能将不可用
    echo.
)

REM 启动程序
echo [INFO] 启动 Kortix AI Agent...
echo.
python run.py %*

pause
