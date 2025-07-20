@echo off
REM Fan Club MkIV - Slave 固件编译脚本
REM 此脚本将自动编译 slave 固件

echo =====================================
echo Fan Club MkIV - Slave 固件编译
echo =====================================
echo.

REM 检查当前目录
if not exist "slave\Makefile" (
    echo 错误: 请在项目根目录运行此脚本
    echo 当前目录应包含 slave 文件夹
    pause
    exit /b 1
)

REM 进入 slave 目录
cd slave

REM 检查工具链
echo 检查编译工具...
arm-none-eabi-gcc --version >nul 2>&1
if errorlevel 1 (
    echo 错误: ARM GCC 工具链未安装或未在 PATH 中
    echo 请运行 install_build_tools.ps1 安装必要工具
    pause
    exit /b 1
)

make --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Make 工具未安装或未在 PATH 中
    echo 请运行 install_build_tools.ps1 安装必要工具
    pause
    exit /b 1
)

echo 工具链检查通过
echo.

REM 询问是否清理之前的编译
set /p clean="是否清理之前的编译文件? (y/n): "
if /i "%clean%"=="y" (
    echo 清理编译文件...
    make clean
    echo.
)

REM 开始编译
echo 开始编译 slave 固件...
echo.
make

REM 检查编译结果
if errorlevel 1 (
    echo.
    echo =====================================
    echo 编译失败!
    echo =====================================
    echo 请检查错误信息并参考 MAKE_COMPILATION_GUIDE.md
    pause
    exit /b 1
) else (
    echo.
    echo =====================================
    echo 编译成功!
    echo =====================================
    echo.
    if exist "BUILD\FCMkII_S.bin" (
        echo 固件文件已生成: BUILD\FCMkII_S.bin
        echo 文件大小:
        dir "BUILD\FCMkII_S.bin" | find "FCMkII_S.bin"
        echo.
        echo 您现在可以将此文件烧录到 NUCLEO-F429ZI 开发板
    ) else (
        echo 警告: 未找到预期的 .bin 文件
    )
)

echo.
echo 编译完成!
pause