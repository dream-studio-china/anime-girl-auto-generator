#!/usr/bin/env python3
"""
ComfyUI 辅助脚本 — 项目本地工具
处理 workflow 提取/缓存、prompt 注入、提交生成、下载、历史记录。

用法:
  python comfyui_helper.py generate --prompt "你的prompt" [--seed 123] [--steps 25] [--cfg 3.5]
  python comfyui_helper.py extract-all           # 从 history 提取所有 workflow 并缓存
  python comfyui_helper.py list-workflows        # 列出已缓存的 workflow
  python comfyui_helper.py extract-workflow      # 提取默认 workflow
  python comfyui_helper.py check-server

修复了 userdata API 500 错误：改用 /history 提取 workflow + 本地缓存机制。
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # project root
BOOTSTRAP_DIR = PROJECT_ROOT / ".bootstrap"
CONFIG_PATH = BOOTSTRAP_DIR / "config" / "runtime.json"
STATE_DIR = BOOTSTRAP_DIR / "state"
HISTORY_PATH = STATE_DIR / "history.json"
CACHE_PATH = STATE_DIR / "workflow_cache.json"
WORKFLOWS_DIR = STATE_DIR / "workflows"
CATALOG_PATH = WORKFLOWS_DIR / "_catalog.json"
IMAGES_DIR = PROJECT_ROOT / "images"

# ── Helpers ────────────────────────────────────────────────────

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def api_get(server, path, timeout=15):
    """GET request with error handling."""
    url = f"{server.rstrip('/')}{path}"
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}

def api_post(server, path, data, timeout=30):
    """POST request with error handling."""
    url = f"{server.rstrip('/')}{path}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return {"error": f"HTTP {e.code}", "body": body[:500]}
    except Exception as e:
        return {"error": str(e)}


def extract_workflow_from_history(server, model_filter=None):
    """
    从 ComfyUI /history 提取最近的工作流 JSON。
    这是 userdata API 500 错误的官方替代方案。
    
    策略:
    1. 获取所有 history IDs
    2. 倒序遍历，找到匹配 model_filter 的工作流
    3. 提取 prompt[2] (workflow dict)
    """
    print(f"[extract] 从 {server}/history 提取 workflow...")
    history = api_get(server, "/history")
    
    if "error" in history:
        print(f"[extract] 错误: {history['error']}")
        return None
    
    ids = list(history.keys())
    print(f"[extract] 共有 {len(ids)} 条历史记录")
    
    for pid in reversed(ids):
        prompt = history[pid].get("prompt", [])
        if len(prompt) < 3 or not isinstance(prompt[2], dict):
            continue
        
        wf = prompt[2]
        nodes = {k: v for k, v in wf.items() if isinstance(v, dict) and "class_type" in v}
        
        # 检查是否有 CheckpointLoader
        has_checkpoint = any(
            isinstance(n, dict) and n.get("class_type") in ("CheckpointLoaderSimple", "CheckpointLoader")
            for n in nodes.values()
        )
        if not has_checkpoint:
            continue
        
        # 检查是否有 KSampler
        has_ksampler = any(
            isinstance(n, dict) and n.get("class_type") == "KSampler" for n in nodes.values()
        )
        if not has_ksampler:
            continue
        
        # Model filter
        if model_filter:
            model_match = False
            for n in nodes.values():
                if isinstance(n, dict):
                    ckpt = n.get("inputs", {}).get("ckpt_name", "")
                    if model_filter.lower() in ckpt.lower():
                        model_match = True
                        break
            if not model_match:
                continue
        
        # 提取 metadata
        classes = set(
            n.get("class_type", "") for n in nodes.values()
            if isinstance(n, dict) and "class_type" in n
        )
        models = []
        for n in nodes.values():
            if not isinstance(n, dict):
                continue
            if n.get("class_type") == "CheckpointLoaderSimple":
                models.append(n["inputs"].get("ckpt_name", "?"))
            if n.get("class_type") == "LoraLoader":
                models.append(f"LoRA: {n['inputs'].get('lora_name', '?')}")
        
        meta = {
            "prompt_id": pid,
            "node_count": len(nodes),
            "models": models,
            "has_empty_latent": "EmptyLatentImage" in classes,
            "has_load_image": "LoadImage" in classes,
            "has_upscale": "ImageUpscaleWithModel" in classes,
            "node_types": sorted(classes),
        }
        
        print(f"[extract] ✓ 找到 workflow: {pid[:8]}... ({len(nodes)} nodes, models={models})")
        return wf, meta
    
    print("[extract] ✗ 未找到匹配的 workflow")
    return None


def load_or_extract_workflow(server, model_filter=None, force_extract=False):
    """
    加载 workflow：优先从缓存，缓存失效则从 history 提取。
    """
    # 尝试缓存
    if not force_extract and CACHE_PATH.exists():
        try:
            with open(CACHE_PATH) as f:
                cache = json.load(f)
            wf = cache.get("workflow")
            meta = cache.get("meta", {})
            cache_age = time.time() - cache.get("cached_at", 0)
            if wf and cache_age < 86400:  # 24h cache
                print(f"[cache] ✓ 使用缓存的 workflow ({meta.get('node_count', '?')} nodes, {cache_age/3600:.1f}h ago)")
                return wf, meta
        except Exception as e:
            print(f"[cache] 缓存损坏: {e}")
    
    # 从 history 提取
    result = extract_workflow_from_history(server, model_filter)
    if result is None:
        return None, None
    
    wf, meta = result
    
    # 保存缓存
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump({
            "workflow": wf,
            "meta": meta,
            "cached_at": time.time(),
            "server": server,
        }, f, indent=2, ensure_ascii=False)
    print(f"[cache] 已缓存 workflow 到 {CACHE_PATH}")
    
    return wf, meta


def find_prompt_node(wf):
    """找到 prompt 注入节点 (PrimitiveStringMultiline)"""
    for nid, node in wf.items():
        if isinstance(node, dict) and node.get("class_type") == "PrimitiveStringMultiline":
            return nid
    return None


def is_api_format(wf):
    """Check if workflow is API format (nodes have class_type)."""
    if not isinstance(wf, dict):
        return False
    if "nodes" in wf and "links" in wf:
        return False  # editor format
    for v in wf.values():
        if isinstance(v, dict) and "class_type" in v:
            return True
    return False


def load_cached_workflow(name=None, category=None):
    """Load a workflow from the local cache (workflows/ dir).
    
    Priority: 1) exact name match, 2) category match (first found),
    3) fall back to quick-access cache (workflow_cache.json).
    Returns (workflow_dict, meta_dict) or (None, None).
    """
    # Try exact name match from workflows dir
    if name and WORKFLOWS_DIR.exists():
        for f in WORKFLOWS_DIR.glob("*.json"):
            if f.name == "_catalog.json":
                continue
            if name in f.name:
                with open(f) as fh:
                    data = json.load(fh)
                wf = data.get("workflow", data.get("content"))
                meta = data.get("meta", {})
                if is_api_format(wf):
                    return wf, meta
                elif isinstance(wf, dict) and "nodes" in wf:
                    print(f"[warn] {f.name}: editor 格式，需要 ComfyUI 前端转换")
                    continue
    
    # Try category match
    if category and WORKFLOWS_DIR.exists() and CATALOG_PATH.exists():
        with open(CATALOG_PATH) as f:
            cat = json.load(f)
        for fn, meta in cat.get("catalog", {}).items():
            if meta.get("category") == category:
                fpath = WORKFLOWS_DIR / fn
                if fpath.exists():
                    with open(fpath) as fh:
                        data = json.load(fh)
                    wf = data.get("workflow", data.get("content"))
                    if is_api_format(wf):
                        return wf, data.get("meta", {})
    
    # Fall back to quick-access cache (always API format)
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            cache = json.load(f)
        return cache.get("workflow"), cache.get("meta", {})
    
    return None, None


def find_ksampler_node(wf):
    """找到 KSampler 节点"""
    for nid, node in wf.items():
        if isinstance(node, dict) and node.get("class_type") == "KSampler":
            return nid
    return None


def find_empty_latent_node(wf):
    """找到 EmptyLatentImage 节点"""
    for nid, node in wf.items():
        if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
            return nid
    return None


def inject_params(wf, prompt=None, seed=None, steps=None, cfg=None, 
                  width=None, height=None, sampler=None, denoise=None):
    """注入参数到 workflow"""
    changes = {}
    
    # Prompt injection
    if prompt is not None:
        node_id = find_prompt_node(wf)
        if node_id:
            old = wf[node_id]["inputs"].get("value", "")
            wf[node_id]["inputs"]["value"] = prompt
            changes["prompt"] = f"node={node_id}"
        else:
            print("[warn] 未找到 PrimitiveStringMultiline 节点，尝试 CLIPTextEncode...")
            # Fallback: find CLIPTextEncode with "positive" in title
            for nid, node in wf.items():
                if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode":
                    title = node.get("_meta", {}).get("title", "").lower()
                    if "positive" in title or "prompt" in title:
                        wf[nid]["inputs"]["text"] = prompt
                        changes["prompt"] = f"node={nid} (CLIPTextEncode fallback)"
                        break
    
    # KSampler params
    ksid = find_ksampler_node(wf)
    if ksid:
        ks = wf[ksid]["inputs"]
        if seed is not None:
            ks["seed"] = seed
            changes["seed"] = seed
        if steps is not None:
            ks["steps"] = steps
            changes["steps"] = steps
        if cfg is not None:
            ks["cfg"] = cfg
            changes["cfg"] = cfg
        if sampler is not None:
            ks["sampler_name"] = sampler
            changes["sampler"] = sampler
        if denoise is not None:
            ks["denoise"] = denoise
            changes["denoise"] = denoise
    
    # Resolution
    elid = find_empty_latent_node(wf)
    if elid:
        el = wf[elid]["inputs"]
        if width is not None:
            el["width"] = width
            changes["width"] = width
        if height is not None:
            el["height"] = height
            changes["height"] = height
    
    return changes


def submit_generation(server, wf, client_id="comfyui-helper"):
    """提交 workflow 到 ComfyUI"""
    payload = {"prompt": wf, "client_id": client_id}
    result = api_post(server, "/prompt", payload)
    
    if "error" in result:
        print(f"[submit] 错误: {result['error']}")
        return None
    
    if "node_errors" in result and result["node_errors"]:
        print(f"[submit] 节点错误: {json.dumps(result['node_errors'], indent=2)}")
        return None
    
    prompt_id = result.get("prompt_id")
    print(f"[submit] ✓ 已提交: {prompt_id}")
    return prompt_id


def poll_completion(server, prompt_id, max_wait=600, interval=2):
    """轮询等待生成完成"""
    print(f"[poll] 等待生成完成 (max {max_wait}s)...")
    start = time.time()
    
    while time.time() - start < max_wait:
        time.sleep(interval)
        
        try:
            qdata = api_get(server, "/queue", timeout=5)
            if "error" in qdata:
                print(f"[poll] 队列查询错误: {qdata['error']}")
                continue
            
            running = qdata.get("queue_running", [])
            pending = qdata.get("queue_pending", [])
            all_ids = [r[1] for r in running] + [r[1] for r in pending]
            
            elapsed = int(time.time() - start)
            
            if prompt_id not in all_ids:
                print(f"[poll] ✓ 生成完成 ({elapsed}s)")
                return True
            
            if elapsed % 10 == 0:
                print(f"[poll] ... {elapsed}s (running={len(running)}, pending={len(pending)})")
                
        except Exception as e:
            print(f"[poll] 轮询异常: {e}")
    
    print(f"[poll] ✗ 超时 ({max_wait}s)")
    return False


def download_outputs(server, prompt_id, output_dir=None):
    """下载生成结果"""
    if output_dir is None:
        output_dir = IMAGES_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    hdata = api_get(server, f"/history/{prompt_id}")
    if "error" in hdata:
        print(f"[download] 获取历史失败: {hdata['error']}")
        return []
    
    entry = hdata.get(prompt_id, {})
    outputs = entry.get("outputs", {})
    
    downloaded = []
    for node_id, node_out in outputs.items():
        for img in node_out.get("images", []):
            filename = img["filename"]
            subfolder = img.get("subfolder", "")
            img_type = img.get("type", "output")
            
            out_path = output_dir / filename
            view_url = f"{server.rstrip('/')}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
            
            try:
                urllib.request.urlretrieve(view_url, str(out_path))
                size = out_path.stat().st_size
                print(f"[download] ✓ {filename} ({size/1024:.0f} KB)")
                downloaded.append({
                    "filename": filename,
                    "path": str(out_path),
                    "size": size,
                    "subfolder": subfolder,
                    "type": img_type,
                })
            except Exception as e:
                print(f"[download] ✗ {filename}: {e}")
    
    return downloaded


def record_history(prompt_id, changes, outputs, extra=None):
    """记录生成历史"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    record = {
        "prompt_id": prompt_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "changes": changes,
        "outputs": [o["path"] for o in outputs],
    }
    if extra:
        record.update(extra)
    
    history.append(record)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print(f"[history] ✓ 已记录到 {HISTORY_PATH}")


# ── Commands ───────────────────────────────────────────────────

def cmd_check_server(args):
    """检查 ComfyUI 服务器状态"""
    config = load_config()
    server = config["comfyui_server"]
    
    print(f"ComfyUI: {server}")
    
    # System stats
    stats = api_get(server, "/system_stats")
    if "error" in stats:
        print(f"  ✗ 无法连接: {stats['error']}")
        return 1
    
    sys_info = stats.get("system", {})
    devices = stats.get("devices", [])
    print(f"  ✓ ComfyUI {sys_info.get('comfyui_version', '?')} | Python {sys_info.get('python_version', '?')[:20]}")
    for d in devices:
        vram_free = d.get("vram_free", 0) / (1024**3)
        vram_total = d.get("vram_total", 0) / (1024**3)
        print(f"  ✓ GPU: {d.get('name', '?')} | VRAM: {vram_free:.1f}/{vram_total:.1f} GB")
    
    # Queue
    queue = api_get(server, "/queue")
    if "error" not in queue:
        print(f"  Queue: {len(queue.get('queue_running',[]))} running, {len(queue.get('queue_pending',[]))} pending")
    
    # Workflow cache
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            cache = json.load(f)
        meta = cache.get("meta", {})
        age = (time.time() - cache.get("cached_at", 0)) / 3600
        print(f"  Workflow cache: {meta.get('node_count','?')} nodes, {age:.1f}h old")
    else:
        print(f"  Workflow cache: 无 (运行 extract-workflow 或 generate 自动创建)")
    
    return 0


def cmd_extract_workflow(args):
    """提取并缓存 workflow"""
    config = load_config()
    server = config["comfyui_server"]
    
    model_filter = args.model or config.get("model_filter")
    wf, meta = load_or_extract_workflow(server, model_filter, force_extract=args.force)
    
    if wf is None:
        print("✗ 提取失败")
        return 1
    
    print(f"\n✓ Workflow: {meta['node_count']} nodes")
    print(f"  Models: {meta['models']}")
    print(f"  Features: {'txt2img' if meta['has_empty_latent'] else 'img2img'}, "
          f"{'upscale' if meta['has_upscale'] else 'no upscale'}")
    print(f"  节点类型: {', '.join(meta['node_types'])}")
    
    # 查找可注入的 prompt 节点
    prompt_node = find_prompt_node(wf)
    print(f"  Prompt 注入点: {prompt_node or '需 fallback CLIPTextEncode'}")
    
    return 0


def cmd_generate(args):
    """生成图片 - 一站式流程"""
    config = load_config()
    server = config["comfyui_server"].rstrip("/")
    
    # 1. Load workflow from cache (or extract from server)
    wf_name = getattr(args, 'workflow_name', None)
    wf, meta = load_cached_workflow(name=wf_name, category="anime")
    
    if wf is None:
        # Fall back to server extraction
        print("[info] 本地缓存无 API 格式 workflow，尝试从服务器提取...")
        model_filter = getattr(args, 'model', None) or config.get("model_filter")
        wf, meta = load_or_extract_workflow(server, model_filter, force_extract=True)
    
    if wf is None:
        print("✗ 无法加载 workflow。请先运行 extract-all 或确保服务器有历史记录。")
        return 1
    
    if not is_api_format(wf):
        print("✗ Workflow 是 editor 格式，需要先通过 ComfyUI 前端转换为 API 格式。")
        print("  浏览器中打开 workflow → app.graphToPrompt() 可获取 API 格式。")
        return 1
    
    print(f"[wf] {meta.get('models', ['?'])[0][:50]} ({meta.get('node_count', '?')} nodes)")
    
    import copy
    wf = copy.deepcopy(wf)
    
    # 2. Inject parameters
    seed = args.seed if args.seed is not None else random.randint(0, 2**63 - 1)
    changes = inject_params(
        wf,
        prompt=args.prompt,
        seed=seed,
        steps=args.steps,
        cfg=args.cfg,
        width=args.width,
        height=args.height,
        sampler=args.sampler,
        denoise=args.denoise,
    )
    print(f"[params] seed={seed} " + " ".join(f"{k}={v}" for k, v in changes.items() if k != "seed"))
    
    # 3. Submit
    prompt_id = submit_generation(server, wf)
    if prompt_id is None:
        return 1
    
    # 4. Poll
    ok = poll_completion(server, prompt_id, max_wait=args.timeout)
    if not ok:
        return 1
    
    # 5. Download
    outputs = download_outputs(server, prompt_id, output_dir=args.output_dir)
    if not outputs:
        print("✗ 没有输出文件")
        return 1
    
    # 6. Record history
    record_history(prompt_id, changes, outputs, extra={
        "prompt": args.prompt,
    })
    
    # 7. Summary
    print(f"\n{'='*50}")
    print(f"✓ 生成完成!")
    print(f"  Prompt ID: {prompt_id}")
    print(f"  Seed: {seed}")
    for o in outputs:
        print(f"  输出: {o['path']} ({o['size']/1024:.0f} KB)")
    
    return 0


def cmd_list_workflows(args):
    """列出已缓存的所有 workflow"""
    if not CATALOG_PATH.exists():
        print("✗ 尚未缓存任何 workflow")
        print("  运行: python .bootstrap/scripts/comfyui_helper.py extract-all")
        return 1
    
    with open(CATALOG_PATH) as f:
        cat = json.load(f)
    
    catalog = cat.get("catalog", {})
    print(f"\n{'='*70}")
    print(f"  已缓存 {len(catalog)} 个 workflow (更新于 {cat.get('updated', '?')})")
    print(f"{'='*70}")
    
    for i, (fn, meta) in enumerate(sorted(catalog.items(), key=lambda x: -x[1].get("usage_count", 0))):
        ks = meta.get("ksampler_defaults", {})
        print(f"\n  [{i+1}] {meta['type']}")
        print(f"      模型: {', '.join(meta['models'][:3])}")
        print(f"      使用: {meta['usage_count']} 次 | 分辨率: {meta.get('resolution', 'N/A')}")
        if ks:
            print(f"      默认: {ks.get('steps','?')}steps cfg{ks.get('cfg','?')} {ks.get('sampler_name','?')}")
        print(f"      Prompt注入: {meta.get('prompt_injection_node', 'unknown')}")
        print(f"      文件: {fn}")
    
    return 0


def cmd_extract_all(args):
    """从 history 提取所有 workflow 并缓存"""
    config = load_config()
    server = config["comfyui_server"].rstrip("/")
    
    print(f"=== 从 {server}/history 提取所有 workflow ===\n")
    
    history = api_get(server, "/history")
    if "error" in history:
        print(f"✗ 获取历史失败: {history['error']}")
        return 1
    
    print(f"总历史: {len(history)} 条\n")
    
    from collections import defaultdict
    groups = defaultdict(list)
    
    for pid, entry in history.items():
        prompt = entry.get("prompt", [])
        if len(prompt) < 3 or not isinstance(prompt[2], dict):
            continue
        wf = prompt[2]
        nodes = {k: v for k, v in wf.items() if isinstance(v, dict) and "class_type" in v}
        classes = sorted(set(n.get("class_type", "") for n in nodes.values()))
        
        models = []
        for n in nodes.values():
            ckpt = n.get("inputs", {}).get("ckpt_name")
            if ckpt:
                models.append(ckpt)
            lora = n.get("inputs", {}).get("lora_name")
            if lora:
                models.append(f"LoRA:{lora}")
            upscale = n.get("inputs", {}).get("model_name")
            if upscale and n.get("class_type") == "UpscaleModelLoader":
                models.append(f"Upscale:{upscale}")
        
        fp = (len(nodes), tuple(sorted(set(models)))[:5], tuple(classes[:15]))
        groups[fp].append((pid, wf))
    
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    catalog = {}
    
    for fp, entries in sorted(groups.items(), key=lambda x: -len(x[1])):
        node_count, models, classes = fp
        latest_pid, latest_wf = entries[-1]
        nodes = {k: v for k, v in latest_wf.items() if isinstance(v, dict) and "class_type" in v}
        
        # Determine workflow type
        has_empty = "EmptyLatentImage" in classes or "EmptySD3LatentImage" in classes or "EmptyFlux2LatentImage" in classes
        has_load = "LoadImage" in classes
        has_upscale = "ImageUpscaleWithModel" in classes
        has_wd14 = "WD14Tagger|pysssss" in classes
        has_lora = any("LoraLoader" in c for c in classes)
        
        wf_type = []
        if has_empty and not has_load:
            wf_type.append("txt2img")
        if has_load and not has_empty:
            wf_type.append("img2img")
        if has_upscale:
            wf_type.append("upscale")
        if has_wd14:
            wf_type.append("auto-tag")
        if has_lora:
            wf_type.append("LoRA")
        
        # Find prompt node
        prompt_node = None
        for nid, node in latest_wf.items():
            if isinstance(node, dict) and node.get("class_type") == "PrimitiveStringMultiline":
                prompt_node = nid
                break
        
        # KSampler params
        ks_params = {}
        for nid, node in nodes.items():
            if node.get("class_type") == "KSampler":
                ks = node.get("inputs", {})
                ks_params = {k: ks[k] for k in ("seed", "steps", "cfg", "sampler_name", "scheduler", "denoise") if k in ks}
                break
        
        # Resolution
        resolution = None
        for nid, node in nodes.items():
            if "Empty" in node.get("class_type", "") and "Image" in node.get("class_type", ""):
                inp = node.get("inputs", {})
                w = inp.get("width")
                h = inp.get("height")
                if isinstance(w, int) and isinstance(h, int):
                    resolution = f"{w}x{h}"
                break
        
        filename = f"{'+'.join(wf_type[:3])}_{'+'.join(m[:30] for m in models[:2])}".replace("/", "-").replace(" ", "_")[:100] + ".json"
        filepath = WORKFLOWS_DIR / filename
        
        meta = {
            "fingerprint": {"nodes": node_count, "models": list(models), "classes": list(classes)},
            "type": "+".join(wf_type),
            "usage_count": len(entries),
            "latest_prompt_id": latest_pid,
            "models": list(models),
            "prompt_injection_node": prompt_node,
            "ksampler_defaults": ks_params,
            "resolution": resolution,
            "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        with open(filepath, "w") as f:
            json.dump({"workflow": latest_wf, "meta": meta}, f, indent=2, ensure_ascii=False)
        
        catalog[filename] = meta
        print(f"  ✓ [{meta['type']:30s}] {len(entries):3d}次 | {meta['prompt_injection_node'] or 'N/A':>8s} | {resolution or 'N/A'}")
    
    # Write catalog
    with open(CATALOG_PATH, "w") as f:
        json.dump({"catalog": catalog, "total": len(catalog), "updated": time.strftime("%Y-%m-%d %H:%M:%S")},
                  f, indent=2, ensure_ascii=False)
    
    # Update quick-access cache with most-used workflow
    if not catalog:
        print("\n✓ 历史记录中没有可提取的 workflow")
        return 0
    
    best = max(catalog.items(), key=lambda x: x[1].get("usage_count", 0))
    best_path = WORKFLOWS_DIR / best[0]
    with open(best_path) as f:
        wf_data = json.load(f)
    with open(CACHE_PATH, "w") as f:
        json.dump({
            "workflow": wf_data["workflow"],
            "meta": {
                "node_count": best[1]["fingerprint"]["nodes"],
                "models": best[1]["models"],
                "has_empty_latent": "txt2img" in best[1]["type"],
                "has_load_image": "img2img" in best[1]["type"],
                "has_upscale": "upscale" in best[1]["type"],
            },
            "cached_at": time.time(),
            "server": server,
            "source": best[0],
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 共缓存 {len(catalog)} 个 workflow → {WORKFLOWS_DIR}/")
    print(f"  默认缓存: {best[0]} ({best[1]['usage_count']} uses)")
    return 0


# ── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ComfyUI 辅助工具 - 项目本地 workflow 管理和生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="命令")
    
    # check-server
    sub.add_parser("check-server", help="检查 ComfyUI 服务器状态")
    
    # extract-all
    sub.add_parser("extract-all", help="从 history 提取所有 workflow 并缓存")
    
    # list-workflows
    sub.add_parser("list-workflows", help="列出已缓存的所有 workflow")
    
    # extract-workflow
    ex = sub.add_parser("extract-workflow", help="提取并缓存默认 workflow")
    ex.add_argument("--model", help="按模型名过滤 (如 novaAnimeXL)")
    ex.add_argument("--force", "-f", action="store_true", help="强制重新提取 (忽略缓存)")
    
    # generate
    gen = sub.add_parser("generate", help="生成图片")
    gen.add_argument("--prompt", "-p", help="正向 prompt (如为空则使用默认)")
    gen.add_argument("--seed", type=int, help="种子 (默认随机)")
    gen.add_argument("--steps", type=int, help="采样步数")
    gen.add_argument("--cfg", type=float, help="CFG scale")
    gen.add_argument("--width", type=int, help="宽度")
    gen.add_argument("--height", type=int, help="高度")
    gen.add_argument("--sampler", help="采样器 (如 euler_ancestral)")
    gen.add_argument("--denoise", type=float, help="降噪强度 (img2img)")
    gen.add_argument("--model", help="按模型名过滤 workflow")
    gen.add_argument("--force-extract", action="store_true", help="强制重新提取 workflow")
    gen.add_argument("--timeout", type=int, default=600, help="生成超时 (秒)")
    gen.add_argument("--output-dir", help="输出目录 (默认 images/)")
    
    args = parser.parse_args()
    
    if args.command == "check-server":
        sys.exit(cmd_check_server(args))
    elif args.command == "extract-all":
        sys.exit(cmd_extract_all(args))
    elif args.command == "list-workflows":
        sys.exit(cmd_list_workflows(args))
    elif args.command == "extract-workflow":
        sys.exit(cmd_extract_workflow(args))
    elif args.command == "generate":
        sys.exit(cmd_generate(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
