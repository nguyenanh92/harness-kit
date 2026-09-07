---
phase: 1
title: "Inline scorer into hk.py"
status: pending
priority: P1
effort: "2h"
dependencies: []
---

# Phase 1: Inline scorer into `hk.py`

## Problem

`py hk.py audit` fails immediately after install with:
```
validate_harness.py not found. Vendor it first:
  git clone --depth 1 https://github.com/nguyenanh92/harness-kit.git .harness-scripts
```

`validate_harness.py` imports `from lib.harness_utils import ...` so downloading
just one file via urllib won't work either. The only dependency-free fix is to
inline the scoring logic directly into `hk.py`.

## Solution: Inline minimal 5-subsystem scorer

Port the exact same scoring logic from `skills/scripts/lib/harness_utils.py`
into `hk.py`. Keep the public algorithm identical so scores stay consistent.

**What to inline** (all from `harness_utils.py`):

| Symbol | Lines | Purpose |
|--------|-------|---------|
| `Check`, `SubsystemResult`, `ScoreResult` dataclasses | ~20 | Score data model |
| `_compile_needle`, `text_has`, `has_file` | ~20 | Text matching helpers |
| `validate_feature_list` | ~45 | Feature list validation |
| `load_governance`, `list_code_modules` | ~25 | File loading |
| The 5 check-builder blocks + `score_harness` | ~100 | Core scoring |
| `format_text_report`, `escape_html`, `html_report`, `_HTML_STYLE` | ~80 | Output |

Total addition: ~290 lines. `hk.py` goes from 466 → ~756 LOC.
Acceptable — it remains stdlib-only and self-contained.

## `cmd_audit` rewrite

```python
def cmd_audit(args: argparse.Namespace, root: Path) -> int:
    """Score the harness inline — no external validate_harness.py needed."""
    result = _score_harness(root)          # inline scorer
    html_out = getattr(args, "html", None)
    if html_out:
        out = Path(html_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_html_report(result, f"Harness: {root.name}"), encoding="utf-8")
        print(f"HTML report: {out}")
    print(_format_text_report(result, root))
    return 0 if result.overall >= 70 else 1
```

Backward compat: if `validate_harness.py` is found in the known locations
**and** the user did NOT pass `--html`, prefer the external validator (power
users may have customised it). If `--html` is requested or the external file is
not found, use the inline scorer. This keeps existing power-user workflows intact.

## Implementation Notes

1. Add a `# ── Inline scorer (ported from harness_utils.py) ──` section near
   the top of `hk.py`, after imports, before the root-resolution helpers.
2. Prefix all ported symbols with `_` (`_score_harness`, `_Check`, etc.) to
   avoid name collisions and signal they are internal.
3. Copy the algorithm verbatim — do not simplify checks. Scores must match
   `validate_harness.py` on the same project.
4. `_HTML_STYLE` constant can be shortened (remove the `extras_html` parameter
   from `_html_report` since `hk.py` doesn't use it).

## Files

- **Modify:** `skills/templates/hk.py`

## Success Criteria

- [ ] `py hk.py audit` in a freshly scaffolded temp dir exits 0 with a score ≥ 0
- [ ] `py hk.py audit --html /tmp/r.html` produces a readable HTML file
- [ ] Score matches `py skills/scripts/validate_harness.py --target <same dir> --json` overall value
- [ ] All 15 `test_skill.py` tests still pass
- [ ] No import beyond stdlib in `hk.py`

## Risk Assessment

Inlining ~290 lines increases `hk.py` file size but not complexity — the added
code is pure data-transformation with no side effects. The risk of drift between
inline and external scorer is real but low: the external scorer is rarely
changed, and the inline one is only used when the external isn't found.
