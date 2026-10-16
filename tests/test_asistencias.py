"""Pruebas sin webcam ni fotos personales; el motor facial se simula."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

import asistencia
import attendance_log as log
import comparar_rostros
import face_recognition_engine as engine


class AttendanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tildes_á" / "ingresos.csv"
        self.today = datetime(2026, 10, 16, 9, 15, 30)

    def record(self, name="Ana", moment=None):
        return log.record_attendance("archivo:" + name.casefold(), name, self.path, now=moment or self.today)

    def test_records_name_date_time_and_header(self):
        self.assertTrue(self.record())
        row, = log.read_attendance(self.path)
        self.assertEqual(row, dict(empleado_id="archivo:ana", nombre="Ana", fecha="2026-10-16", hora="09:15:30", origen="webcam"))

    def test_duplicate_day_preserves_first_time(self):
        self.record()
        self.assertFalse(self.record(moment=datetime(2026, 10, 16, 13, 0)))
        self.assertEqual(log.read_attendance(self.path), [dict(empleado_id="archivo:ana", nombre="Ana", fecha="2026-10-16", hora="09:15:30", origen="webcam")])

    def test_next_day_registers_again(self):
        self.record()
        self.assertTrue(self.record(moment=datetime(2026, 10, 17, 8, 0)))
        self.assertEqual(len(log.read_attendance(self.path)), 2)

    def test_multiple_employees_and_spanish_names(self):
        self.record("Álvaro, Pérez")
        self.record("Bruno")
        self.assertEqual([row["nombre"] for row in log.read_attendance(self.path)], ["Álvaro, Pérez", "Bruno"])

    def test_empty_name_does_not_create_csv(self):
        with self.assertRaises(ValueError):
            self.record(" ")
        self.assertFalse(self.path.exists())

    def test_unknown_csv_format_is_not_overwritten(self):
        self.path.parent.mkdir(parents=True)
        content = "nombre,hora\nAna,09:00\n"
        self.path.write_text(content, encoding="utf-8")
        with self.assertRaises(ValueError):
            self.record()
        self.assertEqual(self.path.read_text(), content)


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

    def test_minimum_distance_and_rejection(self):
        profiles = [engine.Profile("Lejos", np.ones(128)), engine.Profile("Cerca", self.vector)]
        library = Mock()
        library.face_distance.return_value = np.array([.8, .2])
        with patch.object(engine, "face_library", return_value=library):
            library.compare_faces.return_value = [True]
            self.assertEqual(engine.best_match(self.vector, profiles, .5), (1, .2))
            library.compare_faces.assert_called_once()
            self.assertEqual(library.compare_faces.call_args.kwargs["tolerance"], .5)
            np.testing.assert_array_equal(library.compare_faces.call_args.args[0][0], profiles[1].encoding)
            library.compare_faces.return_value = [False]
            self.assertEqual(engine.best_match(self.vector, profiles, .1), (None, .2))

    def test_empty_profiles_and_invalid_tolerance(self):
        self.assertEqual(engine.best_match(self.vector, []), (None, None))
        for tolerance in (0, -1, 2, float("nan")):
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                engine.best_match(self.vector, [], tolerance)

    def test_image_path_with_accents_and_invalid_content(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fotografía_ñ.png"
            path.write_bytes(cv2.imencode(".png", self.image)[1].tobytes())
            np.testing.assert_array_equal(engine.read_image(path), self.image)
            for content in (b"", b"esto no es una imagen"):
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    engine.read_image(path)

    def test_folder_loads_names_and_skips_bad_references(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "Ana_Pérez.png").write_bytes(cv2.imencode(".png", self.image)[1].tobytes())
            (root / "invalida.jpg").write_bytes(b"no imagen")
            (root / "ignorado.txt").write_text("texto")
            with patch.object(engine, "single_face", return_value=self.face):
                profiles, warnings = engine.load_profiles(root)
            self.assertEqual([profile.name for profile in profiles], ["Ana Pérez"])
            self.assertEqual(len(warnings), 1)

    def test_duplicate_employee_names_are_omitted(self):
        with tempfile.TemporaryDirectory() as folder:
            for filename in ("Ana_Perez.png", "Ana Perez.jpg"):
                (Path(folder) / filename).write_bytes(cv2.imencode(".png", self.image)[1].tobytes())
            with patch.object(engine, "single_face", return_value=self.face):
                profiles, warnings = engine.load_profiles(folder)
            self.assertEqual(len(profiles), 1)
            self.assertEqual(len(warnings), 1)

    def test_comparison_displays_both_panels_for_match_and_nonmatch(self):
        for match in (True, False):
            with self.subTest(match=match), patch.object(comparar_rostros, "read_image", return_value=np.zeros((80, 90, 3), dtype=np.uint8)), patch.object(comparar_rostros, "single_face", return_value=self.face), patch.object(comparar_rostros, "best_match", return_value=(0 if match else None, .2 if match else .8)):
                same, distance, image = comparar_rostros.compare_images("a", "b")
            self.assertEqual(same, match)
            self.assertEqual(distance, .2 if match else .8)
            self.assertEqual(image.shape[:2], (620, 1170))


class FrameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv = Path(self.temp.name) / "test.csv"
        self.image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.profiles = [engine.Profile("Ana", np.zeros(128)), engine.Profile("Bruno", np.ones(128))]

    def test_multiple_known_faces_and_daily_deduplication(self):
        faces = [engine.Face((10, 40, 40, 10), profile.encoding) for profile in self.profiles]
        with patch.object(asistencia, "detect_faces", return_value=faces), patch.object(asistencia, "best_match", side_effect=[(0, .1), (1, .1)] * 2):
            result = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
            asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        self.assertEqual([row["nombre"] for row in log.read_attendance(self.csv)], ["Ana", "Bruno"])
        self.assertTrue(np.any(result != self.image))

    def test_unknown_face_never_records_attendance(self):
        with patch.object(asistencia, "detect_faces", return_value=[engine.Face((10, 40, 40, 10), np.full(128, 8.))]), patch.object(asistencia, "best_match", return_value=(None, .9)):
            result = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        self.assertTrue(np.any(result != self.image))
        self.assertFalse(self.csv.exists())

    def test_no_faces_do_not_record_attendance(self):
        with patch.object(asistencia, "detect_faces", return_value=[]):
            result = asistencia.process_frame(self.image, self.profiles, .6, self.csv)
        np.testing.assert_array_equal(result, self.image)
        self.assertFalse(self.csv.exists())

    def test_camera_exit_and_errors_release_resources(self):
        scenarios = [(False, False, 1), (True, False, 1), (True, True, 0)]
        for opened, readable, expected in scenarios:
            with self.subTest(opened=opened, readable=readable):
                capture = Mock()
                capture.isOpened.return_value = opened
                capture.read.return_value = (readable, self.image if readable else None)
                with patch.object(asistencia, "load_profiles", return_value=(self.profiles, [])), patch.object(asistencia.cv2, "VideoCapture", return_value=capture), patch.object(asistencia, "process_frame", return_value=self.image), patch.object(asistencia.cv2, "imshow"), patch.object(asistencia.cv2, "waitKey", return_value=ord("q")), patch.object(asistencia.cv2, "destroyAllWindows") as close:
                    status = asistencia.main(["--fuente", "carpeta", "--csv", str(self.csv)])
                self.assertEqual(status, expected)
                capture.release.assert_called_once()
                close.assert_called_once()

    def test_empty_folder_does_not_open_camera(self):
        with patch.object(asistencia, "load_profiles", return_value=([], [])), patch.object(asistencia.cv2, "VideoCapture") as camera, patch.object(asistencia.cv2, "destroyAllWindows"):
            self.assertEqual(asistencia.main(["--fuente", "carpeta"]), 1)
        camera.assert_not_called()


if __name__ == "__main__":
    unittest.main()
