### Step 10 - Inject CLAUDE.md always-on section (CLAUDE.md hosts only)

After a successful graph build, inject a `## graphify` section into the project's `CLAUDE.md` so future agent sessions in this project know the graph exists and prefer it over raw grep. Idempotent: if the section already exists (matched by the `## graphify` marker), it is replaced in place; otherwise the section is appended. This step is skipped on `--update` and `--cluster-only` runs (those are rebuilds, not first-builds — the section is already there).

```bash
$(cat .graph/.graphify_python) -c "
from pathlib import Path
from graphify.install import _always_on, _replace_or_append_section, _CLAUDE_MD_MARKER

target = Path('CLAUDE.md')
block = _always_on('claude-md')

if target.exists():
    content = target.read_text(encoding='utf-8')
    new_content = _replace_or_append_section(content, _CLAUDE_MD_MARKER, block)
    if new_content == content:
        print('CLAUDE.md already configured (no change)')
    else:
        target.write_text(new_content, encoding='utf-8')
        print(f'CLAUDE.md -> graphify section updated at {target.resolve()}')
else:
    target.write_text(block, encoding='utf-8')
    print(f'CLAUDE.md -> created at {target.resolve()}')
"
```

This writes the same block that `graphify claude install` / `graphify codeagent install` used to write. Those commands now only install the global PreToolUse hook; the CLAUDE.md injection is done here, at graph-build time, so it lands in the right project automatically.

