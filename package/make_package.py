"""Independent beta package assembly; clean source and additional store stay read-only.

Reuse the Import/Diff catalog, path checks, bounded verified copier and atomic
clean-archive publisher. No Git archive, worktree overlay or scientific processing.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile

import package_data as data
from archive_clean_repo import BUILD_INFO, publish

PACKAGE = Path(__file__).resolve().parent
MAJOR_DIRS = ("src_main", "config", "tools", "map", "inp", "gosh_test", "tutorial",
              "visualization", "variable_table", "package", "legacy", "docs")
BUILDER_VERSION = "1"
MANIFEST = "package/PACKAGE_MANIFEST.json"


def forbidden(name):
    parts = PurePosixPath(name).parts
    return (parts[0] in (".git", ".github", "research")
            or any(p in (".git", ".gitignore", ".gitattributes", ".gitmodules") for p in parts)
            or (len(parts) > 1 and parts[0] == "package" and
                (parts[1].startswith(("repo_clean_", ".repo_clean_tmp.", ".cmf-package-"))
                 or (parts[1].startswith("cmf_") and parts[1].endswith("_pkg")))))


def token(path):
    s = path.lstat()
    return (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def tree_files(root):
    """Inventory the clean tree without following symlink directories."""
    result = {}
    def walk_error(error):
        raise error
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in dirs[:]:
            path = Path(parent) / name
            relative = path.relative_to(root).as_posix()
            if forbidden(relative):
                raise data.DataError(f"Forbidden/generated path in clean tree: {relative}")
            if path.is_symlink():
                dirs.remove(name)
                files.append(name)
        for name in files:
            path = Path(parent) / name
            relative = path.relative_to(root).as_posix()
            if forbidden(relative) or relative in (MANIFEST, "PACKAGE_MANIFEST.json", "PACKAGE_BUILD_INFO.txt"):
                raise data.DataError(f"Forbidden/reserved path in clean tree: {relative}")
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                target = os.readlink(path)
                if os.path.isabs(target) or not data.within(path.resolve(), root) or not path.resolve().exists():
                    raise data.DataError(f"Unsafe/dangling clean symlink: {relative} -> {target}")
            elif not stat.S_ISREG(mode):
                raise data.DataError(f"Non-regular clean source: {relative}")
            result[relative] = (path, token(path))
    return result


def build_info(clean, version):
    path = clean / BUILD_INFO
    if (clean / "package").is_symlink() or not path.is_file() or path.is_symlink():
        raise data.DataError(f"Missing regular {BUILD_INFO} in clean tree; regenerate it with p01")
    info = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.partition(": ")
        if not sep or key in info:
            raise data.DataError("Malformed/duplicate clean build information")
        info[key] = value
    if info.get("Package version") != version:
        raise data.DataError("Clean Repository version does not match VER")
    if (not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", info.get("Source commit", ""))
            or not info.get("Source branch") or info.get("Package stage") != "Clean Git source extraction"):
        raise data.DataError("Invalid clean-source provenance")
    return info


def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(data.CHUNK_SIZE), b""):
            h.update(block)
    return h.hexdigest()


def plan(package, version, configured_source):
    if not re.fullmatch(r"v5b01_[A-Za-z0-9][A-Za-z0-9_.-]*", version):
        raise data.DataError("Invalid VER (expected v5b01_ plus letters/numbers/_.-)")
    package = package.resolve()
    clean_path = package / f"repo_clean_{version}"
    clean = clean_path.resolve()
    raw = Path(configured_source).expanduser()
    # Both dry-run and assembly use the script's package directory, never cwd.
    source = (raw if raw.is_absolute() else package / raw).resolve()
    output = package / f"cmf_{version}_pkg"
    print(f"VER: {version}\nClean Repository: {clean}\nPackage Additional Data: {source}\nOutput: {output}", flush=True)
    if clean_path.is_symlink() or not clean.is_dir():
        raise data.DataError("Clean Repository must be an existing real directory")
    if os.path.lexists(output):
        raise data.DataError(f"Output already exists; refusing overwrite: {output}")
    if not source.is_dir():
        raise data.DataError(f"Package Additional Data is missing: {source}")
    if data.within(source, package.parent) or data.within(package.parent, source):
        raise data.DataError("Additional Data and development repository must not overlap")
    for a, b in ((clean, source), (clean, output), (source, output)):
        if data.within(a, b) or data.within(b, a):
            raise data.DataError(f"Unsafe input/output containment: {a}, {b}")
    info = build_info(clean, version)
    for directory in MAJOR_DIRS:
        if not (clean / directory).is_dir() or (clean / directory).is_symlink():
            raise data.DataError(f"Missing real major source directory: {directory}")
    originals = tree_files(clean)
    catalog = package / "package_data.csv"
    catalog_stamp = token(catalog)
    datasets = data.load_catalog(catalog)
    selected, summaries, conflicts, problems = {}, [], [], []
    for dataset in datasets:
        try:
            files = data.files_for(source, dataset.source, dataset, required=True)
            for name in originals:
                relative = PurePosixPath(name)
                if data.within(relative, dataset.target) and relative != dataset.target:
                    if data.excluded(relative.relative_to(dataset.target), dataset.excludes):
                        raise data.DataError(f"Clean source conflicts with catalog exclusion: {name}")
            count, size, duplicates = 0, 0, 0
            for relative, path in sorted(files.items()):
                name = (dataset.target / relative).as_posix()
                if forbidden(name) or name in (MANIFEST, BUILD_INFO, "PACKAGE_MANIFEST.json", "PACKAGE_BUILD_INFO.txt"):
                    raise data.DataError(f"Catalog would restore a forbidden/reserved path: {name}")
                data.no_symlinks(clean, PurePosixPath(name))
                snapshot = data.stamp(path)
                entry = dict(source=path, stamp=snapshot, dataset=dataset.identity)
                selected[name] = entry
                count += 1
                size += snapshot[2]
                if name in originals:
                    if not data.same_contents(path, originals[name][0]):
                        conflicts.append(name)
                    else:
                        duplicates += 1
                elif (clean / name).exists() and (clean / name).is_dir():
                    conflicts.append(name + " (source directory vs data file)")
            summaries.append(dict(dataset_id=dataset.identity, file_count=count, bytes=size, identical_duplicates=duplicates))
            print(f"Dataset {dataset.identity}: {count} files, {size} bytes; identical duplicates {duplicates}")
            print(f"  Include: {dataset.pattern}; exclusions: {';'.join(dataset.excludes) or '(none)'}")
        except (data.DataError, OSError) as exc:
            problems.append(str(exc))
    clean_bytes = sum(s[3] for _, s in originals.values())
    total_files = len(set(originals) | set(selected))
    total_bytes = clean_bytes + sum(e["stamp"][2] for n, e in selected.items() if n not in originals)
    print(f"Clean source: {len(originals)} files, {clean_bytes} bytes")
    print(f"Total before manifest: {total_files} files, {total_bytes} bytes")
    print(f"Conflicts: {len(conflicts)}; missing/invalid datasets: {len(problems)}")
    if conflicts or problems:
        raise data.DataError("\n".join([*("Conflicting path: " + n for n in conflicts), *problems]))
    # Reserve directory/manifest overhead and the largest in-flight verified copy.
    largest = max([0, *(s[3] for _, s in originals.values()), *(e['stamp'][2] for e in selected.values())])
    required = total_bytes + largest + max(1024*1024, total_bytes//100)
    free = shutil.disk_usage(package).free
    print(f"Free disk: {free} bytes; conservative required space: {required} bytes")
    if required > free:
        raise data.DataError("Insufficient free disk space for staged package and verification")
    return dict(package=package, clean=clean, source=source, output=output, version=version,
                configured_source=configured_source, info=info, originals=originals, datasets=datasets,
                selected=selected, summaries=summaries, catalog_stamp=catalog_stamp)


def unchanged(p):
    if tree_files(p['clean']) != p['originals']:
        raise data.DataError("Clean Repository changed during assembly")
    if token(p['package'] / 'package_data.csv') != p['catalog_stamp']:
        raise data.DataError("Selection catalog changed during assembly")
    selected = {}
    for dataset in p['datasets']:
        for relative, path in data.files_for(p['source'], dataset.source, dataset, required=True).items():
            selected[(dataset.target / relative).as_posix()] = (path, data.stamp(path))
    if selected != {n: (e['source'], e['stamp']) for n, e in p['selected'].items()}:
        raise data.DataError("Selected Additional Data changed during assembly")


def copy_one(source, snapshot, relative, tree):
    destination = tree / relative
    difference = data.Difference("assembly", PurePosixPath(relative), source, destination,
                                 snapshot[2], None, "SOURCE_ONLY", snapshot, None)
    data.copy_verified(difference, tree)
    # Import intentionally strips executable flags; assembly preserves source mode.
    destination.chmod(stat.S_IMODE(source.stat().st_mode))


def assemble(p):
    print("\n[STEP 1/3] Copy clean source", flush=True)
    with tempfile.TemporaryDirectory(prefix='.cmf-package-', dir=p['package']) as temporary:
        tree = Path(temporary) / 'tree'
        tree.mkdir()
        # Preserve empty source directories, but never traverse a link directory.
        for parent, dirs, _ in os.walk(p['clean'], followlinks=False):
            for name in dirs:
                path = Path(parent) / name
                if not path.is_symlink():
                    (tree / path.relative_to(p['clean'])).mkdir(parents=True, exist_ok=True)
        for name, (path, snapshot) in sorted(p['originals'].items()):
            if token(path) != snapshot:
                raise data.DataError(f"Clean source changed before copy: {name}")
            if path.is_symlink():
                (tree / name).parent.mkdir(parents=True, exist_ok=True)
                (tree / name).symlink_to(os.readlink(path))
            else:
                copy_one(path, data.stamp(path), name, tree)
        print("\n[STEP 2/3] Integrate catalog-selected additional data", flush=True)
        for name, entry in sorted(p['selected'].items()):
            if name not in p['originals']:
                print(f"Copy {name}: {entry['stamp'][2]} bytes", flush=True)
                copy_one(entry['source'], entry['stamp'], name, tree)
        print("\n[STEP 3/3] Verify complete package and write manifest", flush=True)
        expected = set(p['originals']) | set(p['selected'])
        actual = tree_files(tree)
        if set(actual) != expected:
            raise data.DataError("Staged package inventory differs from planned source/data union")
        records = []
        for name in sorted(expected):
            target = tree / name
            if name in p['originals']:
                source, snapshot = p['originals'][name]
                if target.is_symlink():
                    if not source.is_symlink() or os.readlink(target) != os.readlink(source):
                        raise data.DataError(f"Symlink copy differs: {name}")
                elif not data.same_contents(source, target) or stat.S_IMODE(source.stat().st_mode) != stat.S_IMODE(target.stat().st_mode):
                    raise data.DataError(f"Clean source copy differs: {name}")
            if name in p['selected']:
                if not data.same_contents(p['selected'][name]['source'], target):
                    raise data.DataError(f"Additional Data copy differs: {name}")
            link = target.is_symlink()
            size = target.lstat().st_size
            checksum = hashlib.sha256(os.fsencode(os.readlink(target))).hexdigest() if link else digest_file(target)
            records.append(dict(path=name, size=size, type='symlink' if link else 'file', sha256=checksum))
        manifest = manifest_for(p, records)
        payload = write_manifest(tree, manifest)
        unchanged(p)
        publish(tree, p['output'])
    print(f"\n[SUCCESS] {p['output']}\nPackage: {len(records)+1} entries, {sum(r['size'] for r in records)+len(payload)} bytes including manifest")
    return manifest


def manifest_for(p, records):
    lookup = {r['path']: r for r in records}
    datasets = []
    for summary in p['summaries']:
        h = hashlib.sha256()
        for name in sorted(n for n, e in p['selected'].items() if e['dataset'] == summary['dataset_id']):
            record = lookup[name]
            h.update(json.dumps([name, record['size'], record['sha256']], ensure_ascii=True).encode() + b'\n')
        datasets.append(dict(summary, content_sha256=h.hexdigest()))
    raw = Path(p['configured_source'])
    return dict(package_version=p['version'], generation_date=datetime.now().astimezone().isoformat(),
                source_git_commit=p['info']['Source commit'], source_branch=p['info']['Source branch'],
                clean_repository_version=p['info']['Package version'], package_builder_version=BUILDER_VERSION,
                package_builder_sha256=digest_file(Path(__file__)), catalog_sha256=digest_file(p['package']/'package_data.csv'),
                additional_data_source=dict(path=raw.name if raw.is_absolute() else str(raw),
                    path_basis='absolute host path redacted to store basename' if raw.is_absolute() else 'builder package/ directory',
                    version=None),
                datasets=datasets, files=records, file_checksums='SHA256; symlinks hash link text',
                manifest_self_excluded_from_files=True,
                package_totals=dict(file_count=len(records)+1, bytes=0, includes_manifest=True))


def write_manifest(tree, manifest):
    base_size = sum(r['size'] for r in manifest['files'])
    # Self-size affects the total's digits only; settle before writing once.
    for _ in range(10):
        payload = (json.dumps(manifest, indent=2, ensure_ascii=True) + '\n').encode()
        size = base_size + len(payload)
        if manifest['package_totals']['bytes'] == size:
            (tree / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
            (tree / MANIFEST).write_bytes(payload)
            return payload
        manifest['package_totals']['bytes'] = size
    raise data.DataError("Manifest total size did not stabilize")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--package-data', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    p = plan(PACKAGE, args.version, args.package_data)
    if args.dry_run:
        print("\n[SUCCESS] Dry-run only; no files changed")
    else:
        assemble(p)


if __name__ == '__main__':
    try:
        main()
    except (data.DataError, OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
