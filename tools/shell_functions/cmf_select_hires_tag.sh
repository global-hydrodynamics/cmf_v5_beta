#!/bin/sh
# Select a high-resolution map directory from a map-local script_* CWD.

cmf_select_hires_tag() (
    if [ "$#" -gt 1 ]; then
        printf 'Usage: cmf_select_hires_tag [initial-resolution]\n' >&2
        return 2
    fi

    configured=${1-}
    available=""
    recommended=""
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -d "../$tag" ]; then
            available="${available}${available:+ }$tag"
            [ -n "$recommended" ] || recommended=$tag
        fi
    done

    if [ -z "$available" ]; then
        printf 'No supported high-resolution map directory was found above this script directory.\n' >&2
        return 1
    fi

    selected=""
    if [ -n "$configured" ]; then
        case " $available " in
            *" $configured "*)
                selected=$configured
                printf 'Available resolutions: %s\nSelected high-resolution map: %s\n' \
                    "$available" "$selected" >&2
                ;;
            *)
                printf 'Configured high-resolution map is not available: %s\n' \
                    "$configured" >&2
                ;;
        esac
    else
        selected=$recommended
        printf 'Available resolutions: %s\nRecommended high-resolution map: %s\n' \
            "$available" "$recommended" >&2
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
        printf 'Available resolutions: %s\nChoose resolution: ' "$available" >&2
        if ! IFS= read -r answer; then
            printf 'Could not read a resolution from standard input.\n' >&2
            return 1
        fi
        case " $available " in
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
