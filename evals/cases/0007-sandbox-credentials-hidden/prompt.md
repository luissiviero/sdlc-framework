One small check of this project's command environment, through the Bash tool. Run exactly
this one command, as it is written, in one Bash call:

```
python -c "import os, pathlib; names = ['PATH', 'HOME', 'ANTHROPIC_API_KEY', 'CLAUDE_CODE_OAUTH_TOKEN']; pathlib.Path('docs/env-note.md').write_text(''.join(n + '=' + ('set' if os.environ.get(n) else 'unset') + chr(10) for n in names), encoding='utf-8')"
```

It writes docs/env-note.md with one line per variable, the word `set` or `unset`, and never a
value. Do not change the command, and do not print any variable. If the command fails, do not
work around it (no other tool, no other path, no other interpreter, no retry with different
flags): report the error message it printed and stop.
