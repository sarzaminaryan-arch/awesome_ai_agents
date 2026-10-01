#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ساخت افزونه‌های استاندارد وردپرس درون‌ریز شهرستان‌ها (سازگار با قالب فرزند سرزمین آریان و SA_City_Province_Importer):
  - wp-content/plugins/sa-city-importer-south-khorasan/  -> downloads/sa-city-importer-south-khorasan-v1.0.0.zip
  - wp-content/plugins/sa-city-importer-razavi-khorasan/ -> downloads/sa-city-importer-razavi-khorasan-v1.0.0.zip
"""

import datetime
import hashlib
import html
import json
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(ROOT, "articles")
PLUGINS_DIR = os.path.join(ROOT, "wp-content", "plugins")
DOWNLOADS_DIR = os.path.join(ROOT, "downloads")

PACKAGE_FORMAT = "1.0"
BUILT_DATE = datetime.date.today().isoformat()

PROVINCE_META = {
    "south-khorasan": {
        "slug": "south-khorasan",
        "name_fa": "استان خراسان جنوبی",
        "term_name": "خراسان جنوبی",
        "const_prefix": "SA_CI_SOUTH_KHORASAN",
        "func_prefix": "sa_ci_south_khorasan",
        "version": "1.0.0",
        "description_cities": "بیرجند، بشرویه، خوسف، درمیان، زیرکوه، سرایان، سربیشه، طبس، فردوس، قائنات، نهبندان، عشق‌آباد",
    },
    "razavi-khorasan": {
        "slug": "razavi-khorasan",
        "name_fa": "استان خراسان رضوی",
        "term_name": "خراسان رضوی",
        "const_prefix": "SA_CI_RAZAVI_KHORASAN",
        "func_prefix": "sa_ci_razavi_khorasan",
        "version": "1.0.0",
        "description_cities": "باخرز، بجستان، بردسکن، تایباد، تربت جام، تربت حیدریه",
    },
}

# مشخصات تکمیلی هر شهرستان (مختصات دقیق، نام انگلیسی، جمعیت، ارتفاع، دسترسی‌ها و نامک‌های قدیمی برای جلوگیری از ۴۰۴)
COUNTY_INFO = {
    # --- خراسان جنوبی (۱۲ شهرستان) ---
    "birjand": {
        "name_en": "Birjand County",
        "short_fa": "بیرجند",
        "population": "261324",
        "elevation": "1491",
        "lat": "32.8663",
        "lon": "59.2211",
        "access_air": "فرودگاه بین‌المللی شهید کاوه بیرجند در شمال شهر بیرجند با پروازهای روزانه به تهران و مشهد فعال است.",
        "access_rail": "فاقد ایستگاه راه‌آهن فعال؛ نزدیک‌ترین ایستگاه‌های ریلی در طبس، تربت حیدریه و مشهد قرار دارند و طرح راه‌آهن چابهار–زاهدان–بیرجند–مشهد در دست احداث است.",
        "access_road": "محورهای بزرگراهی بیرجند–قاین–مشهد (شمال)، بیرجند–نهبندان–زاهدان (جنوب) و بیرجند–خوسف–کرمان/یزد (غرب).",
        "legacy_slugs": [],
    },
    "boshruyeh": {
        "name_en": "Boshruyeh County",
        "short_fa": "بشرویه",
        "population": "26064",
        "elevation": "880",
        "lat": "33.8683",
        "lon": "57.4286",
        "access_air": "نزدیک‌ترین فرودگاه‌های فعال، فرودگاه طبس (در غرب) و فرودگاه بیرجند هستند.",
        "access_rail": "ایستگاه راه‌آهن بشرویه بر روی خط سراسری بافق–طبس–مشهد در مجاورت شهر بشرویه فعال است.",
        "access_road": "محورهای جاده‌ای بشرویه–فردوس (شرق) و بشرویه–طبس (جنوب غرب).",
        "legacy_slugs": ["beshrooyeh"],
    },
    "khusf": {
        "name_en": "Khusf County",
        "short_fa": "خوسف",
        "population": "27600",
        "elevation": "1300",
        "lat": "32.7939",
        "lon": "58.8894",
        "access_air": "فرودگاه بین‌المللی بیرجند در فاصلهٔ حدود ۳۶ کیلومتری شرق خوسف نزدیک‌ترین فرودگاه است.",
        "access_rail": "فاقد ایستگاه راه‌آهن؛ ارتباط از طریق شبکهٔ جاده‌ای با مرکز استان برقرار است.",
        "access_road": "بزرگراه بیرجند–خوسف–دیهوک (مسیر اصلی خراسان جنوبی به کرمان، یزد و اصفهان).",
        "legacy_slugs": ["khosf"],
    },
    "darmiyan": {
        "name_en": "Darmian County",
        "short_fa": "درمیان",
        "population": "53714",
        "elevation": "1450",
        "lat": "32.9128",
        "lon": "60.0258",
        "access_air": "فرودگاه بین‌المللی بیرجند در غرب شهرستان نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "فاقد ایستگاه راه‌آهن؛ تردد از طریق جادهٔ بیرجند–اسدیه انجام می‌شود.",
        "access_road": "محور جاده‌ای بیرجند–اسدیه–قهستان–طبس مسینا در شرق استان خراسان جنوبی.",
        "legacy_slugs": ["asadieh"],
    },
    "zirkuh": {
        "name_en": "Zirkuh County",
        "short_fa": "زیرکوه",
        "population": "40155",
        "elevation": "1330",
        "lat": "33.6050",
        "lon": "59.9936",
        "access_air": "فرودگاه بین‌المللی بیرجند در جنوب غرب شهرستان نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "فاقد ایستگاه راه‌آهن؛ دسترسی از طریق محورهای جاده‌ای قائن و بیرجند.",
        "access_road": "محورهای جاده‌ای قائن–حاجی‌آباد، بیرجند–آرین‌شهر–حاجی‌آباد و محور مرزی یزدان.",
        "legacy_slugs": ["hajjiabad"],
    },
    "sarayan": {
        "name_en": "Sarayan County",
        "short_fa": "سرایان",
        "population": "33312",
        "elevation": "1450",
        "lat": "33.8603",
        "lon": "58.5217",
        "access_air": "فرودگاه بین‌المللی بیرجند در جنوب شرق شهرستان نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "نزدیک‌ترین ایستگاه راه‌آهن در شهرستان بشرویه (غرب سرایان) بر خط طبس–مشهد قرار دارد.",
        "access_road": "محور جاده‌ای فردوس–سرایان–آیسک–قائن و محور سرایان–بیرجند.",
        "legacy_slugs": [],
    },
    "sarbisheh": {
        "name_en": "Sarbisheh County",
        "short_fa": "سربیشه",
        "population": "40959",
        "elevation": "1912",
        "lat": "32.5756",
        "lon": "59.7983",
        "access_air": "فرودگاه بین‌المللی بیرجند در فاصلهٔ حدود ۶۶ کیلومتری شمال غرب سربیشه قرار دارد.",
        "access_rail": "فاقد ایستگاه راه‌آهن؛ ارتباط از طریق بزرگراه بیرجند–زاهدان و مرز ماهیرود.",
        "access_road": "بزرگراه بیرجند–سربیشه–نهبندان (کریدور شمال به جنوب شرق کشور) و محور ترانزیتی سربیشه–درح–مرز ماهیرود.",
        "legacy_slugs": [],
    },
    "tabas": {
        "name_en": "Tabas County",
        "short_fa": "طبس",
        "population": "76352",
        "elevation": "690",
        "lat": "33.5959",
        "lon": "56.9244",
        "access_air": "فرودگاه طبس در شمال شهر طبس با پروازهای مسافری به تهران و مشهد فعال است.",
        "access_rail": "ایستگاه راه‌آهن طبس یکی از ایستگاه‌های محوری راه‌آهن شرق کشور در مسیر تهران/یزد/اصفهان به مشهد است.",
        "access_road": "چهارراه کویری مرکز ایران در تقاطع محورهای طبس–یزد، طبس–اصفهان (خور)، طبس–مشهد (دیهوک–فردوس) و طبس–بیرجند.",
        "legacy_slugs": [],
    },
    "ferdows": {
        "name_en": "Ferdows County",
        "short_fa": "فردوس",
        "population": "45523",
        "elevation": "1293",
        "lat": "34.0186",
        "lon": "58.1722",
        "access_air": "نزدیک‌ترین فرودگاه‌های فعال در بیرجند، طبس و مشهد قرار دارند.",
        "access_rail": "نزدیک‌ترین ایستگاه راه‌آهن، ایستگاه بشرویه در جنوب غرب فردوس بر خط ریلی طبس–مشهد است.",
        "access_road": "محور ترانزیتی مشهد–گناباد–فردوس–دیهوک (کریدور ارتباطی خراسان رضوی به یزد، اصفهان، کرمان و جنوب کشور) و محور فردوس–سرایان–بیرجند.",
        "legacy_slugs": [],
    },
    "qayenat": {
        "name_en": "Qaenat County",
        "short_fa": "قائنات",
        "population": "116181",
        "elevation": "1440",
        "lat": "33.7267",
        "lon": "59.1844",
        "access_air": "فرودگاه بین‌المللی بیرجند در فاصلهٔ حدود ۱۰۰ کیلومتری جنوب قائن نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "در مسیر طرح راه‌آهن بیرجند–قائن–گناباد–مشهد؛ در حال حاضر نزدیک‌ترین ایستگاه فعال در تربت حیدریه/بشرویه است.",
        "access_road": "بزرگراه مشهد–گناباد–قائن–بیرجند (شاهراه اصلی شمال به جنوب شرق ایران) و محور قائن–سرایان–فردوس.",
        "legacy_slugs": ["ghaen"],
    },
    "nehbandan": {
        "name_en": "Nehbandan County",
        "short_fa": "نهبندان",
        "population": "51449",
        "elevation": "1100",
        "lat": "31.5419",
        "lon": "60.0364",
        "access_air": "نزدیک‌ترین فرودگاه‌های فعال در بیرجند (شمال) و زابل/زاهدان (جنوب) قرار دارند.",
        "access_rail": "در مسیر طرح راه‌آهن زاهدان–نهبندان–بیرجند؛ دسترسی فعلی از طریق بزرگراه بیرجند–زاهدان است.",
        "access_road": "بزرگراه بیرجند–سربیشه–نهبندان–زاهدان و محور کویری نهبندان–شهداد–کرمان.",
        "legacy_slugs": [],
    },
    "eshqabad": {
        "name_en": "Eshqabad County",
        "short_fa": "عشق‌آباد",
        "population": "10255",
        "elevation": "790",
        "lat": "34.5453",
        "lon": "56.9267",
        "access_air": "فرودگاه طبس در جنوب شهرستان نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "خط راه‌آهن بافق–طبس–مشهد از قلمرو شهرستان عشق‌آباد می‌گذرد.",
        "access_road": "محور اصلی طبس–عشق‌آباد–بردسکن–مشهد (مسیر ترانزیتی زائران استان‌های مرکزی و جنوبی به مشهد).",
        "legacy_slugs": [],
    },
    # --- خراسان رضوی (۶ شهرستان دستهٔ ۱) ---
    "bakharz": {
        "name_en": "Bakharz County",
        "short_fa": "باخرز",
        "population": "54615",
        "elevation": "1280",
        "lat": "34.9919",
        "lon": "60.3172",
        "access_air": "فرودگاه بین‌المللی شهید هاشمی‌نژاد مشهد در شمال غرب نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "نزدیک‌ترین ایستگاه‌های راه‌آهن در تربت جام و تربت حیدریه قرار دارند.",
        "access_road": "محورهای جاده‌ای تایباد–باخرز–تربت حیدریه و باخرز–تربت جام در شرق استان خراسان رضوی.",
        "legacy_slugs": [],
    },
    "bajestan": {
        "name_en": "Bajestan County",
        "short_fa": "بجستان",
        "population": "31207",
        "elevation": "1250",
        "lat": "34.5164",
        "lon": "58.1844",
        "access_air": "فرودگاه شهدای گناباد و فرودگاه بین‌المللی مشهد نزدیک‌ترین فرودگاه‌های فعال هستند.",
        "access_rail": "ایستگاه راه‌آهن بجستان بر روی خط سراسری بافق–طبس–مشهد فعال است.",
        "access_road": "محورهای مواصلاتی فیض‌آباد–بجستان–فردوس و گناباد–بجستان–بردسکن (دروازهٔ جنوبی خراسان رضوی).",
        "legacy_slugs": [],
    },
    "bardaskan": {
        "name_en": "Bardaskan County",
        "short_fa": "بردسکن",
        "population": "75631",
        "elevation": "985",
        "lat": "35.2631",
        "lon": "57.9722",
        "access_air": "فرودگاه بین‌المللی مشهد و فرودگاه سبزوار نزدیک‌ترین فرودگاه‌های منطقه هستند.",
        "access_rail": "نزدیک‌ترین دسترسی‌های ریلی در ایستگاه‌های نقاب/سبزوار (شمال) و بجستان/تربت حیدریه (شرق و جنوب) قرار دارند.",
        "access_road": "تقاطع محورهای کاشمر–خلیل‌آباد–بردسکن، بردسکن–عشق‌آباد–طبس، بردسکن–سبزوار و بردسکن–شاهرود.",
        "legacy_slugs": [],
    },
    "taybad": {
        "name_en": "Taybad County",
        "short_fa": "تایباد",
        "population": "117564",
        "elevation": "810",
        "lat": "34.7400",
        "lon": "60.7756",
        "access_air": "فرودگاه بین‌المللی مشهد در فاصلهٔ حدود ۲۲۵ کیلومتری شمال غرب تایباد نزدیک‌ترین فرودگاه فعال است.",
        "access_rail": "در امتداد کریدور ریلی شرق خراسان (تربت جام–تایباد–دوغارون/خواف–هرات).",
        "access_road": "بزرگراه بین‌المللی مشهد–فریمان–تربت جام–تایباد–مرز دوغارون (اصلی‌ترین گذرگاه زمینی ایران و افغانستان) و محور تایباد–خواف.",
        "legacy_slugs": [],
    },
    "torbatjam": {
        "name_en": "Torbat-e Jam County",
        "short_fa": "تربت جام",
        "population": "267671",
        "elevation": "905",
        "lat": "35.2439",
        "lon": "60.6225",
        "access_air": "فرودگاه بین‌المللی مشهد در فاصلهٔ حدود ۱۶۰ کیلومتری شمال غرب تربت جام قرار دارد.",
        "access_rail": "متصل به شبکهٔ ریلی شرق خراسان از طریق خط راه‌آهن مشهد–فریمان–تربت جام.",
        "access_road": "بزرگراه مشهد–فریمان–تربت جام–تایباد و محورهای تربت جام–باخرز و تربت جام–صالح‌آباد–سرخس.",
        "legacy_slugs": ["torbat-jam"],
    },
    "torbat-heydarieh": {
        "name_en": "Torbat-e Heydarieh County",
        "short_fa": "تربت حیدریه",
        "population": "224626",
        "elevation": "1365",
        "lat": "35.2739",
        "lon": "59.2194",
        "access_air": "فرودگاه بین‌المللی مشهد در فاصلهٔ حدود ۱۴۵ کیلومتری شمال تربت حیدریه قرار دارد.",
        "access_rail": "ایستگاه راه‌آهن تربت حیدریه یکی از ایستگاه‌های مهم خط سراسری مشهد–بافق–بندرعباس/تهران است.",
        "access_road": "شاهراه بزرگراهی مشهد–تربت حیدریه–گناباد–بیرجند/طبس و محورهای تربت حیدریه–کاشمر و تربت حیدریه–خواف.",
        "legacy_slugs": [],
    },
}

EN_TO_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# لینک مارک‌داون با پشتیبانی از یک سطح پرانتز تودرتو در URL
LINK_RE = re.compile(r"\[([^\]\n]+)\]\(((?:[^()\s]|\([^()]*\))*)\)")
SUP_LINK_RE = re.compile(r"<sup>\[([^\]\n]+)\]\(((?:[^()\s]|\([^()]*\))*)\)</sup>")


def fa_digits(val: str) -> str:
    return str(val).translate(EN_TO_FA_DIGITS)


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


def parse_kw_list(raw: str):
    if not raw:
        return []
    raw = raw.strip().strip("[]")
    return [p.strip() for p in raw.split(",") if p.strip()]


def inline_gutenberg(text: str) -> str:
    """تبدیل مارک‌داون درون‌خطی به HTML استاندارد گوتنبرگ با حفظ <sup class="sa-cite">."""
    placeholders = []

    def save_ph(html_frag: str) -> str:
        idx = len(placeholders)
        placeholders.append(html_frag)
        return f"\x00PH{idx}\x00"

    # ۱) ارجاع‌های بالانویس <sup>[n](url)</sup>
    def repl_sup(m):
        num = fa_digits(m.group(1).strip())
        url = html.escape(m.group(2).strip(), quote=True)
        return save_ph(f'<sup class="sa-cite"><a href="{url}">{num}</a></sup>')

    text = SUP_LINK_RE.sub(repl_sup, text)

    # ۲) لینک‌های عادی [label](url)
    def repl_link(m):
        label = html.escape(m.group(1).strip(), quote=False)
        url = html.escape(m.group(2).strip(), quote=True)
        return save_ph(f'<a href="{url}">{label}</a>')

    text = LINK_RE.sub(repl_link, text)

    # ۳) escape مابقی متن
    text = html.escape(text, quote=False)

    # ۴) پررنگ و ایتالیک
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)

    # ۵) بازگردانی placeholderها
    for idx, frag in enumerate(placeholders):
        text = text.replace(f"\x00PH{idx}\x00", frag)

    return text


def render_table_block(rows):
    sep_re = re.compile(r"^\|[\s:\-|]+\|$")
    body_rows = [r for r in rows if not sep_re.match(r.strip())]
    if not body_rows:
        return ""

    def split_cells(row):
        s = row.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    head = split_cells(body_rows[0])
    body = [split_cells(r) for r in body_rows[1:]]
    out = ['<!-- wp:table --><figure class="wp-block-table"><table>']
    out.append("<thead><tr>" + "".join(f"<th>{inline_gutenberg(c)}</th>" for c in head) + "</tr></thead>")
    out.append("<tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline_gutenberg(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></figure><!-- /wp:table -->")
    return "".join(out)


def render_list_block(items, ordered=False):
    tag = "ol" if ordered else "ul"
    attrs = ' {"ordered":true}' if ordered else ""
    lis = "".join(f"<!-- wp:list-item --><li>{inline_gutenberg(it)}</li><!-- /wp:list-item -->" for it in items)
    return f'<!-- wp:list{attrs} --><{tag} class="wp-block-list">{lis}</{tag}><!-- /wp:list -->'


def md_to_gutenberg_blocks(md_body: str) -> str:
    lines = md_body.split("\n")
    out = []
    para = []
    i = 0
    n = len(lines)

    def flush_para():
        if para:
            joined = " ".join(s.strip() for s in para if s.strip())
            if joined:
                out.append(f"<!-- wp:paragraph --><p>{inline_gutenberg(joined)}</p><!-- /wp:paragraph -->")
            para.clear()

    while i < n:
        s = lines[i].strip()
        if not s:
            flush_para()
            i += 1
            continue

        if s in ("---", "***"):
            flush_para()
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush_para()
            lvl = len(m.group(1))
            title_txt = m.group(2).strip()
            if lvl == 1:
                # H1 در هدر قالب (hero.php) چاپ می‌شود؛ داخل بدنه تکرار نمی‌شود
                i += 1
                continue
            attrs = "" if lvl == 2 else f' {{"level":{lvl}}}'
            out.append(
                f'<!-- wp:heading{attrs} --><h{lvl} class="wp-block-heading">{inline_gutenberg(title_txt)}</h{lvl}><!-- /wp:heading -->'
            )
            i += 1
            continue

        if s.startswith("|") and s.endswith("|"):
            flush_para()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            tbl = render_table_block(rows)
            if tbl:
                out.append(tbl)
            continue

        if re.match(r"^[-*]\s+", s):
            flush_para()
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i]).strip()
                i += 1
                items.append(item)
            out.append(render_list_block(items, ordered=False))
            continue

        if re.match(r"^\d+\.\s+", s):
            flush_para()
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip()
                i += 1
                items.append(item)
            out.append(render_list_block(items, ordered=True))
            continue

        if s.startswith(">"):
            flush_para()
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(
                f'<!-- wp:quote --><blockquote class="wp-block-quote"><!-- wp:paragraph --><p>{inline_gutenberg(" ".join(q))}</p><!-- /wp:paragraph --></blockquote><!-- /wp:quote -->'
            )
            continue

        para.append(s)
        i += 1

    flush_para()
    return "\n\n".join(out)


def clean_plain_text(t: str) -> str:
    """حذف ارجاع‌های <sup> و نشانه‌گذاری مارک‌داون برای فیلدهای متنی ساده (FAQ / Excerpt)."""
    t = re.sub(r"<sup>.*?</sup>", "", t, flags=re.S)
    t = LINK_RE.sub(r"\1", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", t).strip()


def extract_sections(body: str):
    """جداسازی بخش پرسش‌های پرتکرار و فهرست منابع از بدنهٔ اصلی مقاله."""
    # ۱) استخراج فهرست منابع
    sources_raw = ""
    if "## فهرست منابع" in body:
        body, sources_raw = body.split("## فهرست منابع", 1)

    # ۲) استخراج پرسش‌های پرتکرار
    faq_list = []
    faq_m = re.search(r"^##\s+پرسش‌های پرتکرار\s*$(.*?)(?=^##\s+|\Z)", body, flags=re.M | re.S)
    if faq_m:
        faq_block = faq_m.group(1)
        for line in faq_block.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            qm = re.match(r"^\*\*(.+?[؟?])\*\*\s*(.+)$", line)
            if qm:
                q_txt = clean_plain_text(qm.group(1))
                a_txt = clean_plain_text(qm.group(2))
                if q_txt and a_txt:
                    faq_list.append({"q": q_txt, "a": a_txt})
        # حذف بخش پرسش‌های پرتکرار از بدنه (چون قالب فرزند از متای sa_faq رندر می‌کند)
        body = body[: faq_m.start()] + "\n\n" + body[faq_m.end() :]

    # ۳) فرمت کردن منابع برای sa_sources: "1. title | org | url | date"
    formatted_sources = []
    sameas_urls = []
    for line in sources_raw.strip().split("\n"):
        line = line.strip()
        m = re.match(r"^(\d+)\.\s+(.+?)\s*\|\s*(https?://\S+)\s*$", line)
        if m:
            num, desc, url = m.group(1), m.group(2).strip(), m.group(3).strip()
            if "—" in desc:
                title_part, org_part = [p.strip() for p in desc.split("—", 1)]
            elif "-" in desc:
                title_part, org_part = [p.strip() for p in desc.split("-", 1)]
            else:
                title_part, org_part = desc, "منبع برخط"
            # حذف برچسب‌های کارگاهی از نام سازمان
            org_part = re.sub(r"\(منبع غیررسمی[^)]*\)", "", org_part).strip()
            formatted_sources.append(f"{num}. {title_part} | {org_part} | {url} | {BUILT_DATE}")
            if ("wikipedia.org/wiki/" in url or "whc.unesco.org" in url) and len(sameas_urls) < 3:
                sameas_urls.append(url)

    sources_str = "\n".join(formatted_sources) + "\n\n--- FACT CHECK ---"
    return body.strip(), faq_list, sources_str, sameas_urls


def build_county_pkg(province_slug: str, md_path: str):
    pmeta = PROVINCE_META[province_slug]
    raw = open(md_path, encoding="utf-8").read()
    fm, body_full = parse_front_matter(raw)

    slug = fm.get("slug") or re.sub(r"^\d+-", "", os.path.splitext(os.path.basename(md_path))[0])
    cinfo = COUNTY_INFO[slug]

    h1_m = re.search(r"^#\s+(.+)$", body_full, flags=re.M)
    seo_title = h1_m.group(1).strip() if h1_m else f"شهرستان {cinfo['short_fa']}؛ راهنمای جامع"
    county_title = fm.get("county") or f"شهرستان {cinfo['short_fa']}"

    body_clean, faq_list, sources_str, sameas_urls = extract_sections(body_full)
    content_html = md_to_gutenberg_blocks(body_clean)

    # شمارش واژه‌های متن
    word_count = len(re.sub(r"<[^>]+>", " ", content_html).split())

    # چکیده از نخستین پاراگراف معرفی شهرستان
    intro_m = re.search(r"^##\s+معرفی شهرستان\s*$\s*(.+?)(?=\n\n|\n-)", body_clean, flags=re.M | re.S)
    excerpt = clean_plain_text(intro_m.group(1)) if intro_m else f"راهنمای جامع و مستند {county_title} در {pmeta['name_fa']}؛ تاریخچه، موقعیت جغرافیایی، آب و هوا، جاذبه‌های گردشگری، صنایع، فرهنگ و مشاهیر."
    if len(excerpt) > 260:
        excerpt = excerpt[:257].rsplit(" ", 1)[0] + "…"

    meta_desc = excerpt
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157].rsplit(" ", 1)[0] + "…"

    focus_kw = fm.get("focus_keyword") or ""
    sec_kws = parse_kw_list(fm.get("secondary_keywords", ""))
    if not focus_kw:
        kws = parse_kw_list(fm.get("focus_keywords", ""))
        focus_kw = kws[0] if kws else county_title
        sec_kws = kws[1:] if len(kws) > 1 else [cinfo["short_fa"], pmeta["term_name"]]
    if focus_kw != county_title and county_title not in sec_kws:
        sec_kws.insert(0, county_title)

    # لینک گوگل‌مپ
    gmap_m = re.search(r"https://(?:www\.)?google\.com/maps/[^\s)\"]+", raw)
    gmap_url = gmap_m.group(0) if gmap_m else f"https://www.google.com/maps/place/{cinfo['name_en'].replace(' ', '+')}"

    img_src_path = os.path.join(ARTICLES_DIR, province_slug, "images", f"{slug}.webp")
    img_alt = fm.get("image_alt", f"تصویر شاخص {county_title}")
    img_bytes = open(img_src_path, "rb").read()
    img_sha1 = hashlib.sha1(img_bytes).hexdigest()

    province_row = {
        "slug": pmeta["slug"],
        "name_fa": pmeta["name_fa"],
        "term_name": pmeta["term_name"],
    }

    pkg = {
        "package_format": PACKAGE_FORMAT,
        "built": BUILT_DATE,
        "source_file": os.path.relpath(md_path, ROOT).replace(os.sep, "/"),
        "source_sha1": hashlib.sha1(raw.encode("utf-8")).hexdigest(),
        "slug": slug,
        "legacy_slugs": cinfo.get("legacy_slugs", []),
        "status": "article",
        "title": county_title,
        "name_fa": county_title,
        "name_en": cinfo["name_en"],
        "province": province_row,
        "post": {
            "title": county_title,
            "excerpt": excerpt,
            "content_html": content_html,
            "word_count": word_count,
        },
        "meta": {
            "sa_city_slug": slug,
            "sa_city_population": cinfo["population"],
            "sa_city_elevation": cinfo["elevation"],
            "sa_city_latitude": cinfo["lat"],
            "sa_city_longitude": cinfo["lon"],
            "sa_access_air": cinfo["access_air"],
            "sa_access_rail": cinfo["access_rail"],
            "sa_access_road": cinfo["access_road"],
            "sa_google_map_url": gmap_url,
            "sa_city_schema_type": "City + TouristDestination",
            "sa_schema_sameas": json.dumps(sameas_urls, ensure_ascii=False) if sameas_urls else "",
            "sa_schema_contained_in": province_slug,
            "sa_facts_checked": BUILT_DATE,
        },
        "seo": {
            "sa_seo_title": seo_title,
            "sa_seo_description": meta_desc,
            "sa_focus_keyword": focus_kw,
            "sa_og_title": f"{county_title} — سرزمین آریان",
            "sa_og_description": meta_desc,
        },
        "secondary_keywords": sec_kws,
        "travel_season": ["spring", "autumn"],
        "google_map_url": gmap_url,
        "faq": faq_list,
        "sources": sources_str,
        "publish_status": "DRAFT ONLY",
        "markers": {
            "review": 0,
            "source_needed": 0,
            "url_needed": 0,
            "coming_soon": 0,
        },
        "image": {
            "file": f"assets/counties/{slug}.webp",
            "source": f"articles/{province_slug}/images/{slug}.webp",
            "mime": "image/webp",
            "alt": img_alt,
            "caption": img_alt,
            "title": f"{county_title} — سرزمین آریان",
            "description": img_alt,
            "sha1": img_sha1,
        },
    }
    return pkg, img_src_path, cinfo["short_fa"]


def generate_main_plugin_php(province_slug: str, count: int) -> str:
    p = PROVINCE_META[province_slug]
    # ساخت نقشهٔ نامک‌های قدیمی به نامک‌های جدید برای ادغام خودکار پیش‌نویس‌های خام اولیه
    legacy_map_entries = []
    for cslug, cinfo in COUNTY_INFO.items():
        for lslug in cinfo.get("legacy_slugs", []):
            legacy_map_entries.append(f"\t\t'{lslug}' => '{cslug}',")
    legacy_map_php = "\n".join(legacy_map_entries)

    return f"""<?php
/**
 * Plugin Name: سرزمین آریان — درون‌ریز شهرستان‌های {p['name_fa']}
 * Plugin URI:  https://github.com/sarzaminaryan-arch/awesome_ai_agents
 * Description: درون‌ریز کامل {fa_digits(count)} شهرستان آمادهٔ {p['name_fa']} ({p['description_cities']}) — متن کامل مقاله (بلوک‌های گوتنبرگ)، جدول‌ها، پرسش‌های متداول (FAQ)، فهرست منابع، فیلدهای مدل داده (sa_city_*، sa_access_*، sa_google_map_url)، اسکیمای City+TouristDestination، سئو رنک‌مث، ارتباط با برگهٔ مادر استان و آپلود تصویر شاخص وب‌پی همراه هر صفحه؛ با قابلیت درون‌ریزی به‌صورت پیش‌نویس یا انتشار مستقیم.
 * Version:     {p['version']}
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * Author:      سرزمین آریان
 * Author URI:  https://sarzaminaryan.ir
 * License:     GPLv2 or later
 * License URI: http://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: sa-province-importer
 *
 * @package Sarzaminaryan_City_Importer
 */

if ( ! defined( 'ABSPATH' ) ) {{
	exit;
}}

define( '{p['const_prefix']}_VERSION', '{p['version']}' );
define( '{p['const_prefix']}_FILE', __FILE__ );

require_once __DIR__ . '/includes/class-sa-city-importer.php';

/**
 * Register this plugin's data batch with the city importer core.
 */
function {p['func_prefix']}_register() {{
	SA_City_Province_Importer::instance()->register_batch(
		array(
			'id'          => '{province_slug}',
			'dir'         => __DIR__ . '/data',
			'plugin_file' => __FILE__,
			'version'     => {p['const_prefix']}_VERSION,
		)
	);
}}
add_action( 'plugins_loaded', '{p['func_prefix']}_register', 20 );

/**
 * افزودن لینک مستقیم «درون‌ریزی و انتشار» در صفحهٔ افزونه‌ها و زیرمنوی «شهرها»
 */
function {p['func_prefix']}_action_links( $links ) {{
	$url = admin_url( 'admin.php?page=sa-city-importer-{province_slug}' );
	array_unshift( $links, '<a href="' . esc_url( $url ) . '" style="font-weight:700;color:#0a7d33;">درون‌ریزی و انتشار شهرستان‌ها</a>' );
	return $links;
}}
add_filter( 'plugin_action_links_' . plugin_basename( __FILE__ ), '{p['func_prefix']}_action_links' );

function {p['func_prefix']}_submenu() {{
	add_submenu_page(
		'edit.php?post_type=city',
		'درون‌ریز {p['term_name']}',
		'درون‌ریز {p['term_name']}',
		'manage_options',
		'sa-city-importer-{province_slug}',
		array( SA_City_Province_Importer::instance(), 'render_page' )
	);
}}
add_action( 'admin_menu', '{p['func_prefix']}_submenu', 45 );

/**
 * یکسان‌سازی نامک‌های قدیمی (در صورت وجود پیش‌نویس‌های خام قبلی) و پشتیبانی از انتشار مستقیم
 */
function {p['func_prefix']}_pre_import() {{
	if ( ! current_user_can( 'manage_options' ) ) {{
		return;
	}}
	$batch_id = isset( $_POST['batch'] ) ? sanitize_key( wp_unslash( $_POST['batch'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Missing
	if ( '{province_slug}' !== $batch_id ) {{
		return;
	}}
	$legacy_map = array(
{legacy_map_php}
	);
	foreach ( $legacy_map as $old_slug => $new_slug ) {{
		$old_posts = get_posts(
			array(
				'post_type'      => 'city',
				'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
				'name'           => $old_slug,
				'posts_per_page' => 1,
				'fields'         => 'objects',
				'no_found_rows'  => true,
			)
		);
		$new_posts = get_posts(
			array(
				'post_type'      => 'city',
				'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
				'name'           => $new_slug,
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'no_found_rows'  => true,
			)
		);
		if ( $old_posts && ! $new_posts ) {{
			wp_update_post(
				array(
					'ID'        => $old_posts[0]->ID,
					'post_name' => $new_slug,
				)
			);
			add_post_meta( $old_posts[0]->ID, '_wp_old_slug', $old_slug );
		}}
	}}
}}
add_action( 'admin_post_sa_city_import', '{p['func_prefix']}_pre_import', 5 );

/**
 * ثبت ریدایرکت نامک‌های قدیمی (_wp_old_slug) و اعمال انتشار مستقیم در صورت انتخاب کاربر
 */
function {p['func_prefix']}_post_meta_hook( $meta_id, $post_id, $meta_key, $meta_value ) {{
	if ( '_sa_import_time' !== $meta_key ) {{
		return;
	}}
	if ( '{province_slug}' !== get_post_meta( $post_id, '_sa_import_batch', true ) ) {{
		return;
	}}
	if ( ! get_post_meta( $post_id, 'sa_province_id', true ) && post_type_exists( 'province' ) ) {{
		$hub = get_posts(
			array(
				'post_type'      => 'province',
				'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
				'name'           => '{province_slug}',
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'no_found_rows'  => true,
			)
		);
		if ( $hub ) {{
			update_post_meta( $post_id, 'sa_province_id', (int) $hub[0] );
		}}
	}}
	$slug = get_post_meta( $post_id, 'sa_city_slug', true );
	$aliases = array(
		'boshruyeh' => 'beshrooyeh',
		'khusf'     => 'khosf',
		'darmiyan'  => 'asadieh',
		'zirkuh'    => 'hajjiabad',
		'qayenat'   => 'ghaen',
		'torbatjam' => 'torbat-jam',
	);
	if ( isset( $aliases[ $slug ] ) ) {{
		$old = $aliases[ $slug ];
		$existing_olds = get_post_meta( $post_id, '_wp_old_slug', false );
		if ( ! in_array( $old, (array) $existing_olds, true ) ) {{
			add_post_meta( $post_id, '_wp_old_slug', $old );
		}}
	}}
	if ( ! empty( $_POST['opt_publish_now'] ) ) {{ // phpcs:ignore WordPress.Security.NonceVerification.Missing
		wp_update_post(
			array(
				'ID'          => $post_id,
				'post_status' => 'publish',
			)
		);
	}}
}}
add_action( 'added_post_meta', '{p['func_prefix']}_post_meta_hook', 10, 4 );
add_action( 'updated_post_meta', '{p['func_prefix']}_post_meta_hook', 10, 4 );

/**
 * افزودن گزینهٔ «انتشار مستقیم پس از درون‌ریزی» به فرم درون‌ریز (حتی اگر هستهٔ قدیمی‌تر فعال باشد)
 */
function {p['func_prefix']}_inject_publish_option() {{
	$page = isset( $_GET['page'] ) ? sanitize_key( wp_unslash( $_GET['page'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	if ( 'sa-city-importer-{province_slug}' !== $page ) {{
		return;
	}}
	?>
	<script>
	jQuery(function($){{
		var $form = $('form input[name="batch"][value="{province_slug}"]').closest('form');
		if ($form.length && !$form.find('input[name="opt_publish_now"]').length) {{
			var $lastCheck = $form.find('input[name="opt_overwrite_featured"]').closest('p');
			if ($lastCheck.length) {{
				$lastCheck.append('<br /><label style="font-weight:700;color:#0a7d33;"><input type="checkbox" name="opt_publish_now" value="1" checked="checked" /> انتشار مستقیم نوشته‌ها پس از درون‌ریزی (Publish — آماده‌ی نمایش در سایت)</label>');
			}}
		}}
	}});
	</script>
	<?php
}}
add_action( 'admin_footer', '{p['func_prefix']}_inject_publish_option' );
"""


def generate_readme_txt(province_slug: str, count: int) -> str:
    p = PROVINCE_META[province_slug]
    return f"""=== سرزمین آریان — درون‌ریز شهرستان‌های {p['name_fa']} ===
Contributors: sarzaminaryan
Requires at least: 6.0
Tested up to: 6.7
Requires PHP: 7.4
Stable tag: {p['version']}
License: GPLv2 or later

درون‌ریز کامل {fa_digits(count)} شهرستان آمادهٔ {p['name_fa']} ({p['description_cities']}) همراه با تصاویر شاخص WebP، فیلدهای سئو Rank Math، پرسش‌های متداول (FAQ)، منابع و مختصات جغرافیایی.

== روش نصب در وردپرس ==
1. از پیشخوان وردپرس به «افزونه‌ها ← افزودن افزونه ← بارگذاری افزونه» بروید و فایل زیپ این افزونه را نصب و فعال کنید.
2. روی لینک سبز «درون‌ریزی و انتشار شهرستان‌ها» زیر نام افزونه (یا از منوی «شهرها ← درون‌ریز {p['term_name']}») کلیک کنید.
3. گزینهٔ «انتشار مستقیم نوشته‌ها پس از درون‌ریزی» را فعال بگذارید و دکمهٔ درون‌ریزی را بزنید.
"""


def build_plugin_for_province(province_slug: str, core_php_content: str):
    p = PROVINCE_META[province_slug]
    plugin_slug = f"sa-city-importer-{province_slug}"
    plugin_dir = os.path.join(PLUGINS_DIR, plugin_slug)
    data_dir = os.path.join(plugin_dir, "data")
    inc_dir = os.path.join(plugin_dir, "includes")
    assets_dir = os.path.join(plugin_dir, "assets", "counties")

    if os.path.exists(plugin_dir):
        shutil.rmtree(plugin_dir)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(inc_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    src_articles_dir = os.path.join(ARTICLES_DIR, province_slug)
    md_files = sorted(
        f for f in os.listdir(src_articles_dir) if f.endswith(".md") and f != "README.md"
    )

    packages = []
    manifest_counties = []
    counties_list_rows = []

    for fname in md_files:
        md_path = os.path.join(src_articles_dir, fname)
        pkg, img_src_path, short_fa = build_county_pkg(province_slug, md_path)
        shutil.copy2(img_src_path, os.path.join(assets_dir, f"{pkg['slug']}.webp"))
        packages.append(pkg)
        src_lines_count = len(
            [l for l in pkg["sources"].split("---")[0].splitlines() if "http" in l]
        )
        manifest_counties.append(
            {
                "slug": pkg["slug"],
                "title": pkg["title"],
                "status": "article",
                "word_count": pkg["post"]["word_count"],
                "faq": len(pkg["faq"]),
                "sources_lines": src_lines_count,
                "publish_status": "DRAFT ONLY",
                "markers": pkg["markers"],
                "featured_image": True,
            }
        )
        counties_list_rows.append(
            {
                "title": short_fa,
                "slug": pkg["slug"],
                "province": province_slug,
                "province_name": p["term_name"],
            }
        )

    province_row = {
        "slug": p["slug"],
        "name_fa": p["name_fa"],
        "term_name": p["term_name"],
    }

    province_json = {
        "batch": province_slug,
        "batch_id": province_slug,
        "label": f"درون‌ریز شهرستان‌های {p['name_fa']}",
        "data_version": p["version"],
        "package_format": PACKAGE_FORMAT,
        "built": BUILT_DATE,
        "province": province_row,
        "counties": packages,
    }
    with open(os.path.join(data_dir, f"{province_slug}.json"), "w", encoding="utf-8") as f:
        json.dump(province_json, f, ensure_ascii=False, indent=1)

    manifest_json = {
        "batch": province_slug,
        "batch_id": province_slug,
        "label": f"درون‌ریز شهرستان‌های {p['name_fa']}",
        "data_version": p["version"],
        "package_format": PACKAGE_FORMAT,
        "built": BUILT_DATE,
        "province": province_row,
        "file": f"{province_slug}.json",
        "counties_count": len(packages),
        "counties": manifest_counties,
    }
    with open(os.path.join(data_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_json, f, ensure_ascii=False, indent=1)

    counties_json = {
        "format": "1.0",
        "built": BUILT_DATE,
        "counties": counties_list_rows,
    }
    with open(os.path.join(data_dir, "counties.json"), "w", encoding="utf-8") as f:
        json.dump(counties_json, f, ensure_ascii=False, indent=1)

    with open(os.path.join(inc_dir, "class-sa-city-importer.php"), "w", encoding="utf-8") as f:
        f.write(core_php_content)

    with open(os.path.join(plugin_dir, f"{plugin_slug}.php"), "w", encoding="utf-8") as f:
        f.write(generate_main_plugin_php(province_slug, len(packages)))

    with open(os.path.join(plugin_dir, "readme.txt"), "w", encoding="utf-8") as f:
        f.write(generate_readme_txt(province_slug, len(packages)))

    # ساخت فایل زیپ استاندارد وردپرس در downloads/
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    zip_filename = f"{plugin_slug}-v{p['version']}.zip"
    zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root_d, _, files in os.walk(plugin_dir):
            for file in sorted(files):
                abs_p = os.path.join(root_d, file)
                rel_p = os.path.relpath(abs_p, PLUGINS_DIR).replace(os.sep, "/")
                zf.write(abs_p, rel_p)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✅ ساخته شد: {zip_filename} ({len(packages)} شهرستان، {size_mb:.2f} MB)")
    for c in manifest_counties:
        print(f"   • {c['title']} ({c['slug']}): {c['word_count']} واژه | FAQ={c['faq']} | منابع={c['sources_lines']}")


if __name__ == "__main__":
    core_path = os.path.join(ROOT, "scripts", "class-sa-city-importer.php")
    core_php = open(core_path, encoding="utf-8").read()
    build_plugin_for_province("south-khorasan", core_php)
    build_plugin_for_province("razavi-khorasan", core_php)
