# Phase 3 Handoff（2026-09-19）

## 当前状态

- 分支 `zcode/iteration-01`，HEAD 为 T3.5c 审查修复提交（序列：T3.1/T3.2 → T3.3 → subdir 补强 → repair skill 入库 → T3.5c 修复）。
- Phase 0/1(T1.2 ⏸)/2/3 全部完成；Phase 4（Skill 管理页前端）待开始。

## 已交付（功能点 → 代码位置）

Skill 库后端全部在 main.py 尾部「# --- 画布 Skill 库 ---」section（约 19100 行起）：

- **解析**：`parse_skill_markdown_text`（GuardedLoader 防别名炸弹 + flat 回退）、`normalize_skill_id`
- **扫描**：`skill_scan_all`（custom/builtin/codex 三来源）、`skill_entry_from_dir`（元数据+统计+警告）、`skill_read_meta`/`skill_write_meta`
- **路径安全**：`skill_source_root`/`skill_dir_for`（realpath+commonpath+basename，全来源拦截穿越）
- **CRUD API**：`GET /api/skills`、`GET /api/skills/{source}/{skill_id}`、`POST /api/skills/custom`、`PUT/DELETE /api/skills/custom/{skill_id}`
- **GitHub 导入**：`github_repo_slug`（re.I）、`github_api_headers`（GITHUB_TOKEN 可选）、`github_resolve_commit`（轻量 SHA 解析）、`github_download_repo_zip`（流式限长下载）、`safe_extract_skill_zip`（zip-slip/单文件/总量/数量四重防护）、`locate_skill_root`（根/唯一子目录/subdir 显式）、`validate_and_stage_skill`
- **导入 API**：`POST /api/skills/github/preview`（确认制）、`POST /api/skills/github/install`（固定 SHA，409+overwrite）、`POST /api/skills/zip/install`（Form overwrite）、`GET /api/skills/custom/{id}/check-update`、`POST /api/skills/custom/{id}/upgrade`（点前缀备份+回滚+warnings）
- **数据规范**：`skills/custom/<id>/SKILL.md` + `.skill_meta.json`（source=local|github|zip、repo_url、commit_sha、ref、skill_root、installed_at）；builtin 首条目 skills/infinite-canvas-gpt-cli-image-repair 已入库
- **测试**：tests/test_skill_library.py（23 项，含注入/穿越/zip-slip/上限/409/覆盖/非 GitHub 拦截/别名炸弹）

## 运行与验证方法

```powershell
.\python\python.exe tests\test_skill_library.py   # 23/23
.\python\python.exe main.py                        # 端口 3000
# 冒烟：GET http://127.0.0.1:3000/api/skills 应列出 builtin repair skill（scripts 警告）与 codex 来源
```

真实 GitHub 冒烟（零额度）：preview `{"url":"https://github.com/anthropics/skills","subdir":"skills/algorithmic-art"}`；匿名限流 60 req/h。

## 关键上下文

- **API 消费约定（Phase 4/5 前端对接）**：列表项含 id/name/description/version/license/source/readonly/has_skill_md/has_scripts/warnings/files/total_bytes/summary/install(GitHub 元数据)；详情额外含 body（SKILL.md 正文）/file_list/metadata（frontmatter 其余字段，**style 配置也在这里**）。
- **导入交互流（FR2-2 确认制）**：preview 返回 repo(sha/ref/commit_message)+skill 元数据 → 用户确认 → install 带 url+sha(+name/overwrite/subdir)。409=已存在需勾选覆盖。
- **升级失败 warnings**：旧目录被占用无法清理/元数据写入失败时，响应含 warnings 数组，前端应展示。
- **安全红线**（勿破坏）：scripts 永不执行；codex/builtin 只读；固定 SHA；第三方内容只进提示词文本（Phase 5 注入时同样适用）。

## 下一阶段入口

**Phase 4：Skill 管理页（T4.1-T4.4）**——新增 static/skill-manager.html（iframe 架构、theme/i18n 接入），列表分组（custom/builtin/codex）、GitHub 导入向导（URL→preview 确认→install→409 处理→overwrite）、zip 上传、自建编辑器（SKILL.md 文本 + 保存）、升级（check-update → diff 展示（SHA+commit message）→ upgrade → warnings）。参考现有页面：api-settings.html（结构）、asset-manager.html（列表+上传模式）。

## 注意事项（勿动清单）

- `C:\Infinite-Canvas` 绝不修改；`API/.env` 永不提交。
- 消耗额度的验证需用户授权（T1.2 探测待额度重置）。
- 前端改动记得刷新 cache-bust 版本号（各 html 引用 + i18n.js VERSION）。
- main.py 已近 2 万行：Skill 相关新增逻辑全部集中在尾部独立 section，继续遵循。
