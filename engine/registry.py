"""Reference registry loading and validation (plan §3.1)."""
import pathlib
import re

from .miniyaml import MiniYamlError, load

REGISTRY = pathlib.Path("references/registry.yaml")
TYPES = {"open", "closed", "docs"}
STATUSES = {"scored", "candidate", "to-score", "unscored-conflict"}
REQUIRED = ["slug", "name", "origin", "url", "licence", "pin", "host", "type", "status",
            "baseline", "benchmark", "publisher"]
BENCHMARK_COUNT = 9
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PIN = re.compile(r"^[0-9a-f]{40}$")


def load_registry(root="."):
    return load(pathlib.Path(root) / REGISTRY)


def entries(reg, variants=True):
    return list(reg.get("references") or []) + (list(reg.get("variants") or []) if variants else [])


def validate(reg, root=".", check_files=True):
    """Return a list of error strings (empty when valid)."""
    errors = []
    if reg.get("schema") != 1:
        errors.append("schema must be 1")
    seen = set()
    for e in entries(reg):
        slug = e.get("slug", "?")
        for k in REQUIRED:
            if k not in e:
                errors.append(f"{slug}: missing {k}")
        if not isinstance(slug, str) or not _SLUG.match(slug):
            errors.append(f"{slug}: slug is not kebab-case")
        if slug in seen:
            errors.append(f"{slug}: duplicate slug")
        seen.add(slug)
        if e.get("type") not in TYPES:
            errors.append(f"{slug}: type not in {sorted(TYPES)}")
        if e.get("status") not in STATUSES:
            errors.append(f"{slug}: status not in {sorted(STATUSES)}")
        if e.get("type") == "open" and not (isinstance(e.get("pin"), str) and _PIN.match(e["pin"])):
            errors.append(f"{slug}: open entries need a 40-hex pin")
        if e.get("type") in ("closed", "docs") and not e.get("docs"):
            errors.append(f"{slug}: closed and docs entries need docs[]")
        for d in e.get("docs") or []:
            if not all(d.get(k) for k in ("url", "snapshot_date", "file")):
                errors.append(f"{slug}: every docs[] entry needs url, snapshot_date and file")
        if not e.get("licence"):
            errors.append(f"{slug}: licence missing")
        if e.get("status") == "scored":
            if not e.get("baseline"):
                errors.append(f"{slug}: status scored implies baseline: true")
            if check_files:
                from .baseline import round_dir
                if not (round_dir(root) / "lenses" / f"{slug}.json").exists():
                    errors.append(f"{slug}: scored but baseline lenses/{slug}.json is missing")
        if e.get("benchmark") and e.get("status") != "scored":
            errors.append(f"{slug}: benchmark implies status scored")
        if e.get("status") == "unscored-conflict" and not e.get("conflict"):
            errors.append(f"{slug}: unscored-conflict needs a conflict reason")
    n = sum(1 for e in entries(reg) if e.get("benchmark"))
    if n != BENCHMARK_COUNT:
        errors.append(f"exactly {BENCHMARK_COUNT} entries must have benchmark: true (found {n})")
    return errors


def benchmark_slugs(reg):
    return [e["slug"] for e in entries(reg, variants=False) if e.get("benchmark")]
