# Handoff：校审修复轮（2026-09-19 深夜）

> 接手人只需读本文件 + [PRD](../PRD.md) + [优化工作总结](../优化工作总结.md) 即可无缝继续。

## 当前状态

- 分支 `zcode/iteration-01`，HEAD `73cd204`（已 rebase 到 codex 推送的校审报告提交 `4fc3644` 之上），全部推送 fork。
- 两轮 Codex 交叉校审（6+4 项）全部修复闭环；63 项单测全绿（证据摘要见 [进度日志](../log/REVIEW-rounds-progress.md)）。
- 工作区未提交内容：仅 API/.env（永不提交）与服务运行时的 HTML 版本戳（正常副产物，随下次提交入库即可）。
- 本地服务已用最新代码重启（端口 3000）。

## 两轮校审修复的代码位置速查

| 修复点 | 位置 |
|---|---|
| FULL_ARGV 日志删除 | main.py（原 5587 行附近，已无该 print） |
| allow_api_fallback 前端提交 | static/js/api-settings.js saveProviders PUT body（搜 allow_api_fallback） |
| allow_api_fallback 后端 | ApiProviderPayload / normalize_provider / public_provider（搜 allow_api_fallback） |
| 缓存 key（含 variant/provider/model） | main.py compile_skill_prompt 内 `key = hashlib.sha256(f"{snapshot}\|{mode}..."` |
| 缓存并发安全 | main.py skill_compile_cache_save（mkstemp+fsync+os.replace）+ skill_compile_cache_merge + _SKILL_CACHE_FILE_LOCK |
| 空提示词放行 + 三选一校验 | main.py OnlineImageRequest.prompt + build_online_image_result 开头 |
| 预览 variant/model/provider | SkillPreviewRequest + skill_selection_from_preview + 两预览端点；前端 previewCompiledPrompt |
| 事务性安装 | main.py swap_staged_into_target（meta_writer 参数）；github/zip install 调用点；upgrade 内联事务 |
| SKILL.md 1MB 上限 | SKILLS_MAX_SKILL_MD_BYTES + validate_and_stage_skill |
| 大文件跳过 | SKILLS_SKIP_FILE_BYTES + safe_extract_skill_zip |
| 画布 Skill 节点全部交互 | static/js/canvas.js 搜 skill-node/skillMode/skillVariant/skillModel |
| 测试隔离写法范例 | tests/test_skill_library.py test_allow_api_fallback_put_get_roundtrip |

## 运行与验证

```powershell
.\python\python.exe tests\test_skill_injection.py      # 11/OK
.\python\python.exe tests\test_skill_library.py        # 29/OK
.\python\python.exe tests\test_gpt_image_2_skill_args.py  # 23/OK
.\python\python.exe main.py                            # 端口 3000
```

浏览器：`http://127.0.0.1:3000` → 无限画布（画布列表链接已带动态版本参数，不再有旧缓存问题）。

## 关键上下文（给下一位）

1. **T1.2 判定已定**：2.5 三变体均返回别名 `gpt-image-2-codex` → 维持"实验性"标注；服务端将来真开放时代码零改动转正（confirmed 标志自动生效）。
2. **测试红线**：任何测试不得触碰 API_PROVIDERS_FILE / API/.env（update_env_values）/ static 模板同步三个真实写点——写法范例见 roundtrip 测试。
3. **codex 校审遗留的"功能稳定后再做"项**：main.py 拆分（skill_library.py / skill_compiler.py / codex_image.py）、SKILL_COMPILE_LOCKS 生命周期控制、预览与生成一致性的端到端测试组、CI 敏感信息检查扩展。
4. **ModelScope 免费聊天通道**平台侧故障（no provider supported）仍未解——影响 GPT 对话/智能模式的 ms 通道，与本项目代码无关。
5. **git 操作提醒**：codex 会直接向远程分支推文档提交——push 被拒时先 `git fetch` + rebase（文档冲突以 codex 版本为准）。

## 待用户决策的事项

1. **验收**：按二次校审"第五阶段"清单手工验收（开关保存刷新 / 样板不串缓存 / 仅 Skill 无提示词生图 / 预览一致性 / 覆盖安装失败恢复）。
2. **第三轮复核**：可请 codex 复核 73cd204 的修复 diff 确认闭环。
3. **合并**：验收通过后是否把 zcode/iteration-01 同步回 `C:\Infinite-Canvas`（操作前备份）。
4. **额度类遗留**：无——T1.2/智能模式/AI 识别/Codex smoke 均已完成。

## 勿动清单（不变）

- `C:\Infinite-Canvas` 绝不修改
- `API/.env` 永不提交
- 测试不得触碰真实 Provider 配置三个写点
- 前端改动后：canvas.html 等 cache-bust（或依赖启动时自动版本戳同步）
