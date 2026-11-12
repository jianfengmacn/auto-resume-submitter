# 通用求职偏好示例（不限定行业）

把下面的 `targets` 改成你自己的即可。`resume_text` 放你的真实简历正文；
如果简历是文件，用 `resume_file` 指路径更省事。

```json
{
  "basics": {
    "name": "（你的名字）",
    "phone": "（手机）",
    "email": "（邮箱）",
    "city": "（所在城市）",
    "years_exp": 10
  },
  "resume_text": "（粘贴真实简历正文：工作经历、项目、技能、证书、教育。保留量化成果，例如：主导 X 项目、降本 Y%、带 N 人团队。）",
  "resume_file": "",
  "cover_text": "（可选：一段通用求职信，或留空，发送时不带求职信。）",
  "targets": {
    "roles": ["（目标岗位1）", "（目标岗位2）"],
    "locations": ["（城市/远程）"],
    "industries": ["（行业1）", "（行业2）"],
    "salary_min": 12000,
    "exclude_keywords": ["销售", "驻外", "996"],
    "required_skills": ["（硬技能/证书1）", "（硬技能/证书2）"]
  },
  "models": {
    "screen": "rule",
    "tailor": "strong"
  }
}
```

字段说明见 `profile-schema.md`。要点：
- `salary_min`：JD 薪资低于此值会直接降权/淘汰（解析到时才生效）。
- `exclude_keywords`：命中即 0 分，用来砍掉不想投的岗（如纯销售、驻外）。
- `required_skills`：硬性要求覆盖率，命中越多分越高。
- 不想初筛就全发：把 `keyword_screen.py` 的 `--threshold` 设成 0，或直接跳过第 2 步。
- 想直接群发现成简历：不写 `tailored/`，`build_send_queue.py` 会自动回退到基底简历。
