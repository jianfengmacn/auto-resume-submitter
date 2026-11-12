# resume_profile.json 字段说明

建档时把这份 JSON 存到工作区（默认 `resume_profile.json`）。结构如下，所有字段都可空，但 `resume_text` 与 `targets` 建议必填。

```json
{
  "basics": {
    "name": "张三",
    "phone": "138****0000",
    "email": "zhangsan@example.com",
    "city": "上海",
    "years_exp": 12
  },
  "resume_text": "粘贴你的完整简历正文……包含工作经历、项目、技能、证书、教育。\n建议保留量化成果，例如：主导降本 8%、搭建某报表体系、管 5 人团队。",
  "targets": {
    "roles": ["财务分析", "会计主管", "FP&A"],
    "locations": ["上海", "远程", "长三角"],
    "industries": ["互联网", "制造业", "新能源"],
    "salary_min": 15000,
    "exclude_keywords": ["销售", "驻外", "996", "纯英文环境"],
    "required_skills": ["CPA", "SAP", "Excel", "用友", "财务报表"]
  },
  "models": {
    "screen": "rule",
    "tailor": "strong"
  }
}
```

字段含义
- `basics`：基础信息，投递填表时用。
- `resume_text`：原始简历全文，定制时的“真相来源”，**只能基于此改写，不得虚构**。
- `targets.roles / locations / industries`：匹配打分与初筛的契合维度。
- `targets.salary_min`：JD 薪资低于此值直接降权/淘汰（解析到时才生效）。
- `targets.exclude_keywords`：命中即 0 分，用于砍掉不想投的岗。
- `targets.required_skills`：硬性要求覆盖率，命中越多分越高（如证书、ERP、语言）。
- `models.screen`：`rule` 表示初筛走纯规则（推荐，0 token）；也可填便宜模型名做语义匹配。
- `models.tailor`：定制阶段用的强模型。
