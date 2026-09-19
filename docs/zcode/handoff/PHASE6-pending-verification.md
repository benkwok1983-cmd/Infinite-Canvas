# Phase 6 待授权验证清单（消耗额度，由用户执行或授权后由助手执行）

生成时间：2026-09-19。Phase 0-5 已完成，以下为唯一剩余工作。**全部需要消耗额度，未获授权不执行。**

## 1. T1.2：Codex Images 2.5 三变体对照探测（3 次 Codex 订阅生图）

前置：ChatGPT 订阅额度已重置（用户确认）。

```powershell
.\python\python.exe tools\zcode-verify\codex_image25_probe.py --run
```

- 默认跑 auto / flare / sunburst 三组（`--only flare` 可单跑）
- 输出：`tools/zcode-verify/out/report.md` + summary.json + 事件日志
- **判定**：flare/sunburst 行的「响应观察 tools[].model」若为 `gpt-image-2-codex` 别名 → 维持「实验性」文案（当前 UI 设计）；若返回值与请求一致 → 2.5 确认生效，回调助手更新 UI 标注与 PRD
- 顺带验证宿主模型 `gpt-5.6-sol` 是否被账户后端接受（若 400 则把 `CODEX_IMAGE_HOST_MODEL` 环境变量设为可用值，如 gpt-6-astra）

## 2. T6.1-a：Codex 订阅生图 smoke（1 次订阅额度）

启动服务 → 画布 → 生成节点选 GPT CLI 平台 → gpt-image-2（auto 档）生成一次简单提示词。
验收：出图正常；结果元数据含 image_model_requested=auto/latest；不产生 API 账单（API 回退开关保持关闭）。

## 3. T6.1-b：带 Skill 的真实生图 smoke

- **fast 模式（推荐，用 ModelScope 免费模型，零 Codex 额度）**：画布创建生成节点（MS 生成）→ 连接 Skill 节点（选 algorithmic-art 或自建）→ 简单提示词生成 → 验收：出图风格体现 skill 影响；生成日志 run.request 含 skill_used
- **llm 模式（消耗少量 LLM 额度）**：同上但 Skill 节点切「智能」→ 生成 → 验收：编译提示词明显融合改写；同组合第二次生成命中缓存（data/skill_compile_cache.json 出现条目且不再调 LLM）

## 4. AI 识别样板验证（少量订阅聊天额度，非生图）

管理页 → 编辑任意 Skill → 点「AI 识别样板」→ 等待 LLM 分析（走 Codex 聊天通道）→ 识别结果填入样板表格 → 删改后保存 → 画布 Skill 节点下拉出现样板。
前置：额度重置；当前 ModelScope 免费聊天通道对该账户模型报 no provider supported（平台侧，建议顺便检查 MODELSCOPE_CHAT_MODELS 配置）。

## 5. 验收后收尾（助手执行）

- 若 2.5 被确认 → 更新 UI 标注（去「实验」字样）与 PRD
- 更新 docs/zcode/log/PHASE6-progress.md 验收记录、WORKPLAN 全表勾结
- 可选：合并 zcode/iteration-01 → main 或保持分支（用户决定）

## 状态速查

| 项 | 消耗 | 状态 |
|---|---|---|
| T1.2 探测 | Codex 订阅 ×3 | ⏸ 待额度 |
| T6.1-a smoke | Codex 订阅 ×1 | ⏸ 待额度 |
| T6.1-b fast smoke | ModelScope 免费 | ⏸ 待用户点头 |
| T6.1-b llm smoke | LLM 少量 | ⏸ 待用户点头 |
