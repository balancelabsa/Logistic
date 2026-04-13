# Logistic Platform (FastAPI + React + React Native Expo)

منصة لوجستية متكاملة لتتبع السائقين من **بدء الوردية** حتى **إنهائها** مع لوحة تحكم إدارية وتطبيق موبايل للسائقين.

## 1) ما كان موجودًا سابقًا
- Backend أساسي بـ FastAPI.
- تسجيل/دخول بسيط.
- رفع نقاط GPS دفعات.

## 2) ما تم استكماله الآن
- نموذج إنتاجي كامل: Users/Roles/Shifts/Visits/Alerts/Audit Logs.
- RBAC (صلاحيات حسب الدور: Admin/Dispatcher/Driver).
- تتبع GPS مرتبط فقط بالوردية النشطة.
- إدارة الزيارات (Check-in / Check-out + GPS + وقت + ملاحظات).
- Route history playback per driver/day.
- تقارير تشغيلية + تنبيهات + سجل تدقيق.
- Alembic migrations + seed script.
- لوحة إدارة React عربية.
- تطبيق سائق Expo (iOS/Android) مع background location tracking.

## 3) هيكلة المشروع
- `app/` FastAPI backend
- `app/alembic/` database migrations
- `admin-web/` React admin dashboard
- `mobile-driver/` Expo mobile app for drivers
- `scripts/seed_demo.py` demo seed data

## 4) تشغيل محلي سريع
### Backend + DB + Admin Web
```bash
docker compose up --build -d
```

### تشغيل المايجريشن
```bash
docker compose exec api alembic upgrade head
```

### بيانات تجريبية
```bash
docker compose exec api python scripts/seed_demo.py
```

### تشغيل تطبيق الموبايل
```bash
cd mobile-driver
npm install
npm run start
```

## 5) حسابات تجريبية
- Admin: `900000001 / Admin@1234`
- Driver: `900000101 / Driver@1234`

## 6) أهم الـ APIs
- `POST /auth/bootstrap-admin`
- `POST /auth/login`
- `POST /auth/register`
- `POST /shifts/start`
- `POST /shifts/{shift_id}/end`
- `POST /shifts/active/locations`
- `POST /visits`
- `GET /visits/mine`
- `POST /visits/{visit_id}/check-in`
- `POST /visits/{visit_id}/check-out`
- `GET /admin/drivers/live`
- `GET /admin/route-history/{driver_id}?day=YYYY-MM-DD`
- `GET /admin/alerts`
- `GET /admin/audit-trail`
- `GET /admin/reports/overview`

## 7) حوكمة وامتثال
- كل حدث تشغيلي حرج يُكتب في `audit_logs`.
- تطبيق الصلاحيات حسب الدور على مستوى الـ API.
- منع التتبع خارج الورديات النشطة.
- إمكانية مراجعة الأحداث والزيارات والتنبيهات للتحكم الداخلي.

## 8) النشر الإنتاجي
- ضع API خلف reverse proxy (Nginx/Traefik).
- فعّل TLS وشهادات صحيحة.
- استخدم managed PostgreSQL مع نسخ احتياطي.
- فعّل مراقبة (Prometheus/Grafana) وlog aggregation.
- أضف queue (Redis streams/Kafka) عند الأحمال الضخمة.
