# start_chrome.ps1 - launches Chrome with CDP, does NOT kill personal Chrome
$chrome  = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profile = "C:\projects\ai_browser_agent\chrome_profile"
$port    = 9222

if (-not (Test-Path $chrome)) {
    Write-Error "Chrome not found at: $chrome"
    exit 1
}
if (-not (Test-Path $profile)) {
    New-Item -ItemType Directory -Path $profile | Out-Null
}

# 1) Is CDP already up on this port?
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$port/json/version" -UseBasicParsing -TimeoutSec 2
    if ($resp.StatusCode -eq 200) {
        Write-Host "[OK] CDP already running on port $port - Chrome agent is up." -ForegroundColor Green
        Write-Host "     Version: $($resp.Content | ConvertFrom-Json | Select-Object -ExpandProperty Browser)"
        Write-Host "     Nothing to do, personal Chrome untouched."
        exit 0
    }
} catch {
    # port is free - continue
}

# 2) Launch separate Chrome instance with its own profile
Write-Host "Launching Chrome agent (profile: $profile)..."
Start-Process -FilePath $chrome -ArgumentList @(
    "--remote-debugging-port=$port",
    "--user-data-dir=`"$profile`"",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window"
)

# 3) Wait for CDP
for ($i = 0; $i -lt 15; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$port/json/version" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            Write-Host "[OK] Chrome agent ready. CDP on http://localhost:$port" -ForegroundColor Green
            Write-Host "     Version: $($resp.Content | ConvertFrom-Json | Select-Object -ExpandProperty Browser)"
            exit 0
        }
    } catch { Start-Sleep -Seconds 1 }
}

Write-Error "Chrome agent did not start within 15 seconds."
exit 1