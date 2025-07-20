@echo off
echo === Mbed Compilation Script ===

set "PATH=C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\14.3 rel1\bin;%PATH%"

cd /d "d:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\slave"

echo Checking ARM toolchain...
arm-none-eabi-gcc --version >nul 2>&1
if errorlevel 1 (
    echo Error: ARM toolchain not found
    pause
    exit /b 1
)
echo ARM toolchain found!

if not exist "mbed-os.lib" (
    echo Error: mbed-os.lib file not found
    pause
    exit /b 1
)

set /p MBED_OS_PATH=<mbed-os.lib
echo Found mbed-os path: %MBED_OS_PATH%

if not exist "BUILD" mkdir BUILD

echo Compiling main.cpp...
arm-none-eabi-g++ -mcpu=cortex-m4 -mthumb -Os -g1 -Wall -fno-exceptions -fno-rtti -std=c++11 -DTARGET_STM32F429xx -DSTM32F429xx -DTARGET_NUCLEO_F429ZI -DTARGET_STM32F4 -DTARGET_STM32F429xI -D__CORTEX_M4 -D__MBED__=1 -DMBED_CONF_RTOS_PRESENT=1 -I. -I"FastPWM" -I"%MBED_OS_PATH%" -I"%MBED_OS_PATH%\platform\include" -I"%MBED_OS_PATH%\drivers\include" -I"%MBED_OS_PATH%\hal\include" -I"%MBED_OS_PATH%\rtos\include" -I"%MBED_OS_PATH%\targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI\TARGET_NUCLEO_F429ZI" -I"%MBED_OS_PATH%\targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI" -I"%MBED_OS_PATH%\targets\TARGET_STM\TARGET_STM32F4" -I"%MBED_OS_PATH%\targets\TARGET_STM" -I"%MBED_OS_PATH%\cmsis\CMSIS_5\CMSIS\Core\Include" -c main.cpp -o BUILD\main.o

if errorlevel 1 (
    echo Compilation failed!
    pause
    exit /b 1
) else (
    echo Compilation successful!
    echo Generated: BUILD\main.o
    dir BUILD\main.o
)

echo.
echo === Compilation Complete ===
pause