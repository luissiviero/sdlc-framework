---
name: spec-template
description: The spec.md template for phase (b) design of the SDLC framework — the requirements-and-design spec the design pass writes from a merged intent.md, with the mandatory "Flagged concerns" section and the header that logs the prompt and the plugin version in force. Use whenever asked to write, review, update or close concerns in a spec.md or a design spec for a change ("write the spec", "spec.md", "design spec for change 0001", "close the flagged concerns").
---

# spec.md template

Source: article p.13–14 (Stage 2 Design: "Claude takes intent.md and produces a requirements
and design spec, constrained by the organization's skills, with areas of concern flagged";
p.14 governance: "The spec, the prompt that produced it, and the skill versions in force are
all logged in version control"). Build guide steps 22–23. The section names are defined once,
in `plugin/gate/artifacts.py` (`SPEC_SECTIONS`); the gate checks them at gate (b).

Write `changes/<id>-<slug>/spec.md` with exactly this shape. Keep the five sections in this
order and never leave one empty ("none" is a valid body).

```markdown
# Spec: <short title, the same as the intent's>
Change id: <id>. Status: proposed. Produced by: sdlc plugin <version>, /sdlc-design prompt v1 (article p.14). Skills: <policy skills applied, comma-separated> (plugin <version>); overrides: none | <project skills under .claude/skills/ that replaced a plugin skill>.

## Requirements
<what the change must do and must not do, one requirement per bullet, each checkable; the
intent's Proposed outcome restated as requirements, plus the ones the policies add>

## Design
<how it fits the existing codebase: modules or files touched at the level of responsibility,
data shapes, interfaces, error behaviour, what stays unchanged; no order of work, no test
names — those belong in plan.md>

## Open questions from intent
<each open question from intent.md, quoted, with its answer or "carried forward: <why and
who decides>"; "none" when the intent had none>

## Flagged concerns
<one list item per concern: a policy the design cannot fully satisfy, two policies that
contradict each other, a risk-list item touched, a guess made because the intent was silent;
"none" when there is none>

## Acceptance
<the quantifiable target the test phase measures (article p.27 step 3): the tests that must
pass by name or by behaviour, the lint and build state, the screenshot or mock to match for
UI, the metric and its threshold>
```

## Rules
- **Header.** The second line is rendered by
  `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" spec-header --root . --id <id>`;
  paste it as printed. It records the pinned plugin version from `sdlc.yaml` and the policy
  skills in force, so the spec, the prompt and the skill versions are logged together
  (p.14). The gate parks a spec whose header lacks `Change id:` or `Produced by:`.
- **Concerns fail closed** (PROGRESS choice 14): every list item under "## Flagged concerns"
  is an open concern unless it starts with `[x]`, `closed`, `resolved` or `decided`. The gate
  parks the change while any concern is open. To close one, edit the item so it starts with
  one of those words followed by the decision, e.g.
  `- [x] Cache location: decided ~/.cache/<app>/ per the data conventions.`
  The closing word must be the first word of the item: `- C3: decided ...` is still open,
  because the gate reads the item from its start.
  Only the owner closes a concern (article p.14 step 4: "the product owner resolves each one
  with its policy owner"); the design pass opens them and may close only the ones the policy
  text itself settles, saying which policy.
- **Open questions are answered or carried forward**, never dropped (p.14 step 3). A
  carried-forward question is also a flagged concern if the build cannot proceed without it.
- **Requirements, not implementation.** Files, order of work, risks and proof go to plan.md
  (skill `plan-template`), written by the read-only planning run that follows the spec.
- **Apply the policies as constraints** (p.14 governance): write the spec with the policy
  skills loaded (`coding-standards`, `security-baseline`, `ux-conventions`,
  `data-conventions`, `definition-of-done`) and say in Requirements which rules apply.
  Where two policies contradict, or a policy cannot be met, that is a flagged concern, not a
  silent choice.
- **Never edit intent.md** in phase (b): it was accepted at gate (a) and the gate parks a
  branch that changes it.
- Plain language, short bullets, English only.
