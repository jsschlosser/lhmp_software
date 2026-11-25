"""LHMP dark, flat-field, spectral, and Stokes-axis calibration utilities."""

import os

import netCDF4 as nc
import numpy as np


def effective_wavelength_um(
    response_wavelength_nm,
    relative_response,
    solar_wavelength_nm,
    solar_spectral_irradiance,
):
    """Estimate a solar-weighted effective wavelength from response curves."""
    response_wavelength = np.asarray(response_wavelength_nm, dtype=np.float64)
    response = np.asarray(relative_response, dtype=np.float64)
    solar_wavelength = np.asarray(solar_wavelength_nm, dtype=np.float64)
    solar_irradiance = np.asarray(solar_spectral_irradiance, dtype=np.float64)

    for name, wavelength, values in (
        ("response", response_wavelength, response),
        ("solar spectrum", solar_wavelength, solar_irradiance),
    ):
        if wavelength.ndim != 1 or values.ndim != 1 or wavelength.size != values.size:
            raise ValueError(f"{name} wavelengths and values must be matching 1D arrays")
        if wavelength.size < 2 or not np.all(np.isfinite(wavelength)):
            raise ValueError(f"{name} must contain at least two finite wavelength samples")
        if np.any(np.diff(wavelength) <= 0):
            raise ValueError(f"{name} wavelengths must be strictly increasing")
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            raise ValueError(f"{name} values must be finite and non-negative")

    lower = max(response_wavelength[0], solar_wavelength[0])
    upper = min(response_wavelength[-1], solar_wavelength[-1])
    if lower >= upper:
        raise ValueError("Spectral response and solar spectrum do not overlap")
    grid = np.unique(
        np.concatenate(
            (
                response_wavelength[
                    (response_wavelength >= lower) & (response_wavelength <= upper)
                ],
                solar_wavelength[
                    (solar_wavelength >= lower) & (solar_wavelength <= upper)
                ],
                np.array([lower, upper]),
            )
        )
    )
    response_on_grid = np.interp(grid, response_wavelength, response)
    solar_on_grid = np.interp(grid, solar_wavelength, solar_irradiance)
    weights = response_on_grid * solar_on_grid
    intervals = np.diff(grid)
    normalization = np.sum((weights[:-1] + weights[1:]) * intervals / 2.0)
    if not np.isfinite(normalization) or normalization <= 0:
        raise ValueError("Spectral response has no positive solar-weighted signal")
    weighted_wavelength = np.sum(
        (grid[:-1] * weights[:-1] + grid[1:] * weights[1:]) * intervals / 2.0
    )
    return float(weighted_wavelength / normalization / 1000.0)


def rotate_stokes_qu(q, u, angle_degrees):
    """Rotate linear Stokes values to axes rotated counterclockwise by angle.

    The angle is measured from the source positive-Q axis to the target
    positive-Q axis, viewed along the propagation direction.
    """
    angle = np.asarray(angle_degrees, dtype=np.float64)
    if not np.all(np.isfinite(angle)):
        raise ValueError("Stokes reference-axis angle must be finite")

    q, u, angle = np.broadcast_arrays(
        np.asarray(q, dtype=np.float64),
        np.asarray(u, dtype=np.float64),
        angle,
    )
    doubled_angle = np.deg2rad(2.0 * angle)
    cosine = np.cos(doubled_angle)
    sine = np.sin(doubled_angle)
    return q * cosine + u * sine, -q * sine + u * cosine


def _read_raw_frames(path):
    with nc.Dataset(path, "r") as dataset:
        calibration_status = str(
            getattr(dataset, "calibration_data_status", "")
        ).lower()
        if "synthetic" in calibration_status:
            raise ValueError(
                f"{path} is marked synthetic and cannot be used to build a calibration"
            )
        if "Raw_Signal" not in dataset.variables:
            raise ValueError(f"{path} does not contain a Raw_Signal variable")

        raw = dataset.variables["Raw_Signal"]
        if raw.ndim != 3:
            raise ValueError(f"{path}: Raw_Signal must have time, H_pixel, V_pixel dimensions")

        exposure = dataset.variables.get("Detector_Exposure_Time")
        gain = dataset.variables.get("Detector_Gain")
        if exposure is None or gain is None:
            raise ValueError(f"{path} must contain Detector_Exposure_Time and Detector_Gain")

        exposure_values = np.asarray(exposure[:]).reshape(-1)
        gain_values = np.asarray(gain[:]).reshape(-1)
        if raw.shape[0] == 0:
            raise ValueError(f"{path} contains no raw frames")
        if exposure_values.size != raw.shape[0] or gain_values.size != raw.shape[0]:
            raise ValueError(f"{path} must have exposure and gain values for every raw frame")
        if not np.all(np.isfinite(exposure_values)) or not np.all(np.isfinite(gain_values)):
            raise ValueError(f"{path} has non-finite exposure or gain metadata")
        if np.any(exposure_values <= 0):
            raise ValueError(f"{path} exposure times must be positive")
        if not np.all(exposure_values == exposure_values[0]):
            raise ValueError(f"{path} must use a constant exposure time")
        if not np.allclose(gain_values, gain_values[0]):
            raise ValueError(f"{path} must use a constant detector gain")

        total = np.zeros(raw.shape[1:], dtype=np.float64)
        for index in range(raw.shape[0]):
            total += np.asarray(raw[index], dtype=np.float64)

        return (
            total / raw.shape[0],
            int(exposure_values[0]),
            float(gain_values[0]),
        )


def build_raw_calibration(dark_file, flat_field_file, output_path):
    """Create a dark-offset and normalized flat-field calibration bundle.

    The dark and flat-field captures must have identical image dimensions,
    exposure time, and detector gain.
    """
    dark_mean, dark_exposure, dark_gain = _read_raw_frames(dark_file)
    flat_mean, flat_exposure, flat_gain = _read_raw_frames(flat_field_file)

    if dark_mean.shape != flat_mean.shape:
        raise ValueError("Dark and flat-field captures must have identical image dimensions")
    if dark_exposure != flat_exposure or not np.isclose(dark_gain, flat_gain):
        raise ValueError("Dark and flat-field captures must use identical exposure and gain")
    if np.any(flat_mean >= 255):
        raise ValueError("Flat-field capture contains saturated pixels")

    signal = flat_mean - dark_mean
    valid = np.isfinite(signal) & (signal > 0)
    if not np.all(valid):
        invalid_count = int(np.count_nonzero(~valid))
        raise ValueError(
            f"Flat-field capture has {invalid_count} non-positive or invalid pixels; "
            "inspect the source captures before calibration"
        )

    flat_field_gain = np.mean(signal, dtype=np.float64) / signal
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as output_file:
        np.savez_compressed(
            output_file,
            dark_offset_dn=dark_mean.astype(np.float32),
            flat_field_gain=flat_field_gain.astype(np.float32),
            exposure_time_us=np.int64(dark_exposure),
            gain_db=np.float64(dark_gain),
        )
    return output_path


def load_raw_calibration(path):
    """Load and validate a calibration bundle created by build_raw_calibration."""
    with np.load(path, allow_pickle=False) as bundle:
        required = {
            "dark_offset_dn",
            "flat_field_gain",
            "exposure_time_us",
            "gain_db",
        }
        missing = required.difference(bundle.files)
        if missing:
            raise ValueError(f"Calibration bundle is missing: {', '.join(sorted(missing))}")

        if "calibration_data_status" in bundle.files:
            calibration_status = str(bundle["calibration_data_status"].item()).lower()
            if "synthetic" in calibration_status:
                raise ValueError("Synthetic raw calibration bundles cannot be applied")

        dark_offset = np.asarray(bundle["dark_offset_dn"], dtype=np.float32)
        flat_gain = np.asarray(bundle["flat_field_gain"], dtype=np.float32)
        exposure_time_us = int(bundle["exposure_time_us"])
        gain_db = float(bundle["gain_db"])

    if dark_offset.ndim != 2 or flat_gain.shape != dark_offset.shape:
        raise ValueError("Calibration maps must be matching two-dimensional arrays")
    if not np.all(np.isfinite(dark_offset)):
        raise ValueError("Dark-offset map contains non-finite values")
    if not np.all(np.isfinite(flat_gain)) or np.any(flat_gain <= 0):
        raise ValueError("Flat-field gain map must contain only finite positive values")

    return {
        "dark_offset_dn": dark_offset,
        "flat_field_gain": flat_gain,
        "exposure_time_us": exposure_time_us,
        "gain_db": gain_db,
    }


def apply_raw_calibration(
    raw_image,
    calibration,
    exposure_time_us=None,
    gain_db=None,
    saturation_dn=None,
):
    """Apply dark subtraction and flat-field correction to one raw image."""
    raw_image = np.asarray(raw_image)
    dark_offset = calibration["dark_offset_dn"]
    flat_gain = calibration["flat_field_gain"]

    if raw_image.ndim != 2 or raw_image.shape != dark_offset.shape:
        raise ValueError("Raw image dimensions do not match the calibration maps")
    if exposure_time_us is not None and int(exposure_time_us) != calibration["exposure_time_us"]:
        raise ValueError("Raw image exposure time does not match the calibration")
    if gain_db is not None and not np.isclose(float(gain_db), calibration["gain_db"]):
        raise ValueError("Raw image detector gain does not match the calibration")

    calibrated = (raw_image.astype(np.float32) - dark_offset) * flat_gain
    if saturation_dn is not None:
        calibrated[raw_image >= saturation_dn] = np.nan
    return calibrated
