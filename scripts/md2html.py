#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مبدل سبک Markdown به HTML برای مقاله‌های شهرستان‌ها (سرزمین آریان).

پشتیبانی: سرتیترها، پاراگراف، فهرست نقطه‌ای و شماره‌دار، جدول GFM، نقل‌قول،
خط جداکننده، پررنگ، ایتالیک و پیوندها — به‌همراه عبور بدون تغییر HTML خام
(مانند بالانویس ارجاع‌ها: <sup>[۱](url)</sup>).

Backlog: کدبلاک و تصویر در مقاله‌ها استفاده نشده است.
"""

import re

# لینک مارک‌داون با پشتیبانی از یک سطح پرانتز تودرتو در URL
LINK_RE = re.compile(r"\[([^\]\n]+)\]\(((?:[^()\s]|\([^()]*\))*)\)")
BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
TABLE_ROW_RE = re.compile(r"^\|.*\|$")
TABLE_SEP_RE = re.compile(r"^\|[\s:\-|]+\|$")
UL_RE = re.compile(r"^[-*]\s+")
OL_RE = re.compile(r"^\d+\.\s+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def inline(text: str) -> str:
    """تبدیل عناصر درون‌خطی (بدون HTML-escape؛ محتوا مورد اعتماد است)."""
    text = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    return text


def _split_row(row: str):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def render_table(rows):
    body_rows = [r for r in rows if not TABLE_SEP_RE.match(r)]
    if not body_rows:
        return ""
    head, body = body_rows[0], body_rows[1:]
    parts = ["<table>", "<thead>", "<tr>"]
    parts += [f"<th>{inline(c)}</th>" for c in _split_row(head)]
    parts += ["</tr>", "</thead>", "<tbody>"]
    for row in body:
        parts.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in _split_row(row)) + "</tr>")
    parts += ["</tbody>", "</table>"]
    return "\n".join(parts)


def _is_block_start(s: str) -> bool:
    return bool(
        TABLE_ROW_RE.match(s)
        or UL_RE.match(s)
        or OL_RE.match(s)
        or HEADING_RE.match(s)
        or s.startswith("> ")
        or s == "---"
    )


def convert(md: str) -> str:
    """Markdown → HTML."""
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    # حذف Front matter
    if lines and lines[0].strip() == "---":
        i = 1
        while i < n and lines[i].strip() != "---":
            i += 1
        i += 1

    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        if s == "---":
            out.append("<hr />")
            i += 1
            continue

        m = HEADING_RE.match(s)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if TABLE_ROW_RE.match(s):
            tbl = []
            while i < n and TABLE_ROW_RE.match(lines[i].strip()):
                tbl.append(lines[i].strip())
                i += 1
            out.append(render_table(tbl))
            continue

        if UL_RE.match(s):
            items = []
            while i < n and UL_RE.match(lines[i].strip()):
                items.append(inline(UL_RE.sub("", lines[i].strip(), count=1).strip()))
                i += 1
            out.append("<ul>\n" + "\n".join(f"  <li>{it}</li>" for it in items) + "\n</ul>")
            continue

        if OL_RE.match(s):
            items = []
            while i < n and OL_RE.match(lines[i].strip()):
                items.append(inline(OL_RE.sub("", lines[i].strip(), count=1).strip()))
                i += 1
            out.append("<ol>\n" + "\n".join(f"  <li>{it}</li>" for it in items) + "\n</ol>")
            continue

        if s.startswith("> "):
            quote = []
            while i < n and lines[i].strip().startswith("> "):
                quote.append(inline(lines[i].strip()[2:].strip()))
                i += 1
            out.append("<blockquote>\n  <p>" + "<br />\n".join(quote) + "</p>\n</blockquote>")
            continue

        # پاراگراف (تا رسیدن به خط خالی یا شروع بلوک بعدی)
        para = [s]
        i += 1
        while i < n:
            ns = lines[i].strip()
            if not ns or _is_block_start(ns):
                break
            para.append(ns)
            i += 1
        out.append("<p>" + "<br />\n".join(inline(p) for p in para) + "</p>")

    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], encoding="utf-8") as f:
        sys.stdout.write(convert(f.read()))
