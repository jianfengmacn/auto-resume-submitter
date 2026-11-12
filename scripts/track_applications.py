#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
track_applications.py — 投递进度追踪（本地 JSON，无外部依赖）

子命令:
  add      记录一条投递
  list     列出全部（可按 --status 过滤）
  update   更新某条状态
  stats    统计各状态分布与平均匹配分

用法:
  python track_applications.py add --company "甲公司" --role "财务分析" \
      --source "Boss直聘" --url "https://..." --match 0.72 \
      --status "已定制待投递" --tailoring "tailored/job_03_resume.md"

  python track_applications.py list --status "已投递"
  python track_applications.py update --id 3 --status "已投递" --applied_at now
  python track_applications.py stats

数据存于工作区 applications.json。
"""
import argparse
import datetime
import json
import os
import sys


def store_path():
    return os.path.join(os.getcwd(), "applications.json")


def load():
    p = store_path()
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": []}


def save(data):
    with open(store_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def cmd_add(args):
    data = load()
    nxt = max([it.get("id", 0) for it in data["items"]] + [0]) + 1
    item = {
        "id": nxt,
        "company": args.company,
        "role": args.role,
        "source": args.source or "",
        "url": args.url or "",
        "match": args.match,
        "status": args.status or "新建",
        "tailoring": args.tailoring or "",
        "applied_at": args.applied_at or "",
        "updated_at": now(),
        "notes": args.notes or "",
    }
    data["items"].append(item)
    save(data)
    print("已记录 #%d %s - %s" % (nxt, args.company, args.role))


def cmd_list(args):
    data = load()
    items = data["items"]
    if args.status:
        items = [it for it in items if it.get("status") == args.status]
    if not items:
        print("无记录。")
        return
    print("\n%-4s %-16s %-14s %-10s %-6s %s" % ("ID", "公司", "岗位", "来源", "匹配", "状态"))
    print("-" * 78)
    for it in items:
        print("%-4d %-16s %-14s %-10s %-6s %s" % (
            it["id"], str(it.get("company", ""))[:16],
            str(it.get("role", ""))[:14], str(it.get("source", ""))[:10],
            it.get("match", ""), it.get("status", "")))
    print("-" * 78)
    print("共 %d 条。" % len(items))


def cmd_update(args):
    data = load()
    found = False
    for it in data["items"]:
        if it["id"] == args.id:
            if args.status:
                it["status"] = args.status
            if args.applied_at == "now":
                it["applied_at"] = now()
            elif args.applied_at:
                it["applied_at"] = args.applied_at
            if args.notes:
                it["notes"] = args.notes
            it["updated_at"] = now()
            found = True
            break
    if not found:
        print("未找到 id=%s" % args.id, file=sys.stderr)
        sys.exit(1)
    save(data)
    print("已更新 #%d" % args.id)


def cmd_stats(args):
    data = load()
    items = data["items"]
    if not items:
        print("无记录。")
        return
    from collections import Counter
    c = Counter(it.get("status", "未知") for it in items)
    avg = sum(float(it.get("match") or 0) for it in items) / len(items)
    print("\n状态分布:")
    for k, v in c.most_common():
        print("  %-16s %d" % (k, v))
    print("平均匹配分: %.3f" % avg)
    print("总投递数: %d" % len(items))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--company", required=True)
    a.add_argument("--role", required=True)
    a.add_argument("--source")
    a.add_argument("--url")
    a.add_argument("--match", type=float, default=0.0)
    a.add_argument("--status")
    a.add_argument("--tailoring")
    a.add_argument("--applied_at")
    a.add_argument("--notes")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list")
    l.add_argument("--status")
    l.set_defaults(func=cmd_list)

    u = sub.add_parser("update")
    u.add_argument("--id", type=int, required=True)
    u.add_argument("--status")
    u.add_argument("--applied_at")
    u.add_argument("--notes")
    u.set_defaults(func=cmd_update)

    s = sub.add_parser("stats")
    s.set_defaults(func=cmd_stats)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
