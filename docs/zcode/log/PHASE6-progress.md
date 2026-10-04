# Phase 6 进度日志（2026-09-19）

## 本期完成（对应任务编号）

- **T6.2 ✅**（不消耗额度的全部收尾）：
  - README 增补「本 fork 新增功能」：Codex 订阅生图实验性 2.5（含诚实反馈/API 回退开关说明）+ Skill 库与画布 Skill 节点使用说明 + 开发说明（测试/探测脚本）
  - 全量单测 47 项全绿（injection 6 + library 23 + codex 18）；main.py 语法 + 前端 JS 语法检查通过
  - **发现并确认项目自带的版本戳自动同步机制**（main.py `sync_static_html_versions`：启动时把所有 HTML 静态引用重写为 `VERSION.mtime`）——此前手工 cache-bust 无害但非必需；服务运行产生的 HTML 版本戳变更已随本次提交入库
  - `docs/zcode/handoff/PHASE6-pending-verification.md`：待授权验证清单（T1.2 / T6.1 的具体命令、判定标准、消耗明细）
- **T6.1 ⏸ / T1.2 ⏸**：消耗额度的端到端验收与 Codex 2.5 探测，等用户确认额度重置后执行（见待授权清单）。

## 遗留问题与风险

- 实验性 2.5 的 UI 标注口径取决于 T1.2 探测结果（别名 → 维持现状；确认 → 去「实验」字样）。
- llm 智能模式的真实改写质量未验证（消耗 LLM 额度，用户执行）。

## 全程总结（Phase 0-6）

- 提交 20+ 个，全部推送 fork `zcode/iteration-01`；全量 47 项单测；3 轮子代理审查（Phase 2/3/5，共修复 P0×3、P1×7、P2×15+）。
- 交付：PRD/WORKPLAN/日志/handoff 全套迭代文档；Codex 订阅实验性 2.5（request create 注入 + 诚实反馈 + UI 开关 API 回退）；Skill 库后端 + 管理页 + 画布 Skill 节点（双模式编译注入 + 缓存 + 溯源）。

## 补记（2026-09-19 晚）：T6.1-b fast 模式端到端验收 ✅ 初步通过

用户授权下在真实画布（文生图与参考图测试）完成全链路验收：

- **链路**：Skill 节点（mono-color·快速）+ 现有提示词节点 + 现有参考图 → 新建 ModelScope 生成节点（Klein 图生图）→ 真实生成
- **fetch 拦截铁证**：compile-prompt 收到 88 字符原始提示词 → /api/ms/generate 发出 3825 字符编译提示词
- **出图验证**：输出图完整呈现 mono-color 风格（暖纸底、单墨半调网点、杂志编辑排版、主动负空间），参考图的写实照片被风格重铸
- **溯源**：生成日志含 request.skill_used = {id: mono-color, mode: fast, sha: content:8274bc1f}，prompt 即编译后最终提示词
- **过程中发现并修复 2 个真实问题**：
  1. 右键创建菜单（canvas.html 硬编码）缺 Skill 项（用户实测发现）→ 已补
  2. fast 拼接 8049 字符超 ModelScope 上游 prompt≤4000 限制被拒 → SKILL_FAST_PROMPT_MAX=3800 总长控制，截断修复后重生成成功
- 另修复：子页面 HTML 走 StaticFiles 被浏览器启发式缓存 → /static/{page} 路由 no-cache（需注册在 mount 前）
- 节点与生成结果保留在用户画布；algorithmic-art 与 mono-color 两个 skill 留在库中
- T1.2 探测与 llm 模式/ Codex 订阅 smoke 仍待用户额度（PHASE6-pending-verification.md）
