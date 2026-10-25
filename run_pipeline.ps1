$root = $PSScriptRoot
& "$root\dbt-env\Scripts\Activate.ps1"
Set-Location "$root\dbt_project\iot_analytics"
dbt build
if ($LASTEXITCODE -ne 0) { Write-Host "dbt build FAILED" -ForegroundColor Red; exit 1 }
Write-Host "Pipeline OK" -ForegroundColor Green