$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) { & py -m venv .venv }
    else { & python -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear .venv. Instalá Python e intentá otra vez.' }
}
$cmakeBin = 'C:\Program Files\CMake\bin'
if (Test-Path -LiteralPath $cmakeBin) { $env:PATH = $cmakeBin + ';' + $env:PATH }
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación. Revisá CMake y Visual Studio Build Tools con Desarrollo de escritorio con C++.' }
& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Hay dependencias incompatibles.' }
Write-Host 'Instalación terminada.'
Write-Host 'Panel: .\.venv\Scripts\python.exe app.py (http://127.0.0.1:5000)'
Write-Host 'Comparación: .\.venv\Scripts\python.exe comparar_rostros.py control.jpg prueba.jpg'
Write-Host 'Webcam: .\.venv\Scripts\python.exe asistencia.py'
