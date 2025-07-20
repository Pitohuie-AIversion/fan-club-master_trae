@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Fan Club MkIV 固件编译脚本
REM 此脚本自动编译从机固件和引导程序固件

echo ========================================
echo Fan Club MkIV 固件编译工具
echo ========================================
echo.

REM 设置编译参数
set TARGET=NUCLEO_F446RE
set TOOLCHAIN=ARMC6
set PROJECT_ROOT=%~dp0
set SLAVE_DIR=%PROJECT_ROOT%slave_upgraded
set BOOTLOADER_DIR=%PROJECT_ROOT%slave_bootloader_upgraded
set OUTPUT_DIR=%PROJECT_ROOT%master\FC_MkIV_binaries

REM 记录开始时间
set START_TIME=%time%
echo [%time%] 🚀 开始编译固件...
echo.

REM 检查 Mbed CLI
echo [%time%] ℹ️ 检查编译环境...
mbed --version >nul 2>&1
if errorlevel 1 (
    echo [%time%] ❌ 错误: Mbed CLI 未安装或不在 PATH 中
    echo.
    echo 请确保已安装 Mbed CLI 2:
    echo   pip install mbed-tools
    echo.
    echo 或者使用 Mbed Studio 进行编译
    pause
    exit /b 1
)
echo [%time%] ✅ Mbed CLI 检查通过

REM 检查项目目录
if not exist "%SLAVE_DIR%" (
    echo [%time%] ❌ 错误: 从机项目目录不存在: %SLAVE_DIR%
    pause
    exit /b 1
)

if not exist "%BOOTLOADER_DIR%" (
    echo [%time%] ❌ 错误: 引导程序项目目录不存在: %BOOTLOADER_DIR%
    pause
    exit /b 1
)

echo [%time%] ✅ 项目目录检查通过
echo.

REM 创建输出目录
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    echo [%time%] 📁 创建输出目录: %OUTPUT_DIR%
)

REM 编译从机固件
echo [%time%] 🔨 编译从机固件...
echo ----------------------------------------
cd /d "%SLAVE_DIR%"

REM 部署依赖
echo [%time%] 📦 部署依赖...
mbed deploy
if errorlevel 1 (
    echo [%time%] ⚠️ 警告: 依赖部署失败，继续编译...
)

REM 编译
echo [%time%] 🔧 开始编译从机固件...
mbed compile -t %TOOLCHAIN% -m %TARGET%
if errorlevel 1 (
    echo [%time%] ❌ 从机固件编译失败
    set SLAVE_SUCCESS=0
) else (
    echo [%time%] ✅ 从机固件编译成功
    set SLAVE_SUCCESS=1
    
    REM 检查生成的文件
    if exist "BUILD\%TARGET%\%TOOLCHAIN%\*.bin" (
        for %%f in (BUILD\%TARGET%\%TOOLCHAIN%\*.bin) do (
            echo [%time%] 📦 生成固件: %%~nxf (%%~zf bytes)
            copy "%%f" "%OUTPUT_DIR%\" >nul
            if not errorlevel 1 (
                echo [%time%] 📋 已复制到输出目录
            )
        )
    )
)
echo.

REM 编译引导程序固件
echo [%time%] 🔨 编译引导程序固件...
echo ----------------------------------------
cd /d "%BOOTLOADER_DIR%"

REM 部署依赖
echo [%time%] 📦 部署依赖...
mbed deploy
if errorlevel 1 (
    echo [%time%] ⚠️ 警告: 依赖部署失败，继续编译...
)

REM 编译
echo [%time%] 🔧 开始编译引导程序固件...
mbed compile -t %TOOLCHAIN% -m %TARGET%
if errorlevel 1 (
    echo [%time%] ❌ 引导程序固件编译失败
    set BOOTLOADER_SUCCESS=0
) else (
    echo [%time%] ✅ 引导程序固件编译成功
    set BOOTLOADER_SUCCESS=1
    
    REM 检查生成的文件
    if exist "BUILD\%TARGET%\%TOOLCHAIN%\*.bin" (
        for %%f in (BUILD\%TARGET%\%TOOLCHAIN%\*.bin) do (
            echo [%time%] 📦 生成固件: %%~nxf (%%~zf bytes)
            copy "%%f" "%OUTPUT_DIR%\" >nul
            if not errorlevel 1 (
                echo [%time%] 📋 已复制到输出目录
            )
        )
    )
)
echo.

REM 返回项目根目录
cd /d "%PROJECT_ROOT%"

REM 生成编译报告
set END_TIME=%time%
echo ========================================
echo 编译报告
echo ========================================
echo 开始时间: %START_TIME%
echo 结束时间: %END_TIME%
echo 目标硬件: %TARGET%
echo 编译工具: %TOOLCHAIN%
echo.

REM 检查编译结果
set TOTAL_SUCCESS=0
if "%SLAVE_SUCCESS%"=="1" (
    echo ✅ 从机固件编译成功
    set /a TOTAL_SUCCESS+=1
) else (
    echo ❌ 从机固件编译失败
)

if "%BOOTLOADER_SUCCESS%"=="1" (
    echo ✅ 引导程序固件编译成功
    set /a TOTAL_SUCCESS+=1
) else (
    echo ❌ 引导程序固件编译失败
)

echo.
echo 成功率: %TOTAL_SUCCESS%/2

REM 显示输出文件
if exist "%OUTPUT_DIR%\*.bin" (
    echo.
    echo 📁 生成的固件文件:
    echo ----------------------------------------
    for %%f in ("%OUTPUT_DIR%\*.bin") do (
        echo   %%~nxf (%%~zf bytes)
    )
    echo.
    echo 📂 输出目录: %OUTPUT_DIR%
) else (
    echo.
    echo ⚠️ 没有找到生成的固件文件
)

echo ========================================

if %TOTAL_SUCCESS%==2 (
    echo 🎉 所有固件编译成功！
    echo.
    echo 下一步:
    echo 1. 将 .bin 文件刷写到 NUCLEO-F446RE 开发板
    echo 2. 运行 master/main.py 开始使用系统
    echo.
    echo 部署方法:
    echo - 使用 Mbed Studio: 连接开发板后点击 Run 按钮
    echo - 手动复制: 将 .bin 文件复制到开发板 USB 存储设备
    echo - ST-Link: 使用 STM32 ST-LINK Utility 刷写固件
) else (
    echo ⚠️ 部分固件编译失败，请检查错误信息
    echo.
    echo 故障排除:
    echo 1. 确认 Mbed CLI 2 已正确安装
    echo 2. 确认 ARM Compiler 6 已安装并在 PATH 中
    echo 3. 检查项目依赖是否完整
    echo 4. 尝试清理构建目录后重新编译
)

echo.
echo 按任意键退出...
pause >nul

REM 设置退出代码
if %TOTAL_SUCCESS%==2 (
    exit /b 0
) else (
    exit /b 1
)