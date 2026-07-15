import numpy as np
import math

def orientation(q_prev, gyro, accel, mag, dt, kp=1.0):
    """
    Updates and calculates Yaw, Pitch, and Roll from 1 set of IMU measurements.
    
    :param q_prev: List or array of the previous quaternion [w, x, y, z]
    :param gyro: Angular velocities [gx, gy, gz] in rad/s
    :param accel: Accelerometer readings [ax, ay, az] (any unit, e.g., g or m/s^2)
    :param mag: Magnetometer readings [mx, my, mz]. Pass [0, 0, 0] to fall back to 6-axis.
    :param dt: Time delta since the last measurement in seconds
    :param kp: Proportional gain for filter stabilization (default 1.0)
    :return: (yaw, pitch, roll) in degrees, and the new updated quaternion array
    """
    # 1. Setup local quaternion variables
    q1, q2, q3, q4 = q_prev
    gx, gy, gz = gyro
    ax, ay, az = accel
    mx, my, mz = mag

    # 2. Normalize accelerometer measurement
    norm_a = math.sqrt(ax*ax + ay*ay + az*az)
    if norm_a > 0.0:
        ax, ay, az = ax/norm_a, ay/norm_a, az/norm_a

    # 3. Check for magnetometer data
    norm_m = math.sqrt(mx*mx + my*my + mz*mz)
    if norm_m > 0.0:
        # Normalize magnetometer measurement
        mx, my, mz = mx/norm_m, my/norm_m, mz/norm_m

        # Reference direction of Earth's magnetic field
        hx = 2.0 * (mx * (0.5 - q3*q3 - q4*q4) + my * (q2*q3 - q1*q4) + mz * (q2*q4 + q1*q3))
        hy = 2.0 * (mx * (q2*q3 + q1*q4) + my * (0.5 - q2*q2 - q4*q4) + mz * (q3*q4 - q1*q2))
        bx = math.sqrt(hx*hx + hy*hy)
        bz = 2.0 * (mx * (q2*q4 - q1*q3) + my * (q3*q4 + q1*q2) + mz * (0.5 - q2*q2 - q3*q3))

        # Estimated direction of gravity and magnetic field
        vx = 2.0 * (q2*q4 - q1*q3)
        vy = 2.0 * (q1*q2 + q3*q4)
        vz = q1*q1 - q2*q2 - q3*q3 + q4*q4

        wx = 2.0 * bx * (0.5 - q3*q3 - q4*q4) + 2.0 * bz * (q2*q4 - q1*q3)
        wy = 2.0 * bx * (q2*q3 - q1*q4) + 2.0 * bz * (q1*q2 + q3*q4)
        wz = 2.0 * bx * (q1*q4 + q2*q3) + 2.0 * bz * (0.5 - q2*q2 - q3*q3)

        # Error is cross product between estimated and measured direction of fields
        ex = (ay * vz - az * vy) + (my * wz - mz * wy)
        ey = (az * vx - ax * vz) + (mz * wx - mx * wz)
        ez = (ax * vy - ay * vx) + (mx * wy - my * wx)
    else:
        # Fallback to 6-axis calculation if magnetometer values are zero
        vx = 2.0 * (q2*q4 - q1*q3)
        vy = 2.0 * (q1*q2 + q3*q4)
        vz = q1*q1 - q2*q2 - q3*q3 + q4*q4

        ex = (ay * vz - az * vy)
        ey = (az * vx - ax * vz)
        ez = (ax * vy - ay * vx)

    # 4. Apply feedback scaling
    gx += kp * ex
    gy += kp * ey
    gz += kp * ez

    # 5. Integrate quaternion rate changes
    q1 += (-q2 * gx - q3 * gy - q4 * gz) * (0.5 * dt)
    q2 += (q1 * gx + q3 * gz - q4 * gy) * (0.5 * dt)
    q3 += (q1 * gy - q2 * gz + q4 * gx) * (0.5 * dt)
    q4 += (q1 * gz + q2 * gy - q3 * gx) * (0.5 * dt)

    # 6. Normalize final updated quaternion
    q_new = np.array([q1, q2, q3, q4])
    norm_q = np.linalg.norm(q_new)
    if norm_q > 0.0:
        q_new = q_new / norm_q

    # 7. Convert newly updated quaternion to Euler Angles
    w, x, y, z = q_new
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x))))
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))

    # Convert radians to degrees
    return math.degrees(yaw), math.degrees(pitch), math.degrees(roll), q_new
    
if __name__ == "__main__":
    orientation()