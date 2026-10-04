# Phase 3 进度日志（2026-09-19）

## 本期完成（对应任务编号）

- **T3.1 ✅**：SKILL.md 解析（`parse_skill_markdown_text`：yaml + GuardedLoader 防炸弹 + flat 回退）；存储规范 `skills/custom/<id>/SKILL.md` + `.skill_meta.json`（安装元数据随目录走，删除即清理，无集中索引需同步）。
- **T3.2 ✅**：三来源扫描（custom 可管理 / builtin=仓库 skills/ 只读 / codex=~/.codex/skills 只读）；`skill_dir_for` realpath+commonpath+basename 三重校验；API：`GET /api/skills`、`GET /api/skills/{source}/{id}`（含正文+文件清单）、`POST/PUT/DELETE /api/skills/custom`。
- **T3.3 ✅**：GitHub 导入三段式（preview 确认 → install 固定 SHA → check-update/upgrade）；zip 导入；monorepo `subdir` 支持（anthropics/skills 类多 skill 仓库的主流形态）；GITHUB_TOKEN 可选。**真实仓库全链路验证**：anthropics/skills 多 SKILL.md 拒绝列候选 → subdir 定位 algorithmic-art → install → scan → check-update(up_to_date) → upgrade → 409 防重 → overwrite → 清理。
- **T3.4 ✅**：自建 skill 创建/编辑/删除（frontmatter 由服务端生成，防注入；style 等自定义 yaml 字段随 SKILL.md 编辑天然支持）。
- **T3.5 ✅**：单测 23 项（tests/test_skill_library.py，全绿）；子代理独立审查（P1×1、P2×7、P3×9，其中安全红线六项实测确认无问题）→ **全部 P1/P2 已修复**（提交记录见下）；repair skill 作为 builtin 首个条目入库（6b432e6）。

## 关键发现/决策

1. **审查抓到的最重要问题（P1-1）**：zip 安装原本静默覆盖同名 skill（用户本地编辑会被无提示抹掉）→ 已加 overwrite 确认 409。
2. **monorepo 支持是实战必需**：真实测试发现 GitHub skill 多为"一仓库多 skill"（anthropics/skills 含几十个），第一版报错文案承诺了不存在的"指定子目录"→ 补 `subdir` 参数（preview/install 显式传，upgrade 锁定已存 skill_root）。
3. **升级备份目录用点前缀**（`.skill_id.upgrade-bak`）：扫描跳过隐藏目录 → 不会出幽灵条目，也不会与用户合法 skill（ID 禁点开头）撞名；Windows 文件占用导致清理失败时响应带 warnings。
4. **check-update 不再下载 zipball**（改 commits API）：大仓库不再被 20MB 上限误伤，检查零大流量。
5. PyYAML `compose_node(self, parent, index)` 是两参签名——审查建议的防护代码初版签名错误，测试（tags list）当场暴露，已修。

## 测试与验证结果

- `tests/test_skill_library.py` 23/23；`tests/test_gpt_image_2_skill_args.py` 18/18。
- 真实网络冒烟：见 T3.3；环境偶发 GitHub 瞬时抖动（502 带可操作文案），重试即恢复。
- 未消耗任何生图/LLM 额度。

## 遗留问题与风险（低优先，记录在案）

- 审查 P3 未修项：detail file_list 先全量后截断（超大目录白耗内存）、畸形 zip（同名文件/目录冲突）的 NotADirectoryError 裸 500、Windows junction 环（Python 3.12 才有 isjunction，需本机手工构造，风险极低）。
- GitHub 匿名限流 60 req/h：无 GITHUB_TOKEN 时频繁导入会触发（错误文案已引导配置 token）。
- 前端管理页（Phase 4）与画布节点（Phase 5）未开始。

## 下一步

- Phase 4：Skill 管理页前端（T4.1-T4.4，复用 iframe 页面架构）。
