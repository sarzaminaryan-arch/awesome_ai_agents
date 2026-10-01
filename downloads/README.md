# بسته‌های ورود و افزونه‌های وردپرس (Downloads)

بستهٔ نهایی هر استان پس از تأیید مقاله‌ها و عبور از فیلتر صحت و گیت انتشار سطح ۷ (`sa_gate_missing`)، در همین پوشه ساخته می‌شود.

## ۱. افزونه‌های مستقل وردپرس (آمادهٔ نصب مستقیم از «افزونه‌ها ← افزودن افزونه تازه ← بارگذاری افزونه»)

| فایل افزونه | استان | شهرستان‌ها | حجم |
|---|---|---|---|
| `sa-city-importer-south-khorasan-v1.0.0.zip` | خراسان جنوبی (۱۲/۱۲ ✅ کامل) | بیرجند، بشرویه، خوسف، درمیان، زیرکوه، سرایان، سربیشه، طبس، فردوس، قائنات، نهبندان، عشق‌آباد | ~۳٫۳ مگابایت |
| `sa-city-importer-razavi-khorasan-v1.0.0.zip` | خراسان رضوی (۶ شهرستان آماده — دستهٔ اول) | باخرز، بجستان، بردسکن، تایباد، تربت جام، تربت حیدریه | ~۱٫۹ مگابایت |

### ویژگی‌های افزونه‌های وردپرس (`sa-city-importer-*`)
- کاملاً منطبق با معماری پوستهٔ فرزند `sarzaminaryan-child` و هستهٔ `SA_City_Province_Importer` (مشابه افزونه‌های استان‌های آذربایجان شرقی، آذربایجان غربی، اردبیل و اصفهان).
- هر بسته شامل متن کامل مقاله با بلوک‌های گوتنبرگ، متادیتای کامل شهرستان (`sa_city_*`, `sa_access_*`, `sa_google_map_url`)، پرسش‌های متداول (`sa_faq` با JSON-LD)، فهرست منابع (`sa_sources`)، اسکیمای `City+TouristDestination`، متای سئو Rank Math، اتصال خودکار به برگهٔ مادر استان (`sa_province_id`) و آپلود خودکار تصویر شاخص `.webp` در رسانهٔ وردپرس است.
- دارای گزینهٔ **«انتشار مستقیم پس از درون‌ریزی»** (`publish`) یا ذخیره به‌صورت **«پیش‌نویس»** (`draft`).

## ۲. بسته‌های جامع داده و محتوا (JSON + Markdown + HTML + WebP)

| فایل | استان | محتوا | حجم |
|---|---|---|---|
| `south-khorasan-counties.zip` | خراسان جنوبی (۱۲/۱۲ ✅) | `data/counties.json` + `data/import-payload.json` + `content/cities/*.md,*.html` + `images/*.webp` | ~۳٫۶ مگابایت |
| `razavi-khorasan-counties.zip` | خراسان رضوی (۶ شهرستان آماده) | `data/counties.json` + `data/import-payload.json` + `content/cities/*.md,*.html` + `images/*.webp` | ~۲٫۰ مگابایت |

## ساخت مجدد بسته‌ها

```bash
# ۱. بررسی فیلتر صحت همهٔ مقاله‌ها
python3 articles/_filter/check.py

# ۲. ساخت افزونه‌های وردپرس (در wp-content/plugins/ و downloads/)
python3 scripts/build_wp_city_plugin.py

# ۳. ساخت بسته‌های داده و HTML ایستا
python3 scripts/import_counties.py build --province south-khorasan --zip
python3 scripts/import_counties.py build --province razavi-khorasan --zip
```
