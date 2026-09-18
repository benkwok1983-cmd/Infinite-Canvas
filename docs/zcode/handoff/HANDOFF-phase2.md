# Phase 2 Handoff（2026-09-19）

## 当前状态

- 分支 `zcode/iteration-01`，HEAD = `bdc6a34`（T2.5b 审查修复）。已提交序列：
  - `f572571` T0.1-T0.3 PRD/WORKPLAN/目录
  - `b72f2f4` T1.1 探测脚本 + Phase1 日志
  - `d49d5dd` T2.1/T2.2/T2.4 后端
  - `b60e8e9` T2.3 前端
  - `bdc6a34` T2.5b 审查修复
- 工作区干净（除 `API/.env`（永不提交）、`logs/`、运行数据等未跟踪文件）。
- WORKPLAN 状态：Phase 0/1（T1.2 除外）✅、Phase 2 ✅（T1.2 ⏸ 待额度）。

## 已交付（功能点 → 代码位置）

- **实验性 2.5 档位**：`main.py` 常量 `CODEX_EXPERIMENTAL_IMAGE_MODELS`（~L355）；`codex_experimental_image_model`（~L4962）；`codex_image_request_body`（~L4975）；`parse_codex_observed_image_model`（~L5005，completed 优先 + pretty JSON 兜底）；`codex_image_dimensions`（~L5053）；`generate_codex_image_via_request_create`（~L5510）；主函数 `generate_codex_provider_image_via_gpt_image_2_skill`（~L5595，实验分支 + 删 API 回退）。
- **元数据透传**：`build_online_image_result`（main.py ~L14250，result 组装后 6 字段透传循环）。
- **请求模型**：`OnlineImageRequest.image_model`（~L2801）；`build_online_image_result` 兼容归一化（~L14199）。
- **前端**：smart-canvas.js `providerImageModels`/`isExperimentalCodexImageModel`（~L2502-2518）、`renderModelControl` 实验标识（~L3257）、`runApiGeneration` payload（~L16300）、`resumeSmartPendingNode` 元数据+toast（~L17190）；canvas.js `providerImageModels`（~L722）、`imageModelOptions`（实验）后缀（~L1077）、`runGenerator` payload（~L11320）、`requestMetaFromResult` 扩展（~L13368）、`showLightToast`（~L862）、`completeCanvasImageTask` toast（~L13760）。
- **探测脚本**：`tools/zcode-verify/codex_image25_probe.py`（默认 dry-run；`--run` 花 3 次额度；`--only flare|sunburst|auto`）。输出目录 out/ 已 gitignore。
- **测试**：`tests/test_gpt_image_2_skill_args.py`（19 用例，4 个测试类）。

## 运行与验证方法

```powershell
# 单测（零额度）
.\python\python.exe tests\test_gpt_image_2_skill_args.py
# 探测 dry-run（零额度，只生成请求体）
.\python\python.exe tools\zcode-verify\codex_image25_probe.py
# 探测真实跑（花 3 次 Codex 订阅额度，须用户授权）
.\python\python.exe tools\zcode-verify\codex_image25_probe.py --run
# 启动服务
run.bat   # 或 .\python\python.exe main.py（端口 3000）
```

浏览器验证入口：`http://127.0.0.1:3000/static/smart-canvas.html`（引擎选 API生成/GPT CLI → 点模型 pill 看 flare/sunburst 带实验标）；canvas.html?id=<画布id>&project=default（生成节点模型下拉）。

## 关键上下文

- **Codex 通道原理**：走 gpt-image-2-skill CLI（本机 0.7.3）＋ `~/.codex/auth.json`，不是 codex CLI 生图本身；`--model` 是宿主模型，图片模型由服务端定；本机 config.toml 宿主 = `gpt-5.6-sol`。
- **诚实反馈口径**：服务端可能返回别名 `gpt-image-2-codex`（不确认 2.5）；观察模型只采信 `response.completed` 事件。
- **已删除 API 回退**：Codex 401 直报并提示重新登录（FR1-6，用户明确要求不产生 API 费用）。
- **审查遗留 P2**（随 T1.2 处理）：lastImageModelMeta 溯源面板接线、401-不回退守护测试、experimental_image_models 后端字段前端消费、smart.imageModelObserved 词条使用。
- **浏览器实测限制**：composer 隐藏态 + touch-mouse.js 自定义指针 → Playwright 合成点击超时；用 evaluate 调渲染函数验证输出替代。

## 下一阶段入口

**Phase 3：Skill 库后端（T3.1-T3.5）**，任务定义见 docs/zcode/WORKPLAN.md；设计基准 = PRD「优化 2」。前置条件：无（纯后端，不依赖 T1.2）。
数据落点：`data/skills.json`（索引）+ `skills/custom/`（skill 目录）；API 前缀 `/api/skills`；安全红线：第三方脚本一律不执行、`~/.codex/skills/` 只读。

## 注意事项（勿动清单）

- `C:\Infinite-Canvas` 是用户原始基准，**绝不修改**。
- `API/.env` 含真实 ModelScope key，**永不提交**。
- 任何消耗生图额度的验证须先获用户授权（T1.2 探测、AC1-5 端到端）。
- ModelScope 免费模型可用于非 Codex 通道生图测试（用户指定）。
- main.py / smart-canvas.js / canvas.js 是巨型文件，改动保持小函数独立可测。
