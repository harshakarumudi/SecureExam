# SecureExam SonarQube Runner Script
param (
    [string]$Token = "sqp_274ac8f6793f0d189f3b202e1ff468aad00522ad"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   SecureExam - SonarQube Static Analysis and Quality Gate   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Generate coverage.xml
Write-Host "[1/3] Generating coverage.xml from automated Pytest suite..." -ForegroundColor Yellow
$env:PYTHONPATH = "."
.\venv\Scripts\pytest tests/ -q --cov=backend.app --cov-report=xml:coverage.xml

if (-not (Test-Path "coverage.xml")) {
    Write-Host "Error: Failed to generate coverage.xml. Please check tests." -ForegroundColor Red
    exit 1
}
Write-Host "Coverage report successfully generated." -ForegroundColor Green

# Step 2: Ensure SonarQube is running
Write-Host "[2/3] Checking SonarQube container..." -ForegroundColor Yellow
$container = docker ps --filter "name=secureexam_sonarqube" --filter "status=running" -q
if (-not $container) {
    Write-Host "Starting SonarQube container..." -ForegroundColor Cyan
    docker compose -f docker-compose.sonar.yml up -d
} else {
    Write-Host "SonarQube container is already running." -ForegroundColor Green
}

# Step 3: Run SonarScanner via Docker
Write-Host "[3/3] Running SonarScanner..." -ForegroundColor Yellow

docker run --rm --network secureexam_sonar-net -v "${PWD}:/usr/src" -e SONAR_HOST_URL="http://sonarqube:9000" -e SONAR_TOKEN="$Token" sonarsource/sonar-scanner-cli

Write-Host "============================================================" -ForegroundColor Green
Write-Host " Analysis finished! View your SonarQube dashboard at:       " -ForegroundColor Green
Write-Host " http://localhost:9000/dashboard?id=secureexam-academic     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
