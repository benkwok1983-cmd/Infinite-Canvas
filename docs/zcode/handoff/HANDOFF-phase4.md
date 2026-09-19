# Phase 4 Handoff（2026-09-19）

## 当前状态

- 分支 `zcode/iteration-01`。Phase 4（Skill 管理页前端）完成并提交；Phase 0-4 全部完成（T1.2 ⏸ 等额度）。
- 测试残留：`skills/custom/algorithmic-art`（真实导入，供用户体验与 Phase 5 测试）。

## 已交付（功能点 → 代码位置）

- **页面三件套**：`static/skill-manager.html`（骨架+四个弹层：详情/编辑/GitHub 向导/检查更新）、`static/css/skill-manager.css`（**含亮色 ：root 变量块与 body 基础样式——新页面必须抄这块，否则黑屏**）、`static/js/skill-manager.js`（状态/渲染/弹层/导入向导/上传/更新）。
- **主框架接入**：`static/index.html`——nav 项（素材库之后，star 图标）、`frame-skill-manager` iframe、PAGE_IDS 含 'skill-manager'。
- **i18n**：`static/js/i18n/common.js` 加 `nav.skillManager`；页面主体硬编码中文（跟随 asset-manager 现状）。
- **后端对接**：`/api/skills`（列表）、`/api/skills/{source}/{id}`（详情）、`POST/PUT/DELETE /api/skills/custom*`（CRUD）、`/api/skills/github/preview|install`（确认制导入，409→overwrite）、`/api/skills/zip/install`（Form 字段 overwrite）、`/api/skills/custom/{id}/check-update|upgrade`。
- **cache-bust**：skill-manager 三件套与 i18n.js VERSION 均刷到最新时间戳。

## 运行与验证方法

```powershell
.\python\python.exe main.py   # 端口 3000
```
浏览器打开 `http://127.0.0.1:3000/` → 左侧导航「Skill 库」；或直接 `/static/skill-manager.html`。
实测流程：GitHub 导入（anthropics/skills + subdir=skills/algorithmic-art）→ 预览确认 → 安装 → 详情 → 检查更新。

## 关键上下文（给 Phase 5）

- **skill 数据消费**：画布节点选 skill 用 `GET /api/skills` 过滤 `source==='custom'||'builtin'` 且 `has_skill_md`；编译要用正文时按需 `GET /api/skills/{source}/{id}` 取 `body`（frontmatter 后正文）与 `metadata`（style 等字段）。
- **溯源字段约定**（Phase 5 结果节点保存）：skill id + install.commit_sha + 编译后最终提示词 + 请求/观察模型（优化 1 元数据字段已就绪：image_model_requested/observed/confirmed/image_size）。
- **编辑器限制**：编辑模式只改 body，frontmatter 服务端管理——Phase 5 若要读 style 配置字段，从详情接口 metadata 拿。
- browser-use 注意：子页面为 iframe 内容时 Playwright 合成点击可能超时（自定义指针处理），优先 evaluate 直调函数验证逻辑。

## 下一阶段入口

**Phase 5：画布「生图 Skill 节点」（T5.1-T5.5）**，任务见 WORKPLAN；设计基准 PRD FR2-5~FR2-10。入口文件：static/js/smart-canvas.js（新节点类型 + runApiGeneration payload + 编译注入请求字段）与 main.py `run_canvas_image_task`（后端统一编译注入点）。双编译模式（快速拼接 / LLM 改写）+ 智能模式缓存 + 溯源记录。

## 注意事项（勿动清单）

- `C:\Infinite-Canvas` 绝不修改；`API/.env` 永不提交。
- 消耗生图/LLM 额度的验证须先获用户授权（T1.2 待额度重置）。
- 前端任何改动后刷新 cache-bust（html 引用 + i18n.js VERSION）。
