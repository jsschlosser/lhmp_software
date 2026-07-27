import cv2
import numpy as np
import glob

# Define your checkerboard inner dimensions (e.g., 9x6 internal corners)
CHECKERBOARD = (9, 6)
square_size = 1.0 # Size of a square side in your chosen unit

# Arrays to store object points and image points
objpoints = [] 
imgpoints = [] 

# Define 3D coordinates for corners
objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * square_size

# Load calibration images (replace path with your images)
images = glob.glob('geometric_calibration_images/*.png')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    
    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)

# Run calibration to extract focal parameters
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("\n--- Camera Matrix (K) Results ---")
print(f"fx (Horizontal Focal Length): {mtx[0,0]:.2f} pixels")
print(f"fy (Vertical Focal Length):   {mtx[1,1]:.2f} pixels")
print(f"u0 (Principal Point X):      {mtx[0,2]:.2f} pixels")
print(f"v0 (Principal Point Y):      {mtx[1,2]:.2f} pixels")
