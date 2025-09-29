# ===================== 用户配置 =====================
$FW_BIN = "D:\wesklake\research\postdoc\exp_set_up\fan_array\fan_code\fan-club-master_trae\slave.bin"
$LABEL_PATTERNS = @('MBED*','DAPLINK*','NUCLEO*','NODE_*','NOD_*','MAINTENANCE*')
$POLL_INTERVAL = 2
$WAIT_AFTER_COPY_SEC = 15
$BEEP = $true
# ===================================================

function BeepOK { if ($BEEP) { [console]::beep(1000,120) } }
function BeepERR { if ($BEEP) { [console]::beep(400,180) } }

if (-not (Test-Path $FW_BIN)) {
  Write-Host "[ERR] Firmware does not exist: $FW_BIN" -ForegroundColor Red; BeepERR; exit 1
}

$labelMatchers = @()
foreach ($pat in $LABEL_PATTERNS) { $labelMatchers += ($pat -as [WildcardPattern]) }

function IsTargetVolume($vol) {
  if (-not $vol.DriveLetter) { return $false }
  foreach ($m in $labelMatchers) { if ($m.IsMatch($vol.FileSystemLabel)) { return $true } }
  return $false
}
function Find-Targets { Get-Volume | Where-Object { IsTargetVolume $_ } }

function Show-Files($root) {
  $fail = Join-Path $root "FAIL.TXT"
  $details = Join-Path $root "DETAILS.TXT"
  if (Test-Path $fail) {
    Write-Host "---- FAIL.TXT ----" -ForegroundColor Red
    try { Get-Content $fail -ErrorAction Stop | ForEach-Object { Write-Host $_ -ForegroundColor Red } } catch {}
  }
  if (Test-Path $details) {
    Write-Host "---- (tail) DETAILS.TXT ----" -ForegroundColor Yellow
    try { Get-Content $details -ErrorAction Stop | Select-Object -Last 20 | ForEach-Object { Write-Host $_ -ForegroundColor Yellow } } catch {}
  }
}

$seen = @{}
Write-Host "Auto-copy started. Insert mbed/DAPLink board for automatic flashing: $FW_BIN"
Write-Host "[DEBUG] Monitoring label patterns: $($LABEL_PATTERNS -join ', ')" -ForegroundColor Cyan
Write-Host "[DEBUG] Poll interval: $POLL_INTERVAL seconds" -ForegroundColor Cyan
Write-Host "[DEBUG] Starting USB device monitoring..." -ForegroundColor Cyan

while ($true) {
  Write-Host "[DEBUG] Scanning USB devices..." -ForegroundColor DarkGray
  $allVolumes = Get-Volume | Where-Object { $_.DriveLetter }
  Write-Host "[DEBUG] Found $($allVolumes.Count) volumes with drive letters" -ForegroundColor DarkGray
  
  $targets = Find-Targets
  Write-Host "[DEBUG] Matched target devices: $($targets.Count)" -ForegroundColor DarkGray
  
  $currentRoots = @($targets | ForEach-Object { "$($_.DriveLetter):\" })

  foreach ($k in @($seen.Keys)) { if ($currentRoots -notcontains $k) { $seen.Remove($k) | Out-Null } }

  foreach ($t in $targets) {
    $root = "$($t.DriveLetter):\"
    if (-not $seen.ContainsKey($root)) {
      $seen[$root] = (Get-Date).Ticks
      $label = $t.Label
      Write-Host "==> [Device Detection] Found new target device $root" -ForegroundColor Green
      Write-Host "    Label: $label" -ForegroundColor Green
      Write-Host "    File System: $($t.FileSystemType)" -ForegroundColor Green
      Write-Host "    Size: $([math]::Round($t.Size/1MB,2)) MB" -ForegroundColor Green

      if ($label -match 'MAINTENANCE') {
        Write-Host "⚠ DAPLink in MAINTENANCE mode, pausing flash operation." -ForegroundColor Yellow
        Show-Files $root; BeepERR; continue
      }

      $dst = Join-Path $root ([IO.Path]::GetFileName($FW_BIN))
      Write-Host "    [File Operation] Preparing to copy firmware file" -ForegroundColor Yellow
      Write-Host "    Source file: $FW_BIN" -ForegroundColor Yellow
      Write-Host "    Target path: $dst" -ForegroundColor Yellow
      Write-Host "    File size: $([math]::Round((Get-Item $FW_BIN).Length/1KB,2)) KB" -ForegroundColor Yellow
      
      try {
        Write-Host "    [File Operation] Starting copy..." -ForegroundColor Yellow
        Copy-Item -Path $FW_BIN -Destination $dst -Force -ErrorAction Stop
        Write-Host "✓ [File Operation] Copy successful to $dst" -ForegroundColor Green
        Write-Host "    [Flash Monitor] Waiting for DAPLink processing (max $WAIT_AFTER_COPY_SEC seconds)..." -ForegroundColor Cyan
      } catch {
        Write-Host "✗ [File Operation] Copy failed: $($_.Exception.Message)" -ForegroundColor Red
        Show-Files $root; BeepERR; continue
      }

      $ok = $false; $failHit = $false
      for ($i=0; $i -lt $WAIT_AFTER_COPY_SEC; $i++) {
        Write-Host "    [Flash Monitor] Check $($i+1) second..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 1
        
        $failPath = Join-Path $root "FAIL.TXT"
        $detailsPath = Join-Path $root "DETAILS.TXT"
        
        if (Test-Path $failPath) { 
          Write-Host "    [Flash Monitor] FAIL.TXT file detected" -ForegroundColor Red
          $failHit = $true; break 
        }
        if (-not (Test-Path $dst)) { 
          Write-Host "    [Flash Monitor] Firmware file disappeared, DAPLink received" -ForegroundColor Green
          $ok = $true; break 
        }
        if (Test-Path $detailsPath) {
          Write-Host "    [Flash Monitor] DETAILS.TXT file detected" -ForegroundColor Cyan
        }
      }

      if ($failHit) {
        Write-Host "✗ [Flash Result] Flash failed (FAIL.TXT detected)" -ForegroundColor Red
        Show-Files $root; BeepERR; continue
      }
      if ($ok) {
        Write-Host "✓ [Flash Result] Flash successful! DAPLink received and processed firmware" -ForegroundColor Green
        Show-Files $root; BeepOK
      } else {
        Write-Host "⚠ [Flash Result] Timeout: Firmware file still on device, may be processing slowly" -ForegroundColor Yellow
        Write-Host "    Suggest checking DETAILS.TXT or re-plugging device" -ForegroundColor Yellow
        Show-Files $root; BeepERR
      }
    }
  }
  Start-Sleep -Seconds $POLL_INTERVAL
}