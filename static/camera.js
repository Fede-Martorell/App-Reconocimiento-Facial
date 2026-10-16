// Capturar una imagen local y enviarla al formulario de verificación.
const video = document.getElementById("camera");
const canvas = document.getElementById("canvas");
const cameraStatus = document.getElementById("camera-status");
const captureButton = document.getElementById("capture");
const verifyButton = document.getElementById("verify");
const snapshot = document.getElementById("snapshot");
const photo = document.getElementById("photo");
let cameraStream;
let pageClosed = false;

photo.addEventListener("change", () => {
  if (photo.files.length) {
    snapshot.value = "";
    cameraStatus.textContent = "Foto seleccionada. Ya podés verificar el ingreso.";
  }
  verifyButton.disabled = !photo.files.length && !snapshot.value;
});

video.addEventListener("loadeddata", () => {
  captureButton.disabled = false;
});

captureButton.addEventListener("click", () => {
  if (!video.videoWidth || !video.videoHeight) return;
  // Limitar la captura para mantenerla por debajo del tamaño máximo del formulario.
  const scale = Math.min(1, 1280 / Math.max(video.videoWidth, video.videoHeight));
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  snapshot.value = canvas.toDataURL("image/jpeg", 0.85);
  photo.value = "";
  verifyButton.disabled = false;
  cameraStatus.textContent = "Imagen capturada. Ya podés verificar el ingreso.";
});

async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
    if (pageClosed) {
      cameraStream.getTracks().forEach(track => track.stop());
      return;
    }
    video.srcObject = cameraStream;
    cameraStatus.textContent = "Cámara lista. Mirá al frente y capturá una imagen.";
  } catch {
    cameraStatus.textContent = "La cámara no está disponible. Podés seleccionar una fotografía.";
  }
}

window.addEventListener("pagehide", () => {
  pageClosed = true;
  cameraStream?.getTracks().forEach(track => track.stop());
});

startCamera();
