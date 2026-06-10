# Scripts Reference — Vibe Context Architect

## Script Index

| Script | Phase | Purpose |
|---|---|---|
| `scan_project.py` | 1 | Scan project topology + detect stack |
| `extract_configs.py` | 2 | Extract facts from config files |
| `extract_git_signals.py` | 2 | Mine git history for patterns |
| `extract_annotations.py` | 2 | Mine TODO/FIXME/HACK comments |
| `resolve_conflicts.py` | 3 | Merge + resolve pattern conflicts |
| `generate_context.py` | 4 | Generate all .ai-context/ files |
| `install_context.py` | 5 | Write files to project |
| `create_update_hook.py` | 5 | Install update hook |
| `update_context.py` | Update | Incremental update mode |
| `diff_context.py` | Update | Diff old vs new context |
| `export_context.py` | Util | Export as single portable file |
| `utils.py` | Util | Shared utilities |

## Full Pipeline Usage

```bash
# Full pipeline
python scripts/scan_project.py --root ./my-project --output /tmp/vca/scan_result.json
python scripts/extract_configs.py --scan /tmp/vca/scan_result.json --output /tmp/vca/config_facts.json
python scripts/extract_git_signals.py --root ./my-project --output /tmp/vca/git_signals.json
python scripts/extract_annotations.py --root ./my-project --output /tmp/vca/annotations.json
# (LLM pattern mining step happens in agent loop using agents/pattern-miner.md)
python scripts/resolve_conflicts.py --patterns /tmp/vca/pattern_raw.json --configs /tmp/vca/config_facts.json --output /tmp/vca/conventions.json
python scripts/generate_context.py --conventions /tmp/vca/conventions.json --scan /tmp/vca/scan_result.json --configs /tmp/vca/config_facts.json --annotations /tmp/vca/annotations.json --output /tmp/vca/output/
python scripts/install_context.py --source /tmp/vca/output/ --target ./my-project/.ai-context/

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VCA_WORKSPACE` | `/tmp/vca` | Intermediate workspace |
| `VCA_MAX_FILES` | `40` | Max files to deep-analyze |
| `VCA_MAX_FILE_LINES` | `500` | Max lines to read per file |
| `VCA_AUTO` | `false` | Skip confirmation prompts |
