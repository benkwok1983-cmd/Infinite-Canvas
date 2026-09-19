# Infinite-Canvas
Supports comfyui/API calls/modelscope calls

配套的chrome采集插件已经上线：https://chromewebstore.google.com/detail/infinite-canvas-%E5%9B%BE%E5%83%8F%E8%A7%86%E9%A2%91%E6%96%87%E5%AD%97%E6%8A%93%E5%8F%96%E5%B7%A5/ajfhnbklbmpfaaookhfakohabnpmlcic?authuser=0&hl=en

详细教程：[https://youtu.be/1y9ShTvgC_w](https://youtu.be/r_y_9ALr7fg)

由于最近很多API网址关停，我找到一个稳定的网址：

https://apib.ai/register?aff=1uyAbb （包含所有生图模型/视频模型/LLM模型）

https://www.fhl.mom/register?aff=86L574B4T2N9  （包含codex和GPT image 2模型）

功能请求/功能更新/视频教程/联系我，都可以在B站评论或私信：https://space.bilibili.com/78652351


----

【新增了version文件，我每次更新都会更新version的版本号，如果你下载version文件，打开项目后，导航栏的GitHub按键就会提示新版本，如果不想查看更新提示，就删除version文件】

【A version file has been added. I update the version number with each update. If you download the version file, the GitHub button in the navigation bar will indicate the new version after opening the project. If you don't want to see update notifications, delete the version file.】

----

支持的功能：
1. 支持几乎所有OpenAI协议的API/异步协议/Gemini协议/方舟协议
2. RunningHub的工作流/AI应用/收费模型调用
3. 火山引擎调用（人脸认证还在修复bug）
4. Modelscope免费LLM模型和图像模型调用
5. 即梦CLI调用，可直接调用即梦高级会员的积分，支持文生图/图生图/文生视频/图生视频
6. 支持调用本地局域网的ComfyUI
7. 扩展图片/360全景图预览截图/视频帧抽取/循环节点等诸多功能
8. tools文件夹中，增加了chrome批量采集到素材库的插件，PS直连画布调用所有功能的插件

--------

## 本 fork 新增功能（zcode/iteration-01 分支）

### 1. Codex 订阅额度生图 · 实验性 Image 2.5

在 API 设置中添加「GPT CLI」（Codex）平台并完成本机 `codex` 登录后，画布生图走 ChatGPT 订阅额度（不消耗 API 费用）。

- 生图模型下拉提供三档：**gpt-image-2**（默认，稳定）、**gpt-image-2.5-flare / sunburst**（实验性）
- 实验档通过底层请求注入图像模型名；服务端可能忽略该选择并返回别名，界面上会如实提示「2.5 选择未被服务端确认」
- 结果元数据记录：请求模型 / 服务端实际观察模型 / 实际尺寸，不做任何虚标
- API 设置的 Codex 卡片内有「API 回退」开关（默认关）：开启后 Codex 登录过期时自动改用 OpenAI API Key 生图（按 API 计费）；关闭时直接报错提示重新登录
- 实验性 2.5 档仅支持文生图，且**只走订阅额度，永不回退 API**

### 2. 画布生图 Skill 节点 + Skill 库

把 GitHub 开源 Skill 或自建风格包导入画布，生成时按 Skill 编译提示词，产出指定风格图像。

- **Skill 库管理**（左侧导航「Skill 库」）：GitHub 导入（预览确认 → 固定 commit SHA → 一键升级）、zip 导入、自建编辑；第三方 Skill 的脚本永不执行
- **生图 Skill 节点**（普通画布）：从「API 生成 / MS 生成」节点的输入端口创建 Skill 节点，下拉选 Skill、选模式、连线即可
  - **快速模式**：Skill 指令与提示词直接拼接，零额外消耗
  - **智能模式**：生成时由 LLM 按 Skill 融合改写提示词（结果缓存复用，消耗少量 LLM 额度）
- 生成节点上的「预览提示词」可查看编译后的最终提示词；每张结果图记录所用 Skill、版本与最终提示词（可溯源）

### 开发说明（本 fork）

- 迭代文档：`docs/zcode/PRD.md`（需求）、`WORKPLAN.md`（进度）、`log/`（各阶段日志）、`handoff/`（交接）
- 单元测试：`.\python\python.exe tests\test_skill_library.py`、`tests\test_skill_injection.py`、`tests\test_gpt_image_2_skill_args.py`（共 47 项，零额度消耗）
- Codex 2.5 探测脚本（额度重置后验证服务端是否真正支持 2.5）：`tools/zcode-verify/codex_image25_probe.py`（默认 dry-run 零消耗，`--run` 才真实调用）

--------

已经申请著作权，禁止商业用途

Commercial use is prohibited.


* 可以自己使用和公司使用，禁止用于任何形式的修改封装成商业产品，商用须取得授权。

* 根据代码二次开发的软件必须保持开源并注明来源作者

* This software is for personal and company use only, but is prohibited from being modified or packaged into commercial products in any way. Commercial use requires authorization.

* Software developed based on this code must remain open source and the original author must be credited.

--------


<img width="2079" height="665" alt="image" src="https://github.com/user-attachments/assets/8469923b-f7a2-403c-9c37-e6e789211f28" />

<img width="1865" height="1503" alt="image" src="https://github.com/user-attachments/assets/f4030201-67c6-4845-b08b-b6fdf304afaa" />


<img width="1696" height="1350" alt="b68e144c5b04a322bfd035da4d89aba3" src="https://github.com/user-attachments/assets/0a6090fb-a8dd-4c3d-adee-b1f9233a2d91" />

   
<img width="1525" height="1473" alt="image" src="https://github.com/user-attachments/assets/6f61fcf9-746c-425b-9e36-cfc8d252da7c" />

   <img width="1261" height="864" alt="image" src="https://github.com/user-attachments/assets/57f3e230-3134-488f-8179-d97e7d15383a" />
<img width="1530" height="858" alt="image" src="https://github.com/user-attachments/assets/9990e42d-22d5-4a10-a1e1-ad35a634edd2" />

<img width="1735" height="1400" alt="image" src="https://github.com/user-attachments/assets/d8328ff8-bbe0-4f1c-9ffa-7b56e8a1a51d" />
<img width="2258" height="969" alt="image" src="https://github.com/user-attachments/assets/4a752d99-885d-4ba9-8b86-91b495786b5c" />


<img width="1531" height="1374" alt="image" src="https://github.com/user-attachments/assets/0af79e38-0955-4740-9e65-5c9bb057f58c" />

<img width="2196" height="1040" alt="image" src="https://github.com/user-attachments/assets/6d823668-cde2-4836-8332-1858efe5f520" />
<img width="2214" height="771" alt="image" src="https://github.com/user-attachments/assets/52e10958-753f-45ba-a50e-3bbec27be436" />
