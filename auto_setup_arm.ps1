#!/usr/bin/env powershell
# Automated ARM Toolchain Detection and Setup

Write-Host "ARM GNU Toolchain Auto-Detection" -ForegroundColor Green
Write-Host "=" * 40

# Extended search paths for ARM toolchain
$searchPaths = @(
    "C:\Program Files (x86)\Arm GNU Toolchain*",
    "C:\Program Files\Arm GNU Toolchain*",
    "C:\Program Files (x86)\GNU Arm Embedded Toolchain*",
    "C:\Program Files\GNU Arm Embedded Toolchain*",
    "C:\arm-gnu-toolchain*",
    "D:\arm-gnu-toolchain*",
    "C:\Users\$env:USERNAME\AppData\Local\Arm GNU Toolchain*",
    "C:\msys64\mingw64\bin",
    "C:\msys64\usr\bin",
    "C:\MinGW\bin",
    "C:\TDM-GCC-64\bin"
)

# Function to find ARM toolchain
function Find-ArmToolchain {
    Write-Host "Searching for ARM toolchain..." -ForegroundColor Yellow
    
    foreach ($searchPath in $searchPaths) {
        Write-Host "Checking: $searchPath" -ForegroundColor Gray
        
        # Handle wildcard paths
        if ($searchPath -like "*`**") {
            $basePath = $searchPath -replace "\*$", ""
            $directories = Get-ChildItem -Path $basePath -Directory -ErrorAction SilentlyContinue
            
            foreach ($dir in $directories) {
                $binPath = Join-Path $dir.FullName "bin"
                $gccPath = Join-Path $binPath "arm-none-eabi-gcc.exe"
                
                if (Test-Path $gccPath) {
                    Write-Host "Found ARM toolchain: $binPath" -ForegroundColor Green
                    return $binPath
                }
            }
        } else {
            # Direct path check
            $gccPath = Join-Path $searchPath "arm-none-eabi-gcc.exe"
            if (Test-Path $gccPath) {
                Write-Host "Found ARM toolchain: $searchPath" -ForegroundColor Green
                return $searchPath
            }
        }
    }
    
    return $null
}

# Function to find Make tool
function Find-MakeTool {
    Write-Host "Searching for Make tool..." -ForegroundColor Yellow
    
    $makeLocations = @(
        "make",
        "mingw32-make",
        "C:\msys64\usr\bin\make.exe",
        "C:\MinGW\bin\mingw32-make.exe",
        "C:\TDM-GCC-64\bin\mingw32-make.exe"
    )
    
    foreach ($makePath in $makeLocations) {
        try {
            $result = & $makePath --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Found Make tool: $makePath" -ForegroundColor Green
                return $makePath
            }
        } catch {
            # Continue searching
        }
    }
    
    return $null
}

# Main execution
$armPath = Find-ArmToolchain

if ($armPath) {
    # Add to PATH if not already present
    if ($env:PATH -notlike "*$armPath*") {
        Write-Host "Adding ARM toolchain to PATH" -ForegroundColor Yellow
        $env:PATH = "$armPath;$env:PATH"
    } else {
        Write-Host "ARM toolchain already in PATH" -ForegroundColor Green
    }
    
    # Verify ARM GCC
    try {
        $gccVersion = & arm-none-eabi-gcc --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "ARM GCC verified successfully" -ForegroundColor Green
            Write-Host ($gccVersion | Select-Object -First 1) -ForegroundColor Cyan
        }
    } catch {
        Write-Host "ARM GCC verification failed" -ForegroundColor Red
    }
} else {
    Write-Host "ARM toolchain not found in common locations" -ForegroundColor Red
    Write-Host "Please install ARM GNU Toolchain from:" -ForegroundColor Yellow
    Write-Host "https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads" -ForegroundColor White
    exit 1
}

# Check for Make tool
$makeTool = Find-MakeTool
if ($makeTool) {
    Write-Host "Make tool available: $makeTool" -ForegroundColor Green
    
    # Test compilation if in slave directory
    if (Test-Path "Makefile") {
        Write-Host "Found Makefile, testing compilation..." -ForegroundColor Yellow
        
        try {
            Write-Host "Running: $makeTool clean" -ForegroundColor Gray
            & $makeTool clean 2>&1
            
            Write-Host "Running: $makeTool" -ForegroundColor Gray
            & $makeTool 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Compilation successful!" -ForegroundColor Green
                
                # Check for output files
                $outputFiles = @("BUILD\FCMkII_S.bin", "BUILD\FCMkII_S.elf", "*.bin", "*.elf")
                foreach ($pattern in $outputFiles) {
                    $files = Get-ChildItem -Path . -Name $pattern -Recurse -ErrorAction SilentlyContinue
                    if ($files) {
                        Write-Host "Generated files:" -ForegroundColor Green
                        foreach ($file in $files) {
                            Write-Host "  $file" -ForegroundColor White
                        }
                        break
                    }
                }
            } else {
                Write-Host "Compilation failed" -ForegroundColor Red
            }
        } catch {
            Write-Host "Compilation error: $($_.Exception.Message)" -ForegroundColor Red
        }
    } elseif (Test-Path "..\slave\Makefile") {
        Write-Host "Found Makefile in parent slave directory" -ForegroundColor Yellow
        Set-Location "..\slave"
        
        try {
            Write-Host "Running: $makeTool clean" -ForegroundColor Gray
            & $makeTool clean 2>&1
            
            Write-Host "Running: $makeTool" -ForegroundColor Gray
            & $makeTool 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Compilation successful!" -ForegroundColor Green
                
                # Check for output files
                $outputFiles = @("BUILD\FCMkII_S.bin", "BUILD\FCMkII_S.elf", "*.bin", "*.elf")
                foreach ($pattern in $outputFiles) {
                    $files = Get-ChildItem -Path . -Name $pattern -Recurse -ErrorAction SilentlyContinue
                    if ($files) {
                        Write-Host "Generated files:" -ForegroundColor Green
                        foreach ($file in $files) {
                            Write-Host "  $file" -ForegroundColor White
                        }
                        break
                    }
                }
            } else {
                Write-Host "Compilation failed" -ForegroundColor Red
            }
        } catch {
            Write-Host "Compilation error: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Set-Location ..
    } else {
        Write-Host "No Makefile found for testing" -ForegroundColor Yellow
    }
} else {
    Write-Host "Make tool not found" -ForegroundColor Red
    Write-Host "Install options:" -ForegroundColor Yellow
    Write-Host "1. Chocolatey: choco install make" -ForegroundColor White
    Write-Host "2. MSYS2: pacman -S make" -ForegroundColor White
    Write-Host "3. MinGW-w64" -ForegroundColor White
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Environment ready for ARM development" -ForegroundColor Cyan