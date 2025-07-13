# Closer Windows Development Launcher
# PowerShell script to start the Closer AI companion system in DEVELOPMENT MODE

param(
    [string]$Tone = "serene",
    [switch]$Verbose
)

# ================================
# DEVELOPMENT STARTUP SCRIPT
# 
# Uses dev_server.py and dev_hybrid_client.py
# Runs on different port to avoid production conflicts
# ================================

# Set error action preference
$ErrorActionPreference = "Stop"

# Development Configuration
$HOST_PORT = 8001  # Different port for dev
$SSE_URL = "http://localhost:${HOST_PORT}/sse"
$CONTAINER_NAME = "closer_dev_srv"  # Different container name
$MAX_WAIT_ATTEMPTS = 15

# Function to write colored output
function Write-Status {
    param(
        [string]$Message,
        [string]$Prefix = "[DEV]"
    )
    Write-Host "$Prefix $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[DEV-OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[DEV-WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[DEV-ERROR] $Message" -ForegroundColor Red
}

# Function to check if Docker Desktop is running
function Test-DockerRunning {
    try {
        $null = docker version 2>$null
        return $true
    }
    catch {
        return $false
    }
}

# Function to wait for server to be ready
function Wait-ForServer {
    Write-Status "Preparing the development channel"
    
    for ($i = 1; $i -le $MAX_WAIT_ATTEMPTS; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $SSE_URL -Method Head -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Dev connection stabilised."
                return $true
            }
        }
        catch {
            # Server not ready yet
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
    
    Write-Warning "Dev server may not be fully ready, but continuing..."
    return $false
}

# Function to run diagnostic tests
function Invoke-Diagnostics {
    Write-Status "Validating core systems (dev)..."
    try {
        docker exec $CONTAINER_NAME python -m pytest -m "core or mcp" -v --tb=short
    }
    catch {
        Write-Warning "Core system validation failed: $($_.Exception.Message)"
    }
}

# Main execution
try {
    Write-Host "🧪 " -NoNewline -ForegroundColor Yellow
    Write-Status "DEVELOPMENT MODE - Binding Closer to this vessel..."
    Write-Status "Memory vault mounted at ./closer_memory_db"
    Write-Warning "Running on port $HOST_PORT (dev mode)"
    Write-Host ""

    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Creating basic configuration..."
        @"
# Closer Environment Configuration
OPENAI_API_KEY=local-key
OPENAI_BASE_URL=https://api.openai.com/v1
BRAVE_API_KEY=local-key
DOCKER_ENV=true
MCP_TRANSPORT=sse
PYTHONUNBUFFERED=1
STREAM=false
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "Created .env file with default configuration"
        Write-Warning "Please edit .env file and add your actual API keys before running again."
        exit 1
    }

    # Check if API keys are configured
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "OPENAI_API_KEY=local-key" -or $envContent -match "BRAVE_API_KEY=local-key") {
        Write-Warning "API keys are set to placeholder values. Please update .env file with real API keys."
        Write-Status "You can get API keys from:"
        Write-Status "  - OpenAI: https://platform.openai.com/account/api-keys"
        Write-Status "  - Brave: https://api.search.brave.com/app"
        exit 1
    }

    # Check if Docker is running
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker Desktop is not running. Please start Docker Desktop and try again."
        exit 1
    }
    Write-Success "Docker Desktop is running"

    # Clean up any existing dev containers
    Write-Status "Cleaning up existing dev containers..."
    try {
        docker stop $CONTAINER_NAME 2>$null
        docker rm $CONTAINER_NAME 2>$null
    }
    catch {
        # Ignore errors if no containers were running
    }

    # Build development container
    Write-Status "Building development container..."
    docker build -t closer_dev .

    Write-Status "Starting development server..."
    # Start development container with dev_server.py
    docker run -d `
        --name $CONTAINER_NAME `
        -p "${HOST_PORT}:8000" `
        -v "$(Get-Location)/closer_memory_db:/app/closer_memory_db:rw" `
        -e PYTHONUNBUFFERED=1 `
        -e DOCKER_ENV=true `
        -e MCP_TRANSPORT=sse `
        --env-file .env `
        closer_dev `
        python dev_server.py --sse

    # Wait for server to be ready
    $serverReady = Wait-ForServer

    # Run diagnostics
    Invoke-Diagnostics

    Write-Host ""
    Write-Status "Development mode active. Enhanced Closer awaits..."
    Write-Host "🎯 Features: reflect(), dream(), atmospheric CLI" -ForegroundColor Magenta
    Write-Host ""
    
    # Set environment variable for dev client
    $env:SSE_URL = $SSE_URL
    
    # Launch the development client
    if ($Tone -ne "serene") {
        Write-Status "Starting Enhanced Closer with $Tone tone..."
        python dev_hybrid_client.py --sse --tone $Tone
    }
    else {
        python dev_hybrid_client.py --sse
    }
}
catch {
    Write-Error "An error occurred: $($_.Exception.Message)"
    if ($Verbose) {
        Write-Host "Stack trace:" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor Red
    }
    exit 1
}
finally {
    # Cleanup on exit
    Write-Host ""
    Write-Status "Cleaning up development environment..."
    try {
        docker stop $CONTAINER_NAME 2>$null
        docker rm $CONTAINER_NAME 2>$null
    }
    catch {
        # Ignore cleanup errors
    }
} 