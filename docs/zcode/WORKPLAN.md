# 工作计划：Codex Images 2.5 ＋ 画布 Skill 节点

- 版本：v1.0（2026-09-19）
- 依据：[PRD.md](./PRD.md)
- 用法：每完成一项把状态改为 ✅ 并填完成日期；状态列含义——`待办` `进行中` `✅完成` `⏸阻塞` `❌取消`。**执行期间以本表为对照基准，不偏离、不私加范围**（范围变更须先改 PRD 再改本表）。
- 分支纪律：全部工作在 `zcode/iteration-01`；每个任务（或紧密关联任务组）独立提交，提交信息引用任务编号（如 `T2.1`）。

---

## Phase 0：规划（本阶段）

| 任务 | 内容 | 状态 |
|---|---|---|
| T0.1 | PRD.md 编写并经用户确认 | ✅ 2026-09-19 |
| T0.2 | WORKPLAN.md 编写并经用户确认 | ✅ 2026-09-19 |
| T0.3 | 日志/handoff 目录与模板建立（`log/`、`handoff/`） | ✅ 2026-09-19 |

## Phase 1：优化 1 —— 只读验证（不动产品代码）

| 任务 | 内容 | 状态 |
|---|---|---|
| T1.1 | 编写独立验证脚本（`tools/zcode-verify/`，不进产品链路）：用 `gpt-image-2-skill request create --body-file` 构造三组 body（auto / flare / sunburst），外层宿主模型取本机解析值；开启 `--json-events` 捕获事件 | ✅ 2026-09-19 |
| T1.2 | **【需用户授权额度】**跑 3 次真实生图，记录：宿主模型、请求的 tools[].model、响应事件中的观察模型、实际图片尺寸、耗时 | ⏸ 阻塞：用户 ChatGPT 订阅额度已耗尽，预计 2026-09-20 重置；用户确认后执行 |
| T1.3 | 输出验证报告 `log/PHASE1-verification.md`；按结果确认实现细节（若三次均返回 `gpt-image-2-codex` 别名 → 维持「实验性」文案与诚实反馈设计；若 flare/sunburst 之一被确认 → 调整 UI 标注） | 待办（依赖 T1.2） |

> T1.2 未授权不阻塞 Phase 2 编码（单测先行），仅阻塞最终验收 AC1-5。
> **额度替代约定（用户 2026-09-19 指示）**：非 Codex 通道的生图测试一律用 ModelScope 免费模型；Codex 通道额度验证统一等用户确认重置后再做。

## Phase 2：优化 1 —— 实现

| 任务 | 内容 | 状态 |
|---|---|---|
| T2.1 | main.py：请求模型加 `image_model` 字段（`OnlineImageRequest` 及内部传递）；`generate_codex_provider_image_via_gpt_image_2_skill`（main.py:5329）增加实验性分支：独立可测的 body 构造函数 ＋ `request create` 执行路径 ＋ 事件解析（观察模型提取） | 待办 |
| T2.2 | main.py：传参最佳实践（检查强化 `gpt_image_2_skill_prompt_arg` 的提示词内嵌尺寸；`background=auto`）；**删除 API 回退**（main.py:5338-5340，401 直报「请重新登录 Codex」）；结果元数据扩展（requested/observed model、尺寸） | 待办 |
| T2.3 | 模型列表与 UI：默认模型常量（main.py:354）与 provider 配置层提供三档（auto=现有 gpt-image-2 条目兼容保留）；zimage/canvas/smart-canvas 下拉与「实验性」标识；i18n 词条（zh/en）同步；FR1-8 文案更新 | 待办 |
| T2.4 | 单测：body 构造（tools[0].model 注入/尺寸映射/背景值）、模型路由（image_model 不漏成宿主模型）、回退禁用（401 路径）、auto 回归；扩展 `tests/test_gpt_image_2_skill_args.py` | 待办 |
| T2.5 | **代码审查**（见审查规程）＋ 浏览器实测（browser-use：三档切换、错误提示、结果元数据展示截图） | 待办 |
| T2.6 | 进度日志 ＋ handoff ＋ 提交推送 | 待办 |

## Phase 3：优化 2 —— Skill 库后端

| 任务 | 内容 | 状态 |
|---|---|---|
| T3.1 | 数据模型与存储：`skills/custom/<id>/` 目录规范 + `.skill_meta.json`（随目录走）；SKILL.md frontmatter 解析（yaml+防炸弹+回退） | ✅ 2026-09-19 |
| T3.2 | `/api/skills` 扫描/列表/详情/删除（custom/builtin/codex 三来源）；路径穿越防护；`~/.codex/skills/` 只读 | ✅ 2026-09-19 |
| T3.3 | GitHub 导入（preview 确认→固定 SHA 安装→409/overwrite）＋ monorepo subdir ＋ zip 导入；check-update（轻量 commits API）/upgrade（点前缀备份回滚）；真实仓库全链路验证 | ✅ 2026-09-19 |
| T3.4 | 自建 skill 创建/更新/删除 API（frontmatter 服务端生成防注入；style 字段随 SKILL.md 编辑） | ✅ 2026-09-19 |
| T3.5 | 单测 23 项全绿；子代理审查（P1×1/P2×7/P3×9 → P1/P2 全修复）；真实仓库冒烟；日志/handoff/推送 | ✅ 2026-09-19 |

## Phase 4：优化 2 —— Skill 管理页（前端）

| 任务 | 内容 | 状态 |
|---|---|---|
| T4.1 | 新增 `static/skill-manager.html`（复用现有 iframe 页面架构/主题/i18n 模式）：列表（按来源分组）、详情、删除 | 待办 |
| T4.2 | 导入流程 UI：GitHub URL 粘贴 → 元数据/能力/许可证确认 → 安装；升级 diff 视图；zip 上传 | 待办 |
| T4.3 | 自建 skill 编辑器（SKILL.md 文本编辑＋style 配置表单） | 待办 |
| T4.4 | 审查 ＋ 浏览器实测（导入真实 GitHub skill 全流程截图）＋ 日志/handoff ＋ 提交推送 | 待办 |

## Phase 5：优化 2 —— 画布节点接入

| 任务 | 内容 | 状态 |
|---|---|---|
| T5.1 | smart-canvas 新节点类型「生图 Skill」：渲染、skill 下拉（分组）、版本/来源显示、参数区、连线规则（至多 1 个/生成节点）；画布数据结构向后兼容（旧画布文件不受影响） | 待办 |
| T5.2 | 生成链路注入：前端 `runApiGeneration`（smart-canvas.js:16266）payload 带 skill 字段 → 后端 `run_canvas_image_task`（main.py:14548）统一编译注入（覆盖 API/ModelScope 等 provider）；快速/智能双模式 ＋ 智能模式缓存 | 待办 |
| T5.3 | 提示词预览 UI ＋ 结果溯源展示（结果节点信息面板显示 skill 版本/最终提示词/模型） | 待办 |
| T5.4 | 回归：不连 skill 节点请求逐字段一致；AC2-1～AC2-7 全过（智能模式 LLM 消耗部分若需真实调用，先获授权） | 待办 |
| T5.5 | 审查 ＋ 浏览器实测 ＋ 日志/handoff ＋ 提交推送 | 待办 |

## Phase 6：收尾

| 任务 | 内容 | 状态 |
|---|---|---|
| T6.1 | 端到端验收（**需用户授权额度**：一次 Codex 订阅生图 smoke ＋ 一次带 skill 生图 smoke） | 待办 |
| T6.2 | 文档更新（README 增补两功能使用说明）＋ 全量单测 ＋ 分支整理推送 fork | 待办 |

---

## 代码审查规程（每 Phase 的 T*.5/收尾任务执行）

1. **自查清单**：diff 仅含计划内变更；无调试残留（console.log/print）；无硬编码路径/密钥；错误提示可操作（告知用户怎么修）。
2. **独立审查**：用 general-purpose 子代理以「新视角」复审 diff（提示词中给 PRD 条目与审查重点，要求按条核对并输出问题清单，P0/P1/P2 分级）。P0/P1 必须修复后才能收尾。
3. **回归红线**：现有单测全绿；`run.bat` 启动无新报错；不选新功能时请求负载与基线一致（Phase 2/5 各做一次负载比对）。
4. **浏览器实测**：UI 变更用 browser-use 实操并截图留档到 `log/`（作为阶段日志附件）。
5. **巨型文件纪律**：main.py（1.9 万行）/smart-canvas.js（1.9 万行）的修改保持小函数、独立可测；新增逻辑优先独立函数/模块，便于单测与回退。

## 子代理使用约定

- 实现主体由主会话完成（保持上下文连续与用户对齐）。
- 委托子代理：① 独立代码审查（每 Phase）；② 机械性大范围检查（如 i18n key 一致性扫描）；③ 独立信息收集类任务。
- 子代理产出必须回主会话核对后才采纳。

## 附则：日志与 handoff 规范

**目录**：`docs/zcode/log/`（进度日志＋验证报告）与 `docs/zcode/handoff/`（阶段交接文件）。

**进度日志模板**（`log/PHASE{n}-progress[-{seq}].md`）：

```markdown
# Phase {n} 进度日志（{日期}）
## 本期完成（对应任务编号）
## 关键发现/决策（含理由）
## 测试与验证结果（单测/浏览器/截图清单）
## 遗留问题与风险
## 下一步
```

**Handoff 模板**（`handoff/HANDOFF-phase{n}.md`）——目标：任何新会话/新代理只读此文件＋PRD＋WORKPLAN 即可无缝接手：

```markdown
# Phase {n} Handoff（{日期}）
## 当前状态：分支/提交/工作区（含未提交内容说明）
## 已交付：功能点 → 代码位置（file:line）/测试/文档
## 运行与验证方法：启动、单测命令、浏览器验证步骤
## 关键上下文：本阶段的重要决策、踩坑、外部依赖状态
## 下一阶段入口：WORKPLAN 中下一项任务及前置条件
## 注意事项：勿动清单（C:\Infinite-Canvas、API/.env）、额度授权要求等
```

**收尾门槛**：日志＋handoff 写完、审查问题清零、提交推送完成 —— 三者齐备才允许进入下一 Phase。
