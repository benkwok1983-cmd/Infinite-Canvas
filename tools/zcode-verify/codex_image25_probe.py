#!/usr/bin/env python3
"""Codex Images 2.5 探测脚本（WORKPLAN T1.1）。

独立于产品链路：不 import main.py，不依赖项目运行环境。
默认 dry-run 只构造请求体；加 --run 才真实调用 gpt-image-2-skill（消耗 Codex 订阅额度，
必须先获用户授权）。

用法：
    python codex_image25_probe.py            # dry-run
    python codex_image25_probe.py --run      # 真实探测（花 3 次额度）
    python codex_image25_probe.py --run --only flare   # 只跑指定变体
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

VARIANTS = {
    "auto": None,  # 不传 tools[].model，走服务端默认路由
    "flare": "gpt-image-2.5-flare",
    "sunburst": "gpt-image-2.5-sunburst",
}

PROBE_PROMPT = (
    "一只橙色纸雕小狐狸，深蓝背景，正方形构图。"
    "画质要求：目标输出 1024x1024 高分辨率图片。"
    "Image quality requirement: output a 1024x1024 high-resolution image."
)


def find_skill_cli():
    configured = str(os.getenv("GPT_IMAGE_2_SKILL_BIN") or "").strip()
    if configured:
        return configured
    for name in ("gpt-image-2-skill", "gpt-image-2-skill.exe", "gpt-image-2-skill.cmd"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def resolve_host_model():
    """与 main.py codex_image_host_model() 同序：env → CODEX_HOME/USERPROFILE config.toml 顶层 model。"""
    for key in ("CODEX_IMAGE_HOST_MODEL", "CODEX_MODEL"):
        value = str(os.getenv(key) or "").strip()
        if value and not value.lower().startswith(("gpt-image", "$imagegen")):
            return value, key
    candidates = []
    codex_home = str(os.getenv("CODEX_HOME") or "").strip()
    if codex_home:
        candidates.append(Path(codex_home) / "config.toml")
    user_profile = str(os.getenv("USERPROFILE") or "").strip()
    if user_profile:
        candidates.append(Path(user_profile) / ".codex" / "config.toml")
    home = Path.home()
    if str(home) != user_profile:
        candidates.append(home / ".codex" / "config.toml")
    for path in dict.fromkeys(candidates):
        if not path or not path.is_file():
            continue
        try:
            section = ""
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("["):
                    section = line
                    continue
                if section:
                    continue
                match = re.fullmatch(r"model\s*=\s*(\"([^\"\\]*)\"|'([^'\\]*)')\s*(?:#.*)?", line)
                if match:
                    value = (match.group(2) if match.group(2) is not None else match.group(3) or "").strip()
                    if value and not value.lower().startswith(("gpt-image", "$imagegen")):
                        return value, str(path)
        except (OSError, UnicodeError):
            continue
    return "", "fallback"


def build_body(host_model, tool_model):
    tool = {"type": "image_generation", "background": "auto", "output_format": "png"}
    if tool_model:
        tool["model"] = tool_model
    return {
        "model": host_model,
        "instructions": "Generate exactly one image using the image_generation tool.",
        "store": False,
        "stream": True,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": PROBE_PROMPT}]}],
        "tools": [tool],
    }


def iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def parse_events(events_text):
    """从 --json-events 的 JSONL 中提取观察到的 tools[].model 与外层 model。"""
    observed_models = []
    outer_models = []
    for line in (events_text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        for item in iter_dicts(event):
            response = item.get("response")
            if isinstance(response, dict):
                for tool in response.get("tools") or []:
                    if isinstance(tool, dict) and tool.get("type") == "image_generation" and tool.get("model"):
                        observed_models.append(str(tool["model"]))
                if response.get("model"):
                    outer_models.append(str(response["model"]))
    return observed_models, outer_models


def png_size(path):
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except Exception:
        try:
            data = Path(path).read_bytes()
            if data[:8] == b"\x89PNG\r\n\x1a\n":
                import struct

                return struct.unpack(">II", data[16:24])
        except Exception:
            pass
    return None


def run_variant(cli, variant, tool_model, host_model, out_dir, timeout):
    body = build_body(host_model, tool_model)
    body_path = out_dir / f"body-{variant}.json"
    body_path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    image_path = out_dir / f"probe-{variant}.png"
    args = [
        cli,
        "--json",
        "--json-events",
        "--provider",
        "codex",
        "request",
        "create",
        "--request-operation",
        "responses",
        "--body-file",
        str(body_path),
        "--out-image",
        str(image_path),
        "--expect-image",
    ]
    started = time.time()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        returncode, stdout_text, stderr_text = proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        returncode, stdout_text, stderr_text = -1, "", "probe timeout"
    duration = round(time.time() - started, 1)
    (out_dir / f"result-{variant}.json").write_text(stdout_text, encoding="utf-8")
    (out_dir / f"events-{variant}.jsonl").write_text(stderr_text, encoding="utf-8")
    observed, outer = parse_events(stderr_text) or parse_events(stdout_text)
    size = png_size(image_path) if image_path.is_file() else None
    return {
        "variant": variant,
        "requested_tool_model": tool_model or "(auto/未指定)",
        "outer_host_model": host_model,
        "observed_tool_models": sorted(set(observed)),
        "observed_outer_models": sorted(set(outer)),
        "image_size": list(size) if size else None,
        "returncode": returncode,
        "ok": returncode == 0 and bool(observed) and bool(size),
        "duration_seconds": duration,
        "image_path": str(image_path) if image_path.is_file() else "",
    }


def write_report(results, host_model, host_source, out_dir):
    lines = [
        "# Codex Images 2.5 探测报告（T1.1/T1.2）",
        "",
        f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 外层宿主模型：`{host_model or '(未解析，CLI 默认)'}`（来源：{host_source}）",
        f"- 计费通道：Codex 订阅额度（--provider codex，auth 走 ~/.codex/auth.json）",
        "",
        "| 变体 | 请求 tools[].model | 响应观察 tools[].model | 实际尺寸 | 退出码 | 耗时(s) |",
        "|---|---|---|---|---|---|",
    ]
    for item in results:
        lines.append(
            "| {variant} | {requested} | {observed} | {size} | {code} | {duration} |".format(
                variant=item["variant"],
                requested=item["requested_tool_model"],
                observed=", ".join(item["observed_tool_models"]) or "(未捕获)",
                size="x".join(str(v) for v in item["image_size"]) if item["image_size"] else "(无图)",
                code=item["returncode"],
                duration=item["duration_seconds"],
            )
        )
    lines += [
        "",
        "## 判定",
        "",
        "- 若 flare/sunburst 行的观察值为 `gpt-image-2-codex`：请求被接受但服务端未确认 2.5（维持「实验性」文案）。",
        "- 若观察值与请求一致：2.5 生效，可升级 UI 标注并更新 PRD。",
        "- 原始事件/请求体见本目录 `body-*.json`、`events-*.jsonl`、`result-*.json`。",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Codex Images 2.5 探测（默认 dry-run 不花额度）")
    parser.add_argument("--run", action="store_true", help="真实调用 CLI（消耗 Codex 订阅额度，须先获授权）")
    parser.add_argument("--only", choices=sorted(VARIANTS), help="只跑指定变体")
    parser.add_argument("--timeout", type=int, default=600, help="单次请求超时秒数（默认 600）")
    args = parser.parse_args()

    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in glob.glob(str(out_dir / "probe-*.png")) + glob.glob(str(out_dir / "*.json")) + glob.glob(str(out_dir / "*.jsonl")):
        # 保留历史 report.md，其余清掉避免混淆
        if not stale.endswith("summary.json"):
            try:
                os.remove(stale)
            except OSError:
                pass

    cli = find_skill_cli()
    host_model, host_source = resolve_host_model()
    variants = {args.only: VARIANTS[args.only]} if args.only else VARIANTS

    print(f"[probe] CLI: {cli or '(未找到 gpt-image-2-skill)'}")
    print(f"[probe] 外层宿主模型: {host_model or '(CLI 默认)'} (来源: {host_source})")

    if not args.run:
        for name, tool_model in variants.items():
            body = build_body(host_model, tool_model)
            path = out_dir / f"body-{name}.json"
            path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[dry-run] {name}: 请求体已写入 {path}（tools[].model = {tool_model or '未指定'}）")
        print("[dry-run] 未调用 CLI、未消耗额度。确认授权后加 --run 执行真实探测。")
        return 0

    if not cli:
        print("[error] 未找到 gpt-image-2-skill，先安装或设置 GPT_IMAGE_2_SKILL_BIN", file=sys.stderr)
        return 2
    if not host_model:
        print("[warn] 未能解析外层宿主模型，将使用 CLI 默认（可能命中账户不兼容的旧默认值）")

    results = []
    for name, tool_model in variants.items():
        print(f"[run] {name} …", flush=True)
        item = run_variant(cli, name, tool_model, host_model, out_dir, args.timeout)
        results.append(item)
        print(
            "[run] {variant}: rc={code} observed={observed} size={size} {duration}s".format(
                variant=item["variant"],
                code=item["returncode"],
                observed=",".join(item["observed_tool_models"]) or "-",
                size="x".join(str(v) for v in item["image_size"]) if item["image_size"] else "-",
                duration=item["duration_seconds"],
            ),
            flush=True,
        )
    (out_dir / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(results, host_model, host_source, out_dir)
    print(f"[done] 报告：{out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
