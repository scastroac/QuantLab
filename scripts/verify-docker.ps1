[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Run
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-CommandAvailable {
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    if ($null -eq (Get-Command -Name $Name -ErrorAction SilentlyContinue)) {
        throw "'$Name' no está disponible en PATH. Revisa la instalación indicada en docs/docker.md."
    }
}

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "El comando '$Command $($Arguments -join ' ')' terminó con código $LASTEXITCODE."
    }
}

Assert-CommandAvailable -Name "wsl"
Assert-CommandAvailable -Name "docker"

# FIX: Added .IsPresent so the switch evaluates to a boolean before casting to an integer
$totalSteps = 4 + [int]$Build.IsPresent + [int]$Run.IsPresent
$currentStep = 0

function Write-Step {
    param(
        [Parameter(Mandatory)]
        [string]$Description
    )

    $script:currentStep += 1
    Write-Host "[$script:currentStep/$script:totalSteps] $Description"
}

Write-Step -Description "WSL"
Invoke-ExternalCommand -Command "wsl" -Arguments @("--status")

Write-Step -Description "Docker CLI y motor"
Invoke-ExternalCommand -Command "docker" -Arguments @("version")

Write-Step -Description "Docker Compose"
Invoke-ExternalCommand -Command "docker" -Arguments @("compose", "version")

Write-Step -Description "Configuración de Compose"
Invoke-ExternalCommand -Command "docker" -Arguments @("compose", "config", "--quiet")

if ($Build) {
    Write-Step -Description "Construcción de imagen"
    Invoke-ExternalCommand -Command "docker" -Arguments @("compose", "build", "--no-cache")
}

if ($Run) {
    Write-Step -Description "Ejecución del smoke test"
    Invoke-ExternalCommand -Command "docker" -Arguments @("compose", "run", "--rm", "quantlab")
}

Write-Host "La verificación de Docker terminó correctamente."