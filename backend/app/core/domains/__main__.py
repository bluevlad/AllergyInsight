"""DomainPack CLI — ``python -m app.core.domains lint <path>``.

Usage:
    python -m app.core.domains lint backend/app/domains/allergy/pack.yaml
    python -m app.core.domains lint --all backend/app/domains
    python -m app.core.domains lint --strict pack.yaml      # warning 도 fail

Exit codes:
    0  ✅ 통과 (errors 0, strict 모드에서 warnings 도 0)
    1  ❌ 검증 실패
    2  사용법 오류

WBS: P1-G-004
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from app.core.domains.pack_linter import LintResult, Severity, validate


def _print_issues(result: LintResult, *, label: str) -> None:
    if result.errors:
        sys.stderr.write(f"\n[{label}] errors:\n")
        for e in result.errors:
            sys.stderr.write(f"  {e}\n")
    if result.warnings:
        sys.stderr.write(f"\n[{label}] warnings:\n")
        for w in result.warnings:
            sys.stderr.write(f"  {w}\n")


def _lint_one(path: Path, *, strict: bool, check_environ: bool) -> bool:
    """returns True if path passes (per strict mode)."""
    if not path.exists():
        sys.stderr.write(f"[{path}] 파일 미존재\n")
        return False

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            sys.stderr.write(f"[{path}] YAML 파싱 실패: {e}\n")
            return False

    if not isinstance(raw, dict):
        sys.stderr.write(f"[{path}] YAML 최상위가 dict 가 아님\n")
        return False

    result = validate(raw, base_dir=path.parent, check_environ=check_environ)
    _print_issues(result, label=str(path))

    if result.fails(strict=strict):
        return False
    sys.stdout.write(
        f"[{path}] ✅ 통과 — errors=0, warnings={len(result.warnings)}\n"
    )
    return True


def _find_packs(domains_dir: Path) -> list[Path]:
    """domains_dir 하위 모든 <domain>/pack.yaml."""
    if not domains_dir.exists():
        return []
    return sorted(domains_dir.glob("*/pack.yaml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.core.domains",
        description="DomainPack YAML 검증 CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    lint = sub.add_parser("lint", help="pack.yaml 검증")
    lint.add_argument(
        "target",
        type=Path,
        nargs="?",
        help="pack.yaml 경로 또는 --all 사용 시 domains 디렉토리",
    )
    lint.add_argument(
        "--all",
        action="store_true",
        help="target 디렉토리 하위의 모든 <domain>/pack.yaml 검증",
    )
    lint.add_argument(
        "--strict",
        action="store_true",
        help="warning 도 실패로 처리",
    )
    lint.add_argument(
        "--check-environ",
        action="store_true",
        help="api_key_env 환경변수 미설정 시 W107 발생",
    )

    args = parser.parse_args(argv)

    if args.cmd != "lint":
        parser.error("unknown command")
        return 2

    if args.target is None:
        parser.error("target 경로 필요")
        return 2

    target = args.target.resolve()

    if args.all:
        if not target.is_dir():
            sys.stderr.write(f"--all 은 디렉토리 필요: {target}\n")
            return 2
        packs = _find_packs(target)
        if not packs:
            sys.stderr.write(f"[{target}] pack.yaml 0개\n")
            return 0
        all_pass = True
        for p in packs:
            ok = _lint_one(
                p, strict=args.strict, check_environ=args.check_environ
            )
            all_pass = all_pass and ok
        return 0 if all_pass else 1

    # 단일 파일
    if target.is_dir():
        sys.stderr.write(
            f"단일 파일 모드인데 디렉토리 — --all 옵션 필요: {target}\n"
        )
        return 2
    return 0 if _lint_one(
        target, strict=args.strict, check_environ=args.check_environ
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
