import os
import json
import tempfile
import unittest

import netCDF4 as nc
import numpy as np
import polanalyser as pa

import calibration
import geometric_correction
import look_vectors
import view_geometry


FIXTURE_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "fixtures", "calibration_standins"
)


class RawCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

    def _write_capture(self, path, frames, exposure=10000, gain=0, status=None):
        with nc.Dataset(path, "w") as dataset:
            if status is not None:
                dataset.calibration_data_status = status
            dataset.createDimension("time", len(frames))
            dataset.createDimension("H_pixel", 2)
            dataset.createDimension("V_pixel", 2)
            raw = dataset.createVariable(
                "Raw_Signal", "u1", ("time", "H_pixel", "V_pixel")
            )
            raw[:] = frames
            exposure_variable = dataset.createVariable("Detector_Exposure_Time", "i4", ("time",))
            exposure_variable[:] = exposure
            gain_variable = dataset.createVariable("Detector_Gain", "f4", ("time",))
            gain_variable[:] = gain

    def test_computes_solar_weighted_effective_wavelength(self):
        wavelength = np.array([400, 500, 600], dtype=np.float64)
        effective = calibration.effective_wavelength_um(
            wavelength,
            np.ones(3),
            wavelength,
            np.ones(3),
        )
        self.assertAlmostEqual(effective, 0.5)

    def test_builds_and_applies_dark_and_flat_field_maps(self):
        dark_path = os.path.join(self.temporary_directory.name, "dark.nc")
        flat_path = os.path.join(self.temporary_directory.name, "flat.nc")
        calibration_path = os.path.join(self.temporary_directory.name, "calibration.npz")
        self._write_capture(
            dark_path,
            np.array([[[2, 2], [2, 2]], [[2, 2], [2, 2]]], dtype=np.uint8),
        )
        self._write_capture(
            flat_path,
            np.array([[[22, 12], [22, 12]], [[22, 12], [22, 12]]], dtype=np.uint8),
        )

        calibration.build_raw_calibration(dark_path, flat_path, calibration_path)
        bundle = calibration.load_raw_calibration(calibration_path)
        corrected = calibration.apply_raw_calibration(
            np.array([[12, 12], [12, 12]], dtype=np.uint8),
            bundle,
            exposure_time_us=10000,
            gain_db=0,
        )
        np.testing.assert_allclose(corrected, [[7.5, 15], [7.5, 15]])

    def test_rejects_capture_settings_that_do_not_match(self):
        dark_path = os.path.join(self.temporary_directory.name, "dark.nc")
        flat_path = os.path.join(self.temporary_directory.name, "flat.nc")
        self._write_capture(dark_path, np.ones((1, 2, 2), dtype=np.uint8), exposure=10000)
        self._write_capture(flat_path, np.full((1, 2, 2), 20, dtype=np.uint8), exposure=20000)

        with self.assertRaisesRegex(ValueError, "identical exposure and gain"):
            calibration.build_raw_calibration(
                dark_path, flat_path, os.path.join(self.temporary_directory.name, "cal.npz")
            )

    def test_refuses_synthetic_captures_for_raw_calibration(self):
        with self.assertRaisesRegex(ValueError, "marked synthetic"):
            calibration.build_raw_calibration(
                os.path.join(FIXTURE_DIRECTORY, "synthetic_dark_capture.nc"),
                os.path.join(FIXTURE_DIRECTORY, "synthetic_flat_capture.nc"),
                os.path.join(self.temporary_directory.name, "cal.npz"),
            )

    def test_refuses_synthetic_raw_calibration_bundle(self):
        with self.assertRaisesRegex(ValueError, "Synthetic raw calibration"):
            calibration.load_raw_calibration(
                os.path.join(FIXTURE_DIRECTORY, "synthetic_raw_calibration.npz")
            )

    def test_refuses_synthetic_stokes_profile(self):
        with self.assertRaisesRegex(ValueError, "Synthetic calibration profiles"):
            calibration.load_grasp_calibration(
                os.path.join(FIXTURE_DIRECTORY, "synthetic_grasp_calibration.json")
            )

    def test_loads_measured_stokes_calibration_fields(self):
        profile_path = os.path.join(self.temporary_directory.name, "stokes.json")
        channels = {}
        for channel, wavelength in zip(("blue", "green", "red"), (0.45, 0.55, 0.65)):
            channels[channel] = {
                "wavelength_um": wavelength,
                "reduced_radiance_per_dn": 0.01,
                "dark_stokes_dn": {"I": 1.0, "Q": 0.2, "U": -0.1},
            }
        with open(profile_path, "w", encoding="utf-8") as profile_file:
            json.dump(
                {
                    "format": "LHMP_GRASP_CALIBRATION_V1",
                    "land_percent": 100,
                    "channels": channels,
                },
                profile_file,
            )

        loaded = calibration.load_grasp_calibration(profile_path)
        self.assertEqual(loaded["channels"]["green"]["wavelength_um"], 0.55)
        self.assertEqual(loaded["channels"]["blue"]["dark_stokes_dn"]["Q"], 0.2)


class StokesRotationTests(unittest.TestCase):
    def test_polanalyser_and_rotation_recover_known_linear_states(self):
        analyzer_angles = np.deg2rad([0, 45, 90, 135])
        target_axis_rotation = 17.0
        for polarization_angle in (0.0, 45.0, 90.0, 135.0):
            stokes = np.array(
                [
                    1.0,
                    np.cos(np.deg2rad(2.0 * polarization_angle)),
                    np.sin(np.deg2rad(2.0 * polarization_angle)),
                ]
            )
            analyzer_intensities = np.array(
                [
                    (pa.polarizer(angle)[:3, :3] @ stokes)[0]
                    for angle in analyzer_angles
                ]
            )

            measured_stokes = pa.calcStokes(analyzer_intensities, analyzer_angles)
            q_target, u_target = calibration.rotate_stokes_qu(
                measured_stokes[1],
                measured_stokes[2],
                target_axis_rotation,
            )
            expected_angle = np.deg2rad(
                2.0 * (polarization_angle - target_axis_rotation)
            )

            np.testing.assert_allclose(measured_stokes, stokes, atol=1e-12)
            np.testing.assert_allclose(
                [q_target, u_target],
                [np.cos(expected_angle), np.sin(expected_angle)],
                atol=1e-12,
            )

    def test_rotates_stokes_axes_with_expected_sign_and_preserves_magnitude(self):
        q, u = calibration.rotate_stokes_qu(1.0, 0.0, 45.0)

        self.assertAlmostEqual(q, 0.0, places=12)
        self.assertAlmostEqual(u, -1.0, places=12)
        self.assertAlmostEqual(np.hypot(q, u), 1.0, places=12)

    def test_broadcasts_pixel_angles_and_preserves_identity(self):
        q, u = calibration.rotate_stokes_qu(
            np.array([0.3, 0.3]),
            np.array([0.4, 0.4]),
            np.array([0.0, 45.0]),
        )

        np.testing.assert_allclose(q, [0.3, 0.4], atol=1e-12)
        np.testing.assert_allclose(u, [0.4, -0.3], atol=1e-12)

    def test_rejects_nonfinite_reference_axis_angle(self):
        with self.assertRaisesRegex(ValueError, "angle must be finite"):
            calibration.rotate_stokes_qu(1.0, 0.0, np.nan)


class GeometricCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

    def test_csv_round_trip_preserves_intrinsics_and_distortion(self):
        expected_matrix = np.array(
            [[1200.0, 0.0, 640.0], [0.0, 1190.0, 480.0], [0.0, 0.0, 1.0]]
        )
        output_path = os.path.join(self.temporary_directory.name, "camera.csv")
        geometric_correction.write_calibration_csv(
            {
                "camera_matrix": expected_matrix,
                "distortion_coefficients": np.array([0.1, -0.02, 0.001, 0.002, 0.0]),
                "image_width_px": 1280,
                "image_height_px": 960,
                "rms_reprojection_error_px": 0.25,
                "checkerboard_columns": 9,
                "checkerboard_rows": 6,
                "square_size": 1.0,
                "accepted_images": ["capture.png"],
                "rotation_vectors": [[0.0, 0.0, 0.0]],
                "translation_vectors": [[1.0, 2.0, 3.0]],
                "per_view_rms_reprojection_error_px": [0.2],
            },
            output_path,
        )

        loaded = calibration.load_geometric_calibration(output_path)
        np.testing.assert_allclose(loaded["camera_matrix"], expected_matrix)
        np.testing.assert_allclose(
            loaded["distortion_coefficients"], [0.1, -0.02, 0.001, 0.002, 0.0]
        )
        self.assertEqual(loaded["image_width_px"], 1280)

    def test_calibration_rejects_empty_image_list(self):
        with self.assertRaisesRegex(ValueError, "No geometric calibration images"):
            geometric_correction.calibrate_camera([])

    def test_camera_to_imu_transform_points_upward_boresight_to_zenith(self):
        camera_to_imu = np.array(
            [[-1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]
        )
        view_zenith, _ = view_geometry.run(
            0.0,
            0.0,
            0.0,
            camera_to_imu_rotation=camera_to_imu,
        )
        self.assertAlmostEqual(view_zenith, 0.0)

    def test_undistorted_look_vector_center_is_camera_boresight(self):
        vectors = look_vectors.run(
            100.0,
            100.0,
            1.0,
            1.0,
            3,
            3,
            distortion_coefficients=np.zeros(5),
        )
        np.testing.assert_allclose(vectors[1, 1], [0.0, 1.0, 0.0])

    def test_loads_only_measured_camera_to_imu_rotations(self):
        profile_path = os.path.join(self.temporary_directory.name, "camera_imu.json")
        rotation = [[-1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]
        with open(profile_path, "w", encoding="utf-8") as profile_file:
            json.dump(
                {
                    "format": "LHMP_CAMERA_IMU_CALIBRATION_V1",
                    "calibration_data_status": "measured",
                    "rotation_camera_to_imu": rotation,
                },
                profile_file,
            )
        np.testing.assert_allclose(
            calibration.load_camera_imu_calibration(profile_path), rotation
        )

        with self.assertRaisesRegex(ValueError, "must be measured and validated"):
            calibration.load_camera_imu_calibration(
                os.path.join(FIXTURE_DIRECTORY, "camera_imu_step_approx.json")
            )


if __name__ == "__main__":
    unittest.main()
