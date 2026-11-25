#!/bin/sh
# Register the CaMa-Flood v5.0 installation root in one user startup file.
set -eu

ENV_NAME=CMF_V50_ROOT
START_MARKER="# >>> CaMa-Flood v5.0 configuration >>>"
END_MARKER="# <<< CaMa-Flood v5.0 configuration <<<"
ACTION=configure
RC_OVERRIDE=
ASSUME_YES=no

usage() {
    cat <<'EOF'
Usage: s00-configure_cama_root.sh [--show | --print] [--rc FILE] [--yes]
       s00-configure_cama_root.sh --help

Detect the installation root from this script and configure CMF_V50_ROOT.
--show       Display detected and current settings without changing files.
--print      Print only a safely quoted export statement.
--rc FILE    Select a startup file explicitly.
--yes        Skip confirmation for a first install or an unchanged install.
             It does not authorize replacing a different configured path.
--help       Show this help.
EOF
}

die() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 1
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --show|--print)
            [ "$ACTION" = configure ] || die "Choose only one of --show and --print."
            ACTION=${1#--}
            shift
            ;;
        --rc)
            [ "$#" -ge 2 ] || die "--rc requires a file path."
            [ -z "$RC_OVERRIDE" ] || die "--rc may be specified only once."
            RC_OVERRIDE=$2
            shift 2
            ;;
        --yes)
            ASSUME_YES=yes
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1 (use --help)."
            ;;
    esac
done

if [ "$ACTION" != configure ] && [ "$ASSUME_YES" = yes ]; then
    die "--yes cannot be combined with --$ACTION."
fi
if [ "$ACTION" = print ] && [ -n "$RC_OVERRIDE" ]; then
    die "--rc is not used with --print."
fi

# Resolve script symlinks relative to the directory containing each link.
SCRIPT_PATH=$0
case "$SCRIPT_PATH" in
    */*) ;;
    # Command substitution captures the executable path while quotes preserve spaces.
    *) SCRIPT_PATH=$(command -v "$SCRIPT_PATH") || die "Cannot locate this script." ;;
esac
LINK_COUNT=0
while [ -L "$SCRIPT_PATH" ]; do
    LINK_COUNT=$((LINK_COUNT + 1))
    [ "$LINK_COUNT" -le 40 ] || die "Too many script symlinks; cannot resolve installation root."
    # Clear CDPATH so cd does not print a directory before pwd captures it.
    LINK_DIR=$(CDPATH= cd "$(dirname "$SCRIPT_PATH")" && pwd -P) || die "Cannot resolve script directory."
    LINK_TARGET=$(readlink "$SCRIPT_PATH") || die "Cannot read script symlink."
    case "$LINK_TARGET" in
        /*) SCRIPT_PATH=$LINK_TARGET ;;
        *) SCRIPT_PATH=$LINK_DIR/$LINK_TARGET ;;
    esac
done
# Physical path resolution removes symlinked parent directories from the root.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$SCRIPT_PATH")" && pwd -P) || die "Cannot resolve installation directory."
ROOT=$SCRIPT_DIR
for required_dir in src_main map config; do
    [ -d "$ROOT/$required_dir" ] || die "Detected directory does not look like a CaMa-Flood v5 root (missing $required_dir/): $ROOT"
done
case "$ROOT" in
    *'
'*) die "Installation paths containing newline characters are not supported." ;;
esac

# POSIX single quotes preserve path characters; embedded quotes are escaped outside the quoted segment.
quote_single() {
    value=$1
    quoted="'"
    while [ -n "$value" ]; do
        # Parameter expansion takes the first character without evaluating its contents.
        char=${value%"${value#?}"}
        value=${value#?}
        if [ "$char" = "'" ]; then
            quoted=$quoted"'\\''"
        else
            quoted=$quoted$char
        fi
    done
    printf "%s'" "$quoted"
}

EXPORT_LINE="export $ENV_NAME=$(quote_single "$ROOT")"
if [ "$ACTION" = print ]; then
    printf '%s\n' "$EXPORT_LINE"
    exit 0
fi

# Use SHELL as the login-Shell hint; an unset value remains empty rather than guessed.
SHELL_PATH=${SHELL:-}
# Remove the directory prefix from the login-Shell path.
SHELL_NAME=${SHELL_PATH##*/}
case "$SHELL_NAME" in
    bash|zsh) ;;
    *)
        if [ "$ACTION" = show ]; then
            printf 'Detected installation: %s\nEnvironment variable: %s\nDetected Shell: %s\n' "$ROOT" "$ENV_NAME" "${SHELL_NAME:-unknown}"
            printf 'Configuration file: unsupported Shell; no automatic file selected.\nManual setting:\n%s\n' "$EXPORT_LINE"
            exit 0
        fi
        die "Unsupported or unknown login Shell '${SHELL_NAME:-unknown}'. No startup file was changed. Add this line manually: $EXPORT_LINE"
        ;;
esac

OS_NAME=$(uname -s 2>/dev/null || printf Unknown)
case "$SHELL_NAME:$OS_NAME" in
    zsh:Darwin|zsh:Linux) DEFAULT_RC=.zshrc ;;
    bash:Darwin) DEFAULT_RC=.bash_profile ;;
    bash:Linux) DEFAULT_RC=.bashrc ;;
    *)
        die "Automatic startup-file selection supports Bash and zsh on macOS/Linux only (detected $SHELL_NAME on $OS_NAME). Use --print and configure this shell manually."
        ;;
esac
# The empty default lets the next check report an unset HOME clearly.
[ -n "${HOME:-}" ] || die "HOME is not set."
HOME_DIR=$HOME
case "$HOME_DIR" in
    /*) ;;
    *) HOME_DIR=$(CDPATH= cd "$HOME_DIR" && pwd -P) || die "Cannot resolve HOME." ;;
esac

canonical_rc() {
    candidate=$1
    case "$candidate" in
        '~') candidate=$HOME_DIR ;;
        # Expand only a leading tilde; the path is never evaluated as Shell code.
        '~/'*) candidate=$HOME_DIR/${candidate#\~/} ;;
        /*) ;;
        *) candidate=$PWD/$candidate ;;
    esac
    rc_parent=$(dirname "$candidate")
    rc_base=$(basename "$candidate")
    [ -d "$rc_parent" ] || die "Startup-file directory does not exist: $rc_parent"
    rc_parent=$(CDPATH= cd "$rc_parent" && pwd -P) || die "Cannot resolve startup-file directory."
    printf '%s/%s\n' "$rc_parent" "$rc_base"
}

DEFAULT_RC_PATH=$(canonical_rc "$HOME_DIR/$DEFAULT_RC")
RC_PATH=
if [ -n "$RC_OVERRIDE" ]; then
    RC_PATH=$(canonical_rc "$RC_OVERRIDE")
else
    RC_PATH=$DEFAULT_RC_PATH
fi

# Find managed blocks in the common startup files to avoid duplicate installs.
BLOCK_FILES=
BLOCK_COUNT=0
UNMANAGED_FILES=
scan_file() {
    file=$1
    [ -e "$file" ] || [ -L "$file" ] || return 0
    [ -f "$file" ] || die "Startup path is not a regular file: $file"
    scan_result=$(awk -v start="$START_MARKER" -v end="$END_MARKER" '
        BEGIN { inside=0; starts=0; ends=0; exports=0; contents=0; outside=0; bad=0 }
        {
            if (index($0, "CaMa-Flood v5.0 configuration") && $0 != start && $0 != end) bad=1
            if ($0 == start) { starts++; if (inside) bad=1; inside=1; next }
            if ($0 == end) { ends++; if (!inside) bad=1; inside=0; next }
            if (inside) {
                contents++
                if ($0 ~ /^export CMF_V50_ROOT=/) exports++
            } else {
                candidate=$0
                sub(/^[[:space:]]+/, "", candidate)
                if (candidate !~ /^#/ && (candidate ~ /(^|[^A-Za-z0-9_])CMF_V50_ROOT[[:space:]]*=/ || candidate ~ /^export[[:space:]]+CMF_V50_ROOT([[:space:]]|=)/)) outside++
            }
        }
        END {
            if (inside || starts != ends || starts > 1 || (starts == 1 && (exports != 1 || contents != 1))) bad=1
            printf "%d|%d|%d\n", starts, outside, bad
        }' "$file") || die "Could not inspect startup file: $file"
    old_ifs=$IFS
    IFS='|'
    # scan_result contains only three numeric fields separated by vertical bars.
    set -f
    set -- $scan_result
    set +f
    IFS=$old_ifs
    [ "$3" -eq 0 ] || die "Malformed or duplicate CaMa-Flood v5.0 managed block in $file; no changes made."
    [ "$2" -eq 0 ] || {
        UNMANAGED_FILES="$UNMANAGED_FILES $file"
        return 0
    }
    if [ "$1" -eq 1 ]; then
        BLOCK_COUNT=$((BLOCK_COUNT + 1))
        BLOCK_FILES="$BLOCK_FILES $file"
    fi
}

CURRENT_EXPORT=
for startup_name in .zshrc .zprofile .bash_profile .bash_login .profile .bashrc; do
    scan_file "$HOME_DIR/$startup_name"
done
if [ -n "$UNMANAGED_FILES" ]; then
    die "An unmanaged $ENV_NAME definition exists in:$UNMANAGED_FILES. It was left untouched; remove or consolidate it manually before using this installer."
fi
[ "$BLOCK_COUNT" -le 1 ] || die "Multiple managed $ENV_NAME blocks were found:$BLOCK_FILES. No changes made."
if [ "$BLOCK_COUNT" -eq 1 ]; then
    existing_file=${BLOCK_FILES# }
    if [ -z "$RC_OVERRIDE" ]; then
        RC_PATH=$existing_file
    elif [ "$RC_PATH" != "$existing_file" ]; then
        die "A managed block already exists in $existing_file; --rc would create a duplicate. No changes made."
    fi
    # Read only the managed export line; never source or eval a startup file.
    CURRENT_EXPORT=$(awk -v start="$START_MARKER" -v end="$END_MARKER" '
        $0 == start { inside=1; next }
        $0 == end { inside=0; next }
        inside && /^export CMF_V50_ROOT=/ { print; exit }
    ' "$RC_PATH")
fi

if [ -e "$RC_PATH" ] || [ -L "$RC_PATH" ]; then
    [ ! -L "$RC_PATH" ] || die "Refusing to replace a startup-file symlink: $RC_PATH"
    [ -f "$RC_PATH" ] || die "Refusing to replace a non-regular startup path: $RC_PATH"
fi

BLOCK_TEXT="$START_MARKER
$EXPORT_LINE
$END_MARKER"

if [ "$ACTION" = show ]; then
    printf 'CaMa-Flood v5.0 Root Configuration\n----------------------------------\n\n'
    printf 'Detected installation:\n  %s\n\nEnvironment variable:\n  %s\n\nDetected Shell:\n  %s\n\nConfiguration file:\n  %s\n\n' "$ROOT" "$ENV_NAME" "$SHELL_NAME" "$RC_PATH"
    if [ -n "$CURRENT_EXPORT" ]; then
        printf 'Current managed setting:\n  %s\n\n' "$CURRENT_EXPORT"
    else
        printf 'Current managed setting: none\n\n'
    fi
    printf 'Proposed configuration:\n\n%s\n' "$BLOCK_TEXT"
    exit 0
fi

if [ -n "$CURRENT_EXPORT" ] && [ "$CURRENT_EXPORT" = "$EXPORT_LINE" ]; then
    printf '[INFO] %s is already configured for this installation in %s. No changes made.\n' "$ENV_NAME" "$RC_PATH"
    exit 0
fi

if [ -n "$CURRENT_EXPORT" ]; then
    printf 'Existing setting:\n  %s\nNew setting:\n  %s\n' "$CURRENT_EXPORT" "$EXPORT_LINE"
    [ "$ASSUME_YES" = no ] || die "--yes cannot authorize replacing an existing different managed path. Run interactively to confirm."
    prompt="Update the managed configuration? [y/N] "
else
    printf 'CaMa-Flood v5.0 Root Configuration\n----------------------------------\n\nDetected installation:\n  %s\n\nEnvironment variable:\n  %s\n\nDetected Shell:\n  %s\n\nConfiguration file:\n  %s\n\nProposed configuration:\n\n%s\n\n' "$ROOT" "$ENV_NAME" "$SHELL_NAME" "$RC_PATH" "$BLOCK_TEXT"
    prompt="Register this configuration? [y/N] "
fi

if [ "$ASSUME_YES" = no ]; then
    printf '%s' "$prompt"
    answer=
    if [ -t 0 ]; then
        IFS= read -r answer || answer=
    fi
    case "$answer" in
        y|Y|yes|YES|Yes) ;;
        *) printf '\n[INFO] No changes made.\n'; exit 0 ;;
    esac
fi

RC_DIR=$(dirname "$RC_PATH")
umask 077
# Create the replacement beside the target so mv can replace it atomically.
TEMP_FILE=$(mktemp "$RC_DIR/.cama-root.XXXXXX") || die "Could not create a temporary file beside $RC_PATH."
cleanup() {
    [ -z "${TEMP_FILE:-}" ] || rm -f "$TEMP_FILE"
}
# Remove only this same-directory temporary file if an update fails or is interrupted.
trap cleanup 0 HUP INT TERM

if [ -e "$RC_PATH" ]; then
    if [ -n "$CURRENT_EXPORT" ]; then
        awk -v start="$START_MARKER" -v end="$END_MARKER" '
            $0 == start { inside=1; next }
            $0 == end { inside=0; next }
            !inside { print }
        ' "$RC_PATH" > "$TEMP_FILE" || die "Could not prepare startup-file update."
    else
        cat "$RC_PATH" > "$TEMP_FILE" || die "Could not copy startup file."
    fi
    mode=$(stat -f '%Lp' "$RC_PATH" 2>/dev/null || stat -c '%a' "$RC_PATH" 2>/dev/null) || die "Could not read startup-file permissions."
    chmod "$mode" "$TEMP_FILE" || die "Could not preserve startup-file permissions."
else
    : > "$TEMP_FILE"
fi

if [ -s "$TEMP_FILE" ]; then
    last_byte=$(tail -c 1 "$TEMP_FILE" | wc -l | tr -d ' ')
    [ "$last_byte" -gt 0 ] || printf '\n' >> "$TEMP_FILE"
fi
printf '%s\n' "$BLOCK_TEXT" >> "$TEMP_FILE" || die "Could not append managed block."
if [ -e "$RC_PATH" ] && cmp -s "$TEMP_FILE" "$RC_PATH"; then
    printf '[INFO] Configuration is unchanged; no backup or rewrite was needed.\n'
    exit 0
fi

BACKUP_PATH=
if [ -e "$RC_PATH" ]; then
    stamp=$(date '+%Y%m%d-%H%M%S')
    BACKUP_PATH=$RC_PATH.cama-backup-$stamp
    suffix=0
    while [ -e "$BACKUP_PATH" ] || [ -L "$BACKUP_PATH" ]; do
        suffix=$((suffix + 1))
        BACKUP_PATH=$RC_PATH.cama-backup-$stamp-$suffix
    done
    cp -p "$RC_PATH" "$BACKUP_PATH" || die "Could not create startup-file backup; original left unchanged."
fi
mv -f "$TEMP_FILE" "$RC_PATH" || die "Could not atomically replace startup file."
TEMP_FILE=
trap - 0 HUP INT TERM

printf '\n[SUCCESS] Updated configuration file: %s\n' "$RC_PATH"
if [ -n "$BACKUP_PATH" ]; then
    printf '[INFO] Backup: %s\n' "$BACKUP_PATH"
fi
printf '[INFO] Registered %s=%s\n' "$ENV_NAME" "$ROOT"
printf '[INFO] Activate in this terminal with: . %s\n' "$RC_PATH"
printf '[INFO] Verify with: echo "$%s"\n' "$ENV_NAME"
