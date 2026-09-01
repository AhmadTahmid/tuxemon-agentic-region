param(
    [Parameter(Mandatory = $true)][string]$MapId,
    [Parameter(Mandatory = $true)][int]$X,
    [Parameter(Mandatory = $true)][int]$Y,
    [Parameter(Mandatory = $true)][string]$Output
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $repo $Output))
$outputDirectory = Split-Path -Parent $outputPath
[System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WorldSynthesisCapture {
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int command);
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@

$existingWindows = @(
    Get-Process -Name python -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq "Tuxemon" } |
        ForEach-Object { $_.Id }
)
$process = Start-Process -FilePath $python -ArgumentList @(
    "-m", "world_synthesis.play", "--map", $MapId,
    "--x", $X, "--y", $Y
) -WorkingDirectory $repo -PassThru

try {
    $deadline = (Get-Date).AddSeconds(25)
    do {
        Start-Sleep -Milliseconds 500
        $windowProcess = Get-Process -Name python -ErrorAction SilentlyContinue |
            Where-Object {
                $_.MainWindowTitle -eq "Tuxemon" -and
                $_.Id -notin $existingWindows
            } |
            Select-Object -First 1
    } while ($null -eq $windowProcess -and (Get-Date) -lt $deadline)

    if ($null -eq $windowProcess) {
        throw "Tuxemon window did not appear for map $MapId."
    }
    Start-Sleep -Seconds 7
    [WorldSynthesisCapture]::ShowWindow($windowProcess.MainWindowHandle, 9) | Out-Null
    [WorldSynthesisCapture]::SetForegroundWindow($windowProcess.MainWindowHandle) | Out-Null
    Start-Sleep -Seconds 2
    $rect = New-Object WorldSynthesisCapture+RECT
    if (-not [WorldSynthesisCapture]::GetWindowRect($windowProcess.MainWindowHandle, [ref]$rect)) {
        throw "Could not read the Tuxemon window bounds."
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen(
            $rect.Left, $rect.Top, 0, 0,
            (New-Object System.Drawing.Size($width, $height))
        )
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
    Write-Output $outputPath
} finally {
    if ($null -ne $windowProcess -and -not $windowProcess.HasExited) {
        Stop-Process -Id $windowProcess.Id
        $windowProcess.WaitForExit()
    }
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id
        $process.WaitForExit()
    }
}
