```powershell
#Requires -Version 5.1
#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# ============================================================
# BetterIt Installer
# GitHub: https://github.com/KavimugilRajasekar/BetterIt
# ============================================================

$RepoOwner = "KavimugilRajasekar"
$RepoName  = "BetterIt"

$InstallDir = Join-Path $env:ProgramFiles "BetterIt"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "BetterIt.lnk"

$TempDir = Join-Path $env:TEMP "BetterItInstaller"
$TempExe = Join-Path $TempDir "BetterIt.exe"

$ApiUrl = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"

# ============================================================
# UI
# ============================================================

function Write-Header {
    Clear-Host

    Write-Host ""
    Write-Host "  BetterIt" -ForegroundColor Cyan
    Write-Host "  ─────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
}

function Write-Step {
    param(
        [string]$Message
    )

    Write-Host "  > $Message" -ForegroundColor Gray
}

function Write-Success {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Failure {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

# ============================================================
# Start
# ============================================================

try {

    Write-Header

    Write-Step "Preparing BetterIt installation..."

    # --------------------------------------------------------
    # Check Administrator
    # --------------------------------------------------------

    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()

    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)

    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Administrator privileges are required."
    }

    # --------------------------------------------------------
    # Prepare temporary directory
    # --------------------------------------------------------

    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

    # --------------------------------------------------------
    # Fetch latest release metadata
    # --------------------------------------------------------

    Write-Step "Checking latest BetterIt release..."

    $headers = @{
        "User-Agent" = "BetterIt-Installer"
        "Accept"     = "application/vnd.github+json"
    }

    $Release = Invoke-RestMethod -Uri $ApiUrl -Headers $headers -Method Get

    if (-not $Release) {
        throw "Unable to retrieve the latest BetterIt release."
    }

    $Version = $Release.tag_name

    if ([string]::IsNullOrWhiteSpace($Version)) {
        $Version = $Release.name
    }

    # --------------------------------------------------------
    # Locate BetterIt.exe
    # --------------------------------------------------------

    $ExeAsset = $Release.assets |
        Where-Object {
            $_.name -ieq "BetterIt.exe"
        } |
        Select-Object -First 1

    if (-not $ExeAsset) {

        # Fallback:
        # Search for an executable containing "BetterIt"

        $ExeAsset = $Release.assets |
            Where-Object {
                $_.name -match "(?i)BetterIt.*\.exe$"
            } |
            Select-Object -First 1
    }

    if (-not $ExeAsset) {
        throw "BetterIt.exe was not found in the latest GitHub release."
    }

    $DownloadUrl = $ExeAsset.browser_download_url

    # --------------------------------------------------------
    # Download with animated progress
    # --------------------------------------------------------

    Write-Host ""
    Write-Host "  Downloading BetterIt $Version" -ForegroundColor Cyan
    Write-Host ""

    $webClient = $null

    try {

        $webClient = New-Object System.Net.WebClient

        $webClient.Headers.Add("User-Agent", "BetterIt-Installer")
        $webClient.Headers.Add("Accept", "application/octet-stream")

        $webClient.DownloadProgressChanged += {
            param($sender, $e)

            $percent = $e.ProgressPercentage

            $downloadedMB = [math]::Round(
                $e.BytesReceived / 1MB,
                2
            )

            $totalMB = [math]::Round(
                $e.TotalBytesToReceive / 1MB,
                2
            )

            $barWidth = 36

            $filled = [math]::Floor(
                ($percent / 100) * $barWidth
            )

            $empty = $barWidth - $filled

            $bar = ("█" * $filled) + ("░" * $empty)

            $line = "  [$bar] $percent%  $downloadedMB MB / $totalMB MB"

            Write-Host "`r$line" -NoNewline -ForegroundColor Cyan
        }

        $webClient.DownloadFile($DownloadUrl, $TempExe)

        $webClient.Dispose()
        $webClient = $null

        Write-Host ""
        Write-Host ""

    }
    catch {

        if ($webClient) {
            $webClient.Dispose()
            $webClient = $null
        }

        throw "Failed to download BetterIt.exe: $($_.Exception.Message)"
    }

    # --------------------------------------------------------
    # Verify downloaded file
    # --------------------------------------------------------

    if (-not (Test-Path $TempExe)) {
        throw "BetterIt.exe could not be downloaded."
    }

    $DownloadedSize = (Get-Item $TempExe).Length

    if ($DownloadedSize -le 0) {
        throw "Downloaded BetterIt.exe is empty."
    }

    Write-Success "Latest BetterIt release downloaded."

    # --------------------------------------------------------
    # Stop currently running BetterIt
    # --------------------------------------------------------

    Write-Step "Stopping existing BetterIt instance..."

    Get-Process -Name "BetterIt" -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 500

    # --------------------------------------------------------
    # Remove existing installation
    # --------------------------------------------------------

    Write-Step "Preparing installation directory..."

    if (Test-Path $InstallDir) {

        # Remove everything inside BetterIt

        Get-ChildItem -Path $InstallDir -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

        # Remove the directory itself

        Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

    # --------------------------------------------------------
    # Install BetterIt.exe
    # --------------------------------------------------------

    Write-Step "Installing BetterIt..."

    $InstalledExe = Join-Path $InstallDir "BetterIt.exe"

    Copy-Item -Path $TempExe -Destination $InstalledExe -Force

    if (-not (Test-Path $InstalledExe)) {
        throw "BetterIt.exe could not be installed."
    }

    # --------------------------------------------------------
    # Create Startup Shortcut
    # --------------------------------------------------------

    Write-Step "Creating Windows startup shortcut..."

    if (Test-Path $ShortcutPath) {
        Remove-Item $ShortcutPath -Force -ErrorAction SilentlyContinue
    }

    $WshShell = New-Object -ComObject WScript.Shell

    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)

    $Shortcut.TargetPath = $InstalledExe
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "BetterIt"
    $Shortcut.WindowStyle = 1

    # Use the application's icon

    $Shortcut.IconLocation = "$InstalledExe,0"

    $Shortcut.Save()

    # --------------------------------------------------------
    # Verify shortcut
    # --------------------------------------------------------

    if (-not (Test-Path $ShortcutPath)) {
        throw "BetterIt startup shortcut could not be created."
    }

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue

    # --------------------------------------------------------
    # Get installed version
    # --------------------------------------------------------

    $FileVersion = (Get-Item $InstalledExe).VersionInfo.FileVersion

    if ([string]::IsNullOrWhiteSpace($FileVersion)) {
        $FileVersion = $Version
    }

    # --------------------------------------------------------
    # Start BetterIt
    # --------------------------------------------------------

    Write-Step "Starting BetterIt..."

    Start-Process -FilePath $InstalledExe -WorkingDirectory $InstallDir

    # --------------------------------------------------------
    # Completion
    # --------------------------------------------------------

    Start-Sleep -Milliseconds 700

    Clear-Host

    Write-Host ""
    Write-Host "  BetterIt" -ForegroundColor Cyan
    Write-Host "  ─────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "  Installation completed successfully." -ForegroundColor Green
    Write-Host ""

    Write-Host "  Version      : " -NoNewline -ForegroundColor Gray
    Write-Host "$FileVersion" -ForegroundColor White

    Write-Host "  Release      : " -NoNewline -ForegroundColor Gray
    Write-Host "$Version" -ForegroundColor White

    Write-Host "  Location     : " -NoNewline -ForegroundColor Gray
    Write-Host "$InstalledExe" -ForegroundColor White

    Write-Host ""
    Write-Host "  BetterIt is now running in the background." -ForegroundColor Green
    Write-Host ""

    Write-Host "  Press " -NoNewline -ForegroundColor Gray
    Write-Host "Ctrl + Space" -NoNewline -ForegroundColor Cyan
    Write-Host " to open BetterIt's configuration." -ForegroundColor Gray

    Write-Host ""

    Write-Host "  Your application is all set." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Have a wonderful day!" -ForegroundColor Cyan
    Write-Host ""

}
catch {

    if ($webClient) {
        $webClient.Dispose()
    }

    $ProgressPreference = "Continue"

    Clear-Host

    Write-Host ""
    Write-Host "  BetterIt Installation Failed" -ForegroundColor Red
    Write-Host "  ─────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red

    Write-Host ""
    Write-Host "  No changes have been intentionally hidden from you because" -ForegroundColor Gray
    Write-Host "  the installer needs your attention." -ForegroundColor Gray
    Write-Host ""

    exit 1
}
```
