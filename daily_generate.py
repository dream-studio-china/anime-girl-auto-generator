#!/usr/bin/env python3
"""
Daily Anime Hot Topic Image Generation Script
Submits prompts to ComfyUI API directly, downloads results.
"""

import json
import os
import random
import time
import urllib.request
import urllib.error
import urllib.parse
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER = "http://100.78.52.73:8188"
OUTPUT_DIR = os.path.join(PROJECT_DIR, "images", "daily") + "/"

# Base workflow template (read from file)
BASE_WORKFLOW_PATH = os.path.join(PROJECT_DIR, ".bootstrap", "state", "yume_api_workflow.json")

# ── 12 SFW Aesthetic Themes ──
THEMES = [
    {
        "name_ja": "夏の花火",
        "name_cn": "夏日花火",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, wearing a light blue yukata with floral pattern, holding a small fan, watching fireworks in the night sky, summer festival, riverbank at dusk, vibrant fireworks bursting in the sky, reflections on water, lanterns glowing, warm atmosphere, cinematic lighting, gorgeous color palette",
        "desc": "身着浴衣的少女在夏日祭典河畔仰望花火"
    },
    {
        "name_ja": "向日葵畑",
        "name_cn": "向日葵花田",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, standing in a vast sunflower field, wearing a white sundress and straw hat, golden sunlight streaming through, bright blue sky with soft clouds, sunflowers blooming all around, warm summer day, gentle breeze, dreamy atmosphere, depth of field, beautiful lighting",
        "desc": "白裙少女置身于金色向日葵花田中"
    },
    {
        "name_ja": "黄昏の教室",
        "name_cn": "黄昏教室",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, sitting by the window in an empty classroom, golden sunset light streaming through the glass, warm orange glow across wooden desks, books scattered, gentle breeze through the window, wistful expression, after school atmosphere, nostalgic mood, cinematic composition",
        "desc": "放学后的空教室，少女独坐窗边沐浴金色夕阳"
    },
    {
        "name_ja": "紫陽花と雨",
        "name_cn": "紫阳花雨",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, holding a transparent umbrella, walking through a garden path lined with blooming hydrangeas, gentle summer rain, blue and purple hydrangea flowers wet with raindrops, wearing a light summer dress, serene expression, misty atmosphere, reflections on wet ground, soft lighting",
        "desc": "少女撑着透明伞漫步在紫阳花盛开的雨中庭院"
    },
    {
        "name_ja": "星空の丘",
        "name_cn": "星空山丘",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, lying on a grassy hill under a brilliant starry night sky, milky way visible, wearing a cozy sweater, small wildflowers around, distant city lights twinkling far below, serene night atmosphere, moonlight gently illuminating her face, peaceful expression, dreamy, magical",
        "desc": "少女躺在草地上仰望满天繁星的夜空"
    },
    {
        "name_ja": "海辺の夕暮れ",
        "name_cn": "海边黄昏",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, standing at the shoreline at sunset, gentle waves lapping at her feet, wearing a flowing white dress, golden and orange sky with soft clouds, sun setting on the horizon, warm light on her face, gentle sea breeze blowing her hair, seashells on the beach, peaceful mood, beautiful reflection on water",
        "desc": "少女站在海边，落日余晖洒满海面与白裙"
    },
    {
        "name_ja": "灯りと蛍",
        "name_cn": "萤火虫之夜",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, standing by a gentle stream in a forest at dusk, hundreds of fireflies floating in the air, warm golden lights, wearing a simple summer yukata, reaching out toward the glowing fireflies, magical atmosphere, soft bokeh, deep greens and golds, serene expression, fairy-tale mood, breathtaking",
        "desc": "少女在夏夜溪边被萤火虫的光芒环绕"
    },
    {
        "name_ja": "竹林の小径",
        "name_cn": "竹林小径",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, walking along a stone path through a towering bamboo grove, dappled sunlight filtering through the green canopy, wearing a light linen kimono-style dress, gentle breeze rustling bamboo leaves, shafts of golden light, peaceful atmosphere, traditional Japanese garden aesthetic, soft greens, serene",
        "desc": "少女穿行于光影斑驳的竹林石径"
    },
    {
        "name_ja": "夏の図書館",
        "name_cn": "夏日图书馆",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, sitting in a quiet library by a large window, afternoon sun streaming in, surrounded by bookshelves filled with colorful books, reading a book with a gentle expression, dust particles dancing in the sunbeams, warm wood tones, peaceful atmosphere, summer cicadas faintly audible through the window, cozy, nostalgic",
        "desc": "少女午后在阳光洒落的图书馆静静阅读"
    },
    {
        "name_ja": "風鈴の縁側",
        "name_cn": "风铃檐廊",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, sitting on a traditional wooden engawa porch, glass wind chimes hanging above gently tinkling in the summer breeze, wearing a light yukata, cool drink beside her, garden view in the background with green leaves and summer flowers, relaxed expression, warm afternoon, peaceful domestic atmosphere, Japanese summer aesthetic",
        "desc": "少女坐在日式檐廊边，风铃轻响，午后悠然"
    },
    {
        "name_ja": "花屋の午後",
        "name_cn": "花店午后",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, inside a cozy flower shop, wearing an apron over a simple dress, arranging a bouquet of mixed summer flowers, warm afternoon light through the shop window, shelves filled with colorful flowers and potted plants, gentle smile, rustic wooden interior, sunbeams illuminating the blossoms, peaceful, charming, beautiful composition",
        "desc": "花店少女在午后的暖光中精心整理花束"
    },
    {
        "name_ja": "月夜の橋",
        "name_cn": "月夜古桥",
        "prompt": "masterpiece, newest, absurdres, best quality, amazing quality, very aesthetic, ultra-detailed, highly detailed, 1girl, solo, standing on a traditional arched wooden bridge under the full moon, wearing an elegant modern dress with traditional elements, the moon reflected on still water below, willow trees framing the scene, soft silver moonlight, lanterns along the path, night insects chirping, dreamy atmosphere, romantic, ethereal lighting",
        "desc": "少女立于月夜古桥上，水面倒映明月与灯火"
    },
]

def load_base_workflow():
    with open(BASE_WORKFLOW_PATH, 'r') as f:
        return json.load(f)

def submit_prompt(workflow):
    """Submit workflow to ComfyUI API and return prompt_id."""
    payload = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(
        f"{SERVER}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("prompt_id")
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error: {e.code} - {e.read().decode()}")
        return None
    except Exception as e:
        print(f"  Error submitting prompt: {e}")
        return None

def poll_result(prompt_id, max_wait=120):
    """Poll for completion and return output filenames."""
    for i in range(max_wait):
        time.sleep(2)
        try:
            req = urllib.request.Request(f"{SERVER}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                if prompt_id in data:
                    outputs = data[prompt_id].get("outputs", {})
                    images = []
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            for img in node_output["images"]:
                                images.append(img)
                    if images:
                        return images
        except Exception as e:
            print(f"  Poll error: {e}")
    print(f"  Timed out waiting for prompt {prompt_id}")
    return None

def download_image(filename, subfolder, save_path):
    """Download an image from ComfyUI output."""
    params = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": "output"
    })
    url = f"{SERVER}/view?{params}"
    try:
        urllib.request.urlretrieve(url, save_path)
        return True
    except Exception as e:
        print(f"  Download error: {e}")
        return False

def build_workflow(theme, seed):
    """Build workflow for a specific theme with given seed."""
    wf = load_base_workflow()
    
    # Set positive prompt (node 39)
    wf["39"]["inputs"]["text"] = theme["prompt"]
    
    # Disable LoRA by setting strength to 0 (node 32)
    wf["32"]["inputs"]["strength_model"] = 0.0
    wf["32"]["inputs"]["strength_clip"] = 0.0
    
    # Set random seed (node 37)
    wf["37"]["inputs"]["seed"] = seed
    
    # Set steps and cfg (already 25, 3.5 but ensure)
    wf["37"]["inputs"]["steps"] = 25
    wf["37"]["inputs"]["cfg"] = 3.5
    
    # Set resolution
    wf["45"]["inputs"]["width"] = 1080
    wf["45"]["inputs"]["height"] = 1920
    
    # Set filename prefix
    safe_name = theme["name_cn"].replace(" ", "_")
    wf["38"]["inputs"]["filename_prefix"] = f"daily_{safe_name}"
    
    return wf

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

    for idx, theme in enumerate(THEMES, 1):
        theme_label = f"{theme['name_cn']} ({theme['name_ja']})"
        print(f"\n[{idx}/{len(THEMES)}] {theme_label}")
        print(f"  └ {theme['desc']}")
        
        seed = random.randint(1, 2**31 - 1)
        workflow = build_workflow(theme, seed)
        
        print(f"  Seed: {seed}")
        print(f"  Submitting to ComfyUI...")
        
        prompt_id = submit_prompt(workflow)
        if not prompt_id:
            print(f"  ✗ Failed to submit")
            results.append((theme, None, "submit_failed"))
            continue
        
        print(f"  Prompt ID: {prompt_id}")
        print(f"  Generating...")
        
        images = poll_result(prompt_id, max_wait=180)
        if not images:
            print(f"  ✗ No output received")
            results.append((theme, None, "no_output"))
            continue
        
        print(f"  Got {len(images)} image(s)")
        
        downloaded = []
        for img_info in images:
            filename = img_info["filename"]
            subfolder = img_info.get("subfolder", "")
            save_name = f"{idx:02d}_{theme['name_cn']}_{filename}"
            save_path = os.path.join(OUTPUT_DIR, save_name)
            
            if download_image(filename, subfolder, save_path):
                print(f"  ✓ Downloaded: {save_name}")
                downloaded.append(save_name)
            else:
                print(f"  ✗ Download failed: {filename}")
        
        results.append((theme, downloaded, "success" if downloaded else "download_failed"))
        
        # Small delay between submissions to avoid overwhelming the server
        if idx < len(THEMES):
            time.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    success_count = sum(1 for _, _, status in results if status == "success")
    print(f"Successful: {success_count}/{len(THEMES)}")
    
    for theme, files, status in results:
        label = f"{theme['name_cn']} ({theme['name_ja']})"
        if status == "success":
            print(f"  ✓ {label} → {', '.join(files)}")
        else:
            print(f"  ✗ {label} → {status}")
    
    print(f"\nAll images saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
