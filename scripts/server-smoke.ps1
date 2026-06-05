$ErrorActionPreference = "Stop"

$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://127.0.0.1:8000" }
$FrontendUrl = if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { "http://127.0.0.1:3001" }

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url
    )

    Write-Host "$Name ... " -NoNewline
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url
    if ($response.StatusCode -ne 200) {
        Write-Host "FAILED ($($response.StatusCode))"
        Write-Host $response.Content
        exit 1
    }
    Write-Host "ok"
}

Test-Endpoint "backend health" "$BaseUrl/api/v1/health"
Test-Endpoint "backend readiness" "$BaseUrl/api/v1/health/readiness"
Test-Endpoint "data health" "$BaseUrl/api/v1/data/health"
Test-Endpoint "frontend" "$FrontendUrl"

Write-Host "DeltaGrid smoke checks passed."
