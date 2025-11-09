# 🚀 Posture Analysis API - Installation & Setup Script

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   POSTURE ANALYSIS API - AUTOMATED SETUP" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check pip
Write-Host "Step 2: Checking pip installation..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version
    Write-Host "✅ pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip not found! Please install pip." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Navigate to project directory
$projectDir = "c:\Users\sayee\Downloads\posture backend\workout_analyzer_backend"
Write-Host "Step 3: Navigating to project directory..." -ForegroundColor Yellow

if (Test-Path $projectDir) {
    Set-Location $projectDir
    Write-Host "✅ Project directory found: $projectDir" -ForegroundColor Green
} else {
    Write-Host "❌ Project directory not found: $projectDir" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install dependencies
Write-Host "Step 4: Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

try {
    pip install -r requirements.txt
    Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error installing dependencies!" -ForegroundColor Red
    Write-Host "Try manually: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if posture_sessions.csv exists, create if not
Write-Host "Step 5: Checking database file..." -ForegroundColor Yellow

if (-not (Test-Path "posture_sessions.csv")) {
    Write-Host "Creating posture_sessions.csv..." -ForegroundColor Gray
    $csvHeader = "timestamp,session_id,session_seconds,total_frames,good_frames,bad_frames,good_percent,bad_percent,average_score,longest_bad_secs"
    $csvHeader | Out-File -FilePath "posture_sessions.csv" -Encoding UTF8
    Write-Host "✅ Database file created" -ForegroundColor Green
} else {
    Write-Host "✅ Database file already exists" -ForegroundColor Green
}

Write-Host ""

# Get local IP address
Write-Host "Step 6: Finding your IP address for Flutter integration..." -ForegroundColor Yellow

$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.PrefixOrigin -eq "Dhcp"}).IPAddress | Select-Object -First 1

if ($ipAddress) {
    Write-Host "✅ Your IP Address: $ipAddress" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 IMPORTANT: Use this in your Flutter app:" -ForegroundColor Cyan
    Write-Host "   const String baseUrl = 'http://${ipAddress}:8000';" -ForegroundColor White
} else {
    Write-Host "⚠️ Could not detect IP automatically" -ForegroundColor Yellow
    Write-Host "Use 'ipconfig' command to find your IPv4 address" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   SETUP COMPLETE! ✅" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start the server:" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test the API (in another terminal):" -ForegroundColor White
Write-Host "   python test_api.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. View API documentation:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Read the documentation:" -ForegroundColor White
Write-Host "   - QUICKSTART.md - Quick start guide" -ForegroundColor Gray
Write-Host "   - API_DOCUMENTATION.md - Full API reference" -ForegroundColor Gray
Write-Host "   - FLUTTER_EXAMPLE.dart - Flutter integration code" -ForegroundColor Gray
Write-Host ""

# Ask if user wants to start the server now
Write-Host "===========================================================" -ForegroundColor Cyan
$response = Read-Host "Do you want to start the server now? (Y/N)"

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Starting server..." -ForegroundColor Green
    Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    python app.py
} else {
    Write-Host ""
    Write-Host "To start the server later, run: python app.py" -ForegroundColor Yellow
    Write-Host ""
}
