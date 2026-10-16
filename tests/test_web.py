"""Pruebas de integración del panel y la webcam, con reconocimiento simulado."""
from __future__ import annotations

import base64
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

import asistencia
import attendance_log as log
import services
from app import create_app
from database import get_connection
from face_recognition_engine import Face


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.app = create_app({
            "TESTING": True, "SECRET_KEY": "test-key",
            "DATABASE_PATH": root / "test.db", "ATTENDANCE_CSV": root / "asistencias.csv",
        })
        self.client = self.app.test_client()
        self.service = self.app.extensions["attendance_service"]
        self.repository = self.service.repository
        self.csv = self.service.csv_path
        self.image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.photo = cv2.imencode(".png", self.image)[1].tobytes()
        self.face = Face((10, 40, 40, 10), np.zeros(128))
        self.client.get("/")
        with self.client.session_transaction() as session:
            self.token = session["csrf_token"]

    def post(self, route, data=None):
        response = self.client.post(route, data={"csrf_token": self.token, **(data or {})})
        self.addCleanup(response.close)
        self.addCleanup(response.request.input_stream.close)
        return response

    def employee(self, name="Ana", email="", status="active"):
        employee_id = self.service.create_employee(name, email, status)
        with patch.object(services, "single_face", return_value=self.face):
            self.service.enroll(employee_id, self.photo)
        return employee_id

    def verify(self):
        return self.post("/access", {"photo": (BytesIO(self.photo), "foto.png")})

    def test_pages_render_with_empty_database(self):
        for route in ("/", "/employees", "/employees/new", "/access", "/attendance"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200)
        self.assertEqual(self.repository.metrics(), dict(employees=0, active=0, enrolled=0))

    def test_csrf_rejects_missing_and_invalid_tokens(self):
        for token in ("", "incorrecto", "á"):
            response = self.client.post("/employees/new", data={"full_name": "Ana", "csrf_token": token})
            self.assertEqual(response.status_code, 400)
        self.assertFalse(self.repository.list_employees())

    def test_create_employee_and_duplicate_email(self):
        response = self.post("/employees/new", {"full_name": "Ana", "email": "ana@empresa.test"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.repository.list_employees()[0]["full_name"], "Ana")
        response = self.post("/employees/new", {"full_name": "Otra Ana", "email": "ana@empresa.test"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(self.repository.list_employees()), 1)

    def test_bad_photo_keeps_employee_pending_without_invalid_biometry(self):
        response = self.post("/employees/new", {"full_name": "Ana", "photo": (BytesIO(b"invalida"), "foto.png")})
        self.assertEqual(response.status_code, 302)
        employee, = self.repository.list_employees()
        self.assertIsNone(employee["biometric_id"])
        self.assertIn(b"falta completar", self.client.get("/employees").data)

    def test_enrollment_uses_shared_engine_and_persists_vector(self):
        employee_id = self.service.create_employee("Ana", "", "active")
        with patch.object(services, "single_face", return_value=self.face):
            response = self.post(f"/employees/{employee_id}/enroll", {"photo": (BytesIO(self.photo), "foto.png")})
        self.assertEqual(response.status_code, 302)
        profile, = self.service.profiles()
        self.assertEqual(profile.employee_id, str(employee_id))
        np.testing.assert_array_equal(profile.encoding, self.face.encoding)
        self.assertEqual(self.client.get(f"/employees/{employee_id}/enroll").status_code, 200)

    def test_failed_reenrollment_preserves_previous_vector(self):
        employee_id = self.employee()
        response = self.post(f"/employees/{employee_id}/enroll", {"photo": (BytesIO(b"invalida"), "foto.jpg")})
        self.assertEqual(response.status_code, 400)
        np.testing.assert_array_equal(self.service.profiles()[0].encoding, self.face.encoding)

    def test_web_known_face_records_once_and_downloads_csv(self):
        self.employee()
        with patch.object(services, "single_face", return_value=self.face), patch.object(services, "best_match", return_value=(0, .1)):
            self.assertEqual(self.verify().status_code, 200)
            self.assertIn(b"Ya registraste", self.verify().data)
        self.assertEqual(len(log.read_attendance(self.csv)), 1)
        self.assertEqual(len(self.repository.recent_accesses()), 2)
        self.assertIn(b"Ana", self.client.get("/attendance").data)
        download = self.client.get("/attendance.csv")
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.data.startswith(b"\xef\xbb\xbf"))
        self.assertIn("attachment", download.headers["Content-Disposition"])

    def test_unknown_and_inactive_people_do_not_register(self):
        employee_id = self.employee()
        self.post(f"/employees/{employee_id}/toggle-status")
        self.assertEqual(self.service.profiles(), [])
        with patch.object(services, "single_face", return_value=self.face):
            self.assertIn(b"Persona no identificada", self.verify().data)
        self.assertFalse(Path(self.csv).exists())
        self.assertEqual(self.repository.recent_accesses()[0]["result"], "denied")

    def test_employee_deactivated_during_recognition_is_rechecked(self):
        employee_id = self.employee()
        profiles = self.service.profiles()
        self.repository.toggle_status(employee_id)
        with patch.object(self.service, "profiles", return_value=profiles), patch.object(services, "single_face", return_value=self.face), patch.object(services, "best_match", return_value=(0, .1)):
            self.assertIn(b"no est", self.verify().data)
        self.assertFalse(Path(self.csv).exists())

    def test_same_names_have_independent_attendance(self):
        self.employee("Ana")
        self.employee("Ana")
        for profile in self.service.profiles():
            self.assertTrue(self.service.register(profile, origin="web"))
        self.assertEqual(len(log.read_attendance(self.csv)), 2)

    def test_web_and_webcam_share_registration_and_status(self):
        employee_id = self.employee()
        with patch.object(services, "single_face", return_value=self.face), patch.object(services, "best_match", return_value=(0, .1)):
            self.verify()
        with patch.object(asistencia, "detect_faces", return_value=[self.face]), patch.object(asistencia, "best_match", return_value=(0, .1)):
            asistencia.process_frame(self.image, [], .6, self.csv, self.service)
        self.assertEqual(len(log.read_attendance(self.csv)), 1)
        self.repository.toggle_status(employee_id)
        with patch.object(asistencia, "detect_faces", return_value=[self.face]), patch.object(asistencia, "best_match", return_value=(None, None)) as match:
            asistencia.process_frame(self.image, [], .6, self.csv, self.service)
        self.assertEqual(match.call_args.args[1], [])

    def test_csv_failure_never_reports_success(self):
        self.employee()
        with patch.object(services, "single_face", return_value=self.face), patch.object(services, "best_match", return_value=(0, .1)), patch.object(services, "record_attendance", side_effect=OSError("disco no disponible")):
            response = self.verify()
        self.assertNotIn(b"Asistencia registrada", response.data)
        self.assertIn(b"disco no disponible", response.data)
        self.assertEqual(self.repository.recent_accesses()[0]["result"], "denied")

    def test_filter_and_download_use_same_date(self):
        employee_id = self.employee()
        log.record_attendance(employee_id, "Ana", self.csv, now=datetime(2026, 10, 16, 9))
        log.record_attendance(employee_id, "Ana", self.csv, now=datetime(2026, 10, 17, 10))
        page = self.client.get("/attendance?fecha=2026-10-16")
        self.assertIn(b"09:00:00", page.data)
        self.assertNotIn(b"10:00:00", page.data)
        download = self.client.get("/attendance.csv?fecha=2026-10-16")
        self.assertIn(b"2026-10-16", download.data)
        self.assertNotIn(b"2026-10-17", download.data)

    def test_invalid_snapshot_and_oversized_upload_are_handled(self):
        self.assertIn(b"inv", self.post("/access", {"snapshot": "data:image/jpeg;base64,***"}).data)
        response = self.post("/access", {"photo": (BytesIO(b"x" * (6 * 1024 * 1024)), "foto.png")})
        self.assertEqual(response.status_code, 413)

    def test_browser_snapshot_uses_same_verification_flow(self):
        self.employee()
        snapshot = "data:image/png;base64," + base64.b64encode(self.photo).decode()
        with patch.object(services, "single_face", return_value=self.face), patch.object(services, "best_match", return_value=(0, .1)):
            response = self.post("/access", {"snapshot": snapshot})
        self.assertIn(b"Asistencia registrada", response.data)

    def test_legacy_vectors_are_preserved_but_require_reenrollment(self):
        employee_id = self.service.create_employee("Anterior", "", "active")
        buffer = BytesIO()
        np.save(buffer, np.ones(512), allow_pickle=False)
        with get_connection(self.repository.path) as db:
            db.execute("INSERT INTO biometric_profiles (employee_id, face_encoding, encoding_model) VALUES (?, ?, ?)",
                       (employee_id, buffer.getvalue(), "insightface_512"))
        self.assertEqual(self.service.profiles(), [])
        self.assertIsNone(self.repository.list_employees()[0]["biometric_id"])
        with get_connection(self.repository.path) as db:
            self.assertEqual(db.execute("SELECT face_encoding FROM biometric_profiles").fetchone()[0], buffer.getvalue())

    def test_concurrent_daily_registration_only_writes_once(self):
        self.employee()
        profile, = self.service.profiles()
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda _: self.service.register(profile, origin="web"), range(8)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(len(log.read_attendance(self.csv)), 1)


if __name__ == "__main__":
    unittest.main()
