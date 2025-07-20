#!/usr/bin/env powershell
# Mbed CLI 2 (mbed-tools) Prerequisites Installation Script
# This script installs CMake and Ninja which are required for mbed-tools

Write-Host "=== Mbed CLI 2 Prerequisites Installation ==="
Write-Host "Checking current system status..."

# Check Python
Write-Host "\nChecking Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion"
} catch {
    Write-Host "❌ Python not found. Please install Python 3.6+ first."
    exit 1
}

# Check pip
Write-Host "\nChecking pip..."
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip found: $pipVersion"
} catch {
    Write-Host "❌ pip not found. Please install pip first."
    exit 1
}

# Check ARM toolchain
Write-Host "\nChecking ARM toolchain..."
try {
    $armVersion = arm-none-eabi-gcc --version 2>&1 | Select-Object -First 1
    Write-Host "✅ ARM toolchain found: $armVersion"
} catch {
    Write-Host "❌ ARM toolchain not found. Please install ARM GNU Toolchain first."
    exit 1
}

# Check CMake
Write-Host "\nChecking CMake..."
try {
    $cmakeVersion = cmake --version 2>&1 | Select-Object -First 1
    Write-Host "✅ CMake found: $cmakeVersion"
    $cmakeInstalled = $true
} catch {
    Write-Host "❌ CMake not found. Will install via pip."
    $cmakeInstalled = $false
}

# Check Ninja
Write-Host "\nChecking Ninja..."
try {
    $ninjaVersion = ninja --version 2>&1
    Write-Host "✅ Ninja found: version $ninjaVersion"
    $ninjaInstalled = $true
} catch {
    Write-Host "❌ Ninja not found. Will install via pip."
    $ninjaInstalled = $false
}

# Install missing components
if (-not $cmakeInstalled -or -not $ninjaInstalled) {
    Write-Host "\n=== Installing missing components ==="
    
    if (-not $cmakeInstalled) {
        Write-Host "Installing CMake via pip..."
        try {
            pip install cmake
            Write-Host "✅ CMake installed successfully"
        } catch {
            Write-Host "❌ Failed to install CMake via pip"
            Write-Host "Please install CMake manually from: https://cmake.org/download/"
        }
    }
    
    if (-not $ninjaInstalled) {
        Write-Host "Installing Ninja via pip..."
        try {
            pip install ninja
            Write-Host "✅ Ninja installed successfully"
        } catch {
            Write-Host "❌ Failed to install Ninja via pip"
            Write-Host "Please install Ninja manually from: https://github.com/ninja-build/ninja/releases"
        }
    }
    
    Write-Host "\nRefreshing PATH..."
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

# Verify installations
Write-Host "\n=== Verifying installations ==="

# Re-check CMake
try {
    $cmakeVersion = cmake --version 2>&1 | Select-Object -First 1
    Write-Host "✅ CMake verified: $cmakeVersion"
} catch {
    Write-Host "❌ CMake still not available. Manual installation may be required."
}

# Re-check Ninja
try {
    $ninjaVersion = ninja --version 2>&1
    Write-Host "✅ Ninja verified: version $ninjaVersion"
} catch {
    Write-Host "❌ Ninja still not available. Manual installation may be required."
}

# Check mbed-tools
Write-Host "\nChecking mbed-tools..."
try {
    $mbedToolsVersion = mbed-tools --version 2>&1
    Write-Host "✅ mbed-tools found: version $mbedToolsVersion"
} catch {
    Write-Host "❌ mbed-tools not found or not working properly."
    Write-Host "You may need to reinstall mbed-tools: pip install mbed-tools"
}

Write-Host "\n=== Prerequisites Check Complete ==="
Write-Host "\nIf all components show ✅, you can proceed with mbed-tools compilation."
Write-Host "If any component shows ❌, please install it manually using the provided links."

Write-Host "\n=== Next Steps ==="
Write-Host "1. Navigate to your project directory (slave folder)"
Write-Host "2. Run: mbed-tools configure -t GCC_ARM -m NUCLEO_F429ZI"
Write-Host "3. Run: mbed-tools compile -t GCC_ARM -m NUCLEO_F429ZI"