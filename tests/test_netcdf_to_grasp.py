import json
import os
import tempfile
import unittest

import netCDF4 as nc
import numpy as np

import netcdf_to_grasp


FIXTURE_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "fixtures", "calibration_standins"
)


class NetcdfToGraspTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.input_path = os.path.join(self.temporary_directory.name, "sample.nc")
        self.calibration_path = os.path.join(self.temporary_directory.name, "calibration.json")
        self.output_path = os.path.join(self.temporary_directory.name, "sample.sdat")
        self._write_input()
        self._write_calibration()

    def _write_input(self):
        with nc.Dataset(self.input_path, "w") as dataset:
            dataset.createDimension("time", 1)
            dataset.createDimension("H_pixel", 2)
            dataset.createDimension("V_pixel", 2)
            dataset.raw_spatial_calibration_applied = "dark subtraction and flat-field correction"

            time = dataset.createVariable("time", "i4", ("time",))
            time.units = "seconds after 2026-01-02 00:00:00 UTC."
            time[:] = [3600]

            for name in (
                "GPS_longitude",
                "GPS_latitude",
                "GPS_altitude",
                "solar_azimuth",
                "solar_altitude",
            ):
                variable = dataset.createVariable(name, "f4", ("time",))
                variable[:] = {
                    "GPS_longitude": -76.3,
                    "GPS_latitude": 37.0,
                    "GPS_altitude": 12.0,
                    "solar_azimuth": 180.0,
                    "solar_altitude": 45.0,
                }[name]

            for name in ("view_azimuth", "view_zenith"):
                variable = dataset.createVariable(
                    name, "f4", ("time", "H_pixel", "V_pixel")
                )
                variable[:] = 0 if name == "view_azimuth" else 45

            for channel_index, channel in enumerate(("blue", "green", "red")):
                for component, value in (("I", 10), ("Q", 2), ("U", 1)):
                    variable = dataset.createVariable(
                        f"{component}_{channel}",
                        "f4",
                        ("time", "H_pixel", "V_pixel"),
                    )
                    variable[:] = value + channel_index

    def _write_calibration(self):
        channels = {}
        for channel, wavelength in zip(("blue", "green", "red"), (0.45, 0.55, 0.65)):
            channels[channel] = {
                "wavelength_um": wavelength,
                "reduced_radiance_per_dn": 0.01,
                "dark_stokes_dn": {"I": 0, "Q": 0, "U": 0},
            }
        with open(self.calibration_path, "w", encoding="utf-8") as calibration_file:
            json.dump(
                {
                    "format": "LHMP_GRASP_CALIBRATION_V1",
                    "stokes_reference_frame": "grasp_scattering_plane",
                    "land_percent": 100,
                    "channels": channels,
                },
                calibration_file,
            )

    def test_writes_sdata_2_with_calibrated_reduced_stokes(self):
        netcdf_to_grasp.convert_nc_to_grasp(
            self.input_path,
            self.output_path,
            self.calibration_path,
            pixel_stride=1,
        )

        with open(self.output_path, "r", encoding="ascii") as output_file:
            lines = output_file.read().splitlines()
        self.assertEqual(lines[0], "SDATA version 2.0")
        self.assertEqual(lines[1], "2 2 1 : NX NY NT")
        self.assertEqual(
            lines[3],
            "4 2026-01-02T01:00:00Z 70000.0 0 0 : NPIXELS TIMESTAMP HOBS_m NSURF IFGAS",
        )
        pixel_fields = lines[4].split()
        self.assertEqual(pixel_fields[9], "3")
        self.assertEqual(pixel_fields[10:13], ["0.45", "0.55", "0.65"])
        self.assertIn("0.1", pixel_fields)
        self.assertIn("0.02", pixel_fields)
        self.assertIn("0.01", pixel_fields)

    def test_rejects_raw_only_file_before_creating_output(self):
        raw_path = os.path.join(self.temporary_directory.name, "raw.nc")
        with nc.Dataset(raw_path, "w") as dataset:
            dataset.createDimension("time", 1)
            dataset.createDimension("H_pixel", 2)
            dataset.createDimension("V_pixel", 2)
            dataset.createVariable(
                "Raw_Signal", "u1", ("time", "H_pixel", "V_pixel")
            )[:] = 0

        with self.assertRaisesRegex(ValueError, "raw-only or incomplete"):
            netcdf_to_grasp.convert_directory(
                self.temporary_directory.name,
                os.path.join(self.temporary_directory.name, "output"),
                self.calibration_path,
            )
        self.assertFalse(os.path.exists(os.path.join(self.temporary_directory.name, "output")))

    def test_rejects_synthetic_calibration_profile(self):
        with self.assertRaisesRegex(ValueError, "Synthetic calibration profiles"):
            netcdf_to_grasp.load_grasp_calibration(
                os.path.join(FIXTURE_DIRECTORY, "synthetic_grasp_calibration.json")
            )


if __name__ == "__main__":
    unittest.main()
