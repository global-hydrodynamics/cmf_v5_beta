#!/bin/sh
# Common Shell functions for CaMa-Flood workflows.
#
# Available functions:
#   cmf_check_init        Initialize error/progress reporting.
#   cmf_check_step        Report the current processing step.
#   cmf_check_success     Report successful completion.
#   cmf_select_hires_tag  Interactively select a high-resolution map.

. "$CMF_V50_ROOT/tools/shell_functions/cmf_check_shell_error.sh"
. "$CMF_V50_ROOT/tools/shell_functions/cmf_select_hires_tag.sh"
