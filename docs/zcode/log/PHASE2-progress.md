# Phase 2 进度日志（2026-09-19）

## 本期完成（对应任务编号）

- **T2.1 ✅**（提交 d49d5dd）：`image_model` 字段全链路穿线（OnlineImageRequest → build_online_image_result → generate_ai_image → generate_codex_provider_image → via_gpt_image_2_skill）；新增 `generate_codex_image_via_request_create`（request create --body-file 注入 `tools[].model`）；`parse_codex_observed_image_model` 解析服务端观察模型。
- **T2.2 ✅**（同 d49d5dd）：实验性档 body 用 `background=auto`（PRD FR1-4）；**删除 Codex 通道 401 自动回退 API key 的行为**（FR1-6），401 直报并提示重新登录；结果元数据扩展（requested/observed/confirmed/size/host_model）；实验档带参考图时 400 明确提示（Codex 通道不支持 edit）。
- **T2.3 ✅**（提交 b60e8e9）：smart-canvas 与 canvas 的 codex provider 模型下拉自动合并 flare/sunburst 并带「实验」标识；生成 payload 携带 `image_model`；smart-canvas 未确认弹 toast + `node.lastImageModelMeta`；canvas 溯源 `requestMeta` 扩展；i18n zh/en；exp-tag 样式；cache-bust 刷新。zimage 页走 ComfyUI 本地生图，不在范围（已确认）。
- **T2.4 ✅**：单测 19/19（body 构造、created 回显 vs completed 别名、pretty JSON 解析、实验档判定、路由穿线、带参考图拒绝、回归项）。
- **T2.5 部分完成**：
  - T2.5a 独立审查（general-purpose 子代理）：P0×1、P1×3、P2×6。
  - T2.5b 修复（提交 bdc6a34）：**P0-1** result 组装丢弃元数据（诚实反馈链路运行时全断）→ 透传 6 个字段；**P1-1** 观察模型改采信 `response.completed`（created 会回显请求值导致虚报确认）+ pretty JSON 兜底，+2 单测；**P1-2** 探测脚本 body 与生产同形；**P1-3** canvas.js 新增 showLightToast 使旧画布未确认可见；**P2-2** probe stderr/stdout 双路解析；**P2-6** 提示条件放宽。
  - T2.5c 浏览器实测（IAB，本地服务）：smart-canvas 与 canvas 页在 codex provider 下验证通过——三档模型列表、实验标识渲染（renderModelControl 输出含 exp-tag；imageModelOptions 含「（实验）」后缀且 value 干净）、isExperimentalCodexImageModel 判定、payload `image_model` 构造。**交互层说明**：composer 隐藏态 + 项目自定义指针处理（touch-mouse.js）导致 Playwright 合成点击超时，未走通真实下拉点击；以页面内直接调用渲染函数验证输出替代（等价于下拉展开后的 DOM）。
  - T2.5d：本日志 + handoff + 推送。

## 关键发现/决策

1. **审查 P0-1 是关键捕获**：`build_online_image_result` 只取 `raw.usage`，后端辛苦记录的元数据到不了前端。修复后 `result` 顶层携带 6 个元数据字段（`image_model_confirmed=False` 也能透传）。
2. **观察模型判定口径**（P1-1）：`response.created` 回显请求值、`response.completed` 才是服务端路由——与上游验证文档判定标准一致，防止虚报「已确认」。
3. **P2 未修项**（记录在案，随 T1.2 一并处理）：P2-1 `lastImageModelMeta` 只写不读（Phase 5 溯源面板时接线）；P2-3 缺 401-不回退的守护测试与 request-create 成功路径 mock 测试；P2-4 `smart.imageModelObserved` 词条暂未被引用（留给溯源面板）；P2-5 实验档列表三处硬编码（后端 `experimental_image_models` 字段前端尚未消费，防漂移改进项）；P2-6 已修。
4. `isGptImageAutoSizeModel` 会把 2.5 名字识别为 gpt-image-2 系（默认 4k 分辨率）——行为合理，未特判。

## 测试与验证结果

- 单测 19/19 通过（`python\python.exe tests\test_gpt_image_2_skill_args.py`）。
- main.py / 两个 canvas.js / probe 脚本语法检查通过；probe dry-run 正常。
- 浏览器实测数据见 T2.5c；i18n validate 通过（1021 keys）。
- 未消耗任何生图额度（真实生图验证待 T1.2/AC1-5）。

## 遗留问题与风险

- ⏸ T1.2 探测（额度明日重置后）：结果可能回填 UI 标注口径（若 flare/sunburst 被服务端确认则去「实验」字样）。
- 宿主模型 `gpt-5.6-sol` 与 2.5 body 的真实兼容性未验证（T1.2 顺带覆盖）。
- P2 未修项见上。

## 补记（2026-09-19 晚，用户澄清后修订）

- **FR1-6 方向修正**：用户澄清「用订阅额度而非 API」指的是 **2.5 通道只走订阅**，并非删除 API 回退。已改为折中方案（经用户确认选 **UI 界面开关**）：
  - 后端：恢复 auto/latest 档的 Codex→OpenAI 回退循环（原基线行为），新增 `codex_image_skill_attempts(provider, auth_file)` 可测函数；回退条件 = provider 开关 `allow_api_fallback` 开 且 本机有 API Key；`ApiProviderPayload`/`normalize_provider`/`public_provider` 全链路支持该字段。**实验档 request create 路径不经过 attempts，严格只走订阅**。
  - 前端：API 设置页 Codex 卡片新增「API 回退」toggle（默认关，存 provider 配置，随「保存」生效），描述文案明示计费含义与 2.5 不受开关影响；i18n 沿用现有中文界面（该页未强制双语键）。
  - 保留的改善：无回退可用时 401 直报「请重新登录 Codex」（替代基线的 `return None`→误导性「未找到 helper」400）。
  - 单测 +4（开关×key 矩阵 + 非 codex 解析不回退），23/23 全绿。

## 下一步

- Phase 2 收尾推送 → Phase 3（Skill 库后端 T3.1-T3.5）。
