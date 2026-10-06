<#
.SYNOPSIS
  启动后端开发服务；启动前清理残留的 uvicorn 进程。

.DESCRIPTION
  `uvicorn --reload` 会派生一个 multiprocessing 子进程，由它真正持有监听套接字。
  父进程被强杀或崩溃后，子进程会变成孤儿继续占用端口，命令行里也不含 "uvicorn"，
  于是下一次启动会以 WinError 10013 / 10048 失败，且看不出是谁占着端口。

  本脚本先按命令行特征找出这类残留进程并结束，再启动服务。

.EXAMPLE
  pwsh scripts/dev.ps1
  pwsh scripts/dev.ps1 -Port 8001
  pwsh scripts/dev.ps1 -NoReload
#>
[CmdletBinding()]
param(
    [int]$Port = 8000,
    [string]$BindHost = '127.0.0.1',
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }

function Get-DevPythonProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and (
                $_.CommandLine -like '*uvicorn*' -or
                $_.CommandLine -like '*multiprocessing*spawn_main*'
            )
        }
}

$stale = Get-DevPythonProcesses
if ($stale) {
    Write-Host "清理 $($stale.Count) 个残留 uvicorn 进程…" -ForegroundColor Yellow
    foreach ($process in $stale) {
        Write-Host "  · PID $($process.ProcessId)"
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

$owners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($owners) {
    $names = ($owners | ForEach-Object {
        (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    }) | Sort-Object -Unique
    Write-Warning "端口 $Port 仍被占用（$($names -join ', ')）。换个端口：pwsh scripts/dev.ps1 -Port 8001"
    exit 1
}

$arguments = @('-m', 'uvicorn', 'app:app', '--host', $BindHost, '--port', $Port)
if (-not $NoReload) { $arguments += '--reload' }

Write-Host "启动 http://${BindHost}:$Port" -ForegroundColor Green
& $python @arguments