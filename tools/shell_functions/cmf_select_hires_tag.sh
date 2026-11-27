#!/bin/sh
# Select a high-resolution map directory from a map-local script_* CWD.

cmf_hires_single_area_check() (
    tag=$1
    directory="../$tag"
    location="$directory/location.csv"

    if [ ! -d "$directory" ]; then
        printf 'The resolution directory is missing: %s\n' "$directory" >&2
        return 1
    fi
    if [ ! -r "$location" ]; then
        location="$directory/location.txt"  # Temporary support for unmigrated legacy maps.
        if [ ! -r "$location" ]; then
            printf 'The resolution has no readable location.csv: ../%s/location.csv\n' "$tag" >&2
            return 1
        fi
    fi

    case "$location" in
        *.csv) area_count=$(awk -F, 'NR > 1 && NF { count++ } END { print count+0 }' "$location") ;;
        *) area_count=$(awk 'NR == 1 { print $1; exit }' "$location") ;;
    esac
    case "$area_count" in
        1) ;;
        ''|*[!0-9]*)
            printf 'Location metadata does not declare a valid area count.\n' >&2
            return 1
            ;;
        *)
            printf 'This resolution contains multiple areas (%s). Allocation requires a single-area high-resolution map.\n' \
                "$area_count" >&2
            return 1
            ;;
    esac

    case "$location" in
        *.csv)
            area_index=$(awk -F, 'NR == 2 { gsub(/^[ \t]+|[ \t]+$/, "", $1); print $1 }' "$location")
            area_tag=$(awk -F, 'NR == 2 { gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2 }' "$location")
            ;;
        *)
            area_index=$(awk 'NR == 3 { print $1; exit }' "$location")
            area_tag=$(awk 'NR == 3 { print $2; exit }' "$location")
            ;;
    esac
    if [ "$area_index" != 1 ] || [ "$area_tag" != "$tag" ]; then
            printf 'Location metadata area identifier does not match the single-area %s naming convention.\n' \
            "$tag" >&2
        return 1
    fi

    found_named_file=false
    for path in "$directory/$tag".?*.nc "$directory/$tag".?*.bin; do
        if [ -f "$path" ]; then
            found_named_file=true
            break
        fi
    done
    if [ "$found_named_file" != true ]; then
        printf 'No %s.<variable>.nc or %s.<variable>.bin files were found for the declared single area.\n' \
            "$tag" "$tag" >&2
        return 1
    fi
)

cmf_select_hires_tag() (
    if [ "$#" -gt 2 ]; then
        printf 'Usage: cmf_select_hires_tag [initial-resolution] [--single-area]\n' >&2
        return 2
    fi

    configured=${1-}
    mode=${2-}
    case "$mode" in
        ''|--single-area) ;;
        *)
            printf 'Usage: cmf_select_hires_tag [initial-resolution] [--single-area]\n' >&2
            return 2
            ;;
    esac

    discovered=""
    available=""
    recommended=""
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -d "../$tag" ]; then
            discovered="${discovered}${discovered:+ }$tag"
            if [ "$mode" != --single-area ] || cmf_hires_single_area_check "$tag" 2>/dev/null; then
                available="${available}${available:+ }$tag"
                [ -n "$recommended" ] || recommended=$tag
            fi
        fi
    done

    if [ -z "$available" ]; then
        if [ "$mode" = --single-area ]; then
            printf 'No compatible single-area high-resolution map was found. Check location.csv and the <TAG>.<VARIABLE> filenames.\n' >&2
        else
            printf 'No supported high-resolution map directory was found above this script directory.\n' >&2
        fi
        return 1
    fi

    candidates=$available
    if [ "$mode" = --single-area ]; then
        printf 'Available single-area resolutions: %s\n' "$available" >&2
    else
        printf 'Available resolutions: %s\n' "$available" >&2
    fi

    selected=""
    if [ -n "$configured" ]; then
        case " $available " in
            *" $configured "*)
                selected=$configured
                printf 'Selected high-resolution map: %s\n' "$selected" >&2
                ;;
            *)
                case " $discovered " in
                    *" $configured "*)
                        printf 'Selected resolution: %s\n' "$configured" >&2
                        if [ "$mode" = --single-area ]; then
                            cmf_hires_single_area_check "$configured"
                        fi
                        ;;
                    *)
                        printf 'Configured high-resolution map is not available: %s\n' \
                            "$configured" >&2
                        ;;
                esac
                ;;
        esac
    else
        selected=$recommended
        printf 'Recommended high-resolution map: %s\n' "$recommended" >&2
    fi

    if [ -n "$selected" ]; then
        while :; do
            printf 'Use this map? [Y/n]: ' >&2
            if ! IFS= read -r answer; then
                printf 'Could not read a confirmation from standard input.\n' >&2
                return 1
            fi
            case "$answer" in
                ''|y|Y|yes|Yes|YES)
                    printf '%s\n' "$selected"
                    return 0
                    ;;
                n|N|no|No|NO)
                    break
                    ;;
                *)
                    printf 'Please answer Yes or No (Enter = Yes).\n' >&2
                    ;;
            esac
        done
    fi

    while :; do
        printf 'Choose resolution from [%s]: ' "$candidates" >&2
        if ! IFS= read -r answer; then
            printf 'Could not read a resolution from standard input.\n' >&2
            return 1
        fi
        case " $candidates " in
            *" $answer "*)
                printf '%s\n' "$answer"
                return 0
                ;;
            *)
                printf 'Choose one of the listed, nonempty resolutions.\n' >&2
                ;;
        esac
    done
)
