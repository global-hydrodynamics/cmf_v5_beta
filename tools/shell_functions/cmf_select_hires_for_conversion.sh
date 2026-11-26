#!/bin/sh
# Select source resolutions from a map-local script_format_conv/ CWD.
# Print only selected tags on stdout; prompts/status go to stderr.
cmf_select_hires_for_conversion() (
    direction=$1
    configured=${2-}
    case "$direction" in
        nc2bin) extension=nc ;;
        bin2nc) extension=bin ;;
        *) printf 'Expected conversion direction nc2bin or bin2nc.\n' >&2; return 1 ;;
    esac
    if [ ! -t 0 ] && [ -z "$configured" ]; then
        printf 'Non-interactive conversion requires an explicit HIRES setting (e.g. "1min 3sec").\n' >&2
        return 1
    fi

    # Only inspect names and location.txt presence, never raster contents.
    variables=$(awk '
        { line=$0
          while (match(line, /<HIRES>\/<AREA>\.[[:alnum:]_-]+\.bin/)) {
              name=substr(line, RSTART, RLENGTH)
              sub(/^<HIRES>\/<AREA>\./, "", name); sub(/\.bin$/, "", name)
              print name
              line=substr(line, RSTART+RLENGTH)
          }
        }' "$CMF_V50_ROOT/variable_table/map_variables.csv")
    available=""
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        directory="../$tag"
        if [ "$direction" = bin2nc ]; then
            # Match the Python planner: standard Binary directory takes precedence.
            [ ! -d "../binary/$tag" ] || directory="../binary/$tag"
            [ -f "../$tag/location.txt" ] || [ -f "../binary/$tag/location.txt" ] || continue
        else
            [ -f "$directory/location.txt" ] || continue
        fi
        found=false
        for variable in $variables; do
            for path in "$directory/"*."$variable.$extension"; do
                if [ -f "$path" ]; then found=true; break 2; fi
            done
        done
        if [ "$found" = true ]; then available="${available}${available:+ }$tag"; fi
    done
    [ -n "$available" ] || { printf 'No registered %s high-resolution source products found.\n' "$extension" >&2; return 1; }
    printf 'Available high-resolution maps:\n  %s\n' "$available" >&2

    # Tag input is a whitespace-separated list, never a filename glob.
    set -f
    answer=$configured
    while :; do
        if [ -z "$configured" ]; then
            printf 'Select resolutions [Enter=%s, all=all]:\n> ' "${available%% *}" >&2
            IFS= read -r answer || return 1
            [ -n "$answer" ] || answer=${available%% *}
            [ "$answer" != all ] || answer=$available
        fi
        valid=true
        selected=""
        for tag in $answer; do
            case " $available " in
                *" $tag "*) ;;
                *) valid=false ;;
            esac
        done
        for tag in $available; do
            case " $answer " in *" $tag "*) selected="${selected}${selected:+ }$tag" ;; esac
        done
        if [ "$valid" = true ] && [ -n "$selected" ]; then break; fi
        printf 'Choose one or more available resolution tags: %s\n' "$available" >&2
        [ -t 0 ] || return 1
        configured=""
    done
    printf 'Selected: %s\n' "$selected" >&2
    if [ -t 0 ]; then
        while :; do
            printf 'Proceed with conversion? [Y/n]: ' >&2
            IFS= read -r answer || return 1
            case "$answer" in
                ''|y|Y|yes|Yes|YES) break ;;
                n|N|no|No|NO) printf 'Conversion cancelled.\n' >&2; return 0 ;;
                *) printf 'Please answer y or n.\n' >&2 ;;
            esac
        done
    fi
    printf '%s\n' "$selected"
)
