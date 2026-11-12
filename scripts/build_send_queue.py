#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_send_queue.py — 生成“投递队列”（自动发简历的核心调度文件）

把 jobs/ 下的岗位，与 tailored/ 下按 id 匹配的定制简历/求职信配对，
没有定制稿则回退到 profile 的基底简历/求职信，输出 send_queue.json + 可读清单。
发送阶段（agent）严格按此队列逐条执行，提交前逐条人工确认。

用法:
  python build_send_queue.py --resume resume_profile.json --jobs jobs/ --tailored tailored/
  python build_send_queue.py --resume resume_profile.json --jobs jobs/ --tailored tailored/ --out send_queue.json
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


def parse_job(md_path):
    txt = open(md_path, "r", encoding="utf-8").read()
    field = lambda label: (re.search(r"%s[：:]\s*(.+)" % label, txt) or [None, ""])[1].strip()
    return {
        "company": field("公司"),
        "role": field("岗位"),
        "salary": field("薪资"),
        "location": field("地点"),
        "url": field("链接"),
    }


def resolve_base(profile, cwd):
    """返回 (base_resume_path, base_cover_path)。优先用 resume_file，否则把 resume_text 落盘。"""
    base_resume = profile.get("resume_file") or ""
    if not base_resume and profile.get("resume_text"):
        base_resume = os.path.join(cwd, "base_resume.md")
        with open(base_resume, "w", encoding="utf-8") as f:
            f.write(profile["resume_text"])
    base_cover = profile.get("cover_file") or ""
    if not base_cover and profile.get("cover_text"):
        base_cover = os.path.join(cwd, "base_cover.md")
        with open(base_cover, "w", encoding="utf-8") as f:
            f.write(profile["cover_text"])
    return base_resume, base_cover


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", required=True)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--tailored", default="tailored")
    ap.add_argument("--out", default="send_queue.json")
    args = ap.parse_args()

    profile = load_json(args.resume)
    cwd = os.getcwd()
    base_resume, base_cover = resolve_base(profile, cwd)

    job_files = sorted(glob.glob(os.path.join(args.jobs, "*.md")))
    if not job_files:
        print("未找到 jobs/*.md，请先收岗。", file=sys.stderr)
        sys.exit(1)

    queue = []
    for jf in job_files:
        m = re.search(r"job_(\d+)", os.path.basename(jf))
        jid = m.group(1) if m else os.path.splitext(os.path.basename(jf))[0]
        meta = parse_job(jf)

        t_resume = os.path.join(args.tailored, "job_%s_resume.md" % jid)
        t_cover = os.path.join(args.tailored, "job_%s_cover.md" % jid)
        resume_file = t_resume if os.path.exists(t_resume) else base_resume
        cover_file = t_cover if os.path.exists(t_cover) else base_cover

        queue.append({
            "id": jid,
            "company": meta.get("company") or "(未知公司)",
            "role": meta.get("role") or "(未知岗位)",
            "url": meta.get("url") or "",
            "salary": meta.get("salary") or "",
            "location": meta.get("location") or "",
            "resume_file": resume_file,
            "cover_file": cover_file or "",
            "status": "待发",
            "note": "",
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"items": queue}, f, ensure_ascii=False, indent=2)

    print("\n%s  %-14s %-16s %s" % ("#", "公司", "岗位", "简历"))
    print("-" * 64)
    for it in queue:
        tag = "定制" if it["resume_file"].endswith("resume.md") and "job_" in os.path.basename(it["resume_file"]) else "基底"
        print("%-3s %-14s %-16s %s" % (it["id"], it["company"][:14], it["role"][:16], tag))
    print("-" * 64)
    print("已生成 %s，共 %d 条待发。发送阶段将逐条人工确认。" % (args.out, len(queue)))


if __name__ == "__main__":
    main()
