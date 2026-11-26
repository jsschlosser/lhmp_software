LHMP calibration workflow
=========================

Calibration is required before producing physically meaningful GRASP SDATA.
The Level 1 ``I_*``, ``Q_*``, and ``U_*`` variables retain detector counts
(DN). When a measured Stokes calibration profile is supplied, L1 also writes
dimensionless reduced-radiance variables (``I_*_reduced``, ``Q_*_reduced``,
and ``U_*_reduced``) and records their wavelengths and calibration factors.
The manufacturer spectral-response curve is not an absolute radiometric
calibration.

Spectral response and effective wavelength
-------------------------------------------

The Sony sensor's manufacturer response curve can be used as an initial
estimate of detector sensitivity versus wavelength. It does not include the
installed lens, cover glass, polarization filter, any other optical filters,
or the camera's complete signal chain. It therefore cannot, by itself, assign
calibrated wavelengths to the ``blue``, ``green``, and ``red`` variables or
convert their DN values to radiance. Confirm the exact camera/sensor variant
and filter stack before interpreting those channels as separate spectral
bands.

Measure the end-to-end response with a monochromator and a traceable
spectroradiometer (or an equivalent calibrated facility). For a broadband
channel, derive its effective wavelength using the measured instrument
response and the relevant incident spectrum; do not infer it from the Bayer
channel name. Record the response curve, wavelength range, effective
wavelength, reference instrument, and uncertainty.
The helper ``calibration.effective_wavelength_um`` calculates a solar-weighted
estimate from sampled response and solar-spectrum arrays. Use the complete
instrument response for the final value.

Calibration data collection
---------------------------

Keep pixel format, black level, gain, exposure, lens, focus, aperture, and
camera temperature controlled and recorded. Disable automatic exposure and
gain. Collect enough frames to estimate repeatability and retain the original
NetCDF captures.

Bench protocol: integrating sphere, monochromator, and polarizer
-----------------------------------------------------------------

Use the Labsphere Heliosphere with its xenon source as the uniform illumination
source, the monochromator to select wavelength, and the wire-grid polarizer on
the rotating stage to create known linear-polarization states. Follow the
equipment manuals for xenon-lamp warm-up, high-voltage and UV precautions,
thermal limits, and eye protection. Do not look into the sphere port or
monochromator output. Keep the camera, lens, filters, focus, aperture, working
distance, and alignment unchanged throughout a calibration series.

**Use the Labsphere calibration certificate as the absolute reference.** Check
that it provides traceable spectral radiance, or the measurements needed to
derive it, at the sphere port for the actual lamp, attenuator, spectrum, and
geometry. The product page describes a solar-like calibrated source and
spectral monitoring, but that alone does not establish the certificate's
quantity, uncertainty, or applicability to this setup. In particular, verify
whether the certificate covers the monochromator in the optical path. If it
does not, measure the spectral radiance downstream of the monochromator with
a calibrated spectroradiometer or obtain a suitable Labsphere calibration.
Do not treat maximum luminance or illuminance specifications as spectral
radiance. Record the applicable certificate, calibration date, uncertainty,
and geometry; without applicable traceability, retain relative measurements
only and do not claim absolute GRASP radiances.

Before acquisition:

* Mount the camera square to the sphere's output port. Use the same optical
  train as field observations, and ensure the port fills the camera field of
  view without vignetting. Record the port, baffle, distance, and aperture
  configuration.
* Warm up the xenon source and sphere per their manuals. Check source stability
  using the reference instrument or repeated camera readings. Allow the
  monochromator and reference detector to stabilize as specified by their
  manuals.
* Fix camera settings for each calibration set. Disable auto exposure, gain,
  white balance, gamma, and any in-camera processing. Record pixel format,
  exposure, gain, black level, temperature, frame rate, lens, filters, focus,
  aperture, and camera/sensor identity. Verify the raw Bayer pattern and the
  mapping from sensor samples to the saved blue, green, and red variables.
* Check the monochromator wavelength calibration, slit settings/bandpass,
  order-sorting filters, and stray-light controls. Use the same geometry for
  reference radiance measurements and camera measurements.

The acquisition application or paper worksheet should request and retain the
following for every run: date/time and operator; camera and optical-train
identifiers; all camera settings; sphere port and lamp configuration; lamp
warm-up and stability check; monochromator wavelength, bandwidth, and slit
settings; reference-instrument identifier, calibration certificate/date, and
reading; polarizer identifier, extinction ratio, stage zero and angle; frame
count; and notes for drift, clipping, or interruptions. Do not allow a
measurement to be marked "absolute radiometry complete" without a valid
traceable radiance reference. Preserve raw frames and the measurement log
together.

1. **Dark and uniform-flat captures.** With the lens capped, acquire a dark
   sequence at each exposure/gain/temperature setting used for the flat and
   science data. Then uncover the lens and acquire an unpolarized sphere flat
   that fills the field. Keep exposure and gain identical to the dark capture,
   keep every pixel below saturation, and record the sphere setting. Repeat
   the flat at a second safe brightness to reveal nonlinearity or clipping.
   The dark and flat used to build one bundle must have the same dimensions,
   exposure, and gain. Build the raw correction maps with::

       python -c "import calibration; calibration.build_raw_calibration('dark.nc', 'flat_field.nc', 'raw_calibration.npz')"

   The dark map is the temporal mean of dark frames. The flat-field gain map
   normalizes each pixel's dark-subtracted response to the sensor-wide mean.
   Inspect the maps and corrected flat before use; investigate hot pixels,
   invalid/non-positive pixels, spatial structure, or source gradients rather
   than masking them silently. The current helper rejects saturated 8-bit
   samples and requires matching exposure/gain.

2. **End-to-end spectral response.** With the polarizer removed, scan the
   monochromator across the full transmitted range of the installed lens,
   filters, and sensor. Use a wavelength step fine enough to resolve response
   features (no larger than half the measured monochromator bandpass near
   sharp features); cover both response tails. At each wavelength, measure
   reference spectral radiance at the camera port and acquire repeated
   camera frames. Interleave dark frames and repeat the sweep to detect drift.
   Avoid saturation and measure enough signal above dark/read noise. Apply
   dark correction and normalize camera response by the measured incident
   spectral radiance and exposure. Save response versus wavelength separately
   for each Bayer channel, including wavelength uncertainty, monochromator
   bandpass, repeatability, and reference uncertainty. Do not substitute the
   Sony sensor curve for the response of the complete optical train.

   From each measured response curve, calculate the channel effective
   wavelength using the spectrum relevant to the intended observation. For
   solar observations, use a documented extraterrestrial solar spectral
   irradiance dataset and the complete instrument response; the helper
   ``calibration.effective_wavelength_um`` accepts sampled response and solar
   spectrum arrays. Keep the response curve and integration method with the
   result; effective wavelength alone is not enough to reproduce the
   calibration.

3. **Linearity and absolute radiometry.** At several monochromator wavelengths
   spanning each channel, measure a series of sphere radiance levels covering
   the intended science range. Change sphere output or a validated attenuator,
   not camera settings, within a single series. Measure each level with the
   traceable reference and camera, acquire repeats, and stay below saturation.
   Verify linearity, dark intercept, repeatability, and absence of hysteresis.
   Then use the measured spectral response and traceable radiance to determine
   a radiance-per-DN slope for each saved channel. Apply the same dark/flat and
   Stokes-processing path used for science data.

   For normalized channel response ``S_c(lambda)``, compute the channel
   radiance and solar irradiance consistently, for example as response-weighted
   band means ``L_c = integral(S_c * L_lambda) / integral(S_c)`` and
   ``E0_c = integral(S_c * E0_lambda) / integral(S_c)``. If the measured slope
   is ``a_c`` DN per ``L_c``, the GRASP scale is
   ``reduced_radiance_per_dn = pi / (E0_c * a_c)``. Use consistent wavelength
   units and spectral-radiance/irradiance units in both integrations. Verify
   this factor against independent source levels before writing the JSON
   profile. Include uncertainty and valid DN range in the calibration record.
   A sensor response curve or uncalibrated xenon/monochromator intensity
   cannot supply this absolute factor.

4. **Polarimetric response.** First acquire the unpolarized sphere with the
   polarizer removed. Then install the wire-grid polarizer between the sphere
   port and camera, with its rotation axis normal to the optical axis. Measure
   or obtain its extinction ratio and angular-zero uncertainty over the
   wavelengths of interest. Sweep known stage angles across 0--180 degrees
   (including 0, 45, 90, and 135 degrees), recording the encoder angle and
   repeats at each position. Keep the camera settings fixed, avoid saturation,
   and repeat at representative monochromator wavelengths and across the
   field of view. If the sphere/polarizer arrangement does not provide a
   known degree of linear polarization, the measured polarimetric efficiency
   is not absolute.

   The L1 pipeline calls ``polanalyser.calcStokes`` with analyzer angles
   0, 45, 90, and 135 degrees. Its linear-Stokes convention is
   ``Q = I_(0) - I_(90)`` and ``U = I_(45) - I_(135)``; the NetCDF variable
   metadata uses these signs. As a software convention check, synthetic ideal
   analyzer measurements for input polarization angles 0, 45, 90, and
   135 degrees must recover respectively ``(Q/I, U/I)`` of ``(1, 0)``,
   ``(0, 1)``, ``(-1, 0)``, and ``(0, -1)``.

   Fit the measured Stokes values against the known input states
   ``[I, p*I*cos(2*theta), p*I*sin(2*theta)]``, using the polarizer's measured
   degree of linear polarization ``p`` and calibrated stage angle ``theta``.
   Determine analyzer-angle zero, I-to-Q/U leakage, Q/U gain and cross-talk,
   spatial variation, and repeatability. Validate the fit with angles not
   used to determine it and with independent repeated captures. A rotating
   linear polarizer can characterize the I/Q/U response to linear input; it
   cannot characterize sensitivity to circular polarization. Additional
   polarization standards are needed if circular-to-linear coupling matters.

   For a pure change of linear-Stokes reference axis, let ``psi`` be the
   counterclockwise angle from the sensor's positive-Q axis to the target
   positive-Q axis, viewed along the camera-to-scene propagation direction.
   The coordinate rotation is::

       Q_target = Q_sensor*cos(2*psi) + U_sensor*sin(2*psi)
       U_target = -Q_sensor*sin(2*psi) + U_sensor*cos(2*psi)

   It must preserve ``sqrt(Q**2 + U**2)``. The helper
   ``calibration.rotate_stokes_qu`` implements this axis rotation; validate it
   with synthetic Stokes vectors and known 0, 45, 90, and 135-degree states
   before applying it.

   Establish the instrument Q/U axes relative to the camera and document the
   exact GRASP positive-Q axis and angle convention. The stage sweep determines
   instrument response and angular zero; it does not by itself determine the
   field-observation transform, which also depends on viewing and solar
   geometry and camera-to-IMU alignment. The current L1 pipeline does not
   transform sensor-frame Q/U into GRASP's reference plane. Its sensor-frame
   Stokes convention and Q/U labels can be
   checked in software, but the end-to-end transform cannot be validated until
   it is implemented and tested against captured polarizer data with
   independently established geometry. Do not set ``stokes_reference_frame`` to
   ``grasp_scattering_plane`` or use the GRASP converter for polarized retrievals
   before both validations pass.

5. **Stokes dark offsets and acceptance.** Process dark captures through the
   same demosaicing and Stokes calculation as science data. Derive residual
   ``I``, ``Q``, and ``U`` dark offsets per channel after raw spatial
   correction, and confirm the offsets are stable across the science exposure,
   gain, and temperature range. These are the ``dark_stokes_dn`` values in
   the GRASP profile; they are not interchangeable with raw-pixel dark maps.
   Record all fitted coefficients, uncertainties, settings, and source files.
   Repeatability, residuals, response curves, linearity range, and
   polarimetric residuals must meet predeclared project tolerances. If a
   channel is non-monotonic, unstable, clipped, or outside its validated
   range, do not issue a calibration profile for it.

The protocol yields the raw dark/flat bundle, per-channel end-to-end response
curves and effective wavelengths, absolute radiance slopes, validated
polarimetric coefficients and frame transform, Stokes dark offsets, and a
traceable record of uncertainty. Only after these products are reviewed
should their values be entered into the GRASP calibration JSON.

Applying raw spatial calibration
---------------------------------

The geometric calibration routine now writes ``geometric_calibration.csv``
with the complete 3x3 camera matrix, distortion coefficients, image size,
checkerboard settings, RMS reprojection error, accepted image names, and
per-image pose/error results::

    python geometric_correction.py --images "geometric_calibration_images/*.png"

Pass the measured calibration products while converting L0 raw data to L1::

    >>> import L1_file_save
    >>> L1_file_save.run(
    ...     raw_calibration_path='raw_calibration.npz',
    ...     stokes_calibration_path='grasp_calibration.json',
    ...     geometric_calibration_path='geometric_calibration.csv',
    ...     camera_imu_calibration_path='camera_imu_calibration.json')

Dark subtraction and flat-field correction are applied to each raw frame
before demosaicing and Stokes calculation. Saturated raw samples are marked
invalid; they cannot be recovered by calibration. The input exposure and gain
must match the calibration bundle. The original ``Raw_Signal`` variable and
the DN Stokes variables are preserved. The measured Stokes dark offsets and
reduced-radiance scale are applied in L1 and stored in separate
dimensionless ``*_reduced`` variables; ``netcdf_to_grasp.py`` now serializes
those values without applying a second calibration. If the Stokes profile is
omitted, the reduced-radiance variables are not created and conversion stops.

The polarimeter faces upward. L1 maps its camera boresight (+Y) to IMU +Z using
the current STEP/datasheet candidate matrix, so a level boresight has view
zenith 0 degrees. This mechanical alignment is explicitly marked as an
unvalidated CAD estimate in the output; it is not sufficient for a science
retrieval. The geometric CSV supplies camera intrinsics and lens distortion,
but does not validate camera-to-IMU mounting or IMU attitude.

After physical alignment is measured, a camera-to-IMU JSON calibration can be
passed with format ``LHMP_CAMERA_IMU_CALIBRATION_V1``, status
``calibration_data_status: measured``, and a proper 3x3
``rotation_camera_to_imu`` matrix using the documented column-vector
convention. The STEP estimate in the fixtures is rejected by this loader.

The GRASP angle convention follows the official ground-based conversion:
``theta_GRASP = 180 - theta_ground`` and ``phi_GRASP = 180 + phi_ground``.
For upward sky observations this means ``solar_zenith_GRASP = 90 +
solar_altitude``; camera view zenith is converted as ``180 - view_zenith``.
The previous converter used the wrong solar-zenith formula, which could
produce invalid GRASP solar geometry.

L1 Stokes calibration profile
------------------------------

``L1_file_save.run(stokes_calibration_path=...)`` accepts a JSON profile with
format ``LHMP_GRASP_CALIBRATION_V1``. It must contain:

* ``land_percent``: the measured/selected land fraction for the observation.
* For each ``blue``, ``green``, and ``red`` channel: ``wavelength_um``,
  ``reduced_radiance_per_dn``, and measured dark offsets for ``I``, ``Q``, and
  ``U`` in ``dark_stokes_dn``.

Use the effective wavelength and radiometric factors measured for the
complete instrument. Do not copy nominal RGB wavelengths or unverified values
from an example. The profile scale converts the dark-corrected Stokes DN to
dimensionless reduced Stokes radiance in L1. The converter reads the L1
calibration metadata and does not load or apply a calibration profile.

GRASP conversion additionally requires a validated camera intrinsic
calibration, camera-to-IMU alignment, and Q/U values already transformed to
``grasp_scattering_plane``. The present L1 pipeline records Q/U as
``sensor_image_plane`` and marks the camera-to-IMU matrix as an unvalidated
estimate unless a measured alignment profile is supplied, so production
conversion correctly refuses these files until Q/U has also been transformed
and validated. The conversion guard is intentional; the existing Q/U helper
validates the algebraic rotation only, not the physical camera-to-GRASP frame.

GRASP retrieval runner
----------------------

``grasp_workflow.py`` converts each eligible L1 file to SDATA, runs the
installed GRASP executable, and asks its NetCDF tile-output function to write
the results. Supply an existing GRASP YAML settings file::

    python grasp_workflow.py "B:\\Hampton_University\\HU_Polarimetry_Lab\\L1_data" `
        --settings "path\\to\\retrieval.yml" `
        --output "B:\\Hampton_University\\HU_Polarimetry_Lab\\GRASP_results" `
        --grasp-executable grasp

The NetCDF file contains the products enabled by that settings file; GRASP
does not have one universal set of outputs. Configure the desired aerosol
products under ``retrieval.products`` and choose a retrieval strategy
appropriate to the measured instrument data. The runner requests
``output.tile.function=netcdf``; the installed GRASP build must include that
optional output function. GRASP is not installed in this development
environment, and no scientific retrieval settings are bundled because the
model, constraints, and priors must be selected for the experiment.
Obtaining and compiling GRASP itself follows the `official installation
documentation <https://www.grasp-open.com/doc/ch03.php>`_; source access may
require a registered GRASP-Open account. Run this local workflow in the same
Linux/WSL environment as the executable so the binary, settings includes,
and data paths share a filesystem namespace.

Software-only stand-ins and CAD estimate
-----------------------------------------

``tests/fixtures/calibration_standins`` contains small deterministic dark and
flat NetCDF captures, an NPZ raw-calibration bundle, and a GRASP calibration
JSON profile. These are synthetic software-test fixtures, each marked
``synthetic_not_for_science``. They exercise rejection guards; do not use them
for instrument calibration, field processing, or scientific GRASP output.
The calibration and conversion loaders reject the marked captures, bundle,
and profile.

The same directory contains ``camera_gps_step_approx.json``, extracted from
the ``LHMP.step`` assembly placements. It records the relative orientation and
origin offset between the selected PHOENIX camera component frame
(``#16792``/``#660609``) and GPS module component frame
(``#16772``/``#659711``). The STEP declares metres; the camera origin is
approximately 41.3 mm, 18.8 mm, and 80.7 mm along the GPS module frame axes.
The GPS module frame is not an ENU, north, or heading reference; GPS provides
location, not camera heading.

``camera_imu_step_approx.json`` records a candidate camera-to-IMU transform
using STEP occurrence ``#17269`` (``NAUO498`` / ``Part 56``), whose 3 x 3 x
1 mm geometry is consistent with the ICM-20948 package. The component-side
axis marking on Adafruit's `pinout page
<https://learn.adafruit.com/adafruit-tdk-invensense-icm-20948-9-dof-imu/pinouts>`_
shows +X toward the left and +Y toward the top; the page links the
`ICM-20948 datasheet
<https://invensense.tdk.com/wp-content/uploads/2016/06/DS-000189-ICM-20948-v1.3.pdf>`_.
Using those axes, the camera convention in ``look_vectors.py`` (+X image
right, +Y boresight, +Z up), and your stated alignment of IMU +Z with camera
+Y gives ``+X_imu = -X_camera``, ``+Y_imu = +Z_camera``, and
``+Z_imu = +Y_camera``. This is a right-handed rotation and agrees with the
candidate STEP component placement. The estimate assumes the CAD ``Part 56``
is the installed sensor package and that “parallel” means the same direction,
not merely a parallel axis.

The estimate is not applied in L1 or GRASP processing. Confirm the physical
mounting, positive-Z direction, and package-axis mapping on the installed unit.
It does not calibrate IMU attitude or magnetic heading, nor does it provide the
camera-to-GRASP scattering-plane transform; the latter still requires the
polarimetric reference-frame calibration described above.

Conversion samples every 128th pixel by default to keep SDATA size practical.
It reads only the calibrated fields already stored in L1::

    python netcdf_to_grasp.py "B:\\Hampton_University\\HU_Polarimetry_Lab\\L1_data" `
        --pixel-stride 128

Set ``--pixel-stride`` to change spatial sampling. A directory conversion
validates every NetCDF file before writing any output. It stops if any input
is raw-only, lacks calibration metadata, or has not passed the physical
reference-frame and camera/IMU checks. Outputs are written as GRASP
``SDATA version 2.0`` files in ``grasp_sdata``. No cloud screening is
performed; available pixels are marked clear in the SDATA file.
