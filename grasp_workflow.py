"""Convert calibrated LHMP L1 data, run GRASP, and retain its NetCDF output."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import netCDF4 as nc

import netcdf_to_grasp


def _resolve_executable(executable):
    resolved = shutil.which(executable)
    if resolved is None and os.path.isfile(executable):
        resolved = os.path.abspath(executable)
    if resolved is None:
        raise ValueError(f"GRASP executable not found: {executable}")
    return resolved


def _build_command(executable, settings_path, sdata_path, output_path):
    """Build GRASP's documented settings-file plus dot-syntax CLI invocation."""
    return [
        executable,
        os.path.abspath(settings_path),
        "input.driver=sdata",
        f"input.file={os.path.abspath(sdata_path)}",
        "output.tile.function=netcdf",
        f"output.tile.stream={os.path.abspath(output_path)}",
    ]


def run_one(input_path, output_path, settings_path, grasp_executable="grasp", pixel_stride=128):
    """Run one calibrated L1 file and return the GRASP-produced NetCDF path."""
    settings_path = os.path.abspath(settings_path)
    if not os.path.isfile(settings_path):
        raise ValueError(f"GRASP settings file not found: {settings_path}")
    executable = _resolve_executable(grasp_executable)
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        raise ValueError(f"Refusing to overwrite existing retrieval output: {output_path}")

    with tempfile.TemporaryDirectory(prefix="lhmp-grasp-") as work_directory:
        sdata_path = os.path.join(work_directory, "input.sdat")
        netcdf_to_grasp.convert_nc_to_grasp(
            input_path,
            sdata_path,
            pixel_stride=pixel_stride,
        )
        file_descriptor, temporary_output = tempfile.mkstemp(
            prefix=os.path.basename(output_path) + ".",
            suffix=".tmp.nc",
            dir=os.path.dirname(output_path),
        )
        os.close(file_descriptor)
        os.remove(temporary_output)
        try:
            command = _build_command(
                executable,
                settings_path,
                sdata_path,
                temporary_output,
            )
            result = subprocess.run(
                command,
                cwd=os.path.dirname(settings_path),
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"GRASP exited with status {result.returncode}")
            if not os.path.isfile(temporary_output) or os.path.getsize(temporary_output) == 0:
                raise RuntimeError(
                    "GRASP completed without creating the requested NetCDF output. "
                    "Confirm this GRASP build includes the NetCDF tile-output function."
                )
            try:
                with nc.Dataset(temporary_output, "r"):
                    pass
            except OSError as error:
                raise RuntimeError(
                    f"GRASP output is not a readable NetCDF file: {temporary_output}"
                ) from error
            os.replace(temporary_output, output_path)
        finally:
            if os.path.exists(temporary_output):
                os.remove(temporary_output)
    return output_path


def run_directory(
    input_directory,
    output_directory,
    settings_path,
    grasp_executable="grasp",
    pixel_stride=128,
):
    """Run GRASP for each L1 NetCDF file, preserving one NetCDF result per input."""
    input_paths = sorted(
        os.path.join(input_directory, name)
        for name in os.listdir(input_directory)
        if name.lower().endswith(".nc")
    )
    if not input_paths:
        raise ValueError(f"No NetCDF files found in {input_directory}")
    os.makedirs(output_directory, exist_ok=True)
    outputs = []
    for input_path in input_paths:
        output_path = os.path.join(
            output_directory,
            os.path.splitext(os.path.basename(input_path))[0] + "_grasp.nc",
        )
        outputs.append(
            run_one(
                input_path,
                output_path,
                settings_path,
                grasp_executable=grasp_executable,
                pixel_stride=pixel_stride,
            )
        )
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Calibrated L1 NetCDF file or directory")
    parser.add_argument("--settings", required=True, help="GRASP YAML retrieval settings")
    parser.add_argument(
        "--grasp-executable",
        default="grasp",
        help="GRASP executable name or path (default: %(default)s)",
    )
    parser.add_argument("--output", required=True, help="NetCDF output file or directory")
    parser.add_argument("--pixel-stride", type=int, default=128)
    args = parser.parse_args(argv)

    try:
        if args.pixel_stride < 1:
            raise ValueError("--pixel-stride must be positive")
        if os.path.isdir(args.input):
            outputs = run_directory(
                args.input,
                args.output,
                args.settings,
                grasp_executable=args.grasp_executable,
                pixel_stride=args.pixel_stride,
            )
        else:
            outputs = [
                run_one(
                    args.input,
                    args.output,
                    args.settings,
                    grasp_executable=args.grasp_executable,
                    pixel_stride=args.pixel_stride,
                )
            ]
    except (OSError, ValueError, RuntimeError) as error:
        print(f"GRASP workflow failed: {error}", file=sys.stderr)
        return 1

    for path in outputs:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
