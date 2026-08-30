```powershell
#Requires -Version 5.1
#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# ============================================================
# BetterIt Installer
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
    Write-Host "  ---------------------------------------------" -ForegroundColor DarkGray
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

# ============================================================
# Download BetterIt.exe
# ============================================================

function Download-BetterIt {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    $downloadFile = "$Destination.download"

    if (Test-Path $downloadFile) {
        Remove-Item $downloadFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "  Downloading BetterIt" -ForegroundColor Cyan
    Write-Host ""

    # --------------------------------------------------------
    # Start BITS download
    # --------------------------------------------------------

    $job = Start-BitsTransfer `
        -Source $Url `
        -Destination $downloadFile `
        -DisplayName "BetterIt" `
        -Description "Downloading BetterIt.exe" `
        -Asynchronous

    try {

        while ($true) {

            $job = Get-BitsTransfer -JobId $job.JobId -ErrorAction Stop

            $state = $job.JobState

            if ($state -eq "Transferred") {

                Complete-BitsTransfer -BitsJob $job

                if (-not (Test-Path $downloadFile)) {
                    throw "Download completed but the downloaded file was not found."
                }

                Move-Item -Path $downloadFile -Destination $Destination -Force

                # Draw final 100% progress bar.
                $bar = "####################################"

                Write-Host "`r  [$bar] 100%   " -NoNewline -ForegroundColor Green
                Write-Host ""
                Write-Host ""

                return
            }

            if ($state -eq "Error") {

                $errorDescription = $job.ErrorDescription

                Remove-BitsTransfer `
                    -BitsJob $job `
                    -Confirm:$false `
                    -ErrorAction SilentlyContinue

                throw "BITS download failed: $errorDescription"
            }

            if ($state -eq "Cancelled") {

                Remove-BitsTransfer `
                    -BitsJob $job `
                    -Confirm:$false `
                    -ErrorAction SilentlyContinue

                throw "The download was cancelled."
            }

            # ------------------------------------------------
            # Calculate progress
            # ------------------------------------------------

            $bytesReceived = [double]$job.BytesTransferred
            $bytesTotal = [double]$job.BytesTotal

            if ($bytesTotal -gt 0) {

                $percentage = [math]::Floor(
                    ($bytesReceived / $bytesTotal) * 100
                )

                if ($percentage -gt 100) {
                    $percentage = 100
                }

                if ($percentage -lt 0) {
                    $percentage = 0
                }

                $downloadedMB = [math]::Round(
                    $bytesReceived / 1MB,
                    2
                )

                $totalMB = [math]::Round(
                    $bytesTotal / 1MB,
                    2
                )

                $barWidth = 36

                $filled = [math]::Floor(
                    ($percentage / 100) * $barWidth
                )

                $empty = $barWidth - $filled

                if ($filled -lt 0) {
                    $filled = 0
                }

                if ($empty -lt 0) {
                    $empty = 0
                }

                $bar = ("#" * $filled) + ("-" * $empty)

                $display = "  [$bar] $percentage%  $downloadedMB MB / $totalMB MB"

                Write-Host "`r$display" -NoNewline -ForegroundColor Cyan
            }
            else {

                Write-Host "`r  [------------------------------------]  Preparing download..." -NoNewline -ForegroundColor Cyan
            }

            Start-Sleep -Milliseconds 150
        }
    }
    catch {

        if ($job) {
            Remove-BitsTransfer `
                -BitsJob $job `
                -Confirm:$false `
                -ErrorAction SilentlyContinue
        }

        if (Test-Path $downloadFile) {
            Remove-Item $downloadFile -Force -ErrorAction SilentlyContinue
        }

        throw $_
    }
}

# ============================================================
# Main Installer
# ============================================================

try {

    Write-Header

    Write-Step "Preparing BetterIt installation..."

    # --------------------------------------------------------
    # Administrator check
    # --------------------------------------------------------

    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()

    $principal = New-Object Security.Principal.WindowsPrincipal($identity)

    $isAdmin = $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )

    if (-not $isAdmin) {
        throw "Administrator privileges are required."
    }

    # --------------------------------------------------------
    # Prepare temporary directory
    # --------------------------------------------------------

    Write-Step "Preparing temporary directory..."

    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

    # --------------------------------------------------------
    # Check latest release
    # --------------------------------------------------------

    Write-Step "Checking latest BetterIt release..."

    $headers = @{
        "User-Agent" = "BetterIt-Installer"
        "Accept" = "application/vnd.github+json"
    }

    $release = Invoke-RestMethod -Uri $ApiUrl -Headers $headers -Method Get

    if (-not $release) {
        throw "Unable to retrieve the latest BetterIt release."
    }

    $version = $release.tag_name

    if ([string]::IsNullOrWhiteSpace($version)) {
        $version = $release.name
    }

    if ([string]::IsNullOrWhiteSpace($version)) {
        throw "The latest BetterIt release does not have a valid version."
    }

    # --------------------------------------------------------
    # Find BetterIt.exe
    # --------------------------------------------------------

    Write-Step "Finding BetterIt.exe..."

    $exeAsset = $release.assets |
        Where-Object {
            $_.name -ieq "BetterIt.exe"
        } |
        Select-Object -First 1

    if (-not $exeAsset) {

        $exeAsset = $release.assets |
            Where-Object {
                $_.name -match "(?i)BetterIt.*\.exe$"
            } |
            Select-Object -First 1
    }

    if (-not $exeAsset) {
        throw "BetterIt.exe was not found in the latest GitHub release."
    }

    $downloadUrl = $exeAsset.browser_download_url

    if ([string]::IsNullOrWhiteSpace($downloadUrl)) {
        throw "The BetterIt.exe download URL is invalid."
    }

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    Download-BetterIt -Url $downloadUrl -Destination $TempExe

    # --------------------------------------------------------
    # Verify download
    # --------------------------------------------------------

    if (-not (Test-Path $TempExe)) {
        throw "BetterIt.exe could not be downloaded."
    }

    $downloadedSize = (Get-Item $TempExe).Length

    if ($downloadedSize -le 0) {
        throw "Downloaded BetterIt.exe is empty."
    }

    Write-Success "BetterIt $version downloaded successfully."

    # --------------------------------------------------------
    # Stop existing BetterIt
    # --------------------------------------------------------

    Write-Step "Stopping existing BetterIt instance..."

    $existingProcesses = Get-Process -Name "BetterIt" -ErrorAction SilentlyContinue

    if ($existingProcesses) {
        $existingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    # --------------------------------------------------------
    # Prepare installation directory
    # --------------------------------------------------------

    Write-Step "Preparing installation directory..."

    if (Test-Path $InstallDir) {

        Get-ChildItem -Path $InstallDir -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

        Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

    # --------------------------------------------------------
    # Install executable
    # --------------------------------------------------------

    Write-Step "Installing BetterIt..."

    $installedExe = Join-Path $InstallDir "BetterIt.exe"

    Copy-Item -Path $TempExe -Destination $installedExe -Force

    if (-not (Test-Path $installedExe)) {
        throw "BetterIt.exe could not be installed."
    }

    # --------------------------------------------------------
    # Create startup shortcut
    # --------------------------------------------------------

    Write-Step "Creating Windows startup shortcut..."

    if (Test-Path $ShortcutPath) {
        Remove-Item $ShortcutPath -Force -ErrorAction SilentlyContinue
    }

    $shell = New-Object -ComObject WScript.Shell

    $shortcut = $shell.CreateShortcut($ShortcutPath)

    $shortcut.TargetPath = $installedExe
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Description = "BetterIt"
    $shortcut.WindowStyle = 1
    $shortcut.IconLocation = "$installedExe,0"

    $shortcut.Save()

    # --------------------------------------------------------
    # Verify shortcut
    # --------------------------------------------------------

    if (-not (Test-Path $ShortcutPath)) {
        throw "BetterIt startup shortcut could not be created."
    }

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    Write-Step "Cleaning up temporary files..."

    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    # --------------------------------------------------------
    # Get installed version
    # --------------------------------------------------------

    $fileVersion = (Get-Item $installedExe).VersionInfo.FileVersion

    if ([string]::IsNullOrWhiteSpace($fileVersion)) {
        $fileVersion = $version
    }

    # --------------------------------------------------------
    # Start BetterIt
    # --------------------------------------------------------

    Write-Step "Starting BetterIt..."

    Start-Process -FilePath $installedExe -WorkingDirectory $InstallDir

    Start-Sleep -Milliseconds 700

    # --------------------------------------------------------
    # Completion
    # --------------------------------------------------------

    Clear-Host

    Write-Host ""
    Write-Host "  BetterIt" -ForegroundColor Cyan
    Write-Host "  ---------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "  Installation completed successfully." -ForegroundColor Green
    Write-Host ""

    Write-Host "  Version      : " -NoNewline -ForegroundColor Gray
    Write-Host "$fileVersion" -ForegroundColor White

    Write-Host "  Release      : " -NoNewline -ForegroundColor Gray
    Write-Host "$version" -ForegroundColor White

    Write-Host "  Location     : " -NoNewline -ForegroundColor Gray
    Write-Host "$installedExe" -ForegroundColor White

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

    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    Clear-Host

    Write-Host ""
    Write-Host "  BetterIt Installation Failed" -ForegroundColor Red
    Write-Host "  ---------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red

    Write-Host ""
    Write-Host "  No changes have been intentionally hidden from you because" -ForegroundColor Gray
    Write-Host "  the installer needs your attention." -ForegroundColor Gray
    Write-Host ""

    exit 1
}
```
