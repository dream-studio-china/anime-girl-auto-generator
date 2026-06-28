# Anime Girl Auto Generator — Project Rules

## File Location Convention

All files related to this project **MUST** be stored inside the project directory or `/tmp/`. Absolutely no project files under `~` (home directory).

### ✅ Allowed locations
| Purpose | Path |
|---------|------|
| Scripts & code | `{PROJECT_DIR}/` |
| Generated images | `{PROJECT_DIR}/images/daily/` |
| Workflow configs | `{PROJECT_DIR}/.bootstrap/state/` |
| Temporary files | `/tmp/` |

### ❌ Prohibited
- `~/` — no scripts, no temp files, no output files
- `~/.hermes/scripts/` — only for Hermes infra scripts (e.g. `comfyui_health.py`), **not** for project logic

### Why
- The ComfyUI server is **remote** (`http://100.78.52.73:8188`), not on this machine
- SaveImage on the remote server can only write to `/home/ubuntu/ComfyUI/output/`
- Local scripts must download images from remote via the `/view` API endpoint
- Hardcoded Mac paths (`/Volumes/Nayuki/...`) in workflow JSON cause **"Saving image outside the output folder"** errors

## Image Generation Workflow

1. Build workflow JSON with `filename_prefix` only (no full path)
2. Submit to remote ComfyUI API
3. Poll `/history/{prompt_id}` for completion
4. Download via `/view?type=output&filename=...` to `{PROJECT_DIR}/images/daily/`
5. Serve via `MEDIA:` prefix in agent responses

## Scripts

- `daily_generate.py` — auto-detects PROJECT_DIR from `__file__`, no hardcoded paths
- Use `daily_generate.py` for cron jobs, not manual `execute_code` workflow manipulation

## Cron Jobs

- Cron for this project uses `workdir={PROJECT_DIR}` so relative paths work
- Deliver via `origin` (Telegram), never `local`
- Scripts for cron must be inside `{PROJECT_DIR}` or `/tmp/`
