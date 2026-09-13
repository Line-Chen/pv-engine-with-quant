param(
    [string]$BaseUrl = "http://localhost:8080"
)

$ErrorActionPreference = "Stop"

Write-Host "GET $BaseUrl/api/quant/capabilities"
Invoke-RestMethod -Uri "$BaseUrl/api/quant/capabilities" -Method Get | ConvertTo-Json -Depth 6

Write-Host "POST $BaseUrl/api/quant/run/oneshot/sample/cny-fr007"
Invoke-RestMethod -Uri "$BaseUrl/api/quant/run/oneshot/sample/cny-fr007" -Method Post | ConvertTo-Json -Depth 8
