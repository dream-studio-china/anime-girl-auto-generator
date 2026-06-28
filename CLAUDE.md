# Anime Girl Auto Generator — Project Rules

## File Location Convention

All files related to this project **MUST** be stored inside the project directory or `/tmp/`. Absolutely no project files under `~` (home directory).

### ✅ Allowed locations
| Purpose | Path |
|---------|------|
| Project code (shared) | `{PROJECT_DIR}/` |
| Generated images (all) | `{PROJECT_DIR}/images/` |
| Workflow configs | `{PROJECT_DIR}/.bootstrap/state/` |
| Temporary files | `/tmp/` (clean up after use) |

### ❌ Prohibited
- `~/` — no scripts, no temp files, no output files
- `~/.hermes/scripts/` — only for Hermes infra scripts (e.g. `comfyui_health.py`), **not** for project logic

### Why
- The ComfyUI server is **remote** (`http://100.78.52.73:8188`), not on this machine
- SaveImage on the remote server can only write to `/home/ubuntu/ComfyUI/output/`
- Local scripts must download images from remote via the `/view` API endpoint
- Hardcoded Mac paths (`/Volumes/Nayuki/...`) in workflow JSON cause **"Saving image outside the output folder"** errors

## Image Generation Workflow (unified — interactive + cron)

All image generation follows the same flow:

1. Build workflow JSON with `filename_prefix` only (no full path)
2. Submit to remote ComfyUI API
3. Poll `/history/{prompt_id}` for completion
4. Download via `/view?type=output&filename=...` to `{PROJECT_DIR}/images/`
5. Serve via `MEDIA:` prefix in agent responses

### Cron differences (daily 18:00)

The daily cron adds a pre-generation step: search trending anime topics → generate 10 prompts from trends → then use the **exact same** generation flow as above. No separate scripts, no special paths.
