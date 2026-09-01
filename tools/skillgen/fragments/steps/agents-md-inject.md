### Step 10 - Inject AGENTS.md always-on section (AGENTS.md hosts only)

After a successful graph build, inject a `## graphify` section into the project's `AGENTS.md` so future agent sessions in this project know the graph exists and prefer it over raw grep. Idempotent: if the section already exists (matched by the `## graphify` marker), it is replaced in place; otherwise the section is appended. This step is skipped on `--update` and `--cluster-only` runs (those are rebuilds, not first-builds — the section is already there).

```bash
"$(cat .graph/.graphify_python)" -c "
from pathlib import Path
from graphify.install import _always_on, _replace_or_append_section, _AGENTS_MD_MARKER

target = Path('AGENTS.md')
block = _always_on('agents-md')

if target.exists():
    content = target.read_text(encoding='utf-8')
    new_content = _replace_or_append_section(content, _AGENTS_MD_MARKER, block)
    if new_content == content:
        print('AGENTS.md already configured (no change)')
    else:
        target.write_text(new_content, encoding='utf-8')
        print(f'AGENTS.md -> graphify section updated at {target.resolve()}')
else:
    target.write_text(block, encoding='utf-8')
    print(f'AGENTS.md -> created at {target.resolve()}')
"
```

This writes the same 12-line block that `graphify install --platform opencode` used to write via `graphify opencode install` — that command is now deprecated. The block tells agents: "check `.graph/graph.json` before answering codebase questions, run `graphify query` for focused questions, run `graphify update .` after code changes."

