"""Calibrate camera intrinsics from checkerboard images and write a CSV record."""

import argparse
import csv
import glob
import json
import os

import cv2
import numpy as np


CHECKERBOARD = (9, 6)
SQUARE_SIZE = 1.0
CSV_FORMAT = "LHMP_CAMERA_CALIBRATION_V1"


def calibrate_camera(image_paths, checkerboard=CHECKERBOARD, square_size=SQUARE_SIZE):
    """Return camera intrinsics and per-image extrinsics for usable checkerboards."""
    if not image_paths:
        raise ValueError("No geometric calibration images were found")
    if len(checkerboard) != 2 or min(checkerboard) < 2:
        raise ValueError("checkerboard must contain at least two inner corners per axis")
    if not np.isfinite(square_size) or square_size <= 0:
        raise ValueError("square_size must be finite and positive")

    template = np.zeros((checkerboard[0] * checkerboard[1], 3), dtype=np.float32)
    template[:, :2] = (
        np.mgrid[0:checkerboard[0], 0:checkerboard[1]]
        .T.reshape(-1, 2)
        .astype(np.float32)
        * square_size
    )
    object_points = []
    image_points = []
    accepted_paths = []
    image_size = None

    for path in image_paths:
        image = cv2.imread(path)
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        current_size = (gray.shape[1], gray.shape[0])
        if image_size is not None and current_size != image_size:
            raise ValueError("All geometric calibration images must have matching dimensions")
        image_size = current_size
        found, corners = cv2.findChessboardCorners(gray, checkerboard, None)
        if not found:
            continue
        refined = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            (
                cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                30,
                0.001,
            ),
        )
        object_points.append(template.copy())
        image_points.append(refined)
        accepted_paths.append(os.path.abspath(path))

    if not object_points:
        raise ValueError("No readable calibration image contains the configured checkerboard")
    if len(object_points) < 3:
        raise ValueError("At least three usable checkerboard images are required")

    rms, camera_matrix, distortion, rotation_vectors, translation_vectors = (
        cv2.calibrateCamera(object_points, image_points, image_size, None, None)
    )
    per_view_rms = []
    for object_points_for_view, image_points_for_view, rotation, translation in zip(
        object_points, image_points, rotation_vectors, translation_vectors
    ):
        projected, _ = cv2.projectPoints(
            object_points_for_view, rotation, translation, camera_matrix, distortion
        )
        residual = image_points_for_view.reshape(-1, 2) - projected.reshape(-1, 2)
        per_view_rms.append(float(np.sqrt(np.mean(np.sum(residual**2, axis=1)))))

    return {
        "rms_reprojection_error_px": float(rms),
        "camera_matrix": np.asarray(camera_matrix, dtype=np.float64),
        "distortion_coefficients": np.asarray(distortion, dtype=np.float64).reshape(-1),
        "image_width_px": int(image_size[0]),
        "image_height_px": int(image_size[1]),
        "checkerboard_columns": int(checkerboard[0]),
        "checkerboard_rows": int(checkerboard[1]),
        "square_size": float(square_size),
        "accepted_images": accepted_paths,
        "rotation_vectors": [np.asarray(value).reshape(-1).tolist() for value in rotation_vectors],
        "translation_vectors": [
            np.asarray(value).reshape(-1).tolist() for value in translation_vectors
        ],
        "per_view_rms_reprojection_error_px": per_view_rms,
    }


def write_calibration_csv(calibration, output_path):
    """Write all intrinsics, distortion, calibration settings, and poses to one CSV row."""
    matrix = calibration["camera_matrix"]
    row = {
        "format": CSV_FORMAT,
        "rms_reprojection_error_px": calibration["rms_reprojection_error_px"],
        "image_width_px": calibration["image_width_px"],
        "image_height_px": calibration["image_height_px"],
        "checkerboard_columns": calibration["checkerboard_columns"],
        "checkerboard_rows": calibration["checkerboard_rows"],
        "square_size": calibration["square_size"],
        "accepted_images_json": json.dumps(calibration["accepted_images"]),
        "distortion_coefficients_json": json.dumps(
            calibration["distortion_coefficients"].tolist()
        ),
        "rotation_vectors_json": json.dumps(calibration["rotation_vectors"]),
        "translation_vectors_json": json.dumps(calibration["translation_vectors"]),
        "per_view_rms_reprojection_error_px_json": json.dumps(
            calibration["per_view_rms_reprojection_error_px"]
        ),
    }
    for row_index in range(3):
        for column_index in range(3):
            row[f"camera_matrix_{row_index}{column_index}"] = matrix[
                row_index, column_index
            ]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return output_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--images",
        default="geometric_calibration_images/*.png",
        help="Glob pattern for checkerboard images",
    )
    parser.add_argument("--output", default="geometric_calibration.csv")
    parser.add_argument("--square-size", type=float, default=SQUARE_SIZE)
    args = parser.parse_args(argv)

    try:
        result = calibrate_camera(
            sorted(glob.glob(args.images)),
            square_size=args.square_size,
        )
        write_calibration_csv(result, args.output)
    except (OSError, ValueError, cv2.error) as error:
        parser.error(str(error))

    print(f"Camera matrix:\n{result['camera_matrix']}")
    print(f"Distortion coefficients: {result['distortion_coefficients']}")
    print(f"RMS reprojection error: {result['rms_reprojection_error_px']:.6g} px")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
