"""Panel Flask: formularios y respuestas HTTP; las reglas están en services.py."""
from __future__ import annotations

import base64
import binascii
import csv
import os
import secrets
from io import BytesIO, StringIO
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for

from attendance_log import DEFAULT_CSV, FIELDS
from database import DATABASE_PATH, EmployeeRepository
from services import AttendanceDecision, AttendanceService


def create_app(config=None):
    """Crear una aplicación con rutas de datos configurables y aislables en pruebas."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        DATABASE_PATH=DATABASE_PATH,
        ATTENDANCE_CSV=DEFAULT_CSV,
        FACE_TOLERANCE=0.6,
    )
    if config:
        app.config.update(config)
    repository = EmployeeRepository(app.config["DATABASE_PATH"])
    service = AttendanceService(repository, app.config["ATTENDANCE_CSV"], app.config["FACE_TOLERANCE"])
    app.extensions["attendance_service"] = service

    @app.context_processor
    def form_token():
        return {"csrf_token": session.setdefault("csrf_token", secrets.token_hex(32))}

    @app.before_request
    def validate_form_token():
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            received = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected.encode(), received.encode()):
                abort(400, "El formulario venció. Volvé a cargar la página.")

    @app.errorhandler(413)
    def upload_too_large(error):
        return render_template("error.html", message="La imagen supera el límite de 5 MB."), 413

    @app.errorhandler(400)
    def invalid_request(error):
        return render_template("error.html", message=error.description), 400

    def photo_bytes():
        photo = request.files.get("photo")
        if photo and photo.filename:
            if Path(photo.filename).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                raise ValueError("La foto debe ser JPG o PNG.")
            return photo.read()
        snapshot = request.form.get("snapshot", "")
        if snapshot.startswith("data:image/") and "," in snapshot:
            try:
                return base64.b64decode(snapshot.split(",", 1)[1], validate=True)
            except binascii.Error as error:
                raise ValueError("La captura de cámara es inválida.") from error
        raise ValueError("Seleccioná una foto o capturá una imagen.")

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html", metrics=repository.metrics(), logs=repository.recent_accesses())

    @app.get("/employees")
    def employees():
        return render_template("employees.html", employees=repository.list_employees())

    @app.route("/employees/new", methods=["GET", "POST"])
    def new_employee():
        if request.method == "POST":
            try:
                employee_id = service.create_employee(
                    request.form.get("full_name", ""), request.form.get("email", ""),
                    request.form.get("status", "active"),
                )
            except ValueError as error:
                flash(str(error), "error")
                return render_template("employee_form.html"), 400
            # El alta de personal es independiente: se puede completar la foto después.
            photo = request.files.get("photo")
            if photo and photo.filename:
                try:
                    service.enroll(employee_id, photo_bytes())
                    flash("Empleado registrado y foto cargada.", "success")
                except (ValueError, RuntimeError, OSError) as error:
                    flash(f"Empleado creado; falta completar su foto: {error}", "error")
            else:
                flash("Empleado creado. Cargá su foto para habilitar el reconocimiento.", "success")
            return redirect(url_for("employees"))
        return render_template("employee_form.html")

    @app.post("/employees/<int:employee_id>/toggle-status")
    def toggle_status(employee_id):
        if repository.get_employee(employee_id) is None:
            abort(404)
        repository.toggle_status(employee_id)
        flash("Estado del empleado actualizado.", "success")
        return redirect(url_for("employees"))

    @app.route("/employees/<int:employee_id>/enroll", methods=["GET", "POST"])
    def enroll_employee(employee_id):
        employee = repository.get_employee(employee_id)
        if employee is None:
            abort(404)
        if request.method == "POST":
            try:
                service.enroll(employee_id, photo_bytes())
            except (ValueError, RuntimeError, OSError) as error:
                flash(f"No se pudo cargar la foto: {error}", "error")
                return render_template("enroll.html", employee=employee), 400
            flash("Foto facial actualizada.", "success")
            return redirect(url_for("employees"))
        return render_template("enroll.html", employee=employee)

    @app.route("/access", methods=["GET", "POST"])
    def access():
        decision = None
        if request.method == "POST":
            try:
                decision = service.verify(photo_bytes())
            except (ValueError, RuntimeError, OSError) as error:
                repository.log_access(None, "denied", str(error))
                decision = AttendanceDecision("denied", str(error))
        return render_template("access.html", decision=decision)

    @app.get("/attendance")
    def attendance():
        date = request.args.get("fecha", "")
        try:
            rows = service.attendance(date)
        except (ValueError, OSError) as error:
            flash(f"No se pudo consultar el registro: {error}", "error")
            rows = []
        return render_template("attendance.html", rows=list(reversed(rows)), date=date)

    @app.get("/attendance.csv")
    def download_attendance():
        try:
            rows = service.attendance(request.args.get("fecha"))
        except (ValueError, OSError) as error:
            flash(f"No se pudo descargar el registro: {error}", "error")
            return redirect(url_for("attendance"))
        text = StringIO(newline="")
        writer = csv.DictWriter(text, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        return send_file(BytesIO(text.getvalue().encode("utf-8-sig")), mimetype="text/csv",
                         as_attachment=True, download_name="asistencias.csv")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
