"""Convert calibrated LHMP Level 1 NetCDF files to GRASP SDATA 2.0."""

import argparse
from datetime import datetime, timedelta, timezone
import math
import os
import re
import sys

import netCDF4 as nc
import numpy as np


DEFAULT_INPUT_DIRECTORY = r"B:\Hampton_University\HU_Polarimetry_Lab\L1_data"
CHANNELS = ("blue", "green", "red")
STOKES_COMPONENTS = ("I", "Q", "U")
REDUCED_STOKES_VARIABLES = {
    f"{component}_{channel}_reduced"
    for channel in CHANNELS
    for component in STOKES_COMPONENTS
}
REQUIRED_VARIABLES = {
    "time",
    "GPS_longitude",
    "GPS_latitude",
    "GPS_altitude",
    "solar_azimuth",
    "solar_altitude",
    "view_azimuth",
    "view_zenith",
}.union(REDUCED_STOKES_VARIABLES)


def _read_l1_grasp_metadata(dataset, path):
    """Read calibration values already applied and recorded during L1 processing."""
    if not getattr(dataset, "radiometric_calibration_applied", "") or (
        str(dataset.radiometric_calibration_applied).lower() == "false"
    ):
        raise ValueError(
            f"{path} has no L1 radiometric calibration; rerun L1_file_save.run "
            "with stokes_calibration_path"
        )
    if getattr(dataset, "stokes_reference_frame", "") != "grasp_scattering_plane":
        raise ValueError(
            f"{path} Q/U values are not in GRASP's validated scattering-plane frame"
        )
    if getattr(dataset, "camera_intrinsics_calibration_status", "") != "checkerboard_calibrated":
        raise ValueError(f"{path} has no checkerboard camera intrinsic calibration")
    if getattr(dataset, "camera_to_imu_alignment_status", "") != "validated":
        raise ValueError(f"{path} has no validated camera-to-IMU alignment")

    try:
        land_percent = float(dataset.grasp_land_percent)
        channels = {}
        for channel in CHANNELS:
            variable = dataset.variables[f"I_{channel}_reduced"]
            wavelength_um = float(variable.wavelength_um)
            scale = float(variable.reduced_radiance_per_dn)
            channels[channel] = {
                "wavelength_um": wavelength_um,
                "reduced_radiance_per_dn": scale,
            }
            for component in ("Q", "U"):
                stokes_variable = dataset.variables[f"{component}_{channel}_reduced"]
                if not math.isclose(
                    float(stokes_variable.wavelength_um), wavelength_um, rel_tol=0.0, abs_tol=1e-12
                ) or not math.isclose(
                    float(stokes_variable.reduced_radiance_per_dn),
                    scale,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                ):
                    raise ValueError(f"{path} {component}/{channel} calibration differs from I")
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path} is missing L1 GRASP calibration metadata") from error
    if not math.isfinite(land_percent) or not 0 <= land_percent <= 100:
        raise ValueError(f"{path} has an invalid grasp_land_percent")
    if any(
        not math.isfinite(values["wavelength_um"])
        or values["wavelength_um"] <= 0
        or not math.isfinite(values["reduced_radiance_per_dn"])
        or values["reduced_radiance_per_dn"] <= 0
        for values in channels.values()
    ):
        raise ValueError(f"{path} has invalid L1 channel calibration values")
    wavelengths = [channels[channel]["wavelength_um"] for channel in CHANNELS]
    if any(right <= left for left, right in zip(wavelengths, wavelengths[1:])):
        raise ValueError(f"{path} channel wavelengths are not increasing")
    for name in REDUCED_STOKES_VARIABLES:
        if getattr(dataset.variables[name], "units", "") != "1":
            raise ValueError(f"{path} {name} must contain dimensionless reduced radiance")
    return {"land_percent": land_percent, "channels": channels}


def _validate_input_file(path, require_spatial_calibration):
    try:
        with nc.Dataset(path, "r") as dataset:
            missing = REQUIRED_VARIABLES.difference(dataset.variables)
            if missing:
                raise ValueError(
                    f"{path} is raw-only or incomplete; missing variables: "
                    f"{', '.join(sorted(missing))}"
                )
            stokes_shape = dataset.variables["I_blue_reduced"].shape
            if len(stokes_shape) != 3:
                raise ValueError(f"{path}: Stokes measurements must have time and two pixel dimensions")
            pixel_variables = REQUIRED_VARIABLES - {
                "time",
                "GPS_longitude",
                "GPS_latitude",
                "GPS_altitude",
                "solar_azimuth",
                "solar_altitude",
            }
            for name in pixel_variables:
                if dataset.variables[name].shape != stokes_shape:
                    raise ValueError(f"{path}: {name} has a different shape from the Stokes data")
            for name in ("time", "GPS_longitude", "GPS_latitude", "GPS_altitude",
                         "solar_azimuth", "solar_altitude"):
                if dataset.variables[name].shape != (stokes_shape[0],):
                    raise ValueError(f"{path}: {name} must have one value per time sample")
            if require_spatial_calibration and not getattr(
                dataset, "raw_spatial_calibration_applied", ""
            ):
                raise ValueError(
                    f"{path} does not record raw dark/flat-field calibration. "
                    "Reprocess the raw file with L1_file_save.run(raw_calibration_path=...)."
                )
            _read_l1_grasp_metadata(dataset, path)
            time_units = getattr(dataset.variables["time"], "units", "")
            if not time_units.startswith("seconds after "):
                raise ValueError(f"{path}: time units must start with 'seconds after '")
            return stokes_shape
    except OSError as error:
        raise ValueError(f"Unable to read NetCDF input {path}: {error}") from error


def _parse_time_origin(units):
    match = re.match(r"seconds after (\d{4}-\d{2}-\d{2})", units)
    if not match:
        raise ValueError(f"Unsupported NetCDF time units: {units}")
    try:
        return datetime.fromisoformat(match.group(1)).replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError(f"Invalid date in NetCDF time units: {units}") from error


def _format_timestamp(origin, seconds):
    if not np.isfinite(seconds):
        raise ValueError("Time coordinate contains a non-finite value")
    return (origin + timedelta(seconds=float(seconds))).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finite_sample(variable, time_index, row_slice, column_slice):
    values = variable[time_index, row_slice, column_slice]
    return np.asarray(np.ma.filled(values, np.nan), dtype=np.float64)


def _sample_frame(dataset, time_index, row_slice, column_slice, calibration):
    fields = {
        name: _finite_sample(dataset.variables[name], time_index, row_slice, column_slice)
        for name in ("view_azimuth", "view_zenith")
    }
    stokes = {}
    for channel in CHANNELS:
        stokes[channel] = {}
        for component in STOKES_COMPONENTS:
            reduced = _finite_sample(
                dataset.variables[f"{component}_{channel}_reduced"],
                time_index,
                row_slice,
                column_slice,
            )
            stokes[channel][component] = reduced

    longitude = float(dataset.variables["GPS_longitude"][time_index])
    latitude = float(dataset.variables["GPS_latitude"][time_index])
    altitude = float(dataset.variables["GPS_altitude"][time_index])
    solar_azimuth = float(dataset.variables["solar_azimuth"][time_index])
    solar_altitude = float(dataset.variables["solar_altitude"][time_index])
    sample_arrays = [*fields.values()]
    sample_arrays.extend(
        stokes[channel][component]
        for channel in CHANNELS
        for component in STOKES_COMPONENTS
    )
    valid = np.logical_and.reduce([np.isfinite(array) for array in sample_arrays])
    valid &= (fields["view_zenith"] >= 0) & (fields["view_zenith"] <= 180)
    valid &= np.logical_and.reduce(
        [stokes[channel]["I"] > 0 for channel in CHANNELS]
    )
    valid &= np.isfinite(longitude) & np.isfinite(latitude) & np.isfinite(altitude)
    valid &= np.isfinite(solar_azimuth) & np.isfinite(solar_altitude)
    valid &= (solar_altitude > 0) & (solar_altitude <= 90)
    valid &= (latitude >= -90) & (latitude <= 90)
    valid &= (longitude >= -180) & (longitude <= 180)
    valid &= (altitude >= -500) & (altitude <= 100000)
    return fields, stokes, valid, longitude, latitude, altitude, solar_azimuth, solar_altitude


def _format_number(value):
    return f"{float(value):.9g}"


def _pixel_line(
    ix,
    iy,
    column,
    row,
    longitude,
    latitude,
    altitude,
    solar_zenith_grasp,
    view_zenith_grasp,
    relative_azimuth_grasp,
    stokes,
    calibration,
):
    fields = [
        str(ix),
        str(iy),
        "1",
        str(column + 1),
        str(row + 1),
        _format_number(longitude),
        _format_number(latitude),
        _format_number(altitude),
        _format_number(calibration["land_percent"]),
        str(len(CHANNELS)),
    ]

    fields.extend(
        _format_number(calibration["channels"][channel]["wavelength_um"])
        for channel in CHANNELS
    )
    fields.extend(["3"] * len(CHANNELS))
    for _channel in CHANNELS:
        fields.extend(("41", "42", "43"))
    fields.extend(["1"] * (len(CHANNELS) * len(STOKES_COMPONENTS)))
    fields.extend(
        _format_number(solar_zenith_grasp)
        for _channel in CHANNELS
    )
    fields.extend(
        _format_number(view_zenith_grasp)
        for _channel in CHANNELS
        for _component in STOKES_COMPONENTS
    )
    fields.extend(
        _format_number(relative_azimuth_grasp)
        for _channel in CHANNELS
        for _component in STOKES_COMPONENTS
    )
    fields.extend(
        _format_number(stokes[channel][component])
        for channel in CHANNELS
        for component in STOKES_COMPONENTS
    )
    fields.extend(["0"] * (len(CHANNELS) * len(STOKES_COMPONENTS)))
    fields.extend(["0"] * (len(CHANNELS) * len(STOKES_COMPONENTS)))
    return " ".join(fields)


def _count_valid_cells(path, stride, calibration):
    with nc.Dataset(path, "r") as dataset:
        shape = dataset.variables["I_blue_reduced"].shape
        row_slice = slice(0, shape[1], stride)
        column_slice = slice(0, shape[2], stride)
        valid_cells = 0
        for time_index in range(shape[0]):
            frame = _sample_frame(
                dataset, time_index, row_slice, column_slice, calibration
            )
            if np.any(frame[2]):
                valid_cells += 1
        return valid_cells


def _write_sdata(path, output_path, stride, calibration):
    with nc.Dataset(path, "r") as dataset:
        stokes_shape = dataset.variables["I_blue_reduced"].shape
        row_slice = slice(0, stokes_shape[1], stride)
        column_slice = slice(0, stokes_shape[2], stride)
        rows = np.arange(stokes_shape[1])[row_slice]
        columns = np.arange(stokes_shape[2])[column_slice]
        time_origin = _parse_time_origin(dataset.variables["time"].units)
        number_of_cells = _count_valid_cells(path, stride, calibration)
        if number_of_cells == 0:
            raise ValueError(f"{path} has no valid daytime pixels to write")
        temporary_path = output_path + ".tmp"

        try:
            with open(temporary_path, "w", encoding="ascii", newline="\n") as output_file:
                output_file.write("SDATA version 2.0\n")
                output_file.write(
                    f"{len(columns)} {len(rows)} {number_of_cells} : NX NY NT\n\n"
                )
                for time_index in range(stokes_shape[0]):
                    frame = _sample_frame(
                        dataset, time_index, row_slice, column_slice, calibration
                    )
                    (
                        geometry,
                        stokes,
                        valid,
                        longitude,
                        latitude,
                        altitude,
                        solar_azimuth,
                        solar_altitude,
                    ) = frame
                    pixel_indices = np.argwhere(valid)
                    if not len(pixel_indices):
                        continue

                    timestamp = _format_timestamp(
                        time_origin, dataset.variables["time"][time_index]
                    )
                    output_file.write(
                        f"{len(pixel_indices)} {timestamp} 70000.0 0 0 "
                        ": NPIXELS TIMESTAMP HOBS_m NSURF IFGAS\n"
                    )
                    solar_zenith_grasp = 90.0 + solar_altitude
                    for row_index, column_index in pixel_indices:
                        view_zenith_grasp = 180.0 - geometry["view_zenith"][
                            row_index, column_index
                        ]
                        relative_azimuth = (
                            geometry["view_azimuth"][row_index, column_index]
                            - solar_azimuth
                            + 180.0
                        ) % 360.0 - 180.0
                        relative_azimuth_grasp = (180.0 + relative_azimuth) % 360.0
                        pixel_stokes = {
                            channel: {
                                component: stokes[channel][component][row_index, column_index]
                                for component in STOKES_COMPONENTS
                            }
                            for channel in CHANNELS
                        }
                        output_file.write(
                            _pixel_line(
                                int(column_index) + 1,
                                int(row_index) + 1,
                                int(columns[column_index]),
                                int(rows[row_index]),
                                longitude,
                                latitude,
                                altitude,
                                solar_zenith_grasp,
                                view_zenith_grasp,
                                relative_azimuth_grasp,
                                pixel_stokes,
                                calibration,
                            )
                            + "\n"
                        )
                    output_file.write("\n")

            os.replace(temporary_path, output_path)
        except Exception:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
            raise


def convert_nc_to_grasp(
    nc_path,
    output_sdata_path,
    pixel_stride=128,
    require_spatial_calibration=True,
):
    """Convert one calibrated LHMP Level 1 NetCDF file to GRASP SDATA 2.0."""
    if not isinstance(pixel_stride, int) or pixel_stride < 1:
        raise ValueError("pixel_stride must be a positive integer")
    _validate_input_file(nc_path, require_spatial_calibration)
    with nc.Dataset(nc_path, "r") as dataset:
        profile = _read_l1_grasp_metadata(dataset, nc_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_sdata_path)), exist_ok=True)
    _write_sdata(nc_path, output_sdata_path, pixel_stride, profile)
    return output_sdata_path


def convert_directory(
    input_directory,
    output_directory,
    pixel_stride=128,
    require_spatial_calibration=True,
):
    """Convert a directory only when every NetCDF file has the required L1 schema."""
    if not isinstance(pixel_stride, int) or pixel_stride < 1:
        raise ValueError("pixel_stride must be a positive integer")
    paths = sorted(
        os.path.join(input_directory, name)
        for name in os.listdir(input_directory)
        if name.lower().endswith(".nc")
    )
    if not paths:
        raise ValueError(f"No NetCDF files found in {input_directory}")

    for path in paths:
        _validate_input_file(path, require_spatial_calibration)

    os.makedirs(output_directory, exist_ok=True)
    outputs = []
    for path in paths:
        with nc.Dataset(path, "r") as dataset:
            profile = _read_l1_grasp_metadata(dataset, path)
        output_path = os.path.join(
            output_directory, os.path.splitext(os.path.basename(path))[0] + ".sdat"
        )
        _write_sdata(path, output_path, pixel_stride, profile)
        outputs.append(output_path)
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        default=DEFAULT_INPUT_DIRECTORY,
        help="L1 NetCDF file or directory (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        help="Output SDATA file for a single input file; otherwise an output directory",
    )
    parser.add_argument(
        "--pixel-stride",
        type=int,
        default=128,
        help="Sample every Nth detector pixel in each dimension (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    try:
        if args.pixel_stride < 1:
            raise ValueError("--pixel-stride must be positive")
        if os.path.isdir(args.input):
            output_directory = args.output or os.path.join(args.input, "grasp_sdata")
            outputs = convert_directory(
                args.input,
                output_directory,
                pixel_stride=args.pixel_stride,
            )
        else:
            output_path = args.output or os.path.splitext(args.input)[0] + ".sdat"
            outputs = [
                convert_nc_to_grasp(
                    args.input,
                    output_path,
                    pixel_stride=args.pixel_stride,
                )
            ]
    except (OSError, ValueError, KeyError) as error:
        print(f"Conversion failed: {error}", file=sys.stderr)
        return 1

    for path in outputs:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
