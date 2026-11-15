# Shared Bash execution flow, sourced by the user-editable wrappers.
# Settings are supplied by each wrapper; this file does not perform NetCDF calculations.

era5_usage() {
    cat <<'HELP'
Stage options (normally supplied by a product Shell):
  --dataset NAME                   Dataset directory name directly under inp/
  --start-date YYYY-MM-DD --end-date YYYY-MM-DD
  --west N --east N --south N --north N
  --tstep HOURS                    One of 1,2,3,4,6,8,12,24
  --download-unit daily|monthly    Input file grouping
  --output-unit monthly|yearly     Converted file grouping
  --format netcdf                  Output format (Binary is not supported)
  --ncpus N                        Parallel jobs (default 1)
  --python PATH                    Python executable (default python3)
  --dry-run                        Print requests/plans; no download or output files
  --overwrite                      Explicitly replace existing data/info files
  --help                           Show this help
HELP
}

era5_wait() {
    local index tag
    for index in "${!PIDS[@]}"; do
        tag=${TAGS[$index]}
        if wait "${PIDS[$index]}"; then
            printf '\n[SUCCESS] %s %s\n' "$MODE" "$tag"
        else
            printf '\n[ERROR] %s %s (log: %s/%s.log)\n' "$MODE" "$tag" "$LOGDIR" "$tag" >&2
            FAILED=1
        fi
        unset 'PIDS[index]'
        cat "$LOGDIR/$tag.log"
    done
    PIDS=()
    TAGS=()
}

era5_stop() {
    # Only pending children are terminated; generated data and logs are retained.
    if [ "${#PIDS[@]}" -gt 0 ]; then
        for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
    fi
    wait || true
}

era5_stage() {
    MODE=$1
    local unit periods pstart pend tag year month day end_day out
    local command
    if [ "$MODE" = download ]; then unit=$DOWNLOAD_UNIT; else unit=$OUTPUT_UNIT; fi
    # Python handles calendar arithmetic and validates destinations before any directories are made.
    periods=$("$PYTHON_CMD" "$SCRIPT_DIR/plan_periods.py" \
        --inp-root "$INP_ROOT" --dataset "$DATASET" --start "$START_DATE" --end "$END_DATE" --unit "$unit")
    LOGDIR=""
    if [ "$DRY_RUN" -eq 0 ]; then
        mkdir -p "$DATADIR/original" "$DATADIR/logs"
        LOGDIR=$(mktemp -d "$DATADIR/logs/$MODE.XXXXXX")
    fi
    FAILED=0
    PIDS=()
    TAGS=()
    while read -r pstart pend tag; do
        [ -n "$tag" ] || continue
        command=()
        if [ "$MODE" = download ]; then
            # IFS separates the ISO date; suffix removal extracts the last date component.
            IFS=- read -r year month day <<< "$pstart"
            end_day=${pend##*-}
            out="$DATADIR/original/ERA5-Land_runoff_$tag.nc"
            command=("$PYTHON_CMD" "$SCRIPT_DIR/download_era5land.py" \
                --year "$year" --month "$month" --variable runoff --time-step "$TSTEP" \
                --area-nswe "$NORTH" "$SOUTH" "$WEST" "$EAST" --area-is edge --out "$out")
            if [ "$DOWNLOAD_UNIT" = daily ]; then
                command+=(--day "$day")
            else
                command+=(--start-day "$day" --end-day "$end_day")
            fi
        else
            out="$DATADIR/runoff_$tag.nc"
            command=("$PYTHON_CMD" "$SCRIPT_DIR/convert_CMF_nc.py" \
                --start "$pstart" --end "$pend" --indir "$DATADIR/original" --out "$out" \
                --input-file-unit "$DOWNLOAD_UNIT" --input-variable runoff --output-variable runoff \
                --timestep-hours "$TSTEP" --fill-value 1.0e20 --lat-order NtoS)
        fi
        if [ "$OVERWRITE" -eq 1 ]; then command+=(--overwrite); fi
        if [ "$DRY_RUN" -eq 1 ]; then
            if [ "$MODE" = download ]; then
                "${command[@]}" --dry-run
            else
                printf '[DRY-RUN] '; printf '%q ' "${command[@]}"; printf '\n'
            fi
            continue
        fi
        if [ -L "$out" ]; then printf '[ERROR] Refusing output symlink: %s\n' "$out" >&2; return 1; fi
        if [ -e "$out" ] && [ "$OVERWRITE" -eq 0 ]; then
            printf '[INFO] Skip existing: %s\n' "$out"
            continue
        fi
        printf '\n[STEP] %s %s → %s\n' "$MODE" "$tag" "$out"
        "${command[@]}" > "$LOGDIR/$tag.log" 2>&1 &
        PIDS+=("$!")
        TAGS+=("$tag")
        if [ "${#PIDS[@]}" -ge "$NCPUS" ]; then era5_wait; fi
    done <<< "$periods"
    if [ "${#PIDS[@]}" -gt 0 ]; then era5_wait; fi
    if [ "$FAILED" -ne 0 ]; then return 1; fi
    if [ "$MODE" = convert ] && [ "$DRY_RUN" -eq 0 ]; then
        if [ -L "$DATADIR/runoff_info_CaMaFlood.txt" ]; then echo '[ERROR] Refusing information-file symlink' >&2; return 1; fi
        if [ -e "$DATADIR/runoff_info_CaMaFlood.txt" ] && [ "$OVERWRITE" -eq 0 ]; then
            printf '[INFO] Existing information file retained (use --overwrite to refresh).\n'
        else
            command=("$PYTHON_CMD" "$SCRIPT_DIR/make_CMF_runoff_info.py"
                --outdir "$DATADIR" --outfile "$DATADIR/runoff_info_CaMaFlood.txt"
                --timestep-hours "$TSTEP" --merge-unit "$OUTPUT_UNIT"
                --start "$START_DATE" --end "$END_DATE" --sample-name "$DATASET")
            if [ "$OVERWRITE" -eq 1 ]; then command+=(--overwrite); fi
            "${command[@]}" > "$LOGDIR/info.log" 2>&1 || { cat "$LOGDIR/info.log"; return 1; }
        fi
        cat "$DATADIR/runoff_info_CaMaFlood.txt"
    fi
}

era5_main() {
    local action=$1
    shift
    DRY_RUN=0
    OVERWRITE=0
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --help|-h) era5_usage; return 0 ;;
            --dry-run) DRY_RUN=1; shift; continue ;;
            --overwrite) OVERWRITE=1; shift; continue ;;
        esac
        if [ "$#" -lt 2 ]; then printf '[ERROR] Missing value for %s\n' "$1" >&2; return 2; fi
        case "$1" in
            --dataset) DATASET=$2 ;; --start-date) START_DATE=$2 ;; --end-date) END_DATE=$2 ;;
            --west) WEST=$2 ;; --east) EAST=$2 ;; --south) SOUTH=$2 ;; --north) NORTH=$2 ;;
            --tstep) TSTEP=$2 ;; --download-unit) DOWNLOAD_UNIT=$2 ;; --output-unit) OUTPUT_UNIT=$2 ;;
            --ncpus) NCPUS=$2 ;; --python) PYTHON_CMD=$2 ;; --format) FORMAT=$2 ;;
            *) printf '[ERROR] Unknown option: %s\n' "$1" >&2; return 2 ;;
        esac
        shift 2
    done
    if [ -z "$DATASET" ] || [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
        echo '[ERROR] Supply --dataset, --start-date and --end-date (normally from a product Shell).' >&2
        return 2
    fi
    if [ "$FORMAT" != netcdf ]; then echo '[ERROR] Only --format netcdf is supported.' >&2; return 2; fi
    case "$TSTEP" in 1|2|3|4|6|8|12|24) ;; *) echo '[ERROR] Invalid TSTEP' >&2; return 2 ;; esac
    if ! [[ "$NCPUS" =~ ^[1-9][0-9]*$ ]] || [ "${#NCPUS}" -gt 6 ]; then echo '[ERROR] NCPUS must be positive' >&2; return 2; fi
    case "$DOWNLOAD_UNIT" in daily|monthly) ;; *) echo '[ERROR] Invalid DOWNLOAD_UNIT' >&2; return 2 ;; esac
    case "$OUTPUT_UNIT" in monthly|yearly) ;; *) echo '[ERROR] Invalid OUTPUT_UNIT' >&2; return 2 ;; esac
    # Command substitution and CDPATH avoid dependence on the caller's directory.
    INP_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
    DATADIR="$INP_ROOT/$DATASET"
    printf '\n[INFO] Dataset: %s\n[INFO] Period: %s – %s; timestep: %sh; jobs: %s\n' "$DATADIR" "$START_DATE" "$END_DATE" "$TSTEP" "$NCPUS"
    PIDS=()
    TAGS=()
    trap era5_stop EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    # End of error handling.
    if [ "$action" = download ]; then era5_stage download; fi
    if [ "$action" = convert ]; then era5_stage convert; fi
    printf '\n[SUCCESS] %s workflow completed%s\n' "$action" "$(if [ "$DRY_RUN" -eq 1 ]; then printf ' (dry-run)'; fi)"
}
