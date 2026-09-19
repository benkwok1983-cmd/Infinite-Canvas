# 进度日志：Codex 交叉校审修复（第一轮 + 二轮）

日期：2026-09-19 深夜
分支：`zcode/iteration-01`
对应：docs/zcode/Codex代码校审报告.md（一轮）、Codex二次代码校审报告.md（二轮）

## 第一轮校审（6 项 → 全部修复）

提交 `91e9b8e`。修复清单：

| # | 级别 | 问题 | 修复 | 回归测试 |
|---|---|---|---|---|
| P1-1 | P1 | 调试日志 FULL_ARGV 打印完整 argv（开回退时真实 API Key 进日志） | 彻底删除该 print | — |
| P1-2 | P1 | saveProviders 提交体缺 allow_api_fallback，开关无法持久化 | 提交体补字段 | PUT→GET 往返测试 |
| P1-3 | P1 | LLM 缓存 key 漏 variant（切样板串用缓存） | key 纳入 selection.variant + 解析后样板指令 | va→vb 不串用、回 va 命中缓存 |
| P1-4 | P1 | API 生成节点拒绝空提示词（min_length=1），"参考图+Skill"仅 ms 节点生效 | prompt 允许空 + 业务层三选一校验（提示词/Skill/参考图，纯空 400）；前端有 Skill 时空串替代英文 fallback | 空 prompt+Skill 通过 / 全空 400 |
| P2-5 | P2 | 预览未携带 variant/model，预览≠实际生成 | 预览请求补齐 | — |
| P2-6 | P2 | 覆盖安装先删后移，失败丢旧 Skill | swap_staged_into_target 事务 helper | 模拟 move 失败验证恢复 |

次要：缓存临时文件+原子替换；SKILL.md 1MB 上限。

## 第二轮校审（4 项 → 全部修复）

提交 `73cd204`。修复清单：

| # | 级别 | 问题 | 修复 | 回归测试 |
|---|---|---|---|---|
| P1 | P1 | roundtrip 回归测试读写**真实 Provider 配置**（可能改掉用户的开关且失败无法恢复） | 测试完全隔离：API_PROVIDERS_FILE→临时文件 + 播种含 codex 的临时配置 + 屏蔽 update_env_values（PUT 会写 API/.env）+ 屏蔽 RunningHub 模板同步；临时文件 tearDown 自动清理 | 隔离后往返仍通过 |
| P2 | P2 | 缓存"原子写"跨 key 并发竞争（固定 .tmp 名 + 无全局锁 → 并发覆盖丢记录） | 全局文件锁 `skill_compile_cache_merge()`（锁内读取→合并→写）+ mkstemp 唯一临时文件 + flush + fsync + os.replace + 失败清理 | 缓存并发由 llm 缓存用例覆盖路径 |
| P2 | P2 | 预览请求发了 model 但后端丢弃；provider 同样缺失 | SkillPreviewRequest 增加 model/provider；preview-prompt 与 compile-prompt 两端点完整传入 SkillSelection | 预览与生成参数一致（结构保证） |
| P2 | P2 | 覆盖安装事务未覆盖元数据写入（meta 失败=新目录在、备份删了） | swap_staged_into_target 接受 meta_writer，元数据写入纳入事务（失败删新目录恢复旧目录）；GitHub/zip 接入；**upgrade 路径同类问题一并收紧**（meta 移入事务） | meta 写入失败回滚测试（旧目录恢复、无备份残留） |

## 附加交付

- **GitHub Actions CI**：`.github/workflows/tests.yml`——push/PR 自动跑三个测试套件 + 敏感信息 guard（扫描 FULL_ARGV 类密钥输出模式，命中即失败）。响应两轮校审共同指出的"缺少独立验证证据"。
- **测试证据留存**（原始摘要，2026-09-19，HEAD 73cd204）：
  ```
  tests/test_skill_injection.py        → Ran 11 tests / OK
  tests/test_skill_library.py          → Ran 29 tests / OK
  tests/test_gpt_image_2_skill_args.py → Ran 23 tests / OK
  ```
  合计 63 项。复现：`.\python\python.exe tests\<文件名>` 逐个执行。

## 过程中的方法论沉淀

1. **bash heredoc 写含 `\n` 转义的代码必炸**：heredoc 的转义层级会把 `\\n` 变成真实换行写进文件。含转义序列的代码一律用 Edit/Write 工具（本轮测试文件被写坏两次）。
2. **测试碰 `/api/providers` 的三个真实写点**：API_PROVIDERS_FILE、update_env_values（写 API/.env）、sync_runninghub_provider_workflows_to_static_template（写 static 模板）——隔离必须三者全覆盖。
3. **unittest patcher 正确姿势**：`p = patch.object(...); p.start(); self.addCleanup(p.stop)`——`addCleanup(patch(...).start)` 是错误写法（teardown 才 start，等于没打补丁且测试假绿）。
4. **观察模型采信 completed、skill 内容哈希作缓存键**等一轮设计经二轮校审确认为正确方向，保留。

## 状态

- 两轮校审问题全部修复闭环；63 项测试全绿；HEAD `73cd204` 已推送 fork。
- 分支仍保留在 `zcode/iteration-01`（按二次校审意见：未经用户验收不合并到使用分支）。
