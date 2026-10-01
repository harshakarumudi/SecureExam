# SecureExam SonarQube Runner Script
param (
    [string]$SonarHost = "http://localhost:9000",
    [string]$Token = ""
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   SecureExam — SonarQube Static Analysis & Quality Gate    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Ensure fresh coverage.xml
Write-Host "[1/3] Generating coverage.xml from automated Pytest suite..." -ForegroundColor Yellow
$env:PYTHONPATH="."
.\venv\Scripts\pytest tests/ -q --cov=backend.app --cov-report=xml:coverage.xml

if (-not (Test-Path "coverage.xml")) {
    Write-Host "Failed to generate coverage.xml. Please check tests." -ForegroundColor Red
    exit 1
}
Write-Host "Coverage report successfully generated." -ForegroundColor Green

# Step 2: Start SonarQube container if not already running
if ($SonarHost -match "localhost|127.0.0.1") {
    Write-Host "[2/3] Checking local SonarQube server..." -ForegroundColor Yellow
    $container = docker ps --filter "name=secureexam_sonarqube" --filter "status=running" -q
    if (-not $container) {
        Write-Host "Launching SonarQube container on port 9000..." -ForegroundColor Cyan
        docker compose -f docker-compose.sonar.yml up -d
        Write-Host "Waiting for SonarQube to initialize (first boot takes ~45-60s)..." -ForegroundColor Cyan
        
        $ready = $false
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 3
            try {
                $resp = Invoke-WebRequest -Uri "http://localhost:9000/api/system/status" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
                if ($resp.StatusCode -eq 200 -and $resp.Content -match '"status":"UP"') {
                    $ready = $true
                    break
                }
            } catch {}
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
        Write-Host ""
        if (-not $ready) {
            Write-Host "SonarQube is still starting up. You can check http://localhost:9000 in your browser." -ForegroundColor Yellow
        } else {
            Write-Host "SonarQube server is UP and ready at http://localhost:9000" -ForegroundColor Green
        }
    } else {
        Write-Host "SonarQube container is already running at http://localhost:9000" -ForegroundColor Green
    }
}

# Step 3: Run SonarScanner
Write-Host "[3/3] Running SonarScanner analysis via Docker..." -ForegroundColor Yellow

$scannerArgs = @(
    "run", "--rm",
    "--network", "host",
    "-v", "${PWD}:/usr/src",
    "sonarsource/sonar-scanner-cli",
    "-Dsonar.host.url=$SonarHost",
    "-Dsonar.projectKey=secureexam-academic",
    "-Dsonar.projectName=SecureExam",
    "-Dsonar.sources=backend/app,frontend/src",
    "-Dsonar.tests=tests",
    "-Dsonar.python.coverage.reportPaths=coverage.xml",
    "-Dsonar.exclusions=**/node_modules/**,**/dist/**,**/venv/**,**/.pytest_cache/**,**/__pycache__/**"
)

if ($Token -ne "") {
    $scannerArgs += "-Dsonar.token=$Token"
}

docker @scannerArgs

Write-Host "============================================================" -ForegroundColor Green
Write-Host " Analysis finished! View your SonarQube dashboard at:       " -ForegroundColor Green
Write-Host " $SonarHost/dashboard?id=secureexam-academic               " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
