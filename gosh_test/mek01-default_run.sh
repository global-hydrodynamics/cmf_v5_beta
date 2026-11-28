#!/bin/sh
# Run a 40-day, non-MPI CaMa-Flood simulation on the Mekong sample.
# Map: map/mekong_15min; forcing: inp/repo-mek_1deg_bin (daily mm/day, monthly files).
# Output, executable, and namelist: gosh_test/out/${PROJ}/.
#
# Normally run from gosh_test/; launching from the repository root also works.
#
# Example:
#   cd gosh_test
#   ./mek01-default_run.sh
set -eu

# CaMa-Flood root; resolve it from this script so either supported launch directory works.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
CMF_V50_ROOT=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# -------------------------- User settings ------------------------------
# Project/output settings. ${VAR:-default} uses the environment value when nonempty.
PROJ=${PROJ:-mek01} # Project name; override with PROJ=name when launching.
RUNDIR=${RUNDIR:-"${CMF_V50_ROOT}/gosh_test/out/${PROJ}"} # Explicit RUNDIR takes precedence.

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
OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}  # Number of OpenMP threads (non-MPI execution).

# Model features and initial conditions.
LADPSTP=".TRUE."              # TRUE: use adaptive time stepping.
LPTHOUT=".TRUE."              # TRUE: activate bifurcation routing.
LDAMOUT=".FALSE."             # TRUE: enable reservoir operation; FALSE: disable.
LRESTART=".FALSE."            # TRUE: read restart initial conditions; FALSE: initialize without restart data.
DT=3600                       # Base timestep [s], multiple of 60; adaptive stepping may adjust it.

# Daily Binary runoff in monthly files; reuse the unchanged regional input matrix.
ROFFTAG="repo-mek_1deg_bin"   # Select inp/repo-mek_1deg_bin/runoff.
INPMAT_TAG="repo-mek_1deg"     # Existing input matrix for the identical 20 x 30 grid.
IFRQ_INP=24                   # Runoff update interval [hours]; examples: 1, 2, 3, 6, 12, 24.
DROFUNIT=86400000             # Input runoff units / DROFUNIT -> m/s; 86400000 converts mm/day.
LINPCDF=".FALSE."             # TRUE: read NetCDF runoff; FALSE: read binary runoff.
CROFFREQ="MON"               # Daily records indexed from 00:00 at each month start.
LINTERP=".TRUE."              # TRUE: map runoff with input matrix; FALSE: use nearest-grid conversion.
LITRPCDF=".TRUE."             # TRUE: read the input-mapping matrix from NetCDF.
CROFPRE="Roff____"            # Monthly filename prefix: Roff____YYYYMM.one.
CROFSUF=".one"                # Monthly filename suffix.

# Daily binary output settings.
CVARSOUT="outflw,storge,sfcelv,flddph,fldfrc"  # Variables saved in binary output.
IFRQ_OUT=24                   # Output interval [hours]; examples: 1, 2, 3, 6, 12, 24.
LOUTCDF=".FALSE."             # TRUE: write NetCDF; FALSE: write binary output.

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

if [ "${LOUTCDF}" = ".FALSE." ]; then
    TOTAL_STEPS=5
    MODEL_STEP=4
else
    TOTAL_STEPS=4
    MODEL_STEP=3
fi
RESTART_STEP=${TOTAL_STEPS}
RUN_END_DATE=$(printf '%s-%02d-%02d' "${END_YEAR}" "${END_MONTH}" "${END_DAY}")
cmf_check_init "Prepare the Mekong experiment directory"

# Reference input directory for daily runoff files.
RUNOFF_DIR="${CMF_V50_ROOT}/inp/${ROFFTAG}/runoff"

# The dimension descriptor and matrix were generated for this map/runoff pair.
DIMINFO="${MAPDIR}/diminfo_${INPMAT_TAG}.nml"
INPMAT="${MAPDIR}/inpmat_${INPMAT_TAG}.nc"

# Source executable; a copy is placed in RUNDIR and executed there.
EXEC_CMF="${CMF_V50_ROOT}/src_main/MAIN_cmf"
NAMELIST="${RUNDIR}/input_cmf.nam"
MODEL_LOG="${RUNDIR}/log_CaMa.nml"
CONSOLE_LOG="${RUNDIR}/run.stdout.log"
RUN_TIME_LOG="${RUNDIR}/run_time.log"

# Replace only files generated by this sample; leave other files in RUNDIR untouched.
printf 'CMF_V50_ROOT = %s\n' "${CMF_V50_ROOT}"
printf 'PROJ = %s\n' "${PROJ}"
printf 'RUNDIR = %s\n' "${RUNDIR}"
printf 'MAPDIR = %s\n' "${MAPDIR}"
printf 'RUNOFF_DIR = %s\n' "${RUNOFF_DIR}"
printf 'Overwriting previous sample results in: %s\n' "${RUNDIR}"

cmf_check_step 1 "${TOTAL_STEPS}" "Prepare the Mekong experiment directory"
mkdir -p "${RUNDIR}"
rm -f "${RUNDIR}/MAIN_cmf" \
    "${RUNDIR}/input_cmf.nam" "${RUNDIR}/log_CaMa.nml" \
    "${RUNDIR}/mapdata.nml" "${RUNDIR}/run.stdout.log" "${RUNDIR}/run_time.log"

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
cmf_check_step 2 "${TOTAL_STEPS}" "Configure the Mekong simulation"
cat > input_cmf.nam <<EOF
&NRUNVER
LADPSTP  = ${LADPSTP}        ! TRUE: use adaptive time stepping.
LPTHOUT  = ${LPTHOUT}        ! TRUE: activate bifurcation routing.
LDAMOUT  = ${LDAMOUT}        ! TRUE: enable reservoir operation; FALSE: disable.
LRESTART = ${LRESTART}       ! TRUE: read restart initial conditions; FALSE: initialize without restart data.
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
LRESTCDF = .FALSE.           ! TRUE: write NetCDF restart; FALSE: write binary restart.
IFRQ_RST = ${IFRQ_RST}       ! 0=end only; 1-24=hour interval; 30=monthly (nonzero also writes at end).
/
&NFORCE
LINPCDF  = ${LINPCDF}         ! TRUE: read NetCDF runoff; FALSE: read binary runoff.
CROFFREQ = "${CROFFREQ}"     ! Explicit grouping mode; DAY/MON/YEAR/SEQ.
LINTERP  = ${LINTERP}         ! TRUE: map runoff with input matrix; FALSE: use nearest-grid conversion.
LITRPCDF  = ${LITRPCDF}        ! TRUE: read the input-mapping matrix from NetCDF.
CINPMAT  = "${INPMAT}"        ! NetCDF runoff-to-river input-mapping matrix.
DROFUNIT = ${DROFUNIT}        ! Input runoff units / DROFUNIT -> m/s; 86400000 converts mm/day.
CROFDIR  = "${RUNOFF_DIR}"    ! Directory containing runoff input files.
CROFPRE  = "${CROFPRE}"       ! Runoff filename prefix before the date.
CROFSUF  = "${CROFSUF}"       ! Runoff filename suffix.
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

# Create descriptors before the model starts so GrADS can inspect written records during a run.
if [ "${LOUTCDF}" = ".FALSE." ]; then
    cmf_check_step 3 "${TOTAL_STEPS}" "Generate planned binary-output CTLs"
    if python3 "${CMF_V50_ROOT}/tools/scripts/generate_output_ctl.py" \
        --run-dir "${RUNDIR}" \
        --mode planned; then
        :
    else
        CTL_STATUS=${?}
        printf '[ERROR] CTL generation failed; the CaMa-Flood model was not started.\n' >&2
        exit "${CTL_STATUS}"
    fi
fi

# Run one continuous period so the model reads daily files across the month boundary.
cmf_check_step "${MODEL_STEP}" "${TOTAL_STEPS}" \
    "Run CaMa-Flood v5 from ${START_YEAR} to ${RUN_END_DATE}"

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

cmf_check_step "${RESTART_STEP}" "${TOTAL_STEPS}" "Generate GrADS CTLs for Binary Restart files"
python3 "${CMF_V50_ROOT}/tools/scripts/generate_restart_ctl.py" --run-dir "${RUNDIR}"

printf 'Results: %s\n' "${RUNDIR}"
printf 'Model log: %s\n' "${MODEL_LOG}"
printf 'Console log: %s\n' "${CONSOLE_LOG}"
cmf_check_success
