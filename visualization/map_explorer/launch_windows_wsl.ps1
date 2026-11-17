# Additive WSL entry point. All user paths are native argument-array values, never shell code.
param([string]$MapDirectory = "")
$ErrorActionPreference = 'Stop'
$originalEncoding = [Console]::OutputEncoding
try {
    # Linux wslpath emits UTF-8; Windows PowerShell 5 otherwise uses a legacy code page.
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if (-not $wsl) { throw 'WSL is unavailable. Install WSL and a Linux distribution manually; see README: Windows Launcher (WSL).' }
    # Decode wsl.exe's UTF-16LE list through a redirected reader, without
    # changing the console to unsupported UTF-16 code page 1200.
    $listInfo = New-Object System.Diagnostics.ProcessStartInfo
    $listInfo.FileName = $wsl.Source
    $listInfo.Arguments = '--list --quiet'
    $listInfo.UseShellExecute = $false
    $listInfo.RedirectStandardOutput = $true
    $listInfo.StandardOutputEncoding = [System.Text.Encoding]::Unicode
    $listing = [System.Diagnostics.Process]::Start($listInfo)
    $listText = $listing.StandardOutput.ReadToEnd()
    $listing.WaitForExit()
    $listExit = $listing.ExitCode
    $listing.Dispose()
    $distros = @($listText -split "`r?`n" | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ })
    if ($listExit -ne 0 -or $distros.Count -eq 0) { throw 'No usable WSL distribution. Run wsl --list --verbose and complete Linux distribution setup.' }
    if (-not $MapDirectory) {
        try {
            Add-Type -AssemblyName System.Windows.Forms
            $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
            $dialog.Description = 'Select a CaMa-Flood map folder containing params.txt (Cancel uses bundled Mekong)'
            if ($dialog.ShowDialog() -eq 'OK') { $MapDirectory = $dialog.SelectedPath }
        } catch { Write-Host 'Folder chooser unavailable; using bundled Mekong.' }
        if (-not $MapDirectory) { $MapDirectory = Join-Path $PSScriptRoot '..\..\map\mekong_15min' }
    }
    $distro = $env:CMF_WSL_DISTRO
    # A UNC Linux path identifies its owning distribution. Refuse cross-distro ambiguity.
    foreach ($path in @($PSScriptRoot, $MapDirectory)) {
        if ($path -match '^\\\\(?:wsl\$|wsl\.localhost)\\([^\\]+)(?:\\|$)') {
            $owner = $Matches[1]
            if ($distro -and $distro -ne $owner) { throw "UNC path belongs to $owner but selected distro is $distro. Use paths in one distro." }
            $distro = $owner
        }
    }
    $prefix = @()
    if ($distro) {
        if ($distros -notcontains $distro) { throw "WSL distribution '$distro' is not installed. Check wsl --list --quiet or CMF_WSL_DISTRO." }
        $prefix = @('--distribution', $distro)
    }
    function Convert-LinuxPath([string]$value) {
        if ($value.StartsWith('/')) { return $value }
        if ($value -match '^\\\\(?:wsl\$|wsl\.localhost)\\([^\\]+)\\?(.*)$') {
            return '/' + ($Matches[2] -replace '\\','/')
        }
        $absolute = [System.IO.Path]::GetFullPath($value)
        $converted = & $wsl.Source @prefix --exec wslpath -u $absolute
        if ($LASTEXITCODE -ne 0 -or -not $converted) { throw "Cannot convert path in WSL: $value" }
        return ($converted -join "`n").Trim()
    }
    $helper = Convert-LinuxPath (Join-Path $PSScriptRoot 'launch_wsl.sh')
    $map = Convert-LinuxPath $MapDirectory
    $powershell = Convert-LinuxPath ([System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName)
    $python = $env:CMF_WSL_PYTHON
    if (-not $python) { $python = '-' }
    Write-Host 'Starting Linux Panel server in WSL; keep this terminal open. Ctrl-C stops it.'
    & $wsl.Source @prefix --exec sh $helper $map $python $powershell
    exit $LASTEXITCODE
} catch {
    Write-Host ('[ERROR] ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    [Console]::OutputEncoding = $originalEncoding
}
