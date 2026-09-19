# Phase 5 Handoff（2026-09-19）

## 当前状态

- 分支 `zcode/iteration-01`。Phase 0-5 全部完成（T1.2 ⏸ 等额度）。仅剩 Phase 6 收尾。
- 用户画布已恢复原状（测试节点全部清理）。

## 已交付（功能点 → 代码位置）

**后端（main.py 尾部「画布生图 Skill 编译注入」section）**
- `SkillSelection` 模型（模型区，OnlineImageRequest 前）；`OnlineImageRequest.skill`
- `compile_skill_prompt`：fast 拼接（body 截 8000）/ llm 改写（组合消息按 LLM_MESSAGE_MAX_LENGTH 校验超限 400）；缓存 key=`snapshot|mode|provider|model|prompt` SHA256；asyncio.Lock 按 key 串行化；LRU 200 落盘 data/skill_compile_cache.json
- `skill_content_snapshot`：SKILL.md 内容哈希（commit_sha 只作溯源展示）
- `build_online_image_result`：编译注入（upscale 跳过）+ result 溯源 skill_used/compiled_prompt
- `/api/skills/preview-prompt`（fast 零成本）、`/api/skills/compile-prompt`（llm 真实编译）

**前端（canvas.js）**
- `addSkillNode`（~L2588）、createNodeByType/menuAdd 的 skill 分支（~L3656/3674）
- `canConnect` skill 规则（~L15479：skill→CANVAS_GENERATOR_TYPES 单向、to=skill 拒绝、目标至多一个 skill 输入）
- canOutput 数组含 'skill'（~L6389）；renderNode title/body 分支；`renderSkillBody`（下拉+模式切换+提示）
- `generatorSources` skill 分支（贡献 skill 不贡献 refs/prompt）；`connectedSkillSource`；`renderSkillLine` + renderGeneratorBody 的 skill 行与预览按钮
- `runGenerator` payload.skill（后端注入路径）；`runMsGenNode` 前端预编译（msgen 专用端点）+ skillUsed 溯源
- `requestMetaFromResult` 条件写 skill_used/compiled_prompt；init 时 `loadSkillLibrary()`（完成后重渲染回显）
- `showPromptPreviewModal`/`previewCompiledPrompt`（llm confirm 额度提示 + 缓存标识）

**测试**：tests/test_skill_injection.py（6 项）。全量 47 项单测绿。

## 运行与验证方法

```powershell
.\python\python.exe main.py
```
画布（canvas.html?id=xxx）→ 从 generator/msgen 输入端口菜单创建「生图 Skill」→ 节点下拉选 skill（如 algorithmic-art）→ 快速/智能切换 → 连线（skill 出端口 → generator）→ generator 显示 Skill 行 → 预览提示词 → 生成。
注意：**验证必须走 createNodeByType/canConnect 等真实闸门，不能直接 push connections**（会绕过白名单造成假绿）。

## 关键上下文

- **至多一个 skill** 在 canConnect 强制；第二个 skill 连线静默拒绝（与项目现有连线拒绝交互一致）。
- **msgen 与 generator 编译路径不同**：generator 后端注入（溯源在 result）；msgen 前端预编译（溯源在 run.request.skill_used）。llm 模式都走 /api/skills/compile-prompt（缓存共享）。
- 缓存文件 data/skill_compile_cache.json 不入库（运行数据）。
- **smart-canvas 未接入**（PRD 已修订范围）；如后续要接，入口是 smart-canvas.js runApiGeneration（16266）+ composer/邻近节点收集 skill，复用同一后端。

## 下一阶段入口

**Phase 6（收尾）**：
- T6.1 端到端验收【需用户授权额度】：① Codex 订阅生图 smoke（验证实验性 2.5/诚实反馈）；② 带 skill 的真实生图 smoke（fast 模式用 ModelScope 免费模型可零 Codex 额度；llm 模式消耗 LLM 额度）
- T6.2 README 增补两功能使用说明 + 全量单测 + 分支整理推送
- T1.2【需用户确认额度重置】：`.\python\python.exe tools\zcode-verify\codex_image25_probe.py --run`

## 注意事项（勿动清单）

- `C:\Infinite-Canvas` 绝不修改；`API/.env` 永不提交。
- 前端改动后刷新 cache-bust（canvas.html 引用 + i18n.js VERSION）。
- 用户画布 data/canvases/*.json 是真实数据，测试时创建的节点必须清理。
