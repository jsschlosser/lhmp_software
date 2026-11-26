import os
import tempfile
import unittest
from unittest import mock

import netCDF4 as nc

import grasp_workflow


class GraspWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.settings_path = os.path.join(self.temporary_directory.name, "settings.yml")
        self.input_path = os.path.join(self.temporary_directory.name, "input.nc")
        self.output_path = os.path.join(self.temporary_directory.name, "result.nc")
        with open(self.settings_path, "w", encoding="utf-8") as settings_file:
            settings_file.write("retrieval:\n    mode: inversion\n")

    def test_runs_grasp_with_sdata_input_and_netcdf_tile_output(self):
        def fake_run(command, **kwargs):
            output_argument = next(
                argument for argument in command if argument.startswith("output.tile.stream=")
            )
            output_path = output_argument.split("=", 1)[1]
            with nc.Dataset(output_path, "w") as dataset:
                dataset.createDimension("pixel", 1)
                dataset.createVariable("aod", "f4", ("pixel",))[:] = [0.2]
            return mock.Mock(returncode=0)

        with (
            mock.patch.object(grasp_workflow, "_resolve_executable", return_value="grasp"),
            mock.patch.object(
                grasp_workflow.netcdf_to_grasp,
                "convert_nc_to_grasp",
                return_value="input.sdat",
            ),
            mock.patch.object(grasp_workflow.subprocess, "run", side_effect=fake_run) as run,
        ):
            result = grasp_workflow.run_one(
                self.input_path,
                self.output_path,
                self.settings_path,
            )

        self.assertEqual(result, self.output_path)
        command = run.call_args.args[0]
        self.assertIn("input.driver=sdata", command)
        self.assertTrue(any(value.startswith("input.file=") for value in command))
        self.assertIn("output.tile.function=netcdf", command)
        with nc.Dataset(self.output_path, "r") as dataset:
            self.assertAlmostEqual(float(dataset.variables["aod"][0]), 0.2, places=6)

    def test_reports_grasp_failure_without_publishing_output(self):
        with (
            mock.patch.object(grasp_workflow, "_resolve_executable", return_value="grasp"),
            mock.patch.object(
                grasp_workflow.netcdf_to_grasp,
                "convert_nc_to_grasp",
                return_value="input.sdat",
            ),
            mock.patch.object(
                grasp_workflow.subprocess,
                "run",
                return_value=mock.Mock(returncode=2),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "status 2"):
                grasp_workflow.run_one(
                    self.input_path,
                    self.output_path,
                    self.settings_path,
                )
        self.assertFalse(os.path.exists(self.output_path))


if __name__ == "__main__":
    unittest.main()
