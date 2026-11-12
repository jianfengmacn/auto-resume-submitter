---
name: auto-resume-submitter
description: 自动发简历 / AI 自动投简历助手。当用户想批量自动发送简历、根据 JD 自动定制并投递、追踪投递进度，或抱怨“投简历太费 token / AI 自动投简历太贵太慢”时使用。覆盖收岗、低成本初筛、简历定制（可选）、投递队列生成与（逐条人工确认）的半自动投递。适用于 Boss 直聘、猎聘、智联招聘、拉勾、LinkedIn、Indeed 等。
---

# Auto Resume Submitter（自动发简历）

## 这个技能解决什么

看到 AI 自动投简历的视频觉得香，但自己跑起来 **token 太贵、流程太散、点投递点到手酸**。本技能把“发简历”做成一条可复用、可省钱的工作流，**核心是“自动填表 + 批量发送”**，同时守住底线：

1. **收岗**：从招聘链接或粘贴的 JD 文本批量收集岗位。
2. **低成本初筛**（可选）：纯规则打分，不值得的岗直接淘汰，**0 token**。
3. **定制简历**（可选）：只对想精投的岗做最小改动；已有简历可直接发，跳过这步。
4. **生成投递队列**：把“岗位 + 用哪份简历 + 求职信”排成队，自动化据此逐条发送。
5. **半自动发送**：浏览器**自动填表/上传**，但**每一条真正提交前必须你确认**——不静默群发、不绕过验证码、不造假。
6. **追踪**：每次投递写入进度表，复盘“哪类岗回复率高”。

> ⚠️ 设计原则：**人始终是最后拍板的人**。本技能不替你编造经历、不绕验证码、不在你不知情时群发。自动化的是“重复填表”，判断与提交由你定。

## 触发场景

- “帮我把简历自动发到这些岗位”“自动发简历”“批量投简历”
- “根据 JD 改一下简历再发”“写封求职信一起投”
- “我投了好多没回音，帮我记一下 / 分析一下”
- “AI 投简历 token 太贵，有没有省钱的发法”
- 用户粘贴招聘链接（Boss / 猎聘 / 智联 / 拉勾 / LinkedIn / Indeed 等）

## 标准流程

### 0. 准备简历与偏好（首次，之后复用）

读取/创建 profile（默认 `resume_profile.json`，字段见 `references/profile-schema.md`）。若没有，向用户收集：

- **简历全文**（`resume_text`）或简历文件路径（`resume_file`）：给一份 txt/md/docx，或粘贴。定制/发送都基于它。
- **求职偏好**（`targets`）：目标岗位、城市、行业、薪资下限、排除关键词（如“销售”“驻外”“996”）。
- **模型档位**（`models`）：`screen`（初筛，默认纯规则）、`tailor`（定制，强模型）。**默认 screen 走规则，tailor 才走模型**，省钱核心。

> 通用偏好模板见 `references/profile-example.md`（不限定行业，按需改）。

### 1. 收岗（Discover）

- 给链接：用浏览器/WebFetch 读取 JD，抽取「公司 / 岗位 / 薪资 / 地点 / 职责 / 要求 / 链接」。
- 给文本：粘贴多条 JD，按 `---` 或空行切分。
- 批量时每条存成 `jobs/job_<n>.md`，便于复用、初筛与追踪。

### 2. 低成本初筛（Screen，可选）—— 省钱关键

**默认不调大模型**，用 `scripts/keyword_screen.py` 规则打分：

```bash
python scripts/keyword_screen.py --resume resume_profile.json --jobs jobs/ --threshold 0.45
```

- 维度：关键词命中率、硬性要求覆盖率、地点/行业/薪资契合度；命中排除词直接 0 分。
- 输出得分 + 淘汰原因，**只把 ≥ threshold 的岗送进后续步骤**。不想筛可直接全部进入发送。

### 3. 定制简历（Tailor，可选）

**如果已有现成简历、想直接群发，可跳过这步。** 只对想精投的岗调用 `models.tailor` 强模型，最小改动：

- 产出 `tailored/<job_id>_resume.md`（只改/加 3–5 条最相关 bullet，不重写全文，省 token、保真实）+ `tailored/<job_id>_cover.md`（一页求职信）。
- **禁止编造**：只重组/强调真实经历；缺的能力写“可学/可快速上手”，不虚构项目、证书、数据。

### 4. 生成投递队列（Build Queue）—— 发送前的核心一步

把“岗位 → 用哪份简历 → 求职信”排好队，后续发送严格按队列执行：

```bash
python scripts/build_send_queue.py --resume resume_profile.json --jobs jobs/ --tailored tailored/
```

- 自动按 `job_<id>` 匹配 `tailored/job_<id>_resume.md` 与 `tailored/job_<id>_cover.md`；没有定制稿则回退到 profile 里的基底简历/求职信。
- 输出 `send_queue.json` + 可读清单，含每条的：公司、岗位、链接、简历文件、求职信文件、状态（待发/已发/跳过）。
- 发送阶段只处理状态为“待发”的条目。

### 5. 半自动发送（Send，逐条人工确认）—— 本技能核心

遍历 `send_queue.json` 里“待发”的条目，**一条一条来**：

1. 用浏览器（agent-browser / playwright）打开岗位链接，**先截图让用户核对岗位信息**（公司、岗位、薪资）。
2. **自动填表**：姓名、电话、邮箱、上传对应简历文件、粘贴求职信（无求职信则跳过）。各平台填法见 `references/job-sources.md` 的“填写要点”。
3. **提交前必须停下确认**：向用户展示「公司 + 岗位 + 用的哪份简历 + 链接」，等用户回“投 / 发 / go”再点提交。
4. 用户确认后提交 → 把该队列条目状态置“已发”，并 `track_applications.py update --status "已投递" --applied_at now`。
5. **守规则**：不绕验证码；同一平台相邻两次投递间隔 ≥ 几分钟（或按平台限流）；不在同一公司重复投多个相似岗刷量。
6. 队列跑完，输出“已发 N / 跳过 M”汇总，并提示哪些待用户补材料。

> 若用户坚持“全自动无确认群发”：**拒绝**。说明风险（账号封禁、平台 ToS 违规、信息造假），改为“批量填表 + 我逐条确认”模式。这是底线，不可让步。

### 6. 追踪（Track）

```bash
python scripts/track_applications.py add --company "X" --role "Y" --source "Boss直聘" \
  --url "..." --match 0.7 --status "已投递"
python scripts/track_applications.py list --status "已投递"
python scripts/track_applications.py stats
```

数据存 `applications.json`，可后续用表格技能转成 Excel 看板复盘。

## 省钱技巧（直接回应“token 太贵”）

1. **初筛永远走规则**（`keyword_screen.py`），0 token 砍掉 60%+ 不相关岗。
2. **能不定制就不定制**：直接发基底简历最省；只对“很想进”的岗精修。
3. **定制只改 bullet，不重写全文**；基底简历复用，省上下文。
4. **批量会话**：一次收 10–20 个 JD，统一初筛 + 统一发，摊薄系统提示词。
5. **模型分级**：screen=规则，tailor=强模型；别拿强模型做筛选。
6. **dry-run**：先只跑初筛 + 列队列，肉眼挑要投的，再对少数几个精修，避免无谓消耗。

## 资源

### references/
- `profile-schema.md` — `resume_profile.json` 字段说明。
- `profile-example.md` — 通用求职偏好示例（不限定行业）。
- `job-sources.md` — 常见招聘站点的 JD 抽取要点与各平台**填写/投递**要点。

### scripts/
- `keyword_screen.py` — 规则化匹配打分（无模型依赖，省 token）。
- `build_send_queue.py` — 生成投递队列（岗位↔简历↔求职信匹配）。
- `track_applications.py` — 投递进度 CRUD + 统计。

## 铁律（Hard Rules）

1. **不造假**：经历、证书、数据只能基于真实简历，缺的写“可学”，不虚构。
2. **提交必确认**：任何真实投递前必须人工拍板，不静默群发。
3. **守规则**：不绕验证码、不违反招聘平台 ToS、不刷量。
4. **按队列发**：发送严格依据 `send_queue.json`，不临时夹带未核对岗位。
5. **简历本地留痕**：定制稿存 `tailored/`，基底简历与 profile 仅存本地，不外传。
6. **先筛后定制（如用）**：没过初筛的岗不调强模型，除非用户明确要求全发。
