from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from database import get_connection, initialize_database, query_all, query_one
from recognition_engine import RecognitionUnavailable, encoding_from_image, find_match


BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "cambiar-antes-de-produccion")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def write_access_log(employee_id: int | None, result: str, detail: str) -> None:
    with get_connection() as db:
        db.execute(
            "INSERT INTO access_logs (employee_id, result, detail) VALUES (?, ?, ?)",
            (employee_id, result, detail),
        )


def save_biometric_profile(employee_id: int, photo) -> None:
    """Create or replace the facial template for one employee."""
    if not photo or not photo.filename:
        raise ValueError("Seleccioná una foto para cargar la biometría.")
    if not allowed_file(photo.filename):
        raise ValueError("La foto debe ser JPG o PNG.")

    UPLOADS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    photo_path = UPLOADS_DIR / f"{employee_id}_{stamp}_{secure_filename(photo.filename)}"
    try:
        photo.save(photo_path)
        encoding = encoding_from_image(str(photo_path))
    except Exception:
        if photo_path.exists():
            photo_path.unlink()
        raise

    with get_connection() as db:
        db.execute(
            """INSERT INTO biometric_profiles (employee_id, face_encoding, source_image_path)
               VALUES (?, ?, ?)
               ON CONFLICT(employee_id) DO UPDATE SET
                 face_encoding = excluded.face_encoding,
                 source_image_path = excluded.source_image_path,
                 enrolled_at = CURRENT_TIMESTAMP""",
            (employee_id, encoding, str(photo_path.relative_to(BASE_DIR))),
        )


@app.get("/")
def dashboard():
    metrics = {
        "employees": query_one("SELECT COUNT(*) AS value FROM employees")["value"],
        "active": query_one("SELECT COUNT(*) AS value FROM employees WHERE status = 'active'")["value"],
        "enrolled": query_one("SELECT COUNT(*) AS value FROM biometric_profiles WHERE face_encoding IS NOT NULL")["value"],
    }
    logs = query_all(
        """SELECT access_logs.*, employees.full_name FROM access_logs
           LEFT JOIN employees ON employees.id = access_logs.employee_id
           ORDER BY access_logs.id DESC LIMIT 8"""
    )
    return render_template("dashboard.html", metrics=metrics, logs=logs)


@app.get("/employees")
def employees():
    rows = query_all(
        """SELECT employees.*, biometric_profiles.id AS biometric_id
           FROM employees LEFT JOIN biometric_profiles ON biometric_profiles.employee_id = employees.id
           ORDER BY employees.full_name"""
    )
    return render_template("employees.html", employees=rows)


@app.route("/employees/new", methods=["GET", "POST"])
def new_employee():
    if request.method == "GET":
        return render_template("employee_form.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip() or None
    status = request.form.get("status", "active")
    photo = request.files.get("photo")
    if not full_name:
        flash("El nombre completo es obligatorio.", "error")
        return redirect(url_for("new_employee"))
    if status not in {"active", "inactive"}:
        flash("Estado no valido.", "error")
        return redirect(url_for("new_employee"))

    try:
        with get_connection() as db:
            cursor = db.execute(
                "INSERT INTO employees (full_name, email, status) VALUES (?, ?, ?)",
                (full_name, email, status),
            )
            employee_id = cursor.lastrowid
        if photo and photo.filename:
            save_biometric_profile(employee_id, photo)
            flash("Personal registrado y biometria cargada.", "success")
        else:
            flash("Personal registrado. Falta cargar una foto para habilitar el reconocimiento.", "success")
        return redirect(url_for("employees"))
    except (ValueError, RecognitionUnavailable) as error:
        # Keep the employee record: it is useful for an administrator to complete enrollment later.
        flash(f"Personal creado, pero no se pudo cargar la biometria: {error}", "error")
        return redirect(url_for("employees"))
    except Exception as error:
        flash(f"No se pudo crear el empleado: {error}", "error")
        return redirect(url_for("new_employee"))


@app.post("/employees/<int:employee_id>/toggle-status")
def toggle_status(employee_id: int):
    employee = query_one("SELECT status FROM employees WHERE id = ?", (employee_id,))
    if employee is None:
        flash("Empleado inexistente.", "error")
    else:
        new_status = "inactive" if employee["status"] == "active" else "active"
        deactivated_at = datetime.now(timezone.utc).isoformat() if new_status == "inactive" else None
        with get_connection() as db:
            db.execute("UPDATE employees SET status = ?, deactivated_at = ? WHERE id = ?", (new_status, deactivated_at, employee_id))
        flash(f"Estado actualizado a {'Activo' if new_status == 'active' else 'Inactivo'}.", "success")
    return redirect(url_for("employees"))


@app.route("/employees/<int:employee_id>/enroll", methods=["GET", "POST"])
def enroll_employee(employee_id: int):
    employee = query_one("SELECT * FROM employees WHERE id = ?", (employee_id,))
    if employee is None:
        flash("Empleado inexistente.", "error")
        return redirect(url_for("employees"))
    if request.method == "GET":
        return render_template("enroll.html", employee=employee)

    try:
        save_biometric_profile(employee_id, request.files.get("photo"))
        flash("Biometría facial cargada correctamente.", "success")
        return redirect(url_for("employees"))
    except (ValueError, RecognitionUnavailable) as error:
        flash(f"No se pudo cargar la biometría: {error}", "error")
        return redirect(url_for("enroll_employee", employee_id=employee_id))


@app.route("/access", methods=["GET", "POST"])
def access():
    decision = None
    if request.method == "POST":
        snapshot = request.form.get("snapshot", "")
        try:
            photo = request.files.get("photo")
            if photo and photo.filename:
                if not allowed_file(photo.filename):
                    raise ValueError("La foto debe ser JPG o PNG.")
                image_bytes = photo.read()
            elif snapshot.startswith("data:image/") and "," in snapshot:
                image_bytes = base64.b64decode(snapshot.split(",", 1)[1])
            else:
                raise ValueError("Captura o carga una imagen antes de verificar.")
            profiles = query_all(
                """SELECT biometric_profiles.face_encoding, employees.id AS employee_id, employees.full_name
                   FROM biometric_profiles JOIN employees ON employees.id = biometric_profiles.employee_id
                   WHERE employees.status = 'active' AND biometric_profiles.face_encoding IS NOT NULL"""
            )
            employee_id, distance = find_match(image_bytes, profiles)
            if employee_id is None:
                write_access_log(None, "denied", "Rostro no identificado o no autorizado")
                decision = {"result": "denied", "message": "Acceso denegado", "distance": distance}
            else:
                employee = query_one("SELECT full_name FROM employees WHERE id = ?", (employee_id,))
                write_access_log(employee_id, "allowed", "Reconocimiento facial validado")
                decision = {"result": "allowed", "message": f"Acceso permitido: {employee['full_name']}", "distance": distance}
        except (ValueError, RecognitionUnavailable) as error:
            write_access_log(None, "denied", str(error))
            decision = {"result": "denied", "message": str(error), "distance": None}
    return render_template("access.html", decision=decision)


if __name__ == "__main__":
    initialize_database()
    app.run(host=os.environ.get("APP_HOST", "127.0.0.1"), port=5000, debug=True)
