#!/usr/bin/env python3
"""Catalog-driven, bounded-memory additional-data comparison and one-time import.

No scientific conversion or synchronization is performed. The external store is
read-only; each imported file is verified before an atomic local replacement.
"""

import argparse
import csv
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import lru_cache
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile


REPOSITORY = Path(__file__).resolve().parent.parent
CATALOG = REPOSITORY / "package/package_data.csv"
COLUMNS = ("dataset_id", "source_path", "target_path", "file_pattern", "format", "description")
STATUSES = ("IDENTICAL", "MODIFIED", "SOURCE_ONLY", "TARGET_ONLY")
CHUNK_SIZE = 1024 * 1024


class DataError(Exception):
    """An invalid catalog, unsafe destination or failed data operation."""


@dataclass(frozen=True)
class Dataset:
    identity: str
    source: PurePosixPath
    target: PurePosixPath
    pattern: str
    excludes: tuple


@dataclass(frozen=True)
class Difference:
    dataset: str
    path: PurePosixPath
    source: Path
    target: Path
    source_size: int
    target_size: int
    status: str
    source_stamp: tuple
    target_stamp: tuple


def relative_path(value, label, pattern=False):
    """Reject traversal before PurePath normalization can hide empty/dot parts."""
    parts = value.split("/")
    if (not value or "\\" in value or any(ord(c) < 32 for c in value)
            or any(p in ("", ".", "..", ".git") for p in parts)
            or PurePosixPath(value).is_absolute() or ":" in parts[0]):
        raise DataError(f"Unsafe {label}: {value!r}")
    if not pattern and any(c in value for c in "*?[]"):
        raise DataError(f"Wildcards are not allowed in {label}: {value!r}")
    return PurePosixPath(value)


def within(path, root):
    return path == root or root in path.parents


def load_catalog(path, identities=None):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames not in (list(COLUMNS), [*COLUMNS, "exclude_patterns"]):
            raise DataError("Catalog must retain the six standard columns, optionally followed by exclude_patterns")
        datasets = []
        seen = set()
        for line, row in enumerate(reader, 2):
            if None in row or any(row.get(k) is None for k in reader.fieldnames):
                raise DataError(f"Malformed catalog row {line}")
            identity = row["dataset_id"].strip()
            if not identity or identity in seen:
                raise DataError(f"Blank or duplicate dataset_id at row {line}: {identity!r}")
            seen.add(identity)
            source = relative_path(row["source_path"], "source_path")
            target = relative_path(row["target_path"], "target_path")
            relative_path(row["file_pattern"], "file_pattern", pattern=True)
            excludes = tuple(p.strip() for p in row.get("exclude_patterns", "").split(";") if p.strip())
            for exclusion in excludes:
                name = exclusion[:-1] if exclusion.endswith("/") else exclusion
                if not name or "/" in name or "\\" in name or name in (".", ".."):
                    raise DataError(f"Invalid component/basename exclusion: {exclusion!r}")
            datasets.append(Dataset(identity, source, target, row["file_pattern"], excludes))
        if not datasets:
            raise DataError("Catalog contains no datasets")
    # Ambiguous ownership must not depend on row order, even for a filtered run.
    for index, a in enumerate(datasets):
        for b in datasets[index + 1:]:
            if within(a.target, b.target) or within(b.target, a.target):
                raise DataError(f"Overlapping catalog targets: {a.identity}, {b.identity}")
    if identities:
        unknown = set(identities) - seen
        if unknown:
            raise DataError("Unknown dataset(s): " + ", ".join(sorted(unknown)))
        datasets = [d for d in datasets if d.identity in identities]
    return datasets


def included(relative, pattern):
    """Path.glob-style component matching, including zero directories for **/*."""
    parts, patterns = relative.parts, PurePosixPath(pattern).parts

    @lru_cache(None)
    def match(i, j):
        if j == len(patterns):
            return i == len(parts)
        if patterns[j] == "**":
            return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
        return i < len(parts) and fnmatchcase(parts[i], patterns[j]) and match(i + 1, j + 1)

    return match(0, 0)


def excluded(relative, rules, directory=False):
    parents = relative.parts if directory else relative.parts[:-1]
    return any(
        any(fnmatchcase(part, rule[:-1]) for part in parents) if rule.endswith("/")
        else (not directory and fnmatchcase(relative.name, rule))
        for rule in rules
    )


def no_symlinks(root, relative):
    """The store root may resolve a link; dataset children/destinations may not."""
    path = root
    for index, part in enumerate(relative.parts):
        path = path / part
        if path.is_symlink():
            raise DataError(f"Symlink inside dataset/destination is not allowed: {path}")
        if index < len(relative.parts) - 1 and path.exists() and not path.is_dir():
            raise DataError(f"Dataset/destination ancestor is not a directory: {path}")
    return path


def files_for(root, relative, dataset, required):
    directory = no_symlinks(root, relative)
    if not directory.exists():
        if required:
            raise DataError(f"Required source dataset is missing: {dataset.identity}: {directory}")
        return {}
    if not directory.is_dir():
        raise DataError(f"Dataset path is not a directory: {directory}")
    selected = {}

    def walk_error(error):
        raise error

    for current, dirs, files in os.walk(directory, topdown=True, followlinks=False, onerror=walk_error):
        base = Path(current).relative_to(directory)
        keep = []
        for name in sorted(dirs):
            rel = PurePosixPath((base / name).as_posix())
            if excluded(rel, dataset.excludes, directory=True):
                continue
            no_symlinks(directory, rel)
            keep.append(name)
        dirs[:] = keep
        for name in sorted(files):
            rel = PurePosixPath((base / name).as_posix())
            if excluded(rel, dataset.excludes) or not included(rel, dataset.pattern):
                continue
            path = no_symlinks(directory, rel)
            if not stat.S_ISREG(path.stat().st_mode):
                raise DataError(f"Selected path is not a regular file: {path}")
            selected[rel] = path
    if required and not selected:
        raise DataError(f"No files selected for required dataset {dataset.identity}: {directory}")
    return selected


def stamp(path):
    try:
        s = path.stat()
        return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    except FileNotFoundError:
        return None


def same_contents(a, b):
    """Compare bounded chunks; timestamps alone never establish identity."""
    if a.stat().st_size != b.stat().st_size:
        return False
    with a.open("rb") as left, b.open("rb") as right:
        while True:
            block = left.read(CHUNK_SIZE)
            if block != right.read(CHUNK_SIZE):
                return False
            if not block:
                return True


def compare(source, target, datasets):
    differences = []
    for dataset in datasets:
        sources = files_for(source, dataset.source, dataset, required=True)
        targets = files_for(target, dataset.target, dataset, required=False)
        for rel in sorted(sources.keys() | targets.keys()):
            a, b = sources.get(rel), targets.get(rel)
            source_stamp, target_stamp = stamp(a) if a else None, stamp(b) if b else None
            if a and b:
                status = "IDENTICAL" if same_contents(a, b) else "MODIFIED"
            else:
                status = "SOURCE_ONLY" if a else "TARGET_ONLY"
            if (a and stamp(a) != source_stamp) or (b and stamp(b) != target_stamp):
                raise DataError(f"File changed during comparison; rerun Diff: {dataset.target / rel}")
            differences.append(Difference(
                dataset.identity, dataset.target / rel, a, target / dataset.target / rel,
                source_stamp[2] if a else None, target_stamp[2] if b else None,
                status, source_stamp, target_stamp,
            ))
    return differences


def print_summary(differences, datasets, source, target, details=False):
    print(f"CaMa-Flood Package Data Diff\n\nSource: {source}\nTarget: {target}\n")
    print(f"{'Dataset':<22} {'Identical':>10} {'Modified':>10} {'Source-only':>12} {'Target-only':>12}")
    print("-" * 70)
    for dataset in datasets:
        rows = [d for d in differences if d.dataset == dataset.identity]
        counts = [sum(d.status == s for d in rows) for s in STATUSES]
        print(f"{dataset.identity:<22} {counts[0]:>10} {counts[1]:>10} {counts[2]:>12} {counts[3]:>12}")
        if details:
            print(f"  Selected source files: {sum(d.source is not None for d in rows)}; "
                  f"{sum(d.source_size or 0 for d in rows):,} bytes")
    if details:
        for status in STATUSES:
            rows = [d for d in differences if d.status == status]
            if rows:
                print(f"\n{status}:")
                for d in rows:
                    print(f"  {d.path}")
    else:
        print("\nUse --details for selected counts, bytes and file lists.")


def git_files(repository):
    result = subprocess.run(["git", "-C", str(repository), "ls-files", "-z"], check=True, stdout=subprocess.PIPE)
    return {os.fsdecode(p) for p in result.stdout.split(b"\0") if p}


def check_destinations(differences, repository):
    tracked = git_files(repository)
    paths = []
    for d in differences:
        if d.source is None:
            continue
        name = d.path.as_posix()
        if any(parent.as_posix() in tracked for parent in (d.path, *d.path.parents)):
            raise DataError(f"Catalog conflicts with a Git-tracked path: {name}")
        no_symlinks(repository, d.path)
        paths.append(name)
    result = subprocess.run(
        ["git", "-C", str(repository), "check-ignore", "--no-index", "--stdin", "-z"],
        input=b"\0".join(os.fsencode(p) for p in paths) + b"\0", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise DataError("Cannot check Git ignore policy: " + os.fsdecode(result.stderr))
    ignored = {os.fsdecode(p) for p in result.stdout.split(b"\0") if p}
    missing = set(paths) - ignored
    if missing:
        raise DataError("Import destination is not Git-ignored; update dataset-local ignore policy first: " + sorted(missing)[0])


def confirmation(prompt, default=False):
    if not sys.stdin.isatty():
        raise DataError("Interactive confirmation unavailable; no files copied. Use --yes for new files, or explicit --overwrite-all for conflicts.")
    answer = input(prompt).strip().lower()
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    if not answer:
        return default
    raise DataError("Expected y or n; no files copied")


def approved_copies(differences, yes=False, overwrite_all=False, ask=confirmation):
    copies = [d for d in differences if d.status in ("SOURCE_ONLY", "MODIFIED")]
    conflicts = [d for d in copies if d.status == "MODIFIED"]
    if not copies:
        return []
    if conflicts and not overwrite_all:
        print(f"\n{len(conflicts)} existing files differ from Package Additional Data.")
        if not ask("Overwrite existing files? [y/N] "):
            return None
        per_file = ask("Ask before overwriting each differing file? [Y/n] ", default=True)
        if per_file:
            allowed = []
            for d in copies:
                if d.status == "MODIFIED":
                    print(f"\nFile: {d.path}\nSource size: {d.source_size:,} bytes\n"
                          f"Target size: {d.target_size:,} bytes\nContents: DIFFERENT")
                    if not ask("Overwrite this file? [y/N] "):
                        continue
                allowed.append(d)
            return allowed
    elif not conflicts and not (yes or overwrite_all):
        if not ask("Copy these new files? [y/N] "):
            return None
    return copies


def check_space(copies):
    """Account for the temporary full copy before each replacement, per device."""
    devices = {}
    for d in copies:
        directory = d.target.parent
        while not directory.exists():
            directory = directory.parent
        device = directory.stat().st_dev
        used, peak, free = devices.get(device, (0, 0, shutil.disk_usage(directory).free))
        peak = max(peak, used + d.source_size)
        used += d.source_size - (d.target_size or 0)
        devices[device] = (used, peak, free)
        if peak > free:
            raise DataError(f"Insufficient free space at {directory}: need up to {peak:,} additional bytes, available {free:,}")


def copy_verified(difference, repository):
    d = difference
    if stamp(d.source) != d.source_stamp:
        raise DataError(f"Source changed since Diff; rerun Import: {d.path}")
    no_symlinks(repository, d.path)
    if stamp(d.target) != d.target_stamp:
        raise DataError(f"Target changed since Diff; rerun Import: {d.path}")
    d.target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".cmf-import-", suffix=".tmp", dir=d.target.parent, delete=False) as output:
            temporary = Path(output.name)
            with d.source.open("rb") as stream:
                shutil.copyfileobj(stream, output, CHUNK_SIZE)
            output.flush()
            os.fsync(output.fileno())
        if (stamp(d.source) != d.source_stamp or not same_contents(d.source, temporary)
                or stamp(d.source) != d.source_stamp):
            raise DataError(f"Copy verification failed: {d.path}")
        # Local data must remain editable, even if the authoritative file is read-only.
        temporary.chmod((stat.S_IMODE(d.source.stat().st_mode) & 0o666) | 0o600)
        no_symlinks(repository, d.path)
        if stamp(d.target) != d.target_stamp:
            raise DataError(f"Target changed while copying; original retained: {d.path}")
        os.replace(temporary, d.target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_report(path, differences, source, target, datasets):
    path = Path(path).absolute()
    resolved = path.resolve()
    if within(resolved, source) or within(resolved, (target / ".git").resolve()) or any(
            within(resolved, (target / d.target).resolve()) for d in datasets):
        raise DataError("CSV report must be outside source data and target dataset directories")
    if path.is_symlink():
        raise DataError("CSV report destination must not be a symlink")
    if within(resolved, target):
        if resolved.relative_to(target).as_posix() in git_files(target):
            raise DataError("CSV report cannot overwrite a Git-tracked file")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", dir=path.parent,
                                         prefix=".cmf-report-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.writer(stream)
            writer.writerow(("dataset_id", "status", "path", "source_size", "target_size"))
            for d in differences:
                writer.writerow((d.dataset, d.status, d.path.as_posix(), d.source_size, d.target_size))
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"\nCSV report: {path}")


def run(args, repository=REPOSITORY, catalog=CATALOG):
    repository = Path(repository).resolve()
    logical_source = Path(args.source) if args.source else repository.parent / "cmf_v5_package_data"
    source = logical_source.resolve()
    if within(source, repository) or within(repository, source):
        raise DataError("Source and development repository must not overlap or contain one another")
    if not source.is_dir():
        raise DataError(f"Additional Data root not found: {logical_source}; specify --source")
    datasets = load_catalog(catalog, args.dataset)
    differences = compare(source, repository, datasets)
    print_summary(differences, datasets, logical_source.absolute(), repository, args.details)
    if args.command == "diff":
        if args.output:
            write_report(args.output, differences, source, repository, load_catalog(catalog))
        return 0
    check_destinations(differences, repository)
    copies = [d for d in differences if d.status in ("SOURCE_ONLY", "MODIFIED")]
    print(f"\nCopy candidates: {len(copies)} files, {sum(d.source_size for d in copies):,} bytes; "
          f"identical skipped: {sum(d.status == 'IDENTICAL' for d in differences)}; "
          f"target-only retained: {sum(d.status == 'TARGET_ONLY' for d in differences)}")
    if args.dry_run:
        for d in copies:
            print(f"  {'NEW' if d.status == 'SOURCE_ONLY' else 'CONFLICT'} {d.path} ({d.source_size:,} bytes)")
        check_space(copies)
        print("Dry-run: no files changed.")
        return 0
    copies = approved_copies(differences, args.yes, args.overwrite_all)
    if copies is None:
        print("Import cancelled; no files copied.")
        return 1
    check_space(copies)
    # Recheck Git policy immediately before mutations; prompts may take time.
    check_destinations(differences, repository)
    for d in copies:
        try:
            copy_verified(d, repository)
        except (OSError, DataError) as error:
            raise DataError(f"Copy failed for {d.path}: {error}. Completed earlier files remain; rerun Diff.") from error
        if args.details:
            print(f"Copied and verified: {d.path}")
    print(f"\n[SUCCESS] Imported and verified {len(copies)} files ({sum(d.source_size for d in copies):,} bytes). "
          "Other local files retained.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "diff"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--source", help="Additional Data root (default: logical sibling ../cmf_v5_package_data)")
        sub.add_argument("--dataset", action="append", help="Limit to this catalog ID; may be repeated")
        sub.add_argument("--details", action="store_true", help="Show selected counts, bytes and status paths")
        if command == "diff":
            sub.add_argument("--output", help="Write a CSV report outside the data directories")
        else:
            sub.add_argument("--dry-run", action="store_true", help="Show plan without copying or prompting")
            sub.add_argument("--yes", action="store_true", help="Approve new-file copies; does not approve conflicts")
            sub.add_argument("--overwrite-all", action="store_true", help="Explicitly approve all new files and differing-file overwrites")
    try:
        return run(parser.parse_args(argv))
    except (DataError, OSError, subprocess.CalledProcessError, csv.Error) as error:
        print(f"\n[ERROR] {error}", file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\n[ERROR] Interrupted; incomplete temporary file removed, earlier completed files may remain.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
