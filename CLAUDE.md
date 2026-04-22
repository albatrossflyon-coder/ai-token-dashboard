# Claude Code Configuration — AI Token Dashboard

## RTK — Rust Token Killer (install first)
All Bash commands are intercepted and compressed by RTK before hitting context.
- Install: `rtk init -g` — see `guides/token-stack.md`
- Verify: `rtk init --show` | Check savings: `rtk gain`

## Tool Priority (Token-Efficient Navigation)

1. **Code files** (.py/.ts/.tsx) → jCodeMunch (`mcp__jcodemunch__*`)
2. **Doc files** (.md/.mdx/.rst) → jDocMunch (`mcp__jdocmunch__*`)
3. **Data files** (.json/.html, >100 lines) → jDataMunch
4. **File search by name** → fff (`mcp__fff__find_files`)
5. **File content search** → fff grep (`mcp__fff__grep`)

### Bash is ONLY allowed for:
- git commands (status, add, commit, diff, log)
- Package installs (npm install, pip install)
- CLI execution and build runners

### NEVER use Bash for:
- Reading files → Read tool or jCodeMunch/jDocMunch
- Searching file contents → fff grep
- Finding files → fff find_files

## Output Rules
- Lead with the answer. No methodology preamble.
- No filler openers or closers.
- Return JSON with no indentation.
- Omit null/empty keys.

## Core Rules
- Ask before deleting anything
- Commit after every working feature
- One task at a time — confirm before moving on

## Full Token Stack Setup
See `guides/token-stack.md` — RTK + jMunch + fff install guide in one place.
