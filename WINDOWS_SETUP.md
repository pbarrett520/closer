# Windows Setup Guide for Closer

This guide helps Windows users set up and run the Closer AI companion system.

## Prerequisites

1. **Docker Desktop for Windows**
   - Download from [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Install and start Docker Desktop
   - Ensure Docker Desktop is running before launching Closer

2. **Python 3.8+**
   - Download from [Python.org](https://www.python.org/downloads/)
   - Ensure Python is added to PATH during installation
   - Verify installation: `python --version`

3. **PowerShell 5.1+**
   - Usually pre-installed on Windows 10/11
   - Verify: `powershell --version`

## Quick Start

### Option 1: Double-Click Launch (Recommended)
1. Double-click `start.bat`
2. The script will automatically:
   - Check prerequisites
   - Start Docker containers
   - Run diagnostic tests
   - Launch the Closer client

### Option 2: PowerShell Command Line
```powershell
# Basic launch
.\start.ps1

# Launch with different tone
.\start.ps1 -Tone intense

# Launch with verbose error reporting
.\start.ps1 -Verbose
```

## Command Line Options

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-Tone` | Set personality tone | `.\start.ps1 -Tone intense` |
| `-Verbose` | Show detailed error information | `.\start.ps1 -Verbose` |

## Troubleshooting

### Docker Desktop Not Running
```
❌ Docker Desktop is not running. Please start Docker Desktop and try again.
```
**Solution**: Start Docker Desktop from the Start menu or system tray.

### PowerShell Execution Policy Error
```
PowerShell execution policy error
```
**Solution**: Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use
```
Port 8000 is already in use
```
**Solution**: 
1. Check what's using the port: `netstat -ano | findstr :8000`
2. Stop the process or change the port in `docker-compose.yml`

### Python Not Found
```
'python' is not recognized as an internal or external command
```
**Solution**: 
1. Reinstall Python and check "Add Python to PATH"
2. Or use the full path: `C:\Python39\python.exe`

## File Structure

```
closer/
├── start.ps1          # Main PowerShell launcher
├── start.bat          # Double-click wrapper
├── start.sh           # Linux/macOS launcher
├── docker-compose.yml # Container configuration
└── ... (other files)
```

## Advanced Usage

### Custom Environment Variables
Create a `.env` file in the project directory:
```env
OPENAI_API_KEY=your_api_key_here
BRAVE_API_KEY=your_brave_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### Manual Container Management
```powershell
# Start containers manually
docker compose up -d

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Rebuild containers
docker compose up -d --build
```

### Running Tests Manually
```powershell
# Memory system test
docker exec closer_srv python test_memory.py

# MCP tools test
docker exec closer_srv python test_mcp_tools.py
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run with verbose mode: `.\start.ps1 -Verbose`
3. Check Docker Desktop logs
4. Verify all prerequisites are installed and running

## Notes

- The script automatically cleans up containers when you exit
- Memory data is persisted in `./closer_memory_db` directory
- The system uses port 8000 by default
- All emoji and Unicode characters should display correctly in modern Windows terminals 