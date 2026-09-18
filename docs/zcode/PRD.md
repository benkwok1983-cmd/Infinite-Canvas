# PRD：Codex 订阅额度接入 Images 2.5 ＋ 画布生图 Skill 节点

- 版本：v1.0（2026-09-19）
- 分支：`zcode/iteration-01`（基线提交 `03f8bdd`）
- 状态：已与用户确认需求方向；依据 = 用户需求 ＋ codex 方案对照 ＋ 本地代码调查（含 gpt-image-2-skill 上游实测记录）
- 配套文档：[WORKPLAN.md](./WORKPLAN.md)（工作计划表，执行对照用）

---

## 优化 1：Codex 订阅额度接入 GPT Image 2.5（实验性）

### 目标

用户希望在画布上像现在使用 gpt-image-2 一样，**通过 Codex 订阅额度**（`~/.codex/auth.json` 的 ChatGPT 登录凭据 → ChatGPT 后端 `backend-api/codex/responses`）使用 GPT Image 2.5（`gpt-image-2.5-flare` / `gpt-image-2.5-sunburst`）生图。

**用户明确：只走订阅额度，不接 API key 计费路径。**

### 背景与约束（已调查确认）

| 事实 | 依据 |
|---|---|
| 画布 Codex 生图走 `gpt-image-2-skill` CLI（本机 0.7.3，npm 安装），不是 codex CLI 本身 | main.py:5501 `generate_codex_provider_image` → main.py:5329 |
| Codex 路径下 CLI 的 `--model` 指外层宿主模型（gpt-5.x/gpt-6-astra），不是图片模型；图片模型由服务端定 | CLI help ＋ 上游源码 `build_codex_image_body` |
| ChatGPT 后端 `image_generation` 工具**接受** `tools[].model`（可填 2.5 型号，不报错），但所有成功响应返回别名 `gpt-image-2-codex`，**无法证实 2.5 生效** | 上游仓库 skills/gpt-image-2-skill/references/codex-local-verification.md（2026-09-09，20 次对照实验） |
| 传参陷阱：size 参数经常被无视（请求 1024 返回 1254×1254），**尺寸写进提示词才真正影响输出**；`background=transparent` 显式传必 400，须 `auto`＋透明提示词；输出格式参数有效；质量档提示词无效 | 同上 |
| 宿主模型账户兼容：`gpt-5.4` 被 ChatGPT 账户后端拒绝，`gpt-6-astra` 可用；本机 config.toml 为 `gpt-5.6-sol`（待验证） | 同上 ＋ 本机配置 |
| 现有代码已把硬编码 `gpt-5.4` 换成 `codex_image_host_model()` 解析链（env → config.toml → UI 值 → 默认） | main.py:4946（基线提交 03f8bdd 的成果） |
| CLI 的 `request create --body-file` 子命令可传任意请求体 → 这是注入 `tools[0].model` 的现成通道 | CLI help ＋ 上游验证文档 |
| 现有代码存在 API 回退：Codex 通道 401 且能发现 API key 时会自动换 openai provider 重试 | main.py:5338-5340 —— 本期必须收紧 |

### 功能需求

| 编号 | 需求 |
|---|---|
| FR1-1 | Codex provider 图像模型列表提供三档：**auto/latest**（默认，行为=现状 gpt-image-2，保持兼容）、**gpt-image-2.5-flare（实验性）**、**gpt-image-2.5-sunburst（实验性）**。UI 上实验性条目需有标识 |
| FR1-2 | 选择实验性档位时，改走 `request create --body-file` 路径：构造含 `tools[0].model = 所选2.5型号` 的请求体；auto 档维持现有 `images generate` 路径不变 |
| FR1-3 | 外层宿主模型始终由 `codex_image_host_model()` 解析，`gpt-image-*` 值不得作为宿主模型传出 |
| FR1-4 | 传参按实测最佳实践：期望尺寸/比例写入提示词（检查并强化现有 `gpt_image_2_skill_prompt_arg`）；`background=auto`；输出格式走参数；`codex_postprocess_image_to_requested_size` 保留尺寸校验，**如实报告原始尺寸，不虚标** |
| FR1-5 | 诚实反馈：任务结果元数据记录并显示「请求的图片模型 / 服务端观察模型（响应事件 `tools[].model`）/ 实际尺寸」；观察为 `gpt-image-2-codex` 别名时明示「服务端未确认 2.5」 |
| FR1-6 | **计费保护**：Codex 通道失败（含 401）一律直报错误并提示重新登录，**禁止自动回退 API key 通道**（收紧 main.py:5338-5340 的回退；不留隐藏开关则直接删除该回退） |
| FR1-7 | 验证：单测覆盖 body 构造 / 模型路由 / 回退禁用 / 尺寸映射，零额度消耗；端到端真实生图验收需用户单独授权额度 |
| FR1-8 | UI 文案：Codex 生图相关文案由「GPT Image 2」更新为「ChatGPT Images / Codex 图像生成」，涉及 i18n 词条同步（zh/en） |

### 非目标

- 不做 OpenAI API key 生图的新功能（现有 API 能力维持原样，不投入）
- 不承诺 2.5 必定生效（服务端别名问题）；产品话术为「实验性请求」
- 不修改 gpt-image-2-skill 本体（不 fork 不打补丁；升级到 0.7.4 为可选项非依赖）

### 验收标准

- AC1-1 选择 flare/sunburst 时，发往后端的请求体 `tools[0].model` 为所选值（`--json-events` 日志可验证）
- AC1-2 选择 auto 时行为与现状完全一致（回归零影响）
- AC1-3 结果元数据含请求/观察模型；别名时明示未确认
- AC1-4 无 API 回退：401 场景直接报错，不产生 API 账单
- AC1-5 单测全绿；一次用户授权的真实生图出图，尺寸如实报告

---

## 优化 2：画布「生图 Skill 节点」

### 目标

用户可将 **GitHub 开源 skill 或自建 skill 导入画布的 Skill 库**；在画布上添加**「生图 Skill」节点**，节点内**下拉选择 skill**；与现有「参考图 + 提示词」组合，**连线接入 API 生图节点 / ModelScope 生图节点**等生图，产出指定风格图像。

### 背景与约束（已调查确认）

| 事实 | 依据 |
|---|---|
| 后端已有提示词库基础设施（`/api/prompt-libraries*` CRUD，data/prompt_libraries.json，条目=正向/负向/参数三段式） | main.py:239/8097 |
| 画布参考图以节点连线流入生图节点（`visibleReferenceImagesFor`）；生图总入口 `run_canvas_image_task` 为全 provider 共享 → **Skill 注入做一处即全覆盖**（含 ModelScope/API/Codex/即梦/RunningHub） | main.py:14548，smart-canvas.js 参考图管线 |
| 前端已有提示词模板 UI 模式可复用（模板面板、插入逻辑） | smart-canvas.js:4494/4833，canvas.js:7768 |
| SKILL.md 是 agent 指令文档（frontmatter name/description ＋ 正文条件指令），**非可执行程序**；「接入」= 生成前把指令注入提示词管线 | Agent Skills 规范 |
| skill 目录现状：仓库 `skills/`、工作区 `.agents/skills/`、`~/.codex/skills/`（agent-reach、opencli）三处 | 本机调查 |

### 功能需求

| 编号 | 需求 |
|---|---|
| FR2-1 | **Skill 库（后端）**：`/api/skills` 系列接口——扫描（`skills/custom/`、仓库 `skills/`、`~/.codex/skills/` 只读）＋ CRUD；条目元数据含 name/description/version/source（本地/GitHub/自建）/commit SHA/能力声明/预览图引用 |
| FR2-2 | **导入-GitHub**：粘贴仓库 URL → 拉取并解析 → 校验结构与许可证 → 展示能力声明（读提示词规则/参考素材/脚本/网络）→ 用户确认 → **固定 commit SHA** 安装到 `skills/custom/<name>/`；升级必须展示差异并重新确认 |
| FR2-3 | **导入-zip／自建**：zip 上传解包导入（同安全校验）；管理页内新建/编辑 SKILL.md（＋可选 style 配置） |
| FR2-4 | **安全**：V1 只支持声明式内容（SKILL.md / references / assets / JSON-YAML 配置）；**第三方 scripts 一律不执行**；导入限大小限类型；`~/.codex/skills/` 只读引用 |
| FR2-5 | **生图 Skill 节点**：smart-canvas 新节点类型；节点上 skill 下拉（按来源分组）；显示名称/版本/来源徽标；可选参数区（读取 skill 声明的可调参数） |
| FR2-6 | **连线语义**：skill 节点作为输入连线接到生图节点（API 生图 / ModelScope 生图等）；V1 限制每个生图节点**至多接一个** skill 节点（避免组合爆炸，后续可放开）；连线后生图请求自动携带 skill 标识 |
| FR2-7 | **编译双模式**：**快速**＝确定性拼接（skill 指令＋用户提示词，零成本零延迟）；**智能**＝LLM 融合改写（用户提示词＋SKILL.md → 已配 LLM 通道或 Codex 额度，按 skill+提示词哈希缓存避免重复消耗）。模式在 skill 节点或全局设置选择 |
| FR2-8 | **提示词预览**：生成前可展开查看编译后最终提示词（两种模式都要能预览） |
| FR2-9 | **溯源**：结果节点/生成记录保存：原始提示词 / skill id＋版本＋SHA / 编译后最终提示词 / 请求模型 / 观察模型 / 尺寸；skill 更新或删除后旧记录仍完整可解释 |
| FR2-10 | **回归**：不连 skill 节点时，现有生图流程**完全不变**（请求逐字段一致） |

### 非目标（V1 不做，留待后续迭代）

- 第三方脚本执行（含沙箱化方案）
- 工作流 skill（多步生成流程：线稿→材质→放大）
- 从满意结果反向创建 skill
- skill 市场 / 在线分享

### 验收标准

- AC2-1 同一提示词选不同 skill → 发出的请求 prompt 有可检差异（快速模式）
- AC2-2 不连 skill 节点 → 请求与现状逐字段一致（回归）
- AC2-3 GitHub 导入固定 SHA；升级有 diff 确认
- AC2-4 畸形/恶意 skill 被结构校验拒绝；后端不执行任何第三方脚本
- AC2-5 结果可溯源（skill 版本＋最终提示词＋模型记录）
- AC2-6 ModelScope 生图节点与 API 生图节点都能接 skill 节点并生效
- AC2-7 智能模式的 LLM 调用有缓存，同组合不重复消耗

---

## 共用设计约定

1. **模型字段拆分**：`host_model`（宿主模型）与 `image_model`（图片模型策略）分离，优化 1/2 共用；溯源记录结构统一设计，优化 2 的「观察模型」显示直接复用优化 1 成果。
2. **Skill 与 Provider 解耦**：Skill 决定「怎么描述图像」，Provider 决定「用哪个模型/哪个额度」；skill 不得改变计费通道。
3. **隔离纪律**：一切修改仅发生在工作区 `C:\agent-workspace\zcode\Infinite-Canvas`（分支 `zcode/iteration-01`）；`C:\Infinite-Canvas` 为用户原始基准，**绝不修改**。`API/.env` 含真实密钥，永不提交。
4. **额度纪律**：任何消耗生图额度/LLM 额度的验证（优化 1 阶段验证、端到端 smoke）必须先获用户明确授权。
5. **进度纪律**：每阶段收尾写进度日志＋handoff 文件（见 WORKPLAN 附则），提交 git 后才进入下一阶段；单阶段内可多次更新。
