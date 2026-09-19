已完成只读校审，没有修改或编辑任何项目文件。

审查对象是远程 Fork 的 `zcode/iteration-01` 分支。代码实现提交为 `c7d8d48`，之后又增加了工作总结文档；当前分支相对基线 `03f8bdd` 共领先 37 个提交、54 个文件。由于本机 Windows 沙箱初始化故障，我无法读取 Zcode 工作区的未提交文件或独立运行测试，因此本报告覆盖“已推送代码”，不代表本地尚未推送内容。

## 总体结论

Zcode 的总体设计方向正确，两个需求都已经形成了相对完整的实现：

* Images 2.5 没有虚假宣称“确认使用”，而是区分请求模型、观察模型和确认状态。
* 2.5 实验通道坚持 Codex 订阅，不自动切 API。
* Skill 使用声明式内容，第三方脚本不执行。
* GitHub Skill 固定 commit SHA，具备 ZIP 路径穿越、数量和大小限制。
* Skill 节点、样板、快速/智能模式、生成溯源均已进入画布链路。
* Zcode 在独立目录和独立分支工作，没有同步覆盖 `C:\\Infinite-Canvas`。

但是，当前版本不建议直接合并到正在使用的项目。静态审查发现至少 5 项需要修复，其中 4 项会直接影响安全、计费开关、样板生成准确性或用户需求完整性。

## 主要问题

### 1\. \[P1] API Key 可能被完整写入后端日志

[main.py](C:/agent-workspace/zcode/Infinite-Canvas/main.py:5587) 输出了完整的 `args`：

```python
print(f"... FULL\_ARGV={json.dumps(args, ensure\_ascii=False)}")
```

当 Codex 自动回退到 OpenAI API 时，`args` 在这里已经包含：

```text
--provider openai --api-key <真实密钥>
```

因此只要用户打开 API 回退，真实 API Key 就可能进入终端、日志采集系统或故障截图。这与计划中的“无调试残留、无密钥泄漏”要求冲突。

建议：

* 完全删除 `FULL\_ARGV` 日志。
* 或只记录 provider、mode、模型、尺寸等白名单字段。
* 通用原则：所有 `--api-key`、Authorization、auth file 内容必须脱敏。

::code-comment{title="\[P1] API Key may be written to logs" body="The fallback provider arguments can contain --api-key followed by the real key. Serializing the complete argv here exposes that secret in terminal logs and diagnostic captures. Log only a redacted whitelist of provider, mode, model, and size fields." file="C:/agent-workspace/zcode/Infinite-Canvas/main.py" start=5587 priority=1}

### 2\. \[P1] “允许 API 回退”开关没有随保存请求提交

后端已经支持 `allow\_api\_fallback`，前端也会把复选框值写进 `item.allow\_api\_fallback`。但是保存 Provider 时构造的 JSON 白名单中缺少这个字段：

[static/js/api-settings.js](C:/agent-workspace/zcode/Infinite-Canvas/static/js/api-settings.js:3775)

结果可能是：

1. 用户打开开关。
2. 点击保存。
3. 后端收到的 Pydantic 默认值仍是 `false`。
4. 页面重新加载后开关恢复关闭。
5. 总结中所称“API 回退 UI 开关可用”实际上无法持久化。

建议在保存请求中明确加入：

```javascript
allow\_api\_fallback: item.id === 'codex'
    ? Boolean(item.allow\_api\_fallback)
    : false
```

还应增加一次 API 往返测试：PUT 保存后重新 GET，确认值保持。

::code-comment{title="\[P1] Fallback toggle is omitted from save payload" body="syncEditor updates item.allow\_api\_fallback, but the provider object serialized in saveProviders does not include that property. The backend therefore receives its false default and the UI setting cannot reliably persist after saving or reloading." file="C:/agent-workspace/zcode/Infinite-Canvas/static/js/api-settings.js" start=3775 priority=1}

### 3\. \[P1] 智能模式缓存没有包含样板 variant

[main.py](C:/agent-workspace/zcode/Infinite-Canvas/main.py:20257) 的缓存键包含：

```text
skill snapshot + mode + provider + model + user prompt
```

但没有包含 `variant`。

因此：

1. 用户选择“钴蓝”样板生成。
2. 再切换到“朱红”样板。
3. Skill、用户提示词、模型均不变。
4. 第二次会命中第一次缓存。
5. 实际生成仍可能使用“钴蓝”提示词。

这会使样板选择器产生错误结果，也是现有测试没有覆盖的路径。

缓存键至少应加入：

* `variant.id`
* `variant.prompt` 或其哈希

::code-comment{title="\[P1] Variant is missing from LLM cache key" body="The compiled message includes the selected variant, but the cache key does not. Switching variants with the same skill, provider, model, and user prompt can return a compiled prompt cached for the previous variant." file="C:/agent-workspace/zcode/Infinite-Canvas/main.py" start=20257 priority=1}

### 4\. \[P1] “参考图 + Skill，无提示词生成”没有在 API 生图后端实现

[main.py](C:/agent-workspace/zcode/Infinite-Canvas/main.py:2820) 仍要求：

```python
prompt: str = Field(min\_length=1, ...)
```

这意味着 API 生图节点即使已经连接参考图和 Skill，只要用户提示词为空，请求就会在进入 Skill 编译前被 Pydantic 以 422 拒绝。

总结中只明确说 ModelScope 节点已经放开提示词，但用户原始需求是 Skill 连线到 API/ModelScope 生图节点，而且提示词为可选项。

建议改成允许空字符串，然后在业务层验证：

```text
至少满足以下一项：
- 有非空提示词；
- 有 Skill；
- 有参考图。
```

纯空请求仍应拒绝。

::code-comment{title="\[P1] API generation still rejects an empty prompt" body="OnlineImageRequest validates prompt with min\_length=1 before Skill compilation runs. This prevents the requested reference-image plus Skill flow from working without a text prompt on API generation nodes. Validate the combined request instead: prompt, Skill, or reference image must be present." file="C:/agent-workspace/zcode/Infinite-Canvas/main.py" start=2820 priority=1}

### 5\. \[P2] 提示词预览没有应用当前样板和智能模型设置

后端快速预览没有将 `variant` 传给拼接函数：

[main.py](C:/agent-workspace/zcode/Infinite-Canvas/main.py:20298)

前端预览请求同样遗漏了：

* `variant`
* 智能模式 `model`
* 智能模式 `provider`

[static/js/canvas.js](C:/agent-workspace/zcode/Infinite-Canvas/static/js/canvas.js:8534)

结果是“预览提示词”和点击生成时真正使用的提示词可能不同。尤其是样板功能的主要价值就在附加风格参数，这会误导用户。

::code-comment{title="\[P2] Prompt preview omits selected variant" body="The preview request sends only source, id, mode, and prompt, while generation also sends variant and model. The backend fast-preview path likewise calls compose\_skill\_prompt\_fast without the resolved variant. Previewed content can therefore differ from the actual generation prompt." file="C:/agent-workspace/zcode/Infinite-Canvas/static/js/canvas.js" start=8534 priority=2}

### 6\. \[P2] 覆盖安装不是事务性的，失败可能丢失旧 Skill

GitHub/ZIP 覆盖安装先执行：

```python
shutil.rmtree(target)
shutil.move(staged, target)
```

位置见 [main.py](C:/agent-workspace/zcode/Infinite-Canvas/main.py:20005)。

如果删除后 `move` 因杀毒软件、文件占用、磁盘问题或权限失败，旧 Skill 已经永久消失。升级接口使用了备份目录，但普通覆盖安装没有采用同样机制。

建议统一为：

1. 将旧目录原子改名为隐藏备份。
2. 将 staged 移入正式位置。
3. 写入并校验元数据。
4. 成功后删除备份。
5. 任一步失败即恢复旧目录。

::code-comment{title="\[P2] Overwrite install deletes the old Skill before replacement succeeds" body="The overwrite path removes the existing directory before moving the staged Skill into place. A move, disk, antivirus, or metadata failure after deletion loses the user's previous Skill. Reuse the upgrade path's backup-and-rollback strategy." file="C:/agent-workspace/zcode/Infinite-Canvas/main.py" start=20005 priority=2}

## 次要缺陷与可维护性问题

* `SKILL\_COMPILE\_LOCKS` 按每个缓存键永久保存 `asyncio.Lock`，没有清理机制。长期使用大量不同提示词后会持续增长。
* 不同缓存键使用不同锁，但共同读写同一个 JSON 文件；两个并发请求可能各自读取旧数据并互相覆盖，甚至在异常中留下损坏文件。建议使用一个缓存文件锁，并采用临时文件加原子替换。
* `main.py` 一次增加约 1319 行，Skill 库、GitHub 下载、缓存、编译和 Codex 探测继续堆在约两万行的单文件中。短期能运行，后续维护和回归风险较高。建议在功能稳定后拆成 `skill\_library.py`、`skill\_compiler.py`、`codex\_image.py`，但不要在本轮修 Bug 时顺带大重构。
* GitHub 导入允许 `SKILL.md` 最大接近 20MB，而扫描和快照会反复完整读取。建议给 `SKILL.md` 单独设置更小上限，例如 512KB～1MB。
* 文档中的测试数字不一致：

  * 工作总结写“51项”，分项却是 `23 + 24 + 6`，算术上为53。
  * Phase 6 日志写47项。
  * 当前分支实际定义的测试方法静态计数约为52项：21 + 24 + 7。
* 工作总结写“35个工作提交”，`c7d8d48` 相对基线实际为36个提交；加入总结文档后当前分支为37个提交。
* 当前 GitHub commit 没有 CI 状态，测试全绿属于 Zcode 自报结果，并未由远程 CI 独立证明。

## 做得比较好的部分

以下设计值得保留：

* `host\_model` 与 `image\_model` 分离方向正确。
* 只采信 `response.completed` 判断观察模型，比使用 created 请求回显可靠。
* 2.5 实验档拒绝 API 回退，符合订阅额度边界。
* Skill 路径使用 `realpath + commonpath`，整体方向正确。
* ZIP 导入具备文件数量、单文件、总大小和路径穿越限制。
* GitHub URL 被限制在 GitHub 仓库解析路径，没有开放任意下载 URL。
* 第三方脚本只标记、不执行。
* Skill 内容哈希用于缓存失效，比仅使用 Git commit SHA 更合理。
* 不连接 Skill 时保持原链路的设计意识正确。
* Zcode 在独立工作区和独立分支操作，没有触碰当前使用目录。

## 建议修复顺序

合并前至少完成：

1. 删除或彻底脱敏 `FULL\_ARGV` 日志。
2. 修复 `allow\_api\_fallback` 保存和重新加载。
3. 将 variant 纳入智能缓存键。
4. 让预览完整携带并应用 variant/provider/model。
5. 实现 API 节点的无提示词 Skill + 参考图路径。
6. 将覆盖安装改成可回滚事务。
7. 增加对应回归测试。
8. 重新跑完整测试和真实浏览器路径。
9. 更新总结中的测试数、提交数和已知边界。

建议新增的关键测试：

* 保存 `allow\_api\_fallback=true` 后 GET 仍为 true。
* fallback 日志不包含真实 API Key。
* 同一提示词切换两个 variant，智能编译结果不同且不会错误命中缓存。
* 快速/智能预览与真实生成使用同一 variant。
* 空提示词 + Skill + 参考图能够通过；三者全空被拒绝。
* GitHub/ZIP 覆盖安装中模拟 `move` 失败，旧 Skill 自动恢复。
* 不同缓存键并发写入后两条记录都存在且 JSON 完整。

## 最终意见

当前成果不是“推倒重做”的水平，主体架构可以保留；但也还不能直接同步到 `C:\\Infinite-Canvas`。最关键的阻断项是密钥日志风险、回退开关无法可靠保存，以及 variant 缓存串用。

建议让 Zcode 在原来的 `zcode/iteration-01` 分支继续做一轮“只修校审问题”的补丁，不增加新功能。修复后再重新审查 diff，最后才考虑合并到你当前使用的分支。

