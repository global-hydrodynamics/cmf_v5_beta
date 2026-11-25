#!/bin/sh
# Shared failure reporting for maintained CaMa-Flood Shell workflows.
# Sourcing defines functions only; call cmf_check_init to install traps.

cmf_check_init() {
    CMF_CHECK_SCRIPT=${0##*/}
    CMF_CHECK_LAST_STEP=${1:-$CMF_CHECK_SCRIPT}

    trap 'cmf_check_on_exit "$?"' 0
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

cmf_check_step() {
    CMF_CHECK_LAST_STEP=$3
    printf '\n==================================================\n[STEP %s/%s] %s\n==================================================\n\n' \
        "$1" "$2" "$3"
}

cmf_check_success() {
    printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' \
        "$CMF_CHECK_SCRIPT"
}

cmf_check_on_exit() {
    CMF_CHECK_EXIT_STATUS=$1
    trap - 0

    if [ "$CMF_CHECK_EXIT_STATUS" -ne 0 ]; then
        printf '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' >&2
        printf '!!! ERROR: %s FAILED !!!\n' "$CMF_CHECK_SCRIPT" >&2
        printf '!!! Step: %s\n' "$CMF_CHECK_LAST_STEP" >&2
        printf '!!! Exit status: %s\n' "$CMF_CHECK_EXIT_STATUS" >&2
        printf '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' >&2
    fi

    exit "$CMF_CHECK_EXIT_STATUS"
}
