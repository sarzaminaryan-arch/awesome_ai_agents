# بسته‌های ورود (Downloads)

بستهٔ نهایی هر استان پس از تأیید مقاله‌ها و عبور از فیلتر صحت، در همین پوشه ساخته می‌شود.

## بسته‌های موجود

| فایل | استان | محتوا | حجم |
|---|---|---|---|
| `south-khorasan-counties.zip` | خراسان جنوبی (۱۲/۱۲ ✅) | `data/counties.json` + `data/import-payload.json` + `content/cities/*.md,*.html` (۱۲ شهرستان) + `images/*.webp` (۱۲ تصویر) + پلاگین وردپرس + README | ~۳٫۶ مگابایت |

## ساخت مجدد بسته

```bash
python3 scripts/import_counties.py check --province south-khorasan   # بازبینی بدون نوشتن
python3 scripts/import_counties.py build --province south-khorasan --zip
```

- ساختار هر ردیف `data/counties.json`: `{title, slug, province, province_name, county, order, file, html_file, image, image_alt, focus_keywords, words, sources, faq, facts, excerpt}`
- تبدیل Markdown → HTML با `scripts/md2html.py` انجام می‌شود (پشتیبانی از جدول GFM، فهرست‌ها، نقل‌قول، پررنگ/ایتالیک، پیوندها با پرانتز تودرتو و عبور HTML خام بالانویس‌ها).
- راهنمای نصب وردپرس در `BUNDLE-README.txt` (درون zip) آمده است.
