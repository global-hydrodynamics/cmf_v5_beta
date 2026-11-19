"""Bounded-memory Git inventory, exact exclusions and safe archive publication.

The Bash entry point owns git archive/tar and temporary-directory cleanup.
This standard-library helper validates paths/links, verifies retained blob bytes
and executable modes, then publishes without replacing even an empty directory.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from collections import Counter


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def inventory(repo, commit):
    """Read size/OID/mode from Git, not worktree files or unpacked samples."""
    entries = {}
    for record in git(repo, "ls-tree", "-r", "-l", "-z", commit).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, oid, size = header.split()
        name = os.fsdecode(raw_path)
        if kind != b"blob":
            raise ValueError(f"Unsupported tracked entry (e.g. submodule): {name}")
        entries[name] = (mode.decode(), oid.decode(), int(size))
    return entries


def rules(path):
    directories, names = [], []
    for line in Path(path).read_text().splitlines():
        rule = line.strip()
        if not rule or rule.startswith("#"):
            continue
        if any(c in rule for c in "*?[]") or ".." in rule.split("/"):
            raise ValueError(f"Unsupported exclusion rule: {rule}")
        if rule.startswith("/") and rule.endswith("/") and rule.strip("/"):
            directories.append(rule.strip("/"))
        elif "/" not in rule and rule not in (".", ".."):
            names.append(rule)
        else:
            raise ValueError(f"Use /root/directory/ or a literal basename: {rule}")
    return directories, names


def excluded(name, directories, names):
    parts = PurePosixPath(name).parts
    # Never re-archive a previously tracked clean output or staging directory.
    if len(parts) > 1 and parts[0] == "package" and parts[1].startswith(("repo_clean_", ".repo_clean_tmp.")):
        return "generated clean-source tree"
    for directory in directories:
        if name.startswith(directory + "/"):
            return "/" + directory + "/"
    if parts[-1] in names:
        return parts[-1]
    return None


def check_links(repo, entries):
    """Resolve retained Git symlink chains lexically, never through host files."""
    links = {name: os.fsdecode(git(repo, "cat-file", "blob", oid))
             for name, (mode, oid, _) in entries.items() if mode == "120000"}
    for name, target in links.items():
        pending = list(PurePosixPath(name).parent.parts) + target.split("/")
        resolved, seen = [], set()
        if target.startswith("/"):
            raise ValueError(f"Unsafe absolute symlink: {name} -> {target}")
        while pending:
            part = pending.pop(0)
            if part in ("", "."):
                continue
            if part == "..":
                if not resolved:
                    raise ValueError(f"Symlink escapes distribution: {name} -> {target}")
                resolved.pop()
                continue
            resolved.append(part)
            prefix = "/".join(resolved)
            if prefix in links:
                if prefix in seen:
                    raise ValueError(f"Symlink cycle: {name}")
                seen.add(prefix)
                nested = links[prefix]
                if nested.startswith("/"):
                    raise ValueError(f"Unsafe symlink chain: {name} via {prefix}")
                resolved.pop()
                pending = nested.split("/") + pending
        destination = "/".join(resolved)
        if destination and destination not in entries and not any(p.startswith(destination + "/") for p in entries):
            raise ValueError(f"Dangling/excluded symlink target: {name} -> {target}")
        print(f"Symlink: {name} -> {target} (inside distribution)")


def plan(repo, commit, excludes, output, version, branch):
    if not re.fullmatch(r"v5b01_[A-Za-z0-9][A-Za-z0-9_.-]*", version):
        raise ValueError("VER must start v5b01_ and contain only letters, numbers, _, . or -")
    if os.path.lexists(output):
        raise ValueError(f"Output already exists; refusing overwrite: {output}")
    expected_parent = Path(repo).resolve() / "package"
    if Path(output).parent.resolve() != expected_parent:
        raise ValueError("Output must be directly inside this repository's package/")
    all_entries = inventory(repo, commit)
    directories, names = rules(excludes)
    removed = {name: excluded(name, directories, names) for name in all_entries}
    kept = {name: entry for name, entry in all_entries.items() if removed[name] is None}
    if "PACKAGE_BUILD_INFO.txt" in all_entries:
        raise ValueError("Tracked PACKAGE_BUILD_INFO.txt would conflict with generated provenance")
    check_links(repo, kept)
    if git(repo, "status", "--porcelain", "--untracked-files=normal").strip():
        print("WARNING: Uncommitted/untracked changes exist; only the pinned HEAD commit is extracted.", file=sys.stderr)
    print(f"VER: {version}\nSource commit: {commit}\nSource branch: {branch}\nOutput: {output}")
    size = sum(entry[2] for entry in kept.values())
    print(f"Git tracked files: {len(all_entries)}\nExcluded files: {len(all_entries)-len(kept)}"
          f"\nExtracted files: {len(kept)}\nEstimated source size: {size} bytes ({size/1024**2:.2f} MiB)")
    for rule, count in sorted(Counter(v for v in removed.values() if v is not None).items()):
        print(f"Exclude {rule}: {count} files")
    return kept


def verify_tree(tree, entries):
    """Detect archive attributes that omit/substitute bytes; never rewrite science."""
    for name, (mode, oid, size) in entries.items():
        path = tree / name
        info = path.lstat()
        digest = hashlib.sha256() if len(oid) == 64 else hashlib.sha1()
        digest.update(f"blob {size}\0".encode())
        if mode == "120000":
            if not stat.S_ISLNK(info.st_mode):
                raise ValueError(f"Archive symlink mode mismatch: {name}")
            digest.update(os.fsencode(os.readlink(path)))
        else:
            if not stat.S_ISREG(info.st_mode) or info.st_size != size:
                raise ValueError(f"Archive type/size mismatch: {name}")
            if bool(info.st_mode & 0o111) != (mode == "100755"):
                raise ValueError(f"Archive executable mode mismatch: {name}")
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024*1024), b""):
                    digest.update(block)
        if digest.hexdigest() != oid:
            raise ValueError(f"Archive content differs from committed blob: {name}")
    # Includes symlink entries without descending into linked directories.
    actual = set()
    for parent, dirs, files in os.walk(tree, followlinks=False):
        for name in list(dirs):
            if (Path(parent) / name).is_symlink():
                files.append(name)
                dirs.remove(name)
        actual.update((Path(parent) / name).relative_to(tree).as_posix() for name in files)
    if actual != set(entries):
        raise ValueError(f"Unexpected archive inventory: {sorted(actual ^ set(entries))[:10]}")


def publish(tree, output):
    """Atomic no-replace rename on the supported macOS/Linux developer hosts."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        result = rename(os.fsencode(tree), os.fsencode(output), 4)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        result = rename(-100, os.fsencode(tree), -100, os.fsencode(output), 1)  # RENAME_NOREPLACE
    else:
        raise ValueError("Atomic no-overwrite publication requires macOS or Linux rename support")
    if result:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(output))


def main():
    action, repo, commit, excludes, output, version, branch, *extra = sys.argv[1:]
    entries = plan(repo, commit, excludes, output, version, branch)
    if action == "plan":
        return
    if action != "finish" or len(extra) != 2:
        raise ValueError("Invalid internal helper arguments")
    tree, timestamp = Path(extra[0]), extra[1]
    # Remove literal excluded paths without following symlinks; prune empty dirs.
    for parent, dirs, files in os.walk(tree, topdown=False, followlinks=False):
        for name in files + dirs:
            path = Path(parent) / name
            relative = path.relative_to(tree).as_posix()
            if path.is_symlink() or path.is_file():
                if relative not in entries:
                    path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    verify_tree(tree, entries)
    (tree / "PACKAGE_BUILD_INFO.txt").write_text(
        f"Package version: {version}\nSource repository: cmf_v5_beta\nSource commit: {commit}\n"
        f"Source branch: {branch}\nArchive date: {timestamp}\n"
        "Archive tool: package/archive_clean_repo.sh\nPackage stage: Clean Git source extraction\n")
    publish(tree, output)
    print(f"Verified {len(entries)} committed files plus PACKAGE_BUILD_INFO.txt")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
