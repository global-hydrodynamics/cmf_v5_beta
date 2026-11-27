#!/bin/sh
# Run the Tutorial 11 Rhine 2021 cold-start hourly experiment.
# Outputs are kept in the Git-ignored experiment/Rhine2021/ directory.
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
CMF_BASE=$(CDPATH= cd "$TUTORIAL_DIR/../.." && pwd -P)

# -------------------------- User settings ------------------------------
PYTHON="python3" # Python for reading Step13 metadata; no model computation.
EXEC_CMF="${CMF_BASE}/src_main/MAIN_cmf" # Existing executable; not rebuilt here.
RESTART_INPUT="NONE" # Restart file path, or NONE for the default cold start.
PROJ="Rhine2021"                                                     # Experiment directory name (not the independent output COUTTAG).
RUNDIR=${RUNDIR:-"${TUTORIAL_DIR}/experiment/${PROJ}"}                 # Run directory; existing RUNDIR override supported; nonempty directories are preserved.

# Simulation interval; the end time is exclusive (31 days, 744 hours).
START_YEAR=2021                                                      # Inclusive start year [UTC Gregorian calendar].
START_MONTH=7                                                        # Inclusive start month [1–12 UTC].
START_DAY=1                                                          # Inclusive start day [calendar day UTC].
START_HOUR=0                                                         # Inclusive start hour [0–23 UTC].
END_YEAR=2021                                                        # Exclusive end year [UTC].
END_MONTH=8                                                          # Exclusive end month [1–12 UTC].
END_DAY=1                                                            # Exclusive end day [calendar day UTC].
END_HOUR=0                                                           # Exclusive end hour [0–23 UTC].
MAPDIR="${CMF_BASE}/map/Rhine_15min"                                 # Matching regional map root.
MAP_NETCDF_DIR="${MAPDIR}/netcdf"                                    # Individual NetCDF map directory.
NEXTXY="${MAP_NETCDF_DIR}/nextxy.nc"                                 # Stored downstream connectivity; select an existing map product.
RIVWTH="${MAP_NETCDF_DIR}/rivwth_merit.nc"                           # River-channel width map [m].

# Step 13 metadata is the source of the regional matrix tag and paired file paths.
STEP13_METADATA="${TUTORIAL_DIR}/metadata/13_runoff_input_matrix.json" # Authoritative regional Input Matrix/diminfo handoff; do not duplicate its values.
RUNOFF_DIR="${CMF_BASE}/inp/tutorial11-ERA5land-Rhine2021Jul"        # Runoff input directory matching the matrix grid.
IFRQ_INP=1                                                           # Runoff update interval [hours].
DROFUNIT=3600000                                                     # Divide input values by this factor to obtain depth rate [m/s]; current mm/hour.
CVNROF="runoff"                                                      # Input NetCDF runoff variable name.
CVNTIME="time"                                                       # Input NetCDF time-coordinate variable name.
CROFPRE="runoff_"                                                    # Filename prefix before date.
CROFSUF=".nc"                                                        # Filename suffix after date.
LINPCDF=".TRUE."                                                     # Fortran logical .TRUE./.FALSE.; input NetCDF enabled by default.
CROFFREQ="DAY"                                                       # Input grouping DAY/MON/YEAR/SEQ; must match prepared files.
LINTERP=".TRUE."                                                     # Fortran logical; .TRUE. uses the Step13 runoff mapping.
LITRPCDF=".TRUE."             # Read the input-mapping matrix from NetCDF.
OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}                                # OpenMP threads [positive integer]; existing env override supported.
DT=3600                                                              # Base timestep [s]; adaptive stepping may shorten it.
LADPSTP=".TRUE."                                                     # Fortran logical; enable adaptive timestep.
LPTHOUT=".TRUE."                                                     # Fortran logical; enable stored bifurcation routing.
LDAMOUT=".FALSE."                                                    # Fortran logical; reservoir operation requires matching data.
LRESTART=".FALSE."                                                   # Fortran logical; .TRUE. requires RESTART_INPUT instead of NONE.
PMANRIV="0.03D0"                                                     # River Manning roughness [s m^-1/3], Fortran real literal.
PMANFLD="0.10D0"                                                     # Floodplain Manning roughness [s m^-1/3], Fortran real literal.
PDSTMTH="10000.D0"                                                   # Mouth downstream distance [m], Fortran real literal.
PCADP="0.7D0"                                                        # Adaptive timestep CFL coefficient [-], Fortran real literal.
LOUTCDF=".TRUE."                                                     # Fortran logical; output NetCDF instead of Binary.
IFRQ_OUT=1                                                           # Model output interval [hours].
CVARSOUT="outflw,pthflw,storge,sfcelv,rivdph,flddph,fldfrc,fldare"   # Comma-separated output Registry variable IDs.
COUTTAG="Rhine2021Jul"                                               # Output filename experiment tag.
LRESTCDF=".TRUE."                                                    # Fortran logical; Restart output NetCDF instead of Binary.
IFRQ_RST=0                                                           # Restart interval [hours]; 0: end only.
CVNREST="restart"                                                    # Restart filename prefix.
# User settings end here. Paths and the one continuous model run follow.
# ----------------------------------------------------------------------

ROFFTAG=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["generator"]["settings"]["ROFFTAG"])' "$STEP13_METADATA")
INPMAT_REL=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["outputs"]["input_matrix"])' "$STEP13_METADATA")
DIMINFO_REL=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["outputs"]["dimension_info"])' "$STEP13_METADATA")
INPMAT="${CMF_BASE}/${INPMAT_REL}"
DIMINFO="${CMF_BASE}/${DIMINFO_REL}"
NAMELIST="${RUNDIR}/input_cmf.nam"
CONSOLE_LOG="${RUNDIR}/console.log"
RUNTIME_LOG="${RUNDIR}/run_time.log"
SCRIPT_NAME=${0##*/}
STEP="Prepare the Rhine 2021 run directory"

trap '
    EXIT_STATUS=$?
    trap - 0
    if [ "$EXIT_STATUS" -ne 0 ]; then
        printf "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" >&2
        printf "!!! ERROR: %s FAILED !!!\n" "$SCRIPT_NAME" >&2
        printf "!!! Step: %s\n" "$STEP" >&2
        printf "!!! Exit status: %s\n" "$EXIT_STATUS" >&2
        printf "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" >&2
    fi
    exit "$EXIT_STATUS"
' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# ----------------------------------------------------------------------
# End of error handling.
# ----------------------------------------------------------------------

if [ -d "$RUNDIR" ] && [ -n "$(find "$RUNDIR" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    printf '[ERROR] Run directory is not empty; preserving its contents: %s\n' "$RUNDIR" >&2
    printf 'Set RUNDIR to a new directory to start another run.\n' >&2
    exit 2
fi

printf '\n==================================================\n'
printf '[STEP 1/3] Prepare the Rhine 2021 experiment\n'
printf '==================================================\n\n'
printf 'RUNDIR = %s\n' "$RUNDIR"
printf 'MAPDIR = %s\n' "$MAPDIR"
printf 'RUNOFF_DIR = %s\n' "$RUNOFF_DIR"
printf 'ROFFTAG = %s\n' "$ROFFTAG"

mkdir -p "$RUNDIR"
cp "$EXEC_CMF" "${RUNDIR}/MAIN_cmf"

cat > "$NAMELIST" <<EOF
&NRUNVER
LADPSTP  = ${LADPSTP}      ! TRUE enables adaptive time stepping.
LPTHOUT  = ${LPTHOUT}      ! TRUE enables bifurcation routing.
LDAMOUT  = ${LDAMOUT}      ! FALSE disables reservoir operation.
LRESTART = ${LRESTART}     ! FALSE starts from the model's standard initial state.
/
&NDIMTIME
CDIMINFO = "${DIMINFO}"   ! Dimensions and regional runoff-grid metadata.
DT       = ${DT}           ! Base timestep [s]; adaptive stepping may reduce it.
IFRQ_INP = ${IFRQ_INP}    ! Runoff update interval [hours].
/
&NPARAM
PMANRIV  = ${PMANRIV}     ! River Manning roughness [s m-1/3], maintained sample value.
PMANFLD  = ${PMANFLD}     ! Floodplain Manning roughness [s m-1/3], maintained sample value.
PDSTMTH  = ${PDSTMTH}     ! Downstream distance assigned at a river mouth [m].
PCADP    = ${PCADP}        ! CFL coefficient for adaptive timestep control [-].
/
&NSIMTIME
SYEAR = ${START_YEAR}     ! Inclusive simulation start year.
SMON  = ${START_MONTH}    ! Inclusive simulation start month.
SDAY  = ${START_DAY}      ! Inclusive simulation start day.
SHOUR = ${START_HOUR}     ! Inclusive simulation start hour [0-23].
EYEAR = ${END_YEAR}       ! Exclusive simulation end year.
EMON  = ${END_MONTH}      ! Exclusive simulation end month.
EDAY  = ${END_DAY}        ! Exclusive simulation end day.
EHOUR = ${END_HOUR}       ! Exclusive simulation end hour.
/
&NMAP
LMAPCDF = .FALSE.                          ! Read individual map files by their extensions.
CNEXTXY = "${NEXTXY}"                     ! Standard Rhine network.
CGRAREA = "${MAP_NETCDF_DIR}/ctmare.nc"   ! Unit-catchment area [m2].
CELEVTN = "${MAP_NETCDF_DIR}/elevtn.nc"   ! Channel-top elevation [m].
CNXTDST = "${MAP_NETCDF_DIR}/nxtdst.nc"   ! Distance to downstream unit catchment [m].
CRIVLEN = "${MAP_NETCDF_DIR}/rivlen.nc"   ! River-channel length [m].
CFLDHGT = "${MAP_NETCDF_DIR}/fldhgt.nc"   ! Floodplain elevation thresholds by layer [m].
CRIVWTH = "${RIVWTH}"                     ! MERIT-based river-channel width [m].
CRIVHGT = "${MAP_NETCDF_DIR}/rivhgt.nc"   ! River-channel depth [m].
CRIVMAN = "${MAP_NETCDF_DIR}/rivman.nc"   ! River Manning roughness map.
CPTHOUT = "${MAP_NETCDF_DIR}/bifprm.nc"   ! Bifurcation channel parameters.
/
&NRESTART
CRESTSTO = "${RESTART_INPUT}"        ! No Restart input; this is a cold-start run.
CRESTDIR = "./"           ! Write Restart in the run directory.
CVNREST  = "${CVNREST}"  ! Prefix for the final Restart file.
LRESTCDF = ${LRESTCDF}    ! Write NetCDF Restart output.
IFRQ_RST = ${IFRQ_RST}    ! 0 writes Restart only at the simulation end.
/
&NFORCE
LINPCDF  = ${LINPCDF}      ! Read runoff from NetCDF.
CROFFREQ = "${CROFFREQ}" ! One input file per calendar day.
LINTERP  = ${LINTERP}      ! Use the map-specific Input Matrix for runoff mapping.
LITRPCDF  = ${LITRPCDF}    ! Read the Step 13 Input Matrix from NetCDF.
CINPMAT  = "${INPMAT}"    ! Step 13 regional runoff-to-river matrix.
DROFUNIT = ${DROFUNIT}     ! Convert mm per hour to depth rate [m/s].
CVNTIME  = "${CVNTIME}"   ! NetCDF time-coordinate variable.
CVNROF   = "${CVNROF}"    ! NetCDF runoff variable.
CROFDIR  = "${RUNOFF_DIR}" ! Directory containing daily runoff files.
CROFPRE  = "${CROFPRE}"   ! Daily filename prefix before YYYYMMDD.
CROFSUF  = "${CROFSUF}"   ! Daily filename suffix.
/
&NOUTPUT
CMF_BASE = "${CMF_BASE}"  ! Repository root used for output-variable metadata.
COUTVAR_TABLE = ""        ! Empty selects the maintained output variable table.
COUTDIR  = "./"            ! Output files are written in the run directory.
CVARSOUT = "${CVARSOUT}"  ! Hourly gridded output variables.
COUTTAG  = "${COUTTAG}"  ! Experiment tag appended to output names.
LOUTVEC  = .FALSE.         ! Write gridded XY output, not river-vector output.
LOUTCDF  = ${LOUTCDF}      ! Write model outputs in NetCDF format.
IFRQ_OUT = ${IFRQ_OUT}     ! Output interval [hours].
/
EOF

printf '\n==================================================\n'
printf '[STEP 2/3] Run CaMa-Flood: %04d-%02d-%02d %02d:00 to %04d-%02d-%02d %02d:00 UTC (end exclusive)\n' \
    "$START_YEAR" "$START_MONTH" "$START_DAY" "$START_HOUR" "$END_YEAR" "$END_MONTH" "$END_DAY" "$END_HOUR"
printf '==================================================\n\n'
cd "$RUNDIR"
START_DATETIME=$(date)
printf 'Start: %s\n' "$START_DATETIME" | tee "$RUNTIME_LOG"
START_SECONDS=$(date +%s)

if OMP_NUM_THREADS="$OMP_NUM_THREADS" ./MAIN_cmf > "$CONSOLE_LOG" 2>&1; then
    RUN_STATUS=0
else
    RUN_STATUS=$?
fi

ELAPSED_SECONDS=$(($(date +%s) - START_SECONDS))
{
    printf 'End: %s\n' "$(date)"
    printf 'Elapsed seconds: %s\n' "$ELAPSED_SECONDS"
    printf 'Exit status: %s\n' "$RUN_STATUS"
} | tee -a "$RUNTIME_LOG"

if [ "$RUN_STATUS" -ne 0 ]; then
    STEP="Run the Rhine 2021 simulation"
    printf '[ERROR] CaMa-Flood failed; inspect %s and %s\n' \
        "$CONSOLE_LOG" "${RUNDIR}/log_CaMa.nml" >&2
    exit "$RUN_STATUS"
fi

printf '\n==================================================\n'
printf '[STEP 3/3] Report run products\n'
printf '==================================================\n\n'
printf '[SUCCESS] %s completed\n' "$SCRIPT_NAME"
printf 'Results: %s\n' "$RUNDIR"
printf 'Namelist: %s\n' "$NAMELIST"
printf 'Model log: %s\n' "${RUNDIR}/log_CaMa.nml"
printf 'Console log: %s\n' "$CONSOLE_LOG"
printf 'Runtime log: %s\n' "$RUNTIME_LOG"
