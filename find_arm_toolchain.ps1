#!/usr/bin/env powershell
# Manual ARM Toolchain Detection Script

Write-Host "ARM Toolchain Detection Utility" -ForegroundColor Green
Write-Host "=" * 35

# Function to search for files
function Search-ArmGcc {
    param([string]$searchPath)
    
    try {
        $files = Get-ChildItem -Path $searchPath -Filter "arm-none-eabi-gcc.exe" -Recurse -ErrorAction SilentlyContinue
        return $files
    } catch {
        return @()
    }
}

# Search in common drive locations
$drives = @("C:", "D:", "E:")
$foundPaths = @()

Write-Host "Searching for ARM toolchain installations..." -ForegroundColor Yellow
Write-Host "This may take a moment..." -ForegroundColor Gray

foreach ($drive in $drives) {
    if (Test-Path $drive) {
        Write-Host "Searching in $drive" -ForegroundColor Gray
        
        # Search in Program Files
        $programFiles = @(
            "${drive}Program Files",
            "${drive}Program Files (x86)"
        )
        
        foreach ($pf in $programFiles) {
            if (Test-Path $pf) {
                $armDirs = Get-ChildItem -Path $pf -Directory -ErrorAction SilentlyContinue | 
                          Where-Object { $_.Name -like "*arm*" -or $_.Name -like "*gnu*" }
                
                foreach ($dir in $armDirs) {
                    $gccFiles = Search-ArmGcc $dir.FullName
                    foreach ($gcc in $gccFiles) {
                        $binPath = Split-Path $gcc.FullName -Parent
                        $foundPaths += $binPath
                        Write-Host "Found: $binPath" -ForegroundColor Green
                    }
                }
            }
        }
        
        # Search in root directory for toolchain folders
        $rootDirs = Get-ChildItem -Path $drive -Directory -ErrorAction SilentlyContinue | 
                   Where-Object { $_.Name -like "*arm*" -or $_.Name -like "*gnu*" }
        
        foreach ($dir in $rootDirs) {
            $gccFiles = Search-ArmGcc $dir.FullName
            foreach ($gcc in $gccFiles) {
                $binPath = Split-Path $gcc.FullName -Parent
                $foundPaths += $binPath
                Write-Host "Found: $binPath" -ForegroundColor Green
            }
        }
    }
}

# Remove duplicates
$foundPaths = $foundPaths | Sort-Object -Unique

Write-Host "`nSearch Results:" -ForegroundColor Cyan
Write-Host "=" * 15

if ($foundPaths.Count -eq 0) {
    Write-Host "No ARM toolchain found." -ForegroundColor Red
    Write-Host "`nPlease install ARM GNU Toolchain from:" -ForegroundColor Yellow
    Write-Host "https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads" -ForegroundColor White
    Write-Host "`nOr check if it's installed in a non-standard location." -ForegroundColor Gray
} else {
    Write-Host "Found $($foundPaths.Count) ARM toolchain installation(s):" -ForegroundColor Green
    
    for ($i = 0; $i -lt $foundPaths.Count; $i++) {
        $path = $foundPaths[$i]
        Write-Host "[$($i+1)] $path" -ForegroundColor White
        
        # Test the toolchain
        $oldPath = $env:PATH
        $env:PATH = "$path;$env:PATH"
        
        try {
            $version = & arm-none-eabi-gcc --version 2>&1 | Select-Object -First 1
            Write-Host "    Version: $version" -ForegroundColor Gray
        } catch {
            Write-Host "    Version: Unable to determine" -ForegroundColor Red
        }
        
        $env:PATH = $oldPath
        Write-Host ""
    }
    
    # Ask user to select a toolchain
    if ($foundPaths.Count -eq 1) {
        $selectedPath = $foundPaths[0]
        Write-Host "Using the only found toolchain: $selectedPath" -ForegroundColor Green
    } else {
        do {
            $selection = Read-Host "Select toolchain to use (1-$($foundPaths.Count), or 'q' to quit)"
            if ($selection -eq 'q') {
                Write-Host "Exiting..." -ForegroundColor Yellow
                exit 0
            }
            $selectionNum = [int]$selection - 1
        } while ($selectionNum -lt 0 -or $selectionNum -ge $foundPaths.Count)
        
        $selectedPath = $foundPaths[$selectionNum]
    }
    
    # Configure environment
    Write-Host "Configuring environment with: $selectedPath" -ForegroundColor Yellow
    $env:PATH = "$selectedPath;$env:PATH"
    
    # Verify configuration
    try {
        $gccVersion = & arm-none-eabi-gcc --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "ARM GCC configured successfully!" -ForegroundColor Green
            Write-Host ($gccVersion | Select-Object -First 1) -ForegroundColor Cyan
        }
    } catch {
        Write-Host "Failed to configure ARM GCC" -ForegroundColor Red
    }
    
    # Check for Make
    Write-Host "`nChecking for Make tool..." -ForegroundColor Yellow
    $makeCommands = @("make", "mingw32-make")
    $makeFound = $false
    
    foreach ($makeCmd in $makeCommands) {
        try {
            $makeVersion = & $makeCmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Make tool found: $makeCmd" -ForegroundColor Green
                Write-Host ($makeVersion | Select-Object -First 1) -ForegroundColor Cyan
                $makeFound = $true
                break
            }
        } catch {
            # Continue checking
        }
    }
    
    if (-not $makeFound) {
        Write-Host "Make tool not found. Install with:" -ForegroundColor Red
        Write-Host "  choco install make" -ForegroundColor White
        Write-Host "  or download from: http://gnuwin32.sourceforge.net/packages/make.htm" -ForegroundColor White
    }
    
    # Test compilation if possible
    if ($makeFound -and (Test-Path "slave\Makefile")) {
        Write-Host "`nFound Makefile in slave directory." -ForegroundColor Green
        $testCompile = Read-Host "Test compilation? (y/n)"
        
        if ($testCompile -eq 'y' -or $testCompile -eq 'Y') {
            Set-Location "slave"
            Write-Host "Starting test compilation..." -ForegroundColor Yellow
            
            try {
                & make clean
                & make
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Compilation successful!" -ForegroundColor Green
                    
                    # Look for output files
                    $binFiles = Get-ChildItem -Name "*.bin" -Recurse
                    if ($binFiles) {
                        Write-Host "Generated files:" -ForegroundColor Green
                        foreach ($file in $binFiles) {
                            Write-Host "  $file" -ForegroundColor White
                        }
                    }
                } else {
                    Write-Host "Compilation failed. Check error messages above." -ForegroundColor Red
                }
            } catch {
                Write-Host "Compilation error: $($_.Exception.Message)" -ForegroundColor Red
            }
            
            Set-Location ..
        }
    }
    
    Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
    Write-Host "You can now use 'make' commands in the slave directory." -ForegroundColor Cyan
}

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")