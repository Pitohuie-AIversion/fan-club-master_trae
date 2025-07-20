# 智能编译脚本 - 自动检测mbed-os库结构

# 设置环境变量
$env:PATH = "C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\14.3 rel1\bin;$env:PATH"

# 进入slave目录
Set-Location "d:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\slave"

Write-Host "=== 智能mbed编译脚本 ===" -ForegroundColor Cyan

# 读取mbed-os.lib文件获取库路径
$mbedLibFile = "mbed-os.lib"
if (Test-Path $mbedLibFile) {
    $mbedOsPath = Get-Content $mbedLibFile -Raw
    $mbedOsPath = $mbedOsPath.Trim()
    Write-Host "Found mbed-os path: $mbedOsPath" -ForegroundColor Green
} else {
    Write-Host "Error: mbed-os.lib file not found" -ForegroundColor Red
    exit 1
}

# 检查ARM工具链
try {
    $armVersion = & arm-none-eabi-gcc --version 2>$null
    Write-Host "ARM toolchain found" -ForegroundColor Green
} catch {
    Write-Host "Error: ARM toolchain not found" -ForegroundColor Red
    exit 1
}

# 创建BUILD目录
if (!(Test-Path "BUILD")) {
    New-Item -ItemType Directory -Path "BUILD" | Out-Null
}

# 定义要编译的源文件
$sourceFiles = @("main.cpp")
$objectFiles = @()

# 基本编译器标志
$compilerFlags = @(
    "-mcpu=cortex-m4",
    "-mthumb",
    "-mfpu=fpv4-sp-d16",
    "-mfloat-abi=softfp",
    "-Os",
    "-g1",
    "-Wall",
    "-Wno-unused-parameter",
    "-fno-exceptions",
    "-fno-rtti",
    "-ffunction-sections",
    "-fdata-sections",
    "-std=c++11",
    "-c"
)

# 基本宏定义
$macros = @(
    "-DTARGET_STM32F429xx",
    "-DSTM32F429xx",
    "-DTARGET_NUCLEO_F429ZI",
    "-DTARGET_STM32F4",
    "-DTARGET_STM32F429xI",
    "-D__CORTEX_M4",
    "-D__MBED__=1",
    "-DARM_MATH_CM4",
    "-DMBED_CONF_RTOS_PRESENT=1",
    "-DMBED_CONF_PLATFORM_STDIO_BAUD_RATE=9600"
)

# 智能检测包含路径
$basePaths = @(
    ".",
    "FastPWM",
    $mbedOsPath
)

# 常见的mbed-os子目录
$mbedSubDirs = @(
    "platform\include",
    "platform\include\platform",
    "drivers\include",
    "drivers\include\drivers",
    "hal\include",
    "hal\include\hal",
    "rtos\include",
    "rtos\include\rtos",
    "events\include",
    "storage\filesystem\include",
    "storage\blockdevice\include",
    "connectivity\netsocket\include",
    "targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI\TARGET_NUCLEO_F429ZI",
    "targets\TARGET_STM\TARGET_STM32F4\TARGET_STM32F429xI",
    "targets\TARGET_STM\TARGET_STM32F4",
    "targets\TARGET_STM",
    "cmsis\CMSIS_5\CMSIS\Core\Include",
    "cmsis\CMSIS_5\CMSIS\RTOS2\Include",
    "cmsis\device\rtos\include"
)

# 检测实际存在的包含路径
$includePaths = @()
foreach ($basePath in $basePaths) {
    if (Test-Path $basePath) {
        $includePaths += $basePath
    }
}

foreach ($subDir in $mbedSubDirs) {
    $fullPath = Join-Path $mbedOsPath $subDir
    if (Test-Path $fullPath) {
        $includePaths += $fullPath
        Write-Host "Found: $fullPath" -ForegroundColor Gray
    }
}

Write-Host "Total include paths found: $($includePaths.Count)" -ForegroundColor Yellow

# 构建包含路径参数
$includeArgs = $includePaths | ForEach-Object { "-I`"$_`"" }

# 编译每个源文件
foreach ($file in $sourceFiles) {
    if (Test-Path $file) {
        $objFile = "BUILD/" + [System.IO.Path]::GetFileNameWithoutExtension($file) + ".o"
        Write-Host "Compiling $file -> $objFile" -ForegroundColor Yellow
        
        $compileArgs = @("-c", $file, "-o", $objFile) + $compilerFlags + $macros + $includeArgs
        
        # 执行编译
        & arm-none-eabi-g++ @compileArgs
        
        if ($LASTEXITCODE -eq 0) {
            $objectFiles += $objFile
            Write-Host "✓ $file compiled successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ $file compilation failed" -ForegroundColor Red
            Write-Host "Command was: arm-none-eabi-g++ $($compileArgs -join ' ')" -ForegroundColor Gray
        }
    } else {
        Write-Host "Warning: File $file does not exist" -ForegroundColor Yellow
    }
}

Write-Host "\n=== Compilation Summary ===" -ForegroundColor Cyan
Write-Host "Object files generated: $($objectFiles.Count)" -ForegroundColor White
$objectFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

if ($objectFiles.Count -gt 0) {
    Write-Host "\nCompilation successful! ✓" -ForegroundColor Green
} else {
    Write-Host "\nNo object files generated ✗" -ForegroundColor Red
}