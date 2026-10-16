from __future__ import annotations

import csv
import gc
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, Mock

import cv2
import numpy as np

import attendance_log as log
import face_recognition_engine as engine
import asistencia
import comparar_rostros


class AttendanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="asistencia-test-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tildes_á" / "ingresos.csv"
        self.today = datetime(2026, 10, 16, 9, 15, 30)

    def record(self, identity="1", name="Ana", moment=None):
        return log.record_attendance(identity, name, self.path, now=moment or self.today)

    def test_records_name_date_time_and_header(self):
        self.assertTrue(self.record())
        row, = log.read_attendance(self.path)
        self.assertEqual(row, dict(empleado_id="1", nombre="Ana", fecha="2026-10-16", hora="09:15:30", origen="webcam"))

    def test_duplicate_day_preserves_first_time(self):
        self.record()
        self.assertFalse(self.record(moment=datetime(2026, 10, 16, 13, 0)))
        self.assertEqual(log.read_attendance(self.path)[0]["hora"], "09:15:30")
        self.assertEqual(len(log.read_attendance(self.path)), 1)

    def test_next_day_registers_again(self):
        self.record()
        self.assertTrue(self.record(moment=datetime(2026, 10, 17, 8, 0)))
        self.assertEqual(len(log.read_attendance(self.path)), 2)

    def test_same_name_different_ids_and_spanish_names(self):
        self.record("1", "Álvaro, Pérez")
        self.record("2", "Álvaro, Pérez")
        self.assertEqual([row["nombre"] for row in log.read_attendance(self.path)], ["Álvaro, Pérez"] * 2)

    def test_invalid_identity_does_not_create_csv(self):
        with self.assertRaises(ValueError):
            self.record(" ")
        self.assertFalse(self.path.exists())

    def test_unknown_csv_format_is_not_overwritten(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("nombre,hora\nAna,09:00\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.record()
        self.assertEqual(self.path.read_text(), "nombre,hora\nAna,09:00\n")

    def test_parallel_threads_only_register_once(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.record(), range(16)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(len(log.read_attendance(self.path)), 1)

    def test_parallel_processes_only_register_once(self):
        script = "from attendance_log import record_attendance; from datetime import datetime; import sys; record_attendance(1,'Ana',sys.argv[1],now=datetime(2026,10,16,9))"
        processes = [subprocess.Popen([sys.executable, "-B", "-c", script, str(self.path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(4)]
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(len(log.read_attendance(self.path)), 1)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.vector = np.zeros(128)
        self.face = engine.Face((1, 8, 8, 1), self.vector)
        self.image = np.zeros((10, 10, 3), dtype=np.uint8)

    def test_bgr_is_converted_to_rgb_before_detection(self):
        self.image[:] = (10, 20, 30)
        library = Mock()
        library.face_locations.return_value = [self.face.location]
        library.face_encodings.return_value = [self.vector]
        with patch.object(engine, "face_library", return_value=library):
            faces = engine.detect_faces(self.image)
        np.testing.assert_array_equal(library.face_locations.call_args.args[0][0, 0], [30, 20, 10])
        self.assertEqual(faces[0].location, self.face.location)

    def test_single_reference_rejects_zero_or_two_faces(self):
        for faces in ([], [self.face, self.face]):
            with self.subTest(count=len(faces)), patch.object(engine, "detect_faces", return_value=faces):
                with self.assertRaises(ValueError):
                    engine.single_face(self.image)

    def test_real_distance_api_selects_minimum_and_rejects_unknown(self):
        profiles = [engine.Profile("1", "Lejos", np.ones(128)), engine.Profile("2", "Cerca", self.vector)]
        index, distance = engine.best_match(self.vector, profiles)
        self.assertEqual(index, 1)
        self.assertEqual(distance, 0)
        index, distance = engine.best_match(np.full(128, 4.), profiles)
        self.assertIsNone(index)
        self.assertGreater(distance, .6)

    def test_tolerance_boundary_is_inclusive(self):
        candidate = np.zeros(128)
        candidate[0] = .6
        index, distance = engine.best_match(candidate, [engine.Profile("1", "Ana", self.vector)], .6)
        self.assertEqual(index, 0)
        self.assertAlmostEqual(distance, .6)

    def test_empty_profiles_and_invalid_tolerance(self):
        self.assertEqual(engine.best_match(self.vector, []), (None, None))
        with self.assertRaises(ValueError):
            engine.best_match(self.vector, [], 2)

    def test_image_path_with_accents_and_invalid_content(self):
        with tempfile.TemporaryDirectory(prefix="imagenes-") as folder:
            path = Path(folder) / "fotografía_ñ.png"
            engine.save_image(path, self.image)
            np.testing.assert_array_equal(engine.read_image(path), self.image)
            path.write_bytes(b"")
            with self.assertRaises(ValueError):
                engine.read_image(path)
            path.write_bytes(b"esto no es una imagen")
            with self.assertRaises(ValueError):
                engine.read_image(path)

    def test_folder_loads_names_and_skips_bad_references(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            engine.save_image(root / "Ana_Pérez.png", self.image)
            (root / "invalida.jpg").write_bytes(b"no imagen")
            (root / "ignorado.txt").write_text("texto")
            with patch.object(engine, "single_face", return_value=self.face):
                profiles, warnings = engine.load_profiles("carpeta", root)
            self.assertEqual([profile.name for profile in profiles], ["Ana Pérez"])
            self.assertEqual(profiles[0].employee_id, "archivo:ana_pérez")
            self.assertEqual(len(warnings), 1)

    def test_comparison_image_contains_both_panels(self):
        with patch.object(comparar_rostros, "read_image", return_value=np.zeros((80, 90, 3), dtype=np.uint8)), patch.object(comparar_rostros, "single_face", return_value=self.face):
            same, distance, image = comparar_rostros.compare_images("a", "b")
        self.assertTrue(same)
        self.assertEqual(distance, 0)
        self.assertEqual(image.shape[:2], (620, 1170))


class FrameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv = Path(self.temp.name) / "test.csv"
        self.image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.profiles = [engine.Profile("1", "Ana", np.zeros(128)), engine.Profile("2", "Bruno", np.ones(128))]

    def test_multiple_known_faces_and_daily_deduplication(self):
        faces = [engine.Face((10, 40, 40, 10), profile.encoding) for profile in self.profiles]
        with patch.object(asistencia, "detect_faces", return_value=faces):
            result, first = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
            _, second = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        self.assertEqual(len(log.read_attendance(self.csv)), 2)
        self.assertTrue(all(row["registered"] for row in first))
        self.assertFalse(any(row["registered"] for row in second))
        self.assertTrue(np.any(result != self.image))

    def test_unknown_face_never_records_attendance(self):
        with patch.object(asistencia, "detect_faces", return_value=[engine.Face((10, 40, 40, 10), np.full(128, 8.))]):
            _, rows = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        self.assertFalse(rows[0]["allowed"])
        self.assertFalse(self.csv.exists())

    def test_deactivated_profile_is_excluded(self):
        with patch.object(asistencia, "is_active", return_value=False), patch.object(asistencia, "detect_faces", return_value=[engine.Face((10, 40, 40, 10), np.zeros(128))]):
            _, rows = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        self.assertFalse(rows[0]["allowed"])
        self.assertFalse(self.csv.exists())

    def test_no_faces_do_not_record_attendance(self):
        with patch.object(asistencia, "detect_faces", return_value=[]):
            _, rows = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        self.assertEqual(rows, [])
        self.assertFalse(self.csv.exists())

    def test_camera_released_when_read_fails(self):
        capture = Mock()
        capture.isOpened.return_value = True
        capture.read.return_value = (False, None)
        with patch.object(asistencia, "load_profiles", return_value=(self.profiles, [])), patch.object(asistencia.cv2, "VideoCapture", return_value=capture):
            status = asistencia.main(["--sin-ventana", "--max-fotogramas", "2"])
        self.assertEqual(status, 1)
        capture.release.assert_called_once()

    def test_bounded_camera_loop_processes_frames_and_releases(self):
        capture = Mock()
        capture.isOpened.return_value = True
        capture.read.return_value = (True, self.image)
        with patch.object(asistencia, "load_profiles", return_value=(self.profiles, [])), patch.object(asistencia.cv2, "VideoCapture", return_value=capture), patch.object(asistencia, "detect_faces", return_value=[]) as detect:
            status = asistencia.main(["--sin-ventana", "--max-fotogramas", "4", "--cada", "3", "--csv", str(self.csv)])
        self.assertEqual(status, 0)
        self.assertEqual(capture.read.call_count, 4)
        self.assertEqual(detect.call_count, 2)
        capture.release.assert_called_once()


class WebTests(unittest.TestCase):
    def setUp(self):
        import app
        import database
        self.app_module = app
        self.database = database
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.csv = self.folder / "asistencias.csv"
        self.patches = [patch.object(database, "DATA_DIR", self.folder), patch.object(database, "DATABASE_PATH", self.folder / "test.db")]
        for item in self.patches:
            item.start()
        database.initialize_database()
        buffer = BytesIO()
        np.save(buffer, np.zeros(512), allow_pickle=False)
        with database.get_connection() as db:
            db.execute("INSERT INTO employees (id,full_name,status) VALUES (1,'Ana','active')")
            db.execute("INSERT INTO biometric_profiles (employee_id,face_encoding) VALUES (1,?)", (buffer.getvalue(),))
        db.close()
        self.previous_testing = app.app.config["TESTING"]
        self.previous_csv = app.app.config["ATTENDANCE_CSV"]
        app.app.config.update(TESTING=True, ATTENDANCE_CSV=self.csv)
        self.client = app.app.test_client()

    def tearDown(self):
        self.app_module.app.config.update(TESTING=self.previous_testing, ATTENDANCE_CSV=self.previous_csv)
        for item in self.patches:
            item.stop()
        gc.collect()
        self.temp.cleanup()

    def post_photo(self):
        return self.client.post("/access", data={"photo": (BytesIO(b"fake for mocked recognizer"), "foto.jpg")})

    def test_database_context_closes_and_rolls_back_on_error(self):
        connection = self.database.get_connection()
        with connection as db:
            db.execute("SELECT 1")
        import sqlite3
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.get_connection() as db:
                db.execute("INSERT INTO employees (full_name) VALUES ('Temporal')")
                db.execute("INSERT INTO employees (full_name,status) VALUES ('Invalido','otro')")
        self.assertEqual(self.database.query_one("SELECT COUNT(*) n FROM employees")["n"], 1)

    def test_database_profiles_reencode_photos_and_respect_status(self):
        path = self.folder / "imagen.png"
        engine.save_image(path, np.zeros((10, 10, 3), dtype=np.uint8))
        with self.database.get_connection() as db:
            db.execute("UPDATE biometric_profiles SET source_image_path = ?", (str(path),))
        vector = np.zeros(128)
        with patch.object(engine, "single_face", return_value=engine.Face((1, 8, 8, 1), vector)):
            profiles, warnings = engine.load_profiles("base", "no-se-usa")
        self.assertEqual(len(profiles), 1)
        self.assertFalse(warnings)
        self.assertEqual(profiles[0].encoding.shape, (128,))
        self.assertTrue(engine.is_active(profiles[0]))
        with self.database.get_connection() as db:
            db.execute("UPDATE employees SET status='inactive'")
        self.assertFalse(engine.is_active(profiles[0]))
        self.assertEqual(engine.load_profiles("base", "no-se-usa"), ([], []))

    def test_web_allowed_records_once_and_downloads_utf8_csv(self):
        with patch.object(self.app_module, "find_match", return_value=(1, .1)):
            self.assertEqual(self.post_photo().status_code, 200)
            self.assertIn("Ya registraste".encode(), self.post_photo().data)
        self.assertEqual(len(log.read_attendance(self.csv)), 1)
        self.assertEqual(self.database.query_one("SELECT COUNT(*) n FROM access_logs")["n"], 2)
        self.assertIn(b"Ana", self.client.get("/attendance").data)
        download = self.client.get("/attendance.csv")
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.data.startswith(b"\xef\xbb\xbf"))
        self.assertIn("attachment", download.headers["Content-Disposition"])

    def test_web_denied_does_not_record_attendance(self):
        with patch.object(self.app_module, "find_match", return_value=(None, .9)):
            self.assertEqual(self.post_photo().status_code, 200)
        self.assertFalse(self.csv.exists())
        self.assertEqual(self.database.query_one("SELECT result FROM access_logs")["result"], "denied")

    def test_web_excludes_inactive_profiles(self):
        with self.database.get_connection() as db:
            db.execute("UPDATE employees SET status='inactive'")
        db.close()
        with patch.object(self.app_module, "find_match", return_value=(None, None)) as match:
            self.post_photo()
        self.assertEqual(len(match.call_args.args[1]), 0)
        self.assertFalse(self.csv.exists())

    def test_missing_csv_download_redirects(self):
        self.assertEqual(self.client.get("/attendance.csv").status_code, 302)
        self.assertEqual(self.client.get("/attendance").status_code, 200)

    def test_write_error_never_claims_attendance_saved(self):
        with patch.object(self.app_module, "find_match", return_value=(1, .1)), patch.object(self.app_module, "record_attendance", side_effect=OSError("disco no disponible")):
            response = self.post_photo()
        self.assertNotIn(b"Asistencia registrada.", response.data)
        self.assertEqual(self.database.query_one("SELECT result FROM access_logs")["result"], "denied")


if __name__ == "__main__":
    unittest.main()
