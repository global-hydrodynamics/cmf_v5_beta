#!/usr/bin/env bash
# Retired historical entry point; do not restore the old 3-second pipeline here.
set -eu
printf '%s\n' 'The historical 3-second GFM inspection workflow is retired.' \
  'Use s03c-classify_gfm_extent.sh and f03c-flood_fraction_1min.sh for the current 20m/1min workflow.' \
  'See AI_work_report/00_synthesis_preparation.md. No files were generated.' >&2
exit 2
