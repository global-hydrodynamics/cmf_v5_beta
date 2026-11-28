#!/bin/sh
# Run the mek_nobif Tutorial 02 experiment for 2000-2003.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# Keep tutorial outputs beside this script, regardless of the launch directory.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
PROJ="mek_nobif"                 # Experiment name and output directory.
START_YEAR=2000                # First calendar year (spin-up).
END_YEAR=2003                  # Last calendar year; exclusive model end is January 1, 2004.
OMP_NUM_THREADS=4              # OpenMP threads for this non-MPI sample.
DT=600                         # Model timestep [s].
LKINE=".FALSE."              # TRUE: Kinematic Wave; FALSE: Local Inertial routing.
LFPLAIN=".TRUE."            # TRUE: include floodplain storage representation.
LPTHOUT=".FALSE."           # TRUE: activate bifurcation routing.
LDAMOUT=".FALSE."               # TRUE: enable reservoir operation.
LFLDOUT=".TRUE."                # TRUE: enable high-water channel flow.
LSLPMIX=".FALSE."               # TRUE: use mixed kinematic/local-inertial routing.
LADPSTP=".TRUE."           # TRUE: adaptive timestep; FALSE: fixed DT.

# ----------------------------------------------------------------------
# User settings end here. Input paths and annual execution follow.
# ----------------------------------------------------------------------
MAPDIR="${CMF_V50_ROOT}/map/mekong_15min"
MAP_NETCDF_DIR="${MAPDIR}"
RUNOFF_DIR="${CMF_V50_ROOT}/inp/repo-mek_1deg"
RUNDIR="${SCRIPT_DIR}/out/${PROJ}"
# Reuse the NetCDF-enabled model already built in Tutorial01; do not compile here.
EXEC_CMF="${CMF_V50_ROOT}/src_main/MAIN_cmf"
DIMINFO="${MAPDIR}/diminfo_repo-mek_1deg.nml"
INPMAT="${MAPDIR}/inpmat_repo-mek_1deg.nc"

YEAR_COUNT=$((END_YEAR - START_YEAR + 1))
TOTAL_STEPS=$((1 + 2 * YEAR_COUNT))
STEP_NUMBER=0
cmf_check_init "Tutorial02 ${PROJ} annual NetCDF simulation"

STEP_NUMBER=$((STEP_NUMBER + 1))
cmf_check_step "$STEP_NUMBER" "$TOTAL_STEPS" "Prepare ${PROJ} experiment directory"

if [ ! -x "$EXEC_CMF" ]; then
    printf '[ERROR] Tutorial01 model executable not found: %s\n' "$EXEC_CMF" >&2
    exit 1
fi

# Dedicated experiment output directory; remove only this sample's known products.
mkdir -p "$RUNDIR"
rm -f "$RUNDIR"/o_outflw*.nc "$RUNDIR"/restart*.nc \
      "$RUNDIR"/input_cmf*.nam "$RUNDIR"/console_*.log \
      "$RUNDIR"/log_CaMa*.nml "$RUNDIR"/log_CaMa*.txt "$RUNDIR"/run_time_*.log \
      "$RUNDIR"/MAIN_cmf "$RUNDIR"/mapdata.nml
cp "$EXEC_CMF" "$RUNDIR/MAIN_cmf"

# Run one calendar year at a time and pass the previous year's final Restart.
YEAR=$START_YEAR
while [ "$YEAR" -le "$END_YEAR" ]; do
    NEXT_YEAR=$((YEAR + 1))
    RUNOFF_FILE="${RUNOFF_DIR}/runoff${YEAR}.nc"
    YEAR_NAMELIST="${RUNDIR}/input_cmf_${YEAR}.nam"
    STEP_NUMBER=$((STEP_NUMBER + 1))
    cmf_check_step "$STEP_NUMBER" "$TOTAL_STEPS" "Configure year ${YEAR}"
    if [ ! -f "$RUNOFF_FILE" ]; then
        printf '[ERROR] Missing annual runoff file: %s\n' "$RUNOFF_FILE" >&2
        exit 1
    fi

    if [ "$YEAR" -eq "$START_YEAR" ]; then
        LRESTART=".FALSE."
        CRESTSTO="NONE"
    else
        PREVIOUS_RESTART="${RUNDIR}/restart$(printf '%04d010100' "$YEAR").nc"
        if [ ! -f "$PREVIOUS_RESTART" ]; then
            printf '[ERROR] Missing Restart for year %s: %s\n' "$YEAR" "$PREVIOUS_RESTART" >&2
            exit 1
        fi
        LRESTART=".TRUE."
        CRESTSTO="$PREVIOUS_RESTART"
    fi

    cat > "$RUNDIR/input_cmf.nam" <<EOF
&NRUNVER
LKINE = $LKINE             ! Routing formulation: Kinematic Wave or Local Inertial.
LFPLAIN = $LFPLAIN         ! TRUE: represent floodplain storage capacity.
LPTHOUT = $LPTHOUT         ! TRUE: route flow through bifurcation paths.
LDAMOUT = .FALSE.           ! TRUE: enable reservoir operation.
LFLDOUT = .TRUE.            ! TRUE: enable high-water channel flow.
LSLPMIX = .FALSE.           ! TRUE: mix Kinematic and Local Inertial routing.
LADPSTP = $LADPSTP         ! TRUE: adaptive timestep; FALSE: fixed DT.
LRESTART = $LRESTART       ! TRUE: read the preceding year's Restart.
LLEAPYR = .TRUE.           ! TRUE: use Gregorian calendar including February 29.
/
&NDIMTIME
CDIMINFO = "$DIMINFO"       ! Map and runoff-grid dimensions.
DT = $DT                   ! Base model timestep [s].
IFRQ_INP = 24              ! Daily runoff update interval [hours].
/
&NPARAM
PMANRIV = 0.03D0           ! River Manning roughness coefficient [s m-1/3].
PMANFLD = 0.10D0           ! Floodplain Manning roughness coefficient [s m-1/3].
PDSTMTH = 10000.D0         ! Downstream distance assigned at a river mouth [m].
PCADP = 0.7D0              ! CFL coefficient for adaptive timestep control [-].
/
&NSIMTIME
SYEAR = $YEAR              ! Start year for this annual segment.
SMON = 1                   ! Start month.
SDAY = 1                   ! Start day.
SHOUR = 0                  ! Start hour [0-23].
EYEAR = $NEXT_YEAR          ! Exclusive end year (January 1).
EMON = 1                   ! Exclusive end month.
EDAY = 1                   ! Exclusive end day.
EHOUR = 0                  ! Exclusive end hour.
/
&NMAP
LMAPCDF = .FALSE.                         ! FALSE: read individual map files by their extensions.
CNEXTXY = "$MAP_NETCDF_DIR/nextxy_noedge.nc" ! River-network downstream indices.
CGRAREA = "$MAP_NETCDF_DIR/ctmare.nc"     ! Unit-catchment area [m2].
CELEVTN = "$MAP_NETCDF_DIR/elevtn.nc"     ! Channel-top elevation [m].
CNXTDST = "$MAP_NETCDF_DIR/nxtdst.nc"     ! Distance to downstream catchment [m].
CRIVLEN = "$MAP_NETCDF_DIR/rivlen.nc"     ! River length within catchment [m].
CFLDHGT = "$MAP_NETCDF_DIR/fldhgt.nc"     ! Floodplain elevation profile [m].
CRIVWTH = "$MAP_NETCDF_DIR/rivwth_merit.nc" ! MERIT-derived channel width [m].
CRIVHGT = "$MAP_NETCDF_DIR/rivhgt.nc"     ! River-channel depth [m].
CRIVMAN = "$MAP_NETCDF_DIR/rivman.nc"     ! River Manning roughness coefficient.
CPTHOUT = "$MAP_NETCDF_DIR/bifprm.nc"    ! Bifurcation channel paths (used when enabled).
/
&NRESTART
CRESTSTO = "$CRESTSTO"    ! Input Restart; NONE for the initial segment.
CRESTDIR = "./"            ! Restart output directory relative to run directory.
CVNREST = "restart"        ! Prefix for dated Restart files.
LRESTCDF = .TRUE.           ! TRUE: write NetCDF Restart files.
IFRQ_RST = 0                ! 0: write Restart at the segment end.
/
&NFORCE
LINPCDF = .TRUE.            ! TRUE: read NetCDF runoff.
CROFFREQ = "YEAR"          ! One runoff file per calendar year.
LINTERP = .TRUE.            ! TRUE: map runoff using the input matrix.
LITRPCDF = .TRUE.           ! TRUE: read the input-mapping matrix from NetCDF.
CINPMAT = "$INPMAT"        ! NetCDF runoff-to-river input matrix.
DROFUNIT = 86400000         ! Divide daily mm input by this factor to obtain m/s.
CVNTIME = "time"            ! CF time-coordinate variable.
CVNROF = "runoff"           ! Runoff variable in annual files.
CROFDIR = "$RUNOFF_DIR"    ! Annual runoff NetCDF directory.
CROFPRE = "runoff"          ! Annual filename prefix: runoffYYYY.nc.
CROFSUF = ".nc"             ! Annual filename suffix.
/
&NOUTPUT
CMF_BASE = "${CMF_V50_ROOT}" ! CaMa-Flood repository root.
COUTVAR_TABLE = ""           ! Use the output-variable registry under CMF_BASE.
COUTDIR = "./"               ! Write model output in this annual run directory.
CVARSOUT = "outflw"          ! Daily mean river/floodplain discharge [m3/s].
COUTTAG = "$YEAR"            ! Annual tag in the output filename.
LOUTVEC = .FALSE.             ! FALSE: write gridded XY output.
LOUTCDF = .TRUE.              ! TRUE: write NetCDF output.
IFRQ_OUT = 24                 ! Daily output interval [hours].
/
EOF
    cp "$RUNDIR/input_cmf.nam" "$YEAR_NAMELIST"

    STEP_NUMBER=$((STEP_NUMBER + 1))
    cmf_check_step "$STEP_NUMBER" "$TOTAL_STEPS" "Run year ${YEAR}"
    START_SECONDS=$(date +%s)
    printf 'Start %s: %s\n' "$YEAR" "$(date)" | tee "$RUNDIR/run_time_${YEAR}.log"
    if (cd "$RUNDIR" && OMP_NUM_THREADS="$OMP_NUM_THREADS" ./MAIN_cmf > "console_${YEAR}.log" 2>&1); then
        RUN_STATUS=0
    else
        RUN_STATUS=$?
    fi
    ELAPSED_SECONDS=$(($(date +%s) - START_SECONDS))
    {
        printf 'End %s: %s\n' "$YEAR" "$(date)"
        printf 'Elapsed: %s seconds\nExit status: %s\n' "$ELAPSED_SECONDS" "$RUN_STATUS"
    } | tee -a "$RUNDIR/run_time_${YEAR}.log"
    if [ "$RUN_STATUS" -ne 0 ]; then
        printf '[ERROR] %s failed in year %s; see %s/console_%s.log\n' \
            "$PROJ" "$YEAR" "$RUNDIR" "$YEAR" >&2
        exit "$RUN_STATUS"
    fi
    cp "$RUNDIR/log_CaMa.txt" "$RUNDIR/log_CaMa_${YEAR}.txt"
    printf '[SUCCESS] %s %s complete: %s/o_outflw%s.nc\n' \
        "$PROJ" "$YEAR" "$RUNDIR" "$YEAR"
    YEAR=$NEXT_YEAR
done

cmf_check_success
printf 'Annual simulations %s-%s completed.\n' "$START_YEAR" "$END_YEAR"
printf 'Results: %s\n' "$RUNDIR"
