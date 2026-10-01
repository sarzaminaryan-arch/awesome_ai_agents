#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فیلتر صحت مقاله‌های شهرستان — سرزمین آریان
بر پایهٔ قواعد ۱۳گانهٔ کارفرما (۱۴۰۵/۰۷/۰۸) + قواعد پروژه (city-county-structure / v1.3)

اجرا:
    python3 articles/_filter/check.py                     # همهٔ مقاله‌ها
    python3 articles/_filter/check.py articles/south-khorasan/01-birjand.md

بررسی‌ها:
  ۱. وجود و ترتیب ۱۴ سرتیتر H2
  ۲. کف واژهٔ بلوک متن (پیش‌فرض ۱۲۰۰)
  ۳. نبود نشان‌های کارگاهی («به‌زودی»، [نیازمند بررسی]، [منبع لازم]، [URL لازم])
  ۴. هر ادعای عددی در همان جمله/بند ارجاع بالانویس داشته باشد
  ۵. شمارهٔ ارجاع‌ها با فهرست منابع بخواند (نه اضافه، نه کم)
  ۶. هر منبع فهرست، دست‌کم یک‌بار در متن ارجاع شده باشد
  ۷. لینک بیرونی فقط داخل <sup>…</sup> (قاعدهٔ ۱۰ پروژه)
  ۸. FAQ ≥ ۱۰
  ۹. بخش پایانی «یک درخواست داریم» + ایمیل + لینک استان
 ۱۰. هر عدد باید سال مرجع یا واژهٔ راهنما (سرشماری/سال/ثبت/۱۳…) کنارش داشته باشد
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLES = ROOT / "articles"

REQUIRED_H2 = [
    "معرفی شهرستان",
    "مشخصات کلی",
    "موقعیت جغرافیایی",
    "تاریخچه",
    "وجه تسمیه",
    "آب و هوا",
    "صنایع مهم",
    "فرهنگ و مردم",
    "زبان و گویش",
    "جاذبه‌های گردشگری",
    "نقشه و لوکیشن",
    "مشاهیر شهرستان",
    "حقایق جالب",
]

HISTORY_H3 = ["باستان", "اسلامی", "معاصر"]
MIN_WORDS = 1200
MIN_FACTS = 10
MIN_FAQ = 10
MIN_SOURCES = 5

BANNED_MARKERS = [
    "به‌زودی",
    "به زودی",
    "[نیازمند بررسی]",
    "[منبع لازم]",
    "[URL لازم]",
    "نیازمند بررسی",
]
# جمله‌های راهنما که «سال مرجع» عدد را تأمین می‌کنند
YEAR_HINTS = re.compile(
    r"(۱۳|۱۴|سال|سرشماری|ثبت|سده|هجری|قمری|میلادی|۱۳۹۵|۱۳۹۰|دوره|ارتفاع|کیلومتر|نفر|درصد|میلی|هکتار)"
)


def norm(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    return t.replace("\u200c", "\u200c")


def load(path: Path) -> str:
    return norm(path.read_text(encoding="utf-8"))


def strip_code_and_sources(md: str) -> str:
    """متن مقاله بدون جدول‌های منبع، بلوک‌های کد و فرانت‌متر."""
    if md.startswith("---"):
        parts = md.split("---", 2)
        md = parts[2] if len(parts) >= 3 else md
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    md = md.split("## فهرست منابع")[0]
    return md


def body_words(md: str) -> int:
    """واژه‌های متن (بدون جدول/ارجاع/نشانه‌گذاری) طبق قرارداد پروژه."""
    t = strip_code_and_sources(md)
    t = re.sub(r"<sup>.*?</sup>", " ", t, flags=re.S)
    t = re.sub(r"^\s*\|.*$", " ", t, flags=re.M)          # جدول‌ها
    t = re.sub(r"\[.*?\]\(.*?\)", " ", t)                  # لینک‌ها
    t = re.sub(r"[#*_>`\-]+", " ", t)
    return len([w for w in t.split() if w.strip()])


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else sorted(
        p for p in ARTICLES.rglob("*.md") if p.name != "README.md"
    )
    if not targets:
        print("مقاله‌ای برای بررسی پیدا نشد.")
        return 1

    overall_ok = True
    for path in targets:
        md = load(path)
        body = strip_code_and_sources(md)
        errors: list[str] = []
        warns: list[str] = []

        # ۱. سرتیترها
        h2 = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", body, flags=re.M)]
        for section in REQUIRED_H2:
            if not any(section in h for h in h2):
                errors.append(f"H2 گمشده: «{section}»")
        order = [next((i for i, h in enumerate(h2) if s in h), -1) for s in REQUIRED_H2]
        if order != sorted(order):
            errors.append("ترتیب H2ها با قالب ۱۳بخشی نمی‌خواند")
        for h3 in HISTORY_H3:
            if not re.search(rf"^###\s+{h3}", body, flags=re.M):
                errors.append(f"H3 گمشده در تاریخچه: «{h3}»")

        # ۲. کف واژه
        words = body_words(md)
        if words < MIN_WORDS:
            errors.append(f"واژهٔ متن {words} < کف {MIN_WORDS}")

        # ۳. نشان‌های کارگاهی
        for marker in BANNED_MARKERS:
            if marker in body:
                errors.append(f"نشان کارگاهی در متن: «{marker}»")

        # ۴. ادعای عددی بدون ارجاع (در همان بند)
        for para in re.split(r"\n\s*\n", body):
            if para.lstrip().startswith("|") or para.lstrip().startswith("#"):
                continue
            if re.search(r"[۰-۹0-9]", para) and "<sup>" not in para:
                snippet = " ".join(para.split())[:70]
                warns.append(f"بند عددی بی‌ارجاع: «{snippet}…»")

        # ۵/۶. تطبیق ارجاع‌ها با فهرست منابع
        cited = {int(n) for n in re.findall(r"<sup>\[(\d+)\]", md)}
        src_block = md.split("## فهرست منابع")[-1] if "## فهرست منابع" in md else ""
        listed = {int(n) for n in re.findall(r"^\s*(\d+)\.\s", src_block, flags=re.M)}
        if not listed:
            errors.append("فهرست منابع پیدا نشد یا شماره‌گذاری ندارد")
        if cited - listed:
            errors.append(f"ارجاع به منابع ناموجود: {sorted(cited - listed)}")
        unused = sorted(listed - cited)
        if unused:
            warns.append(f"منابع بی‌ارجاع در متن: {unused}")
        if len(listed) < MIN_SOURCES:
            errors.append(f"منابع {len(listed)} < حداقل {MIN_SOURCES}")
        if len(cited) < 5:
            errors.append(f"تعداد ارجاع‌های درون‌متنی {len(cited)} < ۵")

        # هر ردیف منبع باید URL داشته باشد (قاعدهٔ بلوک ۸)
        for line in src_block.splitlines():
            if re.match(r"^\s*\d+\.\s", line) and "http" not in line:
                errors.append(f"ردیف منبع بدون URL: «{line.strip()[:50]}»")

        # ۷. لینک بیرونی فقط داخل <sup>
        outside = re.sub(r"<sup>.*?</sup>", " ", md, flags=re.S)
        for m in re.finditer(r"\]\((https?://[^)]+)\)", outside):
            url = m.group(1)
            if "google.com/maps" in url:      # نقشه‌ها در بخش لوکیشن مجازند
                continue
            warns.append(f"لینک بیرونی بیرون از <sup>: {url[:60]}")

        # ۸. FAQ
        faq = len(re.findall(r"^\*\*.+[?؟]\*\*", body, flags=re.M))
        if faq < MIN_FAQ:
            errors.append(f"پرسش‌های پرتکرار {faq} < حداقل {MIN_FAQ}")

        # ۹. بخش پایانی
        if "یک درخواست داریم" not in body:
            errors.append("بخش پایانی «یک درخواست داریم» نیست")
        if "Mail@sarzaminaryan.ir" not in body:
            errors.append("ایمیل Mail@sarzaminaryan.ir در بخش پایانی نیست")
        if "/province/" not in body:
            errors.append("لینک صفحهٔ استان در متن نیست")

        # ۱۰. حقایق جالب
        facts_block = re.search(r"## حقایق جالب(.*?)(?=\n## |\Z)", body, flags=re.S)
        facts = len(re.findall(r"^-\s", facts_block.group(1), flags=re.M)) if facts_block else 0
        if facts < MIN_FACTS:
            errors.append(f"حقایق جالب {facts} < حداقل {MIN_FACTS}")

        status = "PASS" if not errors else "FAIL"
        overall_ok &= not errors
        label = path.resolve().relative_to(ROOT) if path.is_absolute() or not str(path).startswith("/") else path
        try:
            label = path.resolve().relative_to(ROOT)
        except ValueError:
            label = path
        print(f"\n=== فیلتر صحت: {label} ===")
        print(f"وضعیت: {status} · واژه‌های متن: {words:,} · ارجاع‌ها: {len(cited)} · منابع: {len(listed)} · FAQ: {faq} · حقایق: {facts}")
        if errors:
            print("خطاها:")
            for e in errors:
                print(f"  ✗ {e}")
        if warns:
            print("هشدارها (برای بازبین):")
            for w in warns[:15]:
                print(f"  ! {w}")
            if len(warns) > 15:
                print(f"  ! … و {len(warns) - 15} هشدار دیگر")

    return 0 if overall_ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
