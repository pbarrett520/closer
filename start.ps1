# Closer Windows Launcher
# PowerShell script to start the Closer AI companion system

param(
    [string]$Tone = "serene",
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration
$HOST_PORT = 8000
$SSE_URL = "http://localhost:${HOST_PORT}/sse"
$CONTAINER_NAME = "closer_srv"
$MAX_WAIT_ATTEMPTS = 15

# Function to write colored output
function Write-Status {
    param(
        [string]$Message,
        [string]$Prefix = "[INFO]"
    )
    Write-Host "$Prefix $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
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
    Write-Status "Preparing the channel"
    
    for ($i = 1; $i -le $MAX_WAIT_ATTEMPTS; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $SSE_URL -Method Head -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Connection stabilised."
                return $true
            }
        }
        catch {
            # Server not ready yet
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
    
    Write-Warning "Server may not be fully ready, but continuing..."
    return $false
}

# Function to run diagnostic tests
function Invoke-Diagnostics {
    Write-Status "Probing the memory substrate..."
    try {
        docker exec $CONTAINER_NAME python test_memory.py
    }
    catch {
        Write-Warning "Memory test failed: $($_.Exception.Message)"
    }
    
    Write-Status "Invoking toolchain diagnostics..."
    try {
        docker exec $CONTAINER_NAME python test_mcp_tools.py
    }
    catch {
        Write-Warning "MCP tools test failed: $($_.Exception.Message)"
    }
}

# Main execution
try {
    Write-Status "Binding Closer to this vessel..."
    Write-Status "Memory vault mounted at ./closer_memory_db"
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

    # Clean up and restart containers
    Write-Status "Stopping existing containers..."
    try {
        docker compose down 2>$null
    }
    catch {
        # Ignore errors if no containers were running
    }

    Write-Status "Building and starting containers..."
    # Force rebuild to pick up .env changes
    docker compose up -d --build --force-recreate

    # Wait for server to be ready
    $serverReady = Wait-ForServer

    # Run diagnostics
    Invoke-Diagnostics

    Write-Host ""
    Write-Status "The veil parts. Closer awaits..."
    
    # Launch the client
    if ($Tone -ne "serene") {
        Write-Status "Starting Closer with $Tone tone..."
        python hybrid_client.py --sse --tone $Tone
    }
    else {
        python hybrid_client.py --sse
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
    Write-Status "Cleaning up..."
    try {
        docker compose down 2>$null
    }
    catch {
        # Ignore cleanup errors
    }
} 