# 简化的编译脚本 - 只编译核心文件

Write-Host "Starting minimal compilation..." -ForegroundColor Green

# 检查 ARM 工具链
try {
    $null = Get-Command "arm-none-eabi-g++" -ErrorAction Stop
} catch {
    Write-Host "Error: ARM toolchain not found. Please install arm-none-eabi-gcc" -ForegroundColor Red
    exit 1
}

# 创建 BUILD 目录
if (-not (Test-Path "BUILD")) {
    New-Item -ItemType Directory -Path "BUILD" | Out-Null
}

# 定义源文件
$sourceFiles = @("main.cpp")
$objectFiles = @()

# 基本编译标志
$compilerFlags = @(
    "-mcpu=cortex-m4",
    "-mthumb",
    "-Os",
    "-g1",
    "-Wall",
    "-std=c++11",
    "-fno-exceptions",
    "-fno-rtti",
    "-c"
)

# 基本宏定义
$macros = @(
    "-DTARGET_STM32F429xx",
    "-DSTM32F429xx",
    "-D__CORTEX_M4",
    "-DARM_MATH_CM4"
)

foreach ($file in $sourceFiles) {
    if (Test-Path $file) {
        $objFile = "BUILD/" + [System.IO.Path]::GetFileNameWithoutExtension($file) + ".o"
        Write-Host "Compiling $file -> $objFile" -ForegroundColor Yellow
        
        $compileArgs = @("-c", $file, "-o", $objFile) + $compilerFlags + $macros
        
        # 执行编译
        & arm-none-eabi-g++ @compileArgs
            
        if ($LASTEXITCODE -eq 0) {
            $objectFiles += $objFile
            Write-Host "Success: $file compiled" -ForegroundColor Green
        } else {
            Write-Host "Failed: $file compilation failed" -ForegroundColor Red
        }
    } else {
        Write-Host "Warning: File $file does not exist" -ForegroundColor Yellow
    }
}

Write-Host "Compilation finished. Object files: $($objectFiles.Count)" -ForegroundColor Cyan
$objectFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor White }

if ($objectFiles.Count -gt 0) {
    Write-Host "Minimal compilation completed successfully!" -ForegroundColor Green
} else {
    Write-Host "No object files generated" -ForegroundColor Red
}