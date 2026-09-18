# Phase 1 进度日志（2026-09-19）

## 本期完成（对应任务编号）

- **T0.2 补充**：WORKPLAN 更新——T1.2 标记 ⏸（用户 ChatGPT 订阅额度耗尽，预计 2026-09-20 重置，用户确认后执行）；新增「额度替代约定」：非 Codex 通道生图测试用 ModelScope 免费模型。
- **T1.1 ✅**：探测脚本 `tools/zcode-verify/codex_image25_probe.py` ＋ `README.md`。自测通过（dry-run 模式）：
  - CLI 定位正常：`C:\Users\Administrator\AppData\Roaming\npm\gpt-image-2-skill.CMD`
  - 外层宿主模型解析：`gpt-5.6-sol`（来源 `~/.codex/config.toml`，与 main.py `codex_image_host_model()` 同序解析链一致）
  - 三组请求体构造正确：auto（无 tools[].model）/ flare（`gpt-image-2.5-flare`）/ sunburst（`gpt-image-2.5-sunburst`），`background=auto`、提示词内嵌 1024x1024 尺寸要求（按上游实测最佳实践）
  - 安全设计：默认 dry-run 零额度；`--run` 才真实调用；`--only` 支持单变体重跑

## 关键发现/决策

1. 现有 main.py `gpt_image_2_skill_prompt_arg`（5181 行）已在 codex provider 路径把尺寸/比例/横竖版写进提示词——T2.2 的「提示词内嵌尺寸」项基本已就绪，剩余工作是背景参数与 API 回退删除。
2. `--quality high` 目前硬编码在 `generate_codex_provider_image_via_gpt_image_2_skill`（5363 行）；上游实测显示质量档请求经常不被执行（返回 low/medium），观察模型元数据里如实记录即可，不强求。
3. 按计划约定，T1.2 阻塞不阻塞 Phase 2 编码：**立即进入 Phase 2**（单测先行），实验性文案与诚实反馈设计维持 PRD 原案，待 T1.2 结果再定 UI 标注口径。

## 测试与验证结果

- 脚本 dry-run 自测：3/3 请求体生成成功，内容目检正确（见 `tools/zcode-verify/out/body-*.json`）。
- 未消耗任何额度。

## 遗留问题与风险

- ⏸ T1.2/T1.3：待用户确认额度重置（预计 2026-09-20）。若探测显示 flare/sunburst 被服务端确认 → 回调 T2.3 的 UI 标注（去「实验性」字样）。
- 宿主模型 `gpt-5.6-sol` 是否被 ChatGPT 后端接受尚未实测（上游验证时 gpt-5.4 被拒、gpt-6-astra 可用；本机配置值待 T1.2 顺带验证）。

## 下一步

- Phase 2：T2.1（image_model 字段 + request-create 分支）→ T2.2 → T2.3 → T2.4 → T2.5。
