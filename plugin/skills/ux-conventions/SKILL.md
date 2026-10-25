---
name: ux-conventions
description: The organization's UX and brand conventions for user-facing interfaces. Use whenever designing, building or reviewing a screen, page, component, form, CLI output or error message that a person sees — the spec.md design pass, UI work in the build phase and the visual loop in the test phase ("follow the UX conventions", "design the form", "match the mock", "write the error message").
---

# UX conventions

## Source
- Article p.12–14 (design phase: "brand, security, compliance, and UX policies written as
  skills"; the spec must "conform to our brand guidelines ... and UX standards" and flag
  "areas of concern, especially where you cannot satisfy contradicting policies"), p.17
  (a mock from Claude Design exported to build), p.28 step 5 (the visual loop: "Give Claude a
  browser or screenshot tool, give it the mock, and let it iterate. Implement, screenshot,
  compare, and adjust. Two or three rounds is normal").
- Owner's brand and UX guidelines (colors, type, spacing, tone of voice, component
  library): the project's `policies/ux-conventions.md`, written by the owner in their own
  words (ROADMAP R27). Read it first when it exists: where it and this skill differ, the
  source wins, over a project override too; a rule here it does not mention still
  applies. No file means these rules alone. It is a guardrail path (decision 40): never
  edit it in a run.
- Project override: `.claude/skills/ux-conventions/SKILL.md`. Projects without a user
  interface leave this skill unused; the check says so.

## Rules
1. Start from the mock or the existing screen; a new pattern is a flagged concern in
   `spec.md`, not an invention in the build phase.
2. Reuse the project's component library and tokens; no ad-hoc colors, fonts or spacing.
3. Every action has a visible result: loading, success, error and empty states are designed,
   not left to the framework's defaults.
4. Error messages say what happened and what the person can do next, in the project's tone;
   never expose stack traces, identifiers or internal names.
5. Accessibility is part of done: labels on every control, keyboard reachability, contrast,
   no information carried by color alone.
6. Visible copy lives where the project keeps copy (translations, constants), not inline in
   markup.
7. The test phase closes the visual loop: implement, screenshot, compare with the mock, adjust;
   the screenshots go into `changes/<id>-<slug>/evidence/screenshots/` by hand, or, when
   `sdlc.yaml: commands.drive` is set, the drive writes them into `evidence/proof/` and the
   plan names each as a `screenshot:` item (change 0004).

## Check
Run the deterministic check and include its output in your summary (article p.22 pattern):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/ux-conventions/check.py" --root "${CLAUDE_PROJECT_DIR}" --id <change id>
```
It lists the UI files in the diff, flags copy hard-coded in markup, and reports whether
`evidence/proof/` or `evidence/screenshots/` holds a screenshot. Example output:
```
## ux-conventions check
- UI changed but evidence/proof/ and evidence/screenshots/ hold no screenshot: run the visual loop (implement, screenshot, compare with the mock) and save the result
- note: UI files changed: src/components/Form.tsx
```
Deterministic backing, rule by rule (R27): rules 1 to 6 have no hook or gate check. Rule 7 has
one only when `sdlc.yaml: commands.drive` is set: the gate's `proof` entry checks that each
`screenshot:` item of the approved plan exists under `evidence/proof/` (change 0004); the
gate's evidence check requires the verifier report and the toolchain logs, never a by-hand
screenshot (`REQUIRED_EVIDENCE`), so otherwise only this skill's own advisory check looks for
one, in the two folders. The REVIEW.md pass at deploy re-checks rules 1 to 7. This skill is
advisory (p.22 governance).
