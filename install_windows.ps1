$ErrorActionPreference = "Stop"

$ProjectPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $ProjectPython)) {
    throw "No existe .venv. Ejecuta primero: py -m venv .venv"
}

& $ProjectPython -m pip install "setuptools<81" "dlib-bin==20.0.1.post1" `
    "face-recognition-models==0.3.0" "opencv-python>=4.9" Pillow Click
& $ProjectPython -m pip install "face-recognition==1.3.0" --no-deps
& $ProjectPython -c "import cv2, dlib, face_recognition, numpy; print('Instalacion correcta'); print('OpenCV:', cv2.__version__); print('dlib:', dlib.__version__); print('face_recognition:', face_recognition.__version__); print('NumPy:', numpy.__version__)"
