#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بسته‌ساز خروجی مقاله‌های شهرستان‌ها برای سایت «سرزمین آریان».

خروجی‌ها:
  content/cities/<slug>.md        نسخهٔ خام مقاله (کپی از articles/<province>/)
  content/cities/<slug>.html      نسخهٔ HTML آمادهٔ ورود به وردپرس
  data/counties.json              فهرست ماشین‌خوان شهرستان‌ها (هر ردیف: title, slug, province, province_name, ...)
  data/import-payload.json        بستهٔ کامل (شامل متن HTML) برای ایمپورترهای مستقل
  downloads/<province>-counties.zip   بستهٔ نهایی (متن + داده + تصاویر + پلاگین)

دستورها:
  python3 scripts/import_counties.py check --province south-khorasan
  python3 scripts/import_counties.py build --province south-khorasan [--zip]
"""

import argparse
import json
import os
import re
import sys
import zipfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2html import convert as md_to_html  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
CONTENT_CITIES = os.path.join(ROOT, "content", "cities")
DATA = os.path.join(ROOT, "data")
DOWNLOADS = os.path.join(ROOT, "downloads")

PROVINCE_NAMES = {
    "south-khorasan": "خراسان جنوبی",
    "razavi-khorasan": "خراسان رضوی",
    "north-khorasan": "خراسان شمالی",
}

MIN_WORDS = 1200
MIN_SOURCES = 5
MIN_FAQ = 10
MIN_FACTS = 10


def slug_of(filename: str) -> str:
    return re.sub(r"^\d+-", "", os.path.splitext(os.path.basename(filename))[0])


def parse_front_matter(text: str):
    meta = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    block = text[3:end].strip("\n")
    for line in block.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[end + 4 :]


def parse_kw(raw: str):
    if not raw:
        return []
    raw = raw.strip().strip("[]")
    return [p.strip() for p in raw.split(",") if p.strip()]


def count_section(body: str, heading: str):
    """شمارش آیتم‌های یک بخش (جدول/فهرست) تا سرتیتر بعدی."""
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", body, flags=re.M)
    if not m:
        return 0, ""
    start = m.end()
    nxt = re.search(r"^##\s+", body[start:], flags=re.M)
    section = body[start : start + nxt.start()] if nxt else body[start:]
    return section.count("\n"), section


def collect_records(province: str):
    src_dir = os.path.join(ARTICLES, province)
    records = []
    for name in sorted(os.listdir(src_dir)):
        if not name.endswith(".md") or name == "README.md":
            continue
        path = os.path.join(src_dir, name)
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        meta, body = parse_front_matter(raw)

        title_m = re.search(r"^#\s+(.+)$", body, flags=re.M)
        title = title_m.group(1).strip() if title_m else meta.get("county", name)

        # آمار
        words = len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", body)))
        src_rows = len(re.findall(r"^\d+\.\s+", body, flags=re.M))
        faq_sec = re.search(r"^##\s+پرسش‌های پرتکرار\s*$", body, flags=re.M)
        faq = 0
        if faq_sec:
            nxt = re.search(r"^##\s+", body[faq_sec.end() :], flags=re.M)
            sec = body[faq_sec.end() : faq_sec.end() + nxt.start()] if nxt else body[faq_sec.end() :]
            faq = len(re.findall(r"^\*\*.+؟", sec, flags=re.M))
        facts_sec = re.search(r"^##\s+حقایق جالب\s*$", body, flags=re.M)
        facts = 0
        if facts_sec:
            nxt = re.search(r"^##\s+", body[facts_sec.end() :], flags=re.M)
            sec = body[facts_sec.end() : facts_sec.end() + nxt.start()] if nxt else body[facts_sec.end() :]
            facts = len(re.findall(r"^-\s+", sec, flags=re.M))

        slug = meta.get("slug") or slug_of(name)
        order = int(re.sub(r"\D", "", name.split("-")[0]) or 0)
        image = meta.get("image", f"assets/featured/counties/{province}/{slug}.webp")

        records.append(
            {
                "title": title,
                "slug": slug,
                "province": province,
                "province_name": meta.get("province", PROVINCE_NAMES.get(province, province)),
                "county": meta.get("county", ""),
                "order": order,
                "file": f"content/cities/{slug}.md",
                "html_file": f"content/cities/{slug}.html",
                "image": image,
                "image_basename": f"images/{slug}.webp",
                "image_alt": meta.get("image_alt", ""),
                "focus_keywords": parse_kw(meta.get("focus_keywords", "")),
                "words": words,
                "sources": src_rows,
                "faq": faq,
                "facts": facts,
                "_raw": raw,
                "_body": body,
            }
        )
    records.sort(key=lambda r: r["order"])
    return records


def check(records, province, *, verbose=True):
    problems = []
    for r in records:
        if r["words"] < MIN_WORDS:
            problems.append(f"{r['slug']}: واژه‌ها {r['words']} < {MIN_WORDS}")
        if r["sources"] < MIN_SOURCES:
            problems.append(f"{r['slug']}: منابع {r['sources']} < {MIN_SOURCES}")
        if r["faq"] < MIN_FAQ:
            problems.append(f"{r['slug']}: FAQ {r['faq']} < {MIN_FAQ}")
        if r["facts"] < MIN_FACTS:
            problems.append(f"{r['slug']}: حقایق {r['facts']} < {MIN_FACTS}")
        if "Mail@sarzaminaryan.ir" not in r["_body"]:
            problems.append(f"{r['slug']}: ایمیل درخواست پایانی یافت نشد")
        if "google.com/maps" not in r["_body"]:
            problems.append(f"{r['slug']}: ردیف نقشهٔ گوگل‌مپ یافت نشد")
        img_src = os.path.join(ARTICLES, province, "images", f"{r['slug']}.webp")
        if not os.path.exists(img_src):
            problems.append(f"{r['slug']}: تصویر شاخص {img_src} موجود نیست")

    if verbose:
        print(f"=== بازبینی بسته — {province} — {len(records)} شهرستان ===")
        for r in records:
            print(
                f"  {r['order']:>2}. {r['slug']:<12} {r['words']:>5} واژه | منابع {r['sources']:>2} "
                f"| FAQ {r['faq']:>2} | حقایق {r['facts']:>2} | {r['title'][:46]}"
            )
        if problems:
            print("\nمشکل‌ها:")
            for p in problems:
                print("  ✗", p)
        else:
            print("\nوضعیت: OK — بستهٔ ورود آماده است ✅")
    return problems


def build(province: str, make_zip: bool):
    records = collect_records(province)
    problems = check(records, province)
    if problems:
        print("توقف ساخت بسته به‌سبب مشکل‌های بالا.")
        return 1

    os.makedirs(CONTENT_CITIES, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(DOWNLOADS, exist_ok=True)

    payload = []
    for r in records:
        raw_path = os.path.join(CONTENT_CITIES, f"{r['slug']}.md")
        html_path = os.path.join(CONTENT_CITIES, f"{r['slug']}.html")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(r["_raw"])
        html = md_to_html(r["_raw"])
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        # چکیده: نخستین پاراگراف متن اصلی
        body_wo_head = re.sub(r"^#\s+.+$", "", r["_body"], count=1, flags=re.M)
        first_p = re.search(r"^(\*\*[^\n]+|[^#\-\|\n][^\n]{40,})$", body_wo_head.strip(), flags=re.M)
        excerpt = re.sub(r"<[^>]+>", "", md_to_html(first_p.group(1))) if first_p else ""
        excerpt = re.sub(r"\s+", " ", excerpt).strip()

        entry = {k: v for k, v in r.items() if not k.startswith("_")}
        entry["excerpt"] = excerpt
        payload.append({"meta": entry, "content_html": html, "content_markdown": r["_body"]})

        r["_html"] = html

    counties_json = {
        "province": province,
        "province_name": PROVINCE_NAMES.get(province, province),
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "count": len(records),
        "counties": [{k: v for k, v in r.items() if not k.startswith("_")} for r in records],
    }
    with open(os.path.join(DATA, "counties.json"), "w", encoding="utf-8") as f:
        json.dump(counties_json, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA, "import-payload.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"✓ content/cities/ — {len(records)} فایل MD + {len(records)} فایل HTML")
    print(f"✓ data/counties.json — {len(records)} ردیف")
    print(f"✓ data/import-payload.json — بستهٔ کامل")

    if make_zip:
        zip_name = f"{province}-counties.zip"
        zip_path = os.path.join(DOWNLOADS, zip_name)
        src_images = os.path.join(ARTICLES, province, "images")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            readme = os.path.join(ROOT, "downloads", "BUNDLE-README.txt")
            if os.path.exists(readme):
                z.write(readme, "south-khorasan-counties/README.txt")
            z.write(os.path.join(DATA, "counties.json"), "south-khorasan-counties/data/counties.json")
            z.write(os.path.join(DATA, "import-payload.json"), "south-khorasan-counties/data/import-payload.json")
            for r in records:
                base = f"south-khorasan-counties/content/cities/{r['slug']}"
                z.write(os.path.join(CONTENT_CITIES, f"{r['slug']}.md"), base + ".md")
                z.write(os.path.join(CONTENT_CITIES, f"{r['slug']}.html"), base + ".html")
                z.write(os.path.join(src_images, f"{r['slug']}.webp"), f"south-khorasan-counties/images/{r['slug']}.webp")
            plugin = os.path.join(ROOT, "wordpress", "sarzamin-counties-importer.php")
            if os.path.exists(plugin):
                z.write(plugin, "south-khorasan-counties/wordpress/sarzamin-counties-importer.php")
        size = os.path.getsize(zip_path)
        print(f"✓ downloads/{zip_name} — {size/1024:.0f} KB")
    return 0


def main():
    ap = argparse.ArgumentParser(description="بسته‌ساز مقاله‌های شهرستان‌ها")
    ap.add_argument("command", choices=["check", "build"])
    ap.add_argument("--province", default="south-khorasan")
    ap.add_argument("--zip", action="store_true", help="ساخت بستهٔ zip در downloads/")
    args = ap.parse_args()

    records = collect_records(args.province)
    if args.command == "check":
        return 1 if check(records, args.province) else 0
    return build(args.province, args.zip)


if __name__ == "__main__":
    sys.exit(main())
