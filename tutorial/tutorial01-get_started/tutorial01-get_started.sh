#!/bin/sh
# Run a 40-day, non-MPI CaMa-Flood simulation on the Mekong sample.
# Map: map/mekong_15min; forcing: monthly files under inp/repo-mek_1deg_bin/runoff (daily mm/day).
# Outputs, executable, and namelist: out/${PROJ}/ under this tutorial directory.
#
# Execution requirement:
#   Run this script from the tutorial/tutorial01-get_started/ directory.
#
# Example:
#   cd tutorial/tutorial01-get_started
#   ./tutorial01-get_started.sh
# Stop if a command fails or an unset variable is used.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# Resolve the script directory so tutorial outputs remain beside this workflow.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)

# Project name follows the convention used by other tutorial experiment scripts.
PROJ="tutorial01-get_started"

# Keep every product of this experiment in its own directory under out/.
RUNDIR="${SCRIPT_DIR}/out/${PROJ}"

# -------------------------- User settings ------------------------------
# Simulation interval. The end time is exclusive; this interval is 40 days.
START_YEAR=2000               # Start year.
START_MONTH=1                 # Start month.
START_DAY=1                   # Start day.
START_HOUR=0                  # Start hour (00:00).
END_YEAR=2000                 # End year.
END_MONTH=2                   # End month.
END_DAY=10                    # End day, at 00:00 (exclusive).
END_HOUR=0                    # End hour (00:00).

# River map configuration.
MAPDIR="${CMF_V50_ROOT}/map/mekong_15min"

# River network connectivity.
# nextxy.nc:        Includes rivers draining outside the regional domain.
# nextxy_noedge.nc: Excludes river networks affected by regional boundaries (default).
#NEXTXY="${MAPDIR}/nextxy.nc"
NEXTXY="${MAPDIR}/nextxy_noedge.nc"

# River channel width.
# rivwth_merit.nc: Satellite-derived river width (default).
# rivwth.nc:       Power-law river width estimated from upstream area.
#RIVWTH="${MAPDIR}/rivwth.nc"
RIVWTH="${MAPDIR}/rivwth_merit.nc"

# CPU execution settings; this sample runs with OpenMP and without MPI.
OMP_NUM_THREADS=1             # Number of OpenMP threads (non-MPI execution).

# Model features and initial conditions.
LADPSTP=".TRUE."              # TRUE: use adaptive time stepping.
LPTHOUT=".TRUE."              # TRUE: activate bifurcation routing.
LDAMOUT=".FALSE."             # TRUE: enable reservoir operation; FALSE: disable.
LRESTART=".FALSE."            # TRUE: read restart initial conditions; FALSE: initialize without restart data.
DT=3600                       # Base timestep [s], multiple of 60; adaptive stepping may adjust it.

# Monthly Binary runoff and its matching map-specific input matrix.
ROFFTAG="repo-mek_1deg_bin"  # Runoff dataset/grid identifier.
INPMAT_TAG="repo-mek_1deg"    # Unchanged matrix for the same 20 x 30 runoff grid.
IFRQ_INP=24                   # Runoff update interval [hours]; examples: 1, 2, 3, 6, 12, 24.
DROFUNIT=86400000             # Input runoff units / DROFUNIT -> m/s; 86400000 converts mm/day.
LINPCDF=".FALSE."             # FALSE: read Binary runoff.
CROFFREQ="MON"                # Daily Binary records are grouped by calendar month.
LINTERP=".TRUE."              # TRUE: map runoff with input matrix; FALSE: use nearest-grid conversion.
LITRPCDF=".TRUE."             # TRUE: read the input-mapping matrix from NetCDF.
CROFPRE="Roff____"            # Monthly filename prefix: Roff____YYYYMM.one.
CROFSUF=".one"                # Binary runoff filename suffix.
LLEAPYR=".TRUE."              # Use the Gregorian leap-year calendar.

# Daily NetCDF output settings.
CVARSOUT="outflw,storge,sfcelv,flddph,fldfrc"  # Variables saved in NetCDF output.
IFRQ_OUT=24                   # Output interval [hours]; examples: 1, 2, 3, 6, 12, 24.
LOUTCDF=".TRUE."              # TRUE: write NetCDF; FALSE: write binary output.
LRESTCDF=".TRUE."             # TRUE: write a NetCDF Restart; FALSE: write Binary Restart.

# Model output directory, relative to the model execution directory.
# "./" means outputs are saved in RUNDIR,
# because CaMa-Flood is executed after "cd ${RUNDIR}".
COUTDIR="./"

# Restart output remains enabled at the model's standard end-of-run behavior.
CVNREST="restart"            # Prefix used for restart-output filenames.
IFRQ_RST=0                    # 0=end only; 1-24=hour interval; 30=monthly (nonzero also writes at end).
# ----------------------------------------------------------------------
# User settings end here. Paths, namelist generation, and execution follow.
# ----------------------------------------------------------------------

TOTAL_STEPS=3
cmf_check_init "Tutorial01 40-day Mekong simulation"

# Reference input directory for monthly Binary runoff files.
RUNOFF_DIR="${CMF_V50_ROOT}/inp/${ROFFTAG}/runoff"

# The dimension descriptor and matrix were generated for this map/runoff pair.
DIMINFO="${MAPDIR}/diminfo_${INPMAT_TAG}.nml"
INPMAT="${MAPDIR}/inpmat_${INPMAT_TAG}.nc"

# Source executable; a copy is placed in RUNDIR and executed there.
EXEC_CMF="${CMF_V50_ROOT}/src_main/MAIN_cmf"
NAMELIST="${RUNDIR}/input_cmf.nam"
MODEL_LOG="${RUNDIR}/log_CaMa.txt"
CONSOLE_LOG="${RUNDIR}/run.stdout.log"
RUN_TIME_LOG="${RUNDIR}/run_time.log"

# Replace only files generated by this sample; leave other files in RUNDIR untouched.
cmf_check_step 1 "${TOTAL_STEPS}" "Prepare the Tutorial01 Mekong experiment directory"
printf 'CMF_V50_ROOT = %s\n' "${CMF_V50_ROOT}"
printf 'PROJ = %s\n' "${PROJ}"
printf 'RUNDIR = %s\n' "${RUNDIR}"
printf 'MAPDIR = %s\n' "${MAPDIR}"
printf 'RUNOFF_DIR = %s\n' "${RUNOFF_DIR}"
printf 'Overwriting previous sample results in: %s\n' "${RUNDIR}"

mkdir -p "${RUNDIR}"
rm -f "${RUNDIR}/MAIN_cmf" \
    "${RUNDIR}/input_cmf.nam" "${RUNDIR}/log_CaMa.txt" \
    "${RUNDIR}/mapdata.txt" "${RUNDIR}/mapdata.nml" \
    "${RUNDIR}/run.stdout.log" "${RUNDIR}/run_time.log"

# Remove this sample's output variables, including old tags and the former pthflw output.
rm -f "${RUNDIR}/outflw"* "${RUNDIR}/storge"* "${RUNDIR}/sfcelv"* \
    "${RUNDIR}/flddph"* "${RUNDIR}/fldfrc"* "${RUNDIR}/pthflw"* \
    "${RUNDIR}/o_outflw"* "${RUNDIR}/o_storge"* "${RUNDIR}/o_sfcelv"* \
    "${RUNDIR}/o_flddph"* "${RUNDIR}/o_fldfrc"* "${RUNDIR}/o_pthflw"*

# Restart files use the configured prefix and may include a bifurcation .pth companion.
rm -f "${RUNDIR}/${CVNREST}"*

cp "${EXEC_CMF}" "${RUNDIR}/MAIN_cmf"

# Run in RUNDIR so the namelist, model logs, restart, and default outputs stay together.
cd "${RUNDIR}"

# Write the namelist in the run directory; the model reads input_cmf.nam from its CWD.
cmf_check_step 2 "${TOTAL_STEPS}" "Configure the Tutorial01 Mekong simulation"
cat > input_cmf.nam <<EOF
&NRUNVER
LADPSTP  = ${LADPSTP}        ! TRUE: use adaptive time stepping.
LPTHOUT  = ${LPTHOUT}        ! TRUE: activate bifurcation routing.
LDAMOUT  = ${LDAMOUT}        ! TRUE: enable reservoir operation; FALSE: disable.
LRESTART = ${LRESTART}       ! TRUE: read restart initial conditions; FALSE: initialize without restart data.
LLEAPYR = ${LLEAPYR}         ! TRUE: use Gregorian calendar including February 29.
/
&NDIMTIME
CDIMINFO = "${DIMINFO}"       ! Map and runoff-grid dimensions and input-matrix metadata.
DT       = ${DT}             ! Base timestep [s], multiple of 60; adaptive stepping may adjust it.
IFRQ_INP = ${IFRQ_INP}       ! Runoff update interval [hours]; examples: 1, 2, 3, 6, 12, 24.
/
&NPARAM
PMANRIV  = 0.03D0            ! River Manning roughness coefficient [s m-1/3].
PMANFLD  = 0.10D0            ! Floodplain Manning roughness coefficient [s m-1/3].
PDSTMTH  = 10000.D0          ! Downstream distance at river mouth [m].
PCADP    = 0.7D0             ! CFL coefficient for adaptive time-step control [-].
/
&NSIMTIME
SYEAR = ${START_YEAR}        ! Simulation start year.
SMON  = ${START_MONTH}       ! Simulation start month.
SDAY  = ${START_DAY}         ! Simulation start day.
SHOUR = ${START_HOUR}        ! Simulation start hour [0-23].
EYEAR = ${END_YEAR}          ! Simulation end year (end time is exclusive).
EMON  = ${END_MONTH}         ! Simulation end month (end time is exclusive).
EDAY  = ${END_DAY}           ! Simulation end day (end time is exclusive).
EHOUR = ${END_HOUR}          ! Simulation end hour (end time is exclusive).
/
&NMAP
LMAPCDF = .FALSE.                   ! FALSE: read individual NetCDF files; TRUE: legacy consolidated NetCDF maps.
CNEXTXY = "${NEXTXY}"               ! River-network downstream connectivity.
CGRAREA = "${MAPDIR}/ctmare.nc"     ! Unit catchment area [m2].
CELEVTN = "${MAPDIR}/elevtn.nc"     ! River-bank elevation [m].
CNXTDST = "${MAPDIR}/nxtdst.nc"     ! Distance to downstream outlet [m].
CRIVLEN = "${MAPDIR}/rivlen.nc"     ! River channel length [m].
CFLDHGT = "${MAPDIR}/fldhgt.nc"     ! Floodplain elevation profile [m].
CRIVWTH = "${RIVWTH}"               ! River channel width [m].
CRIVHGT = "${MAPDIR}/rivhgt.nc"     ! River channel depth [m].
CRIVMAN = "${MAPDIR}/rivman.nc"     ! River Manning roughness [s m-1/3].
CPTHOUT = "${MAPDIR}/bifprm.csv"    ! Bifurcation channel parameters.
/
&NRESTART
CRESTDIR = "./"              ! Restart-output directory relative to the run directory.
CVNREST  = "${CVNREST}"      ! Prefix for restart-output filenames.
LRESTCDF = ${LRESTCDF}        ! TRUE: write NetCDF Restart; FALSE: write Binary Restart.
IFRQ_RST = ${IFRQ_RST}       ! 0=end only; 1-24=hour interval; 30=monthly (nonzero also writes at end).
/
&NFORCE
LINPCDF  = ${LINPCDF}         ! FALSE: read Binary runoff; TRUE: read NetCDF runoff.
CROFFREQ = "${CROFFREQ}"     ! Monthly files contain daily records indexed from month start.
LINTERP  = ${LINTERP}         ! TRUE: map runoff with input matrix; FALSE: use nearest-grid conversion.
LITRPCDF  = ${LITRPCDF}        ! TRUE: read the input-mapping matrix from NetCDF.
CINPMAT  = "${INPMAT}"        ! NetCDF runoff-to-river input-mapping matrix.
DROFUNIT = ${DROFUNIT}        ! Input runoff units / DROFUNIT -> m/s; 86400000 converts mm/day.
CROFDIR  = "${RUNOFF_DIR}"    ! Directory containing runoff input files.
CROFPRE  = "${CROFPRE}"      ! Monthly Binary filename prefix before YYYYMM.
CROFSUF  = "${CROFSUF}"      ! Binary runoff filename suffix.
/
&NOUTPUT
CMF_BASE = "${CMF_V50_ROOT}"   ! CaMa-Flood repository/package root.
COUTVAR_TABLE = ""              ! Defaults to CMF_BASE/variable_table/output_variables.csv.
COUTDIR  = "${COUTDIR}"       ! Output directory relative to the model run directory.
CVARSOUT = "${CVARSOUT}"      ! Comma-separated list of output variables.
COUTTAG  = "${START_YEAR}"    ! Tag appended to output filenames.
LOUTVEC  = .FALSE.            ! TRUE: write vector output; FALSE: write gridded XY output.
LOUTCDF  = ${LOUTCDF}         ! TRUE: write NetCDF; FALSE: write binary output.
IFRQ_OUT = ${IFRQ_OUT}        ! Output interval [hours]; examples: 1, 2, 3, 6, 12, 24.
/
EOF

# Run the 40-day NetCDF experiment as one continuous period.
cmf_check_step 3 "${TOTAL_STEPS}" \
    "Run CaMa-Flood v5 from ${START_YEAR} to ${END_YEAR}-${END_MONTH}-${END_DAY}"

# Measure only the model process; setup and executable-copy time are excluded.
START_DATETIME=$(date)
printf 'Start: %s\n' "${START_DATETIME}" | tee "${RUN_TIME_LOG}"
START_TIME=$(date +%s)

if OMP_NUM_THREADS="${OMP_NUM_THREADS}" ./MAIN_cmf > "${CONSOLE_LOG}" 2>&1; then
    RUN_STATUS=0
else
    RUN_STATUS=${?}
fi

END_TIME=$(date +%s)
END_DATETIME=$(date)
ELAPSED_SECONDS=$((END_TIME - START_TIME))
{
    printf 'End: %s\n' "${END_DATETIME}"
    printf 'Elapsed time: %s seconds\n' "${ELAPSED_SECONDS}"
    printf 'Exit status: %s\n' "${RUN_STATUS}"
} | tee -a "${RUN_TIME_LOG}"

if [ "${RUN_STATUS}" -ne 0 ]; then
    exit "${RUN_STATUS}"
fi

cmf_check_success
printf 'Results: %s\n' "${RUNDIR}"
printf 'Model log: %s\n' "${MODEL_LOG}"
printf 'Console log: %s\n' "${CONSOLE_LOG}"
