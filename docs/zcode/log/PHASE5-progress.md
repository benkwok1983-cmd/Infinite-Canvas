# Phase 5 进度日志（2026-09-19）

## 本期完成（对应任务编号）

- **T5.1 ✅（范围修订）**：普通画布 canvas.js 新节点 `type:'skill'`（用户所指"API/ModelScope 生图节点"即普通画布 generator/msgen；smart-canvas 是 composer 流没有生成节点，PRD 已同步修订）。工厂/尺寸/title/body 渲染/skill 下拉（我的+内置分组）/快速-智能模式切换；连线闸门全链打通（canConnect 规则、canOutput 端口、createNodeByType/menuAdd 入口、sanitizeConnections 复用）；至多一个 skill 输入强制。
- **T5.2 ✅**：generator 走 payload.skill → build_online_image_result 统一编译注入（全 provider 覆盖）；msgen 专用端点走前端 compile-prompt 预编译；快速=确定性拼接、智能=canvas-llm 改写；缓存（key 含 skill 内容快照+mode+provider+model+prompt 哈希，LRU 200）+ asyncio.Lock 按 key 串行化。
- **T5.3 ✅**：generator 节点"已连 Skill 行"+ 预览按钮（fast 即时弹层；llm confirm 额度提示后真实编译，缓存命中显示标识）；requestMeta 条件写 skill_used/compiled_prompt 溯源。
- **T5.4 ✅**：tests/test_skill_injection.py 6 项（fast 拼接/不同 skill 差异=AC2-1/无 skill 回归=AC2-2/llm 缓存=AC2-7/编辑失效缓存/注入溯源）；真实闸门 E2E（创建/单向连线/至多一个/端口/Skill 行/清理）全过。
- **T5.5 ✅**：子代理审查 P0×2/P1×3/P2×6/P3×4 → **全部修复**；浏览器实测（真实闸门路径，教训见下）。

## 关键发现/决策

1. **审查两大 P0（血泪教训）**：canvas.js 有 canConnect/canOutput/createNodeByType 白名单闸门体系，我首轮实现只加了菜单和工厂，**节点根本无法创建、连线全被拒绝且保存时被清理**——而我此前的"E2E 验证"用直接 push connections 绕过了闸门，全绿假象。修复后重测严格走 createNodeByType/canConnect 真实路径。**方法论沉淀：前端交互验证必须走产品的真实入口函数，不能直接操作内部数据结构。**
2. **P1-2 快照语义**：GitHub skill 的 commit_sha 在编辑后不变，作缓存键会让编辑不失效缓存 → 一律改内容哈希（升级后内容未变命中缓存反而更精确），commit_sha 只作溯源展示。
3. **async 锁选型**：同 key 串行化最初误用 threading.Lock（会阻塞事件循环死锁），改 asyncio.Lock——async 代码里同步锁的阻塞语义要警惕。
4. **范围修订（P3-4）**：PRD FR2-5 与 WORKPLAN T5.1/T5.2 的 "smart-canvas" 全部修订为普通画布 canvas.js，smart-canvas composer 接入明确留待后续迭代（用户需求原文即"连到 API/ModelScope 生图节点"）。

## 测试与验证结果

- 全量单测 47 项全绿（injection 6 + library 23 + codex 18）。
- 浏览器 E2E：真实闸门路径全过（数据见上方 TODO 流程）；测试节点已清理（画布恢复原状）。
- llm 模式真实改写端到端未验证（消耗 LLM 额度，留待用户授权/Phase 6）。

## 遗留问题与风险

- llm 智能模式的真实 LLM 改写效果与额度消耗待 Phase 6 验收（需授权）。
- skill 节点提示词注入面：第三方 SKILL.md 文本进入最终提示词（功能定位使然，导入 UI 已有脚本警告；信任提示可后续加）。

## 下一步

- Phase 6：端到端验收（Codex 订阅生图 smoke + 带 skill 生图 smoke，需用户授权额度）+ README + 分支整理。
