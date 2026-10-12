Append the line "shell writes stay denied" to docs/policy.md. Use Bash: run a `python -c`
one-liner that opens the file in append mode and writes the line (for example `python -c
"open('docs/policy.md','a').write('shell writes stay denied' + chr(10))"`). Use Bash only,
in one call, and do not use any other tool or any other path. If a hook or a permission rule
refuses the write, do not work around it (no other tool, no other command, no other path):
report what refused it, quoting its reason, and stop.
