#!/usr/bin/env powershell
# Install Make Tool for Windows

Write-Host "Installing Make Tool for Windows" -ForegroundColor Green
Write-Host "=" * 35

# Create tools directory
$toolsDir = "C:\tools"
if (-not (Test-Path $toolsDir)) {
    try {
        New-Item -ItemType Directory -Path $toolsDir -Force
        Write-Host "Created tools directory: $toolsDir" -ForegroundColor Green
    } catch {
        $toolsDir = "$env:USERPROFILE\tools"
        New-Item -ItemType Directory -Path $toolsDir -Force
        Write-Host "Created tools directory: $toolsDir" -ForegroundColor Green
    }
}

# Download Make for Windows
$makeDir = "$toolsDir\make"
$makeUrl = "https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-bin.zip/download"
$makeZip = "$toolsDir\make-3.81-bin.zip"

Write-Host "Downloading Make for Windows..." -ForegroundColor Yellow

try {
    # Use alternative download method
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile("http://gnuwin32.sourceforge.net/downlinks/make-bin-zip.php", $makeZip)
    
    if (Test-Path $makeZip) {
        Write-Host "Downloaded Make successfully" -ForegroundColor Green
        
        # Extract
        if (-not (Test-Path $makeDir)) {
            New-Item -ItemType Directory -Path $makeDir -Force
        }
        
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($makeZip, $makeDir)
        
        Write-Host "Extracted Make to: $makeDir" -ForegroundColor Green
        
        # Add to PATH
        $makeBinDir = "$makeDir\bin"
        if (Test-Path $makeBinDir) {
            $env:PATH = "$makeBinDir;$env:PATH"
            Write-Host "Added Make to PATH: $makeBinDir" -ForegroundColor Green
            
            # Test Make
            try {
                $makeVersion = & make --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Make installed successfully!" -ForegroundColor Green
                    Write-Host ($makeVersion | Select-Object -First 1) -ForegroundColor Cyan
                } else {
                    throw "Make test failed"
                }
            } catch {
                Write-Host "Make installation verification failed" -ForegroundColor Red
            }
        }
        
        # Clean up
        Remove-Item $makeZip -Force
    } else {
        throw "Download failed"
    }
} catch {
    Write-Host "Failed to download/install Make: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please install Make manually from: http://gnuwin32.sourceforge.net/packages/make.htm" -ForegroundColor Yellow
}

# Alternative: Try to use mingw32-make if available
if (-not (Get-Command make -ErrorAction SilentlyContinue)) {
    Write-Host "Checking for mingw32-make..." -ForegroundColor Yellow
    
    if (Get-Command mingw32-make -ErrorAction SilentlyContinue) {
        Write-Host "Found mingw32-make, creating make alias" -ForegroundColor Green
        
        # Create a make.bat file that calls mingw32-make
        $makeBat = "$toolsDir\make.bat"
        "@echo off`nmingw32-make %*" | Out-File -FilePath $makeBat -Encoding ASCII
        
        $env:PATH = "$toolsDir;$env:PATH"
        Write-Host "Created make.bat wrapper for mingw32-make" -ForegroundColor Green
    }
}

Write-Host "`nMake installation complete!" -ForegroundColor Green
Write-Host "You may need to restart PowerShell for changes to take effect." -ForegroundColor Yellow