#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
keyword_screen.py — 规则化岗位初筛（无模型依赖，0 token）

根据 resume_profile.json 的简历与偏好，对 jobs/ 下每条 JD 打分，
输出得分表与淘汰原因。只有 >= threshold 的岗位才值得进入“定制”阶段，
从而把昂贵的强模型调用压到最低。

用法:
  python keyword_screen.py --resume resume_profile.json --jobs jobs/ --threshold 0.45
  python keyword_screen.py --resume resume_profile.json --job jobs/job_03.md
"""
import argparse
import glob
import json
import os
import re
import sys


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text):
    """CJK 整词 + 二元组 + ASCII 词，兼顾中英文匹配。"""
    text = (text or "").lower()
    chunks = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9\.\+\#]+", text)
    out = set()
    for c in chunks:
        out.add(c)
        if re.search(r"[\u4e00-\u9fff]", c) and len(c) > 1:
            for i in range(len(c) - 1):
                out.add(c[i:i + 2])
    return out


def parse_salary(jd_text):
    """粗略抽取 JD 薪资下限（k/K/万），返回月薪下限数字或 None。"""
    # 形如 15-25k / 15-25K / 1.5-2万
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*[kK]", jd_text)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*万", jd_text)
    if m:
        return float(m.group(1)) * 10000 / 12  # 年转月（粗）
    return None


def score_one(resume_text, jd_text, targets):
    reasons = []
    r_tokens = tokenize(resume_text)
    j_tokens = tokenize(jd_text)

    jd_kw = {t for t in j_tokens if len(t) >= 2}
    hit = jd_kw & r_tokens
    coverage = len(hit) / max(1, len(jd_kw))

    required = targets.get("required_skills", []) or []
    req_hit = [s for s in required if s.lower() in jd_text.lower()]
    req_cov = (len(req_hit) / max(1, len(required))) if required else 0.5

    # 地点 / 行业契合
    loc_fit = 1.0
    if targets.get("locations"):
        loc_fit = 1.0 if any(l.lower() in jd_text.lower() for l in targets["locations"]) else 0.0
        if loc_fit == 0.0:
            reasons.append("地点不匹配(偏好:" + "/".join(targets["locations"]) + ")")

    ind_fit = 1.0
    if targets.get("industries"):
        ind_fit = 1.0 if any(i.lower() in jd_text.lower() for i in targets["industries"]) else 0.3
        if ind_fit < 1.0:
            reasons.append("行业偏弱(偏好:" + "/".join(targets["industries"]) + ")")

    # 排除词 -> 直接 0 分
    exclude = targets.get("exclude_keywords", []) or []
    hit_excl = [e for e in exclude if e.lower() in jd_text.lower()]
    if hit_excl:
        return 0.0, ["命中排除词: " + ", ".join(hit_excl)]

    # 薪资下限
    sal_fit = 1.0
    sal_min = targets.get("salary_min")
    if sal_min:
        low = parse_salary(jd_text)
        if low is not None and low < sal_min:
            sal_fit = 0.0
            reasons.append("薪资低于下限(%d)" % sal_min)

    total = (0.45 * coverage + 0.30 * req_cov +
             0.10 * loc_fit + 0.10 * ind_fit + 0.05 * sal_fit)
    # 薪资不达标直接砍
    if sal_fit == 0.0:
        total = 0.0
    total = round(total, 3)

    if coverage < 0.15:
        reasons.append("关键词命中过低(%.0f%%)" % (coverage * 100))
    if required and len(req_hit) == 0:
        reasons.append("硬性技能0命中(" + "/".join(required) + ")")
    return total, reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", required=True, help="resume_profile.json 路径")
    ap.add_argument("--jobs", help="jobs 目录（批量）")
    ap.add_argument("--job", help="单个 JD 文件")
    ap.add_argument("--threshold", type=float, default=0.45)
    args = ap.parse_args()

    profile = load_json(args.resume)
    resume_text = profile.get("resume_text", "")
    targets = profile.get("targets", {})

    files = []
    if args.job:
        files = [args.job]
    elif args.jobs:
        files = sorted(glob.glob(os.path.join(args.jobs, "*.md")))
    if not files:
        print("未找到 JD 文件，请用 --jobs <dir> 或 --job <file>", file=sys.stderr)
        sys.exit(1)

    rows = []
    for fp in files:
        txt = open(fp, "r", encoding="utf-8").read()
        s, reasons = score_one(resume_text, txt, targets)
        rows.append((os.path.basename(fp), s, "; ".join(reasons) or "通过"))

    rows.sort(key=lambda x: x[1], reverse=True)
    print("\n%s  %-22s %-7s %s" % ("#", "JD", "得分", "结论"))
    print("-" * 70)
    for i, (name, s, note) in enumerate(rows, 1):
        flag = "★投" if s >= args.threshold else "淘汰"
        print("%-2d %-22s %-7.3f %s | %s" % (i, name[:22], s, flag, note))
    print("-" * 70)
    keep = [r for r in rows if r[1] >= args.threshold]
    print("共 %d 条，建议进入定制 %d 条（threshold=%.2f），其余跳过省 token。"
          % (len(rows), len(keep), args.threshold))


if __name__ == "__main__":
    main()
