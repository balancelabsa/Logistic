# منصة لوجستيات المختبرات الطبية

منصة تشغيل ومتابعة للسائقين بين الفروع ونقاط السحب والتسليم، مبنية على:
- FastAPI (Backend)
- React/Vite (لوحة الإدارة)
- React Native Expo (تطبيق السائق)
- PostgreSQL

## ما هو المنفذ حاليًا
- مصادقة JWT وصلاحيات (admin/dispatcher/driver)
- بدء/إنهاء الوردية
- تتبع GPS أثناء الوردية النشطة فقط
- زيارات مخططة + وصول/مغادرة + ملاحظة + صورة إثبات
- تنبيهات: تأخير/توقف طويل/انحراف/زيارة فائتة
- إشعارات مباشرة للإدارة عبر polling
- سجل تدقيق شامل للأحداث الحساسة
- مسار السائق حسب التاريخ + كشف توقفات + Playback
- تقرير PDF للمسار
- واجهة عربية RTL للإدارة

## المتطلبات
- Python 3.11+
- Node 20+
- Docker + Docker Compose

## متغيرات البيئة
استخدم `.env.example`:
- `DATABASE_URL`
- `JWT_SECRET`
- `VITE_API_URL`
- `VITE_GOOGLE_MAPS_API_KEY`
- `EXPO_PUBLIC_API_URL`

## تشغيل Docker
```bash
docker compose up --build -d
```

## إعداد قاعدة البيانات
```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_demo.py
```

## تشغيل الـ Backend محليًا
```bash
pip install -e .
uvicorn app.main:app --reload
```

## تشغيل لوحة الإدارة
```bash
cd admin-web
npm install
npm run dev
```

## تشغيل تطبيق السائق (Expo)
```bash
cd mobile-driver
npm install
npm run start
```

## إضافة Google Maps API Key
ضع المفتاح في:
```env
VITE_GOOGLE_MAPS_API_KEY=YOUR_KEY
```
وعند عدم إضافته تظهر رسالة: `يرجى إضافة مفتاح Google Maps API في إعدادات البيئة`.

## سيناريو اختبار كامل
1) تسجيل دخول Admin من لوحة الإدارة
2) إنشاء/اعتماد سائق وزيارات
3) تسجيل دخول السائق من التطبيق
4) بدء الوردية
5) التحقق من وصول نقاط GPS إلى `/shifts/active/locations`
6) تنفيذ check-in/check-out
7) رفع صورة إثبات
8) إدخال ملاحظة
9) إنهاء الوردية
10) مراجعة مسار السائق في صفحة `مسار السائقين`
11) تجربة playback بسرعات 1x/2x/4x
12) مراجعة التنبيهات والإشعارات
13) تصدير PDF من صفحة التقارير

## اختبار التنبيهات
- **Delay**: Check-in بعد 15 دقيقة من planned time
- **Route deviation**: check-in بعيد > 1 كم عن إحداثية الزيارة المخططة
- **Long stop**: بطء الحركة لفترة طويلة أثناء الوردية
- **Missed visit**: زيارة بقيت planned/delayed بعد threshold

## افتراضات منطق التحليل
- stop radius = 50m
- minimum stop duration = 5min
- delay threshold = 15min
- route deviation threshold = 1km من إحداثية الزيارة

## نقاط الامتثال التشغيلي
- جميع الأحداث الحساسة تُكتب في audit trail
- كل العمليات مرتبطة بزمن وفاعل
- الزيارات تشمل مخطط مقابل فعلي
- تتبع السائق محصور داخل الوردية النشطة
