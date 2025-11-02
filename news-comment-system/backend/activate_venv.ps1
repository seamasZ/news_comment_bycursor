# PowerShell 虚拟环境激活脚本
# 使用方法: .\activate_venv.ps1

if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} elseif (Test-Path "venv\Scripts\activate.bat") {
    Write-Host "PowerShell执行策略限制，使用CMD方式激活..." -ForegroundColor Yellow
    Write-Host "请运行: venv\Scripts\activate.bat" -ForegroundColor Yellow
    Write-Host "或者运行以下命令允许脚本执行:" -ForegroundColor Yellow
    Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
} else {
    Write-Host "虚拟环境不存在，请先运行: python -m venv venv" -ForegroundColor Red
}



