# Codex Images 2.5 探测脚本（T1.1）

用途：验证 ChatGPT Codex 后端是否真正接受/切换 `image_generation` 工具的 2.5 模型
（`gpt-image-2.5-flare` / `gpt-image-2.5-sunburst`）。对应 PRD 优化 1 / WORKPLAN Phase 1。

## 使用

```powershell
# 默认 dry-run：只构造并打印三组请求体，不调用 CLI、不花额度
python tools/zcode-verify/codex_image25_probe.py

# 真实探测（花 3 次 Codex 订阅额度，必须先获用户授权！）
python tools/zcode-verify/codex_image25_probe.py --run
```

结果输出到 `tools/zcode-verify/out/`（summary.json + report.md + 事件原始日志）。

## 判定

- 响应事件 `response.completed` 中 `tools[].model` 若返回 `gpt-image-2-codex`
  别名 → 2.5 请求被接受但**未被服务端确认**（维持"实验性"文案）。
- 若返回值与请求一致 → 2.5 生效，可升级 UI 标注。

依据：gpt-image-2-skill 上游 `skills/gpt-image-2-skill/references/codex-local-verification.md`
（2026-09-09 实测：别名问题、background=transparent 400、size 参数被无视等结论）。
