Fix the typo in docs/policy.md with the Edit tool: "Teh rule" must read "The rule". Make the
edit directly, in one Edit call, and do not touch any other file. If a hook or a permission
rule refuses the edit, do not work around it (no other tool, no other path): report what
refused it, quoting its reason, and stop.
