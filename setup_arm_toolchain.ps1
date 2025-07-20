#!/usr/bin/env powershell
# ARM Toolchain Environment Setup Script

Write-Host "ARM GNU Toolchain Environment Setup" -ForegroundColor Green
Write-Host "=" * 40

# Common ARM toolchain installation paths
$possiblePaths = @(
    "C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\*\bin",
    "C:\Program Files\Arm GNU Toolchain arm-none-eabi\*\bin",
    "C:\arm-gnu-toolchain-*\bin",
    "D:\arm-gnu-toolchain-*\bin",
    "C:\Users\$env:USERNAME\AppData\Local\Arm GNU Toolchain arm-none-eabi\*\bin"
)

# Search for ARM toolchain
Write-Host "Searching for ARM toolchain..." -ForegroundColor Yellow
$foundPath = $null

foreach ($path in $possiblePaths) {
    $resolvedPaths = Get-ChildItem -Path (Split-Path $path -Parent) -Directory -ErrorAction SilentlyContinue | 
                     Where-Object { $_.Name -match "arm-none-eabi|arm-gnu-toolchain" } |
                     ForEach-Object { Join-Path $_.FullName "bin" }
    
    foreach ($resolvedPath in $resolvedPaths) {
        if (Test-Path (Join-Path $resolvedPath "arm-none-eabi-gcc.exe")) {
            $foundPath = $resolvedPath
            Write-Host "Found ARM toolchain: $foundPath" -ForegroundColor Green
            break
        }
    }
    if ($foundPath) { break }
}

if (-not $foundPath) {
    Write-Host "ARM toolchain not found, please specify path manually" -ForegroundColor Red
    $manualPath = Read-Host "Please enter the full path to ARM toolchain bin directory"
    if (Test-Path (Join-Path $manualPath "arm-none-eabi-gcc.exe")) {
        $foundPath = $manualPath
        Write-Host "Manual path verified successfully" -ForegroundColor Green
    } else {
        Write-Host "Invalid path specified, exiting" -ForegroundColor Red
        exit 1
    }
}

# Check current PATH
$currentPath = $env:PATH
if ($currentPath -like "*$foundPath*") {
    Write-Host "ARM toolchain already in PATH" -ForegroundColor Green
} else {
    Write-Host "Adding ARM toolchain to current session PATH" -ForegroundColor Yellow
    $env:PATH = "$foundPath;$env:PATH"
    
    # Ask if user wants to add permanently to system PATH
    $addPermanent = Read-Host "Add permanently to system PATH? (y/n)"
    if ($addPermanent -eq 'y' -or $addPermanent -eq 'Y') {
        try {
            $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
            if ($userPath -notlike "*$foundPath*") {
                [Environment]::SetEnvironmentVariable("PATH", "$foundPath;$userPath", "User")
                Write-Host "Permanently added to user PATH" -ForegroundColor Green
                Write-Host "Please restart PowerShell for permanent settings to take effect" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Failed to add to permanent PATH: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Verify toolchain
Write-Host "`nVerifying ARM toolchain..." -ForegroundColor Yellow
try {
    $gccVersion = & arm-none-eabi-gcc --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "ARM GCC toolchain verified successfully" -ForegroundColor Green
        Write-Host ($gccVersion | Select-Object -First 1) -ForegroundColor Cyan
    } else {
        throw "GCC verification failed"
    }
    
    $makeVersion = & make --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Make tool verified successfully" -ForegroundColor Green
        Write-Host ($makeVersion | Select-Object -First 1) -ForegroundColor Cyan
    } else {
        Write-Host "Make tool not found, installation needed" -ForegroundColor Yellow
        Write-Host "Suggested installation methods:" -ForegroundColor Yellow
        Write-Host "1. Using Chocolatey: choco install make" -ForegroundColor White
        Write-Host "2. Using MSYS2: pacman -S make" -ForegroundColor White
        Write-Host "3. Download GNU Make for Windows" -ForegroundColor White
    }
} catch {
    Write-Host "Toolchain verification failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test compilation
Write-Host "`nPreparing to test compilation..." -ForegroundColor Yellow
$slaveDir = "slave"
if (Test-Path $slaveDir) {
    Set-Location $slaveDir
    Write-Host "Entered slave directory" -ForegroundColor Cyan
    
    if (Test-Path "Makefile") {
        Write-Host "Found Makefile" -ForegroundColor Green
        
        $testCompile = Read-Host "Test compilation now? (y/n)"
        if ($testCompile -eq 'y' -or $testCompile -eq 'Y') {
            Write-Host "`nStarting compilation..." -ForegroundColor Yellow
            try {
                if (Get-Command make -ErrorAction SilentlyContinue) {
                    & make clean 2>&1
                    & make 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "`nCompilation successful!" -ForegroundColor Green
                        if (Test-Path "BUILD\FCMkII_S.bin") {
                            Write-Host "Firmware file generated: BUILD\FCMkII_S.bin" -ForegroundColor Green
                        }
                    } else {
                        Write-Host "`nCompilation failed, please check error messages" -ForegroundColor Red
                    }
                } else {
                    Write-Host "Make tool not available, cannot compile" -ForegroundColor Red
                }
            } catch {
                Write-Host "Compilation process error: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Makefile not found" -ForegroundColor Red
    }
    
    Set-Location ..
} else {
    Write-Host "slave directory not found" -ForegroundColor Red
}

Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
Write-Host "If compilation was successful, you can use these commands:" -ForegroundColor Yellow
Write-Host "  cd slave" -ForegroundColor White
Write-Host "  make clean  # Clean" -ForegroundColor White
Write-Host "  make        # Compile" -ForegroundColor White
Write-Host "  make -j4    # Parallel compile" -ForegroundColor White