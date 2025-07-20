# 完整的ARM编译脚本，包含mbed-os支持
# 设置环境变量
$env:PATH = "C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\14.3 rel1\bin;$env:PATH"

# 进入slave目录
Set-Location "d:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\slave"

Write-Host "Checking ARM toolchain..." -ForegroundColor Cyan
arm-none-eabi-gcc --version

if ($LASTEXITCODE -ne 0) {
    Write-Host "ARM toolchain not found or misconfigured" -ForegroundColor Red
    exit 1
}

# 检查mbed-os路径
$mbedOsPath = "D:\mbed-os-shared\mbed-os"
if (!(Test-Path $mbedOsPath)) {
    Write-Host "mbed-os not found at $mbedOsPath" -ForegroundColor Red
    exit 1
}

Write-Host "Starting compilation..." -ForegroundColor Cyan

# 创建BUILD目录
if (!(Test-Path "BUILD")) {
    New-Item -ItemType Directory -Path "BUILD"
}

# 编译主要的C++文件
$sourceFiles = @(
    "main.cpp",
    "Communicator.cpp",
    "Fan.cpp",
    "Processor.cpp",
    "print.cpp"
)

$objectFiles = @()

# 定义包含路径
$includePaths = @(
    ".",
    "FastPWM",
    "$mbedOsPath",
    "$mbedOsPath\platform\include",
    "$mbedOsPath\platform\include\platform",
    "$mbedOsPath\drivers\include",
    "$mbedOsPath\hal\include",
    "$mbedOsPath\hal\include\hal",
    "$mbedOsPath\events\include",
    "$mbedOsPath\storage\filesystem\include",
    "$mbedOsPath\storage\blockdevice\include",
    "$mbedOsPath\rtos\include",
    "$mbedOsPath\rtos\include\rtos",
    "$mbedOsPath\events\include",
    "$mbedOsPath\connectivity\FEATURE_BLE\include",
    "$mbedOsPath\connectivity\include",
    "$mbedOsPath\connectivity\netsocket\include",
    "$mbedOsPath\connectivity\netsocket\include\netsocket",
    "$mbedOsPath\features\FEATURE_LWIP\lwip-interface",
    "$mbedOsPath\features\FEATURE_LWIP\lwip-interface\lwip\src\include",
    "$mbedOsPath\features\frameworks",
    "$mbedOsPath\features\filesystem\include",
    "$mbedOsPath\filesystem\include",
    "$mbedOsPath\features\mbedtls\inc",
    "$mbedOsPath\features\mbedtls\include",
    "$mbedOsPath\connectivity\mbedtls\include",
    "$mbedOsPath\connectivity\mbedtls\platform\inc",
    "$mbedOsPath\connectivity\mbedtls\platform",
    "$mbedOsPath\connectivity",
    "$mbedOsPath\connectivity\mbedtls",
    "$mbedOsPath\rtos\include",
    "$mbedOsPath\targets\TARGET_STM",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\TARGET_NUCLEO_F429ZI",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI\TARGET_NUCLEO_F429ZI",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI\device",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\device",
    "$mbedOsPath\cmsis",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\Core\Include",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\TARGET_CORTEX_M",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\TARGET_CORTEX_M\Include",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\RTOS2\Include",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\RTOS2\RTX\Include1",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\RTOS2\RTX\Include",
    "$mbedOsPath\cmsis\CMSIS_5\CMSIS\RTOS2\RTX\Config",
    "$mbedOsPath\cmsis\device\rtos\include",
    "$mbedOsPath\cmsis\device\stm32f4xx",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\STM32Cube_FW\CMSIS",
    "$mbedOsPath\targets\TARGET_STM\TARGET_STM32F4\STM32Cube_FW\STM32F4xx_HAL_Driver",
    "$mbedOsPath\platform\cxxsupport",
    "$mbedOsPath\rtos",
    "$mbedOsPath\features\netsocket"
)

# 构建包含路径参数
$includeArgs = $includePaths | ForEach-Object { "-I`"$_`"" }

foreach ($file in $sourceFiles) {
    if (Test-Path $file) {
        $objFile = "BUILD/" + [System.IO.Path]::GetFileNameWithoutExtension($file) + ".o"
        Write-Host "Compiling $file -> $objFile" -ForegroundColor Yellow
        
        # Define compiler flags
        $compilerFlags = @(
            "-mcpu=cortex-m4",
            "-mthumb",
            "-mfpu=fpv4-sp-d16",
            "-mfloat-abi=softfp",
            "-Os",
            "-g1",
            "-Wall",
            "-Wextra",
            "-Wno-unused-parameter",
            "-Wno-missing-field-initializers",
            "-fmessage-length=0",
            "-fno-exceptions",
            "-fno-builtin",
            "-ffunction-sections",
            "-fdata-sections",
            "-funsigned-char",
            "-MMD",
            "-fno-delete-null-pointer-checks",
            "-fomit-frame-pointer",
            "-std=gnu++11",
            "-fno-rtti",
            "-Wvla",
            "-c"
        )

        # Define macros (from original Makefile)
        $macros = @(
            "-DTARGET_STM32F429xx",
            "-DSTM32F429xx",
            "-DDEVICE_SPISLAVE=1",
            "-DFEATURE_LWIP=1",
            "-D__MBED__=1",
            "-DDEVICE_I2CSLAVE=1",
            "-D__FPU_PRESENT=1",
            "-DTRANSACTION_QUEUE_SIZE_SPI=2",
            "-DUSBHOST_OTHER",
            "-DDEVICE_PORTINOUT=1",
            "-DTARGET_RTOS_M4_M7",
            "-DTARGET_NUCLEO_F429ZI",
            "-DDEVICE_LOWPOWERTIMER=1",
            "-DDEVICE_RTC=1",
            "-DTOOLCHAIN_object",
            "-DTARGET_STM32F4",
            "-D__CMSIS_RTOS",
            "-DTARGET_FLASH_CMSIS_ALGO",
            "-DTOOLCHAIN_GCC",
            "-DDEVICE_CAN=1",
            "-DTARGET_CORTEX_M",
            "-DDEVICE_I2C_ASYNCH=1",
            "-DTARGET_LIKE_CORTEX_M4",
            "-DDEVICE_ANALOGOUT=1",
            "-DTARGET_M4",
            "-DTARGET_UVISOR_UNSUPPORTED",
            "-DDEVICE_PORTOUT=1",
            "-DDEVICE_SPI_ASYNCH=1",
            "-DDEVICE_PWMOUT=1",
            "-DDEVICE_INTERRUPTIN=1",
            "-DTARGET_CORTEX",
            "-DDEVICE_I2C=1",
            "-DTARGET_STM32F429",
            "-D__CORTEX_M4",
            "-DDEVICE_STDIO_MESSAGES=1",
            "-DTARGET_LIKE_MBED",
            "-DTARGET_FF_ARDUINO",
            "-DDEVICE_PORTIN=1",
            "-DTARGET_RELEASE",
            "-DTARGET_STM",
            "-DDEVICE_SERIAL_FC=1",
            "-DMBED_BUILD_TIMESTAMP=1525122716.16",
            "-DDEVICE_TRNG=1",
            "-DTARGET_STM32F429ZI",
            "-D__MBED_CMSIS_RTOS_CM",
            "-DDEVICE_SLEEP=1",
            "-DTOOLCHAIN_GCC_ARM",
            "-DDEVICE_SPI=1",
            "-DUSB_STM_HAL",
            "-DDEVICE_ERROR_RED=1",
            "-DTARGET_STM32F429xI",
            "-DDEVICE_ANALOGIN=1",
            "-DDEVICE_SERIAL=1",
            "-DDEVICE_FLASH=1",
            "-DARM_MATH_CM4",
            "-DMBED_CONF_RTOS_PRESENT=1",
            "-DMBED_CONF_PLATFORM_STDIO_BAUD_RATE=9600",
            "-include",
            "mbed_config.h"
        )

        $compileArgs = @(
            "-c", $file, "-o", $objFile
        ) + $compilerFlags + $macros
        
        # 添加包含路径
        $compileArgs += $includeArgs
        
        # 执行编译
        & arm-none-eabi-g++ @compileArgs
            
        if ($LASTEXITCODE -eq 0) {
            $objectFiles += $objFile
            Write-Host "✓ $file compiled successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ $file compilation failed" -ForegroundColor Red
        }
    } else {
        Write-Host "Warning: File $file does not exist" -ForegroundColor Yellow
    }
}

Write-Host "Compilation finished. Object files: $($objectFiles.Count)" -ForegroundColor Cyan
Write-Host "Generated object files:"
$objectFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor White }

if ($objectFiles.Count -gt 0) {
    Write-Host "Compilation completed, generated $($objectFiles.Count) object files" -ForegroundColor Green
    
    # Link all object files to create ELF file
    Write-Host "Linking object files to create ELF..." -ForegroundColor Cyan
    $elfFile = "BUILD/FCMkII_S.elf"
    $linkerScript = "D:\mbed-os-shared\mbed-os\targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI\device\TOOLCHAIN_GCC_ARM\STM32F429xI.ld"
    
    # Properly quote object file paths
    $quotedObjectFiles = $objectFiles | ForEach-Object { "`"$_`"" }
    $linkCommand = "arm-none-eabi-gcc -Wl,--gc-sections -Wl,--wrap,main -Wl,--wrap,_malloc_r -Wl,--wrap,_free_r -Wl,--wrap,_realloc_r -Wl,--wrap,_memalign_r -Wl,--wrap,_calloc_r -Wl,--wrap,exit -Wl,--wrap,atexit -Wl,-n -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=softfp -T `"$linkerScript`" -o `"$elfFile`" $($quotedObjectFiles -join ' ') -Wl,--start-group -lstdc++ -lsupc++ -lm -lc -lgcc -lnosys -Wl,--end-group"
    
    Write-Host "Executing: $linkCommand" -ForegroundColor Gray
    Invoke-Expression $linkCommand
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $elfFile)) {
        Write-Host "ELF file created successfully: $elfFile" -ForegroundColor Green
        
        # Convert ELF to BIN
        Write-Host "Converting ELF to BIN..." -ForegroundColor Cyan
        $binFile = "BUILD/FCMkII_S.bin"
        $binCommand = "arm-none-eabi-objcopy -O binary `"$elfFile`" `"$binFile`""
        
        Write-Host "Executing: $binCommand" -ForegroundColor Gray
        Invoke-Expression $binCommand
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $binFile)) {
            Write-Host "BIN file created successfully: $binFile" -ForegroundColor Green
            $binSize = (Get-Item $binFile).Length
            Write-Host "BIN file size: $binSize bytes" -ForegroundColor Yellow
        } else {
            Write-Host "Failed to create BIN file" -ForegroundColor Red
        }
    } else {
        Write-Host "Failed to create ELF file" -ForegroundColor Red
    }
} else {
    Write-Host "No object files generated" -ForegroundColor Red
}