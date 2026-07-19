#!/usr/bin/env python3
"""
validate_output.py — enforce agent output formats defined in data/formats/

Usage:
  python scripts/validate_output.py <agent_type> <output_file>
  python scripts/validate_output.py --list

Exit codes:
  0  all required checks pass (warnings may be present)
  1  one or more required checks failed
  2  usage error (unknown agent type, file not found, etc.)

Examples:
  python scripts/validate_output.py almanac_agent reports/week_22.txt
  python scripts/validate_output.py technical_agent reports/spx_tech.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from the repo root without installing the package
# Keeping this one, its fine.
sys.path.insert(0, str(Path(__file__).parent))

from rules import REGISTRY
from rules.base import Finding
from rules import AgentSpec


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


COLOR = _supports_color()
RED = "\033[31m" if COLOR else ""
YELLOW = "\033[33m" if COLOR else ""
GREEN = "\033[32m" if COLOR else ""
BOLD = "\033[1m" if COLOR else ""
RESET = "\033[0m" if COLOR else ""


def _sev_color(sev: str) -> str:
    return {
        "FAIL": f"{BOLD}{RED}FAIL{RESET}",
        "WARN": f"{YELLOW}WARN{RESET}",
        "PASS": f"{GREEN}PASS{RESET}",
    }.get(sev, sev)


def _format_finding(f: Finding, agent: str) -> str:
    sev, rule_name, lineno, msg = f
    location = f"line {lineno}" if lineno > 0 else "not found"
    return (
        f"  {_sev_color(sev)}"
        f"  {BOLD}{agent}{RESET} › {rule_name}"
        f"  [{location}]"
        f"\n        {msg}"
    )


def _format_pass(rule_name: str, agent: str) -> str:
    return f"  {_sev_color('PASS')}  {agent} › {rule_name}"


def _run_rules(rules, lines) -> list[Finding]:
    findings: list[Finding] = []
    for rule in rules:
        findings.extend(rule.check(lines))
    return findings


def validate(agent_type: str, text: str) -> list[tuple[str, list[Finding]]]:
    """
    Returns a list of (block_label, findings) pairs.
    Single-block agents return one pair with label "".
    Multi-block agents (e.g. technical_agent) return one pair per instrument.
    """
    spec: AgentSpec = REGISTRY[agent_type]
    lines = text.splitlines()

    if spec.split_blocks:
        blocks = spec.split_blocks(lines)
        return [(label, _run_rules(spec.rules, block_lines))
                for label, block_lines in blocks]
    else:
        return [("", _run_rules(spec.rules, lines))]


def _print_block(block_label: str, findings: list[Finding], rules, agent: str, verbose: bool) -> tuple[int, int, int]:
    """Print results for one block. Returns (pass, warn, fail) counts."""
    if block_label:
        print(f"\n  {BOLD}── {block_label}{RESET}")

    failed_names = {f[1] for f in findings if f[0] == "FAIL"}
    warned_names = {f[1] for f in findings if f[0] == "WARN"}

    for rule in rules:
        rule_findings = [f for f in findings if f[1] == rule.name]
        if rule_findings:
            for f in rule_findings:
                print(_format_finding(f, agent))
        elif verbose:
            print(_format_pass(rule.name, agent))

    fail_count = len(failed_names)
    warn_count = len(warned_names)
    pass_count = len(rules) - fail_count - warn_count
    return pass_count, warn_count, fail_count


def run(agent_type: str, filepath: Path, verbose: bool = False) -> int:
    if agent_type not in REGISTRY:
        known = ", ".join(sorted(REGISTRY))
        print(
            f"Error: unknown agent type '{agent_type}'. Known: {known}", file=sys.stderr
        )
        return 2

    if not filepath.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        return 2

    text = filepath.read_text(encoding="utf-8")
    blocks = validate(agent_type, text)
    spec = REGISTRY[agent_type]
    rules = spec.rules

    print(f"\n{BOLD}Validating:{RESET} {filepath}  ({agent_type})")
    if len(blocks) > 1:
        print(f"  {len(blocks)} instrument blocks found")

    total_pass = total_warn = total_fail = 0
    for block_label, findings in blocks:
        p, w, f = _print_block(block_label, findings, rules, agent_type, verbose)
        total_pass += p
        total_warn += w
        total_fail += f

    rules_per_block = len(rules)
    total_rules = rules_per_block * len(blocks)

    print(f"\n{'─' * 60}")
    print(
        f"  {GREEN}{total_pass} passed{RESET}"
        f"  {YELLOW}{total_warn} warnings{RESET}"
        f"  {RED}{total_fail} failed{RESET}"
        f"  ({total_rules} checks across {len(blocks)} block(s))"
    )

    if total_fail > 0:
        print(
            f"\n{RED}RESULT: FAIL{RESET} — {total_fail} required check(s) did not pass.\n"
        )
        return 1

    print(f"\n{GREEN}RESULT: PASS{RESET}\n")
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate agent output files against their format specs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "agent_type",
        nargs="?",
        help="Agent type to validate against (e.g. almanac_agent)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        type=Path,
        help="Path to the agent output file to validate",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all known agent types and exit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Also print passing checks",
    )

    args = parser.parse_args()

    if args.list:
        print("Known agent types:")
        for name in sorted(REGISTRY):
            spec = REGISTRY[name]
            multi = "  [multi-block]" if spec.split_blocks else ""
            print(f"  {name}  ({len(spec.rules)} rules){multi}")
        sys.exit(0)

    if not args.agent_type or not args.output_file:
        parser.print_help()
        sys.exit(2)

    sys.exit(run(args.agent_type, args.output_file, verbose=args.verbose))


if __name__ == "__main__":
    main()
