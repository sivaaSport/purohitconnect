# PurohitConnect — live status

Update this file in the same change as behavior work. Do not treat `agent_handover.md` as current.

## Last shipped

Flutter devotee app on `main`: auth, cream/gold home, purohit list/filters/gallery/avatars, bookings calendar, travel requests, wallet, support bot, live/mock Razorpay. **Purohit Flutter workspace:** incoming bookings, travel requests, My pujas, availability calendar. Same Django DB.

OTP/Razorpay glance (code): wrong OTP now counts toward lockout; unused codes expire when a new one is sent; 45s resend cooldown; mock OTP only in DEBUG; CORS no longer reflects random browser origins; Razorpay webhooks need `RAZORPAY_WEBHOOK_SECRET` when DEBUG and mock are off. Commands: `python manage.py check_twilio` and `python manage.py check_razorpay`.

Flutter tests: `mobile/test/` covers JSON models, booking coverage rules, mock Razorpay collect, workspace flags, and widgets that do not call Django.

**Still human:** paste real Twilio + Razorpay test keys in `.env`, send yourself an OTP, pay ₹1 on Flutter, then set the webhook URL to `/accounts/webhook/razorpay/` with the dashboard webhook secret. Live `rzp_live_` keys after that. Service locations / coverage editing can wait.

GitHub: https://github.com/sivaaSport/purohitconnect (`github` remote). Cursor `origin` is separate.

## Run locally

```text
python manage.py runserver 0.0.0.0:8001
cd mobile && flutter run -d chrome --web-port=5173
```

- Website and API: `http://localhost:8001`
- Flutter: `http://localhost:5173`
- API: `http://localhost:8001/api/v1`
- Tests: `python manage.py test apps.api` (also `apps.accounts`, `apps.bookings`)
- Flutter: `cd mobile && flutter test` (models, coverage, mock Razorpay, welcome/login widgets; no live HTTP)

If Flutter web assets lock on OneDrive: kill port 5173 and leftover `flutter_tools_chrome_device` Chrome, delete `mobile/build/flutter_assets`, then `flutter run` again.

## Known risks

- Port 8000 is often another local app; always use **8001**.
- Do not add runtime `google_fonts` on Flutter web.
- Payments, OTP, Twilio, Razorpay, and CORS: code glance is in; live keys, a ₹1 test payment, and the webhook secret are still a human step.
- Mixed Cursor Workspace also contains `noorella-bandham`; stay in `purohitconnect/` unless the ticket names that product.
- Prefer opening `purohitconnect` as its own Cursor window so always-on rules do not leak.

## Product map

| Surface | Path |
|---|---|
| Django website | `templates/`, `apps/` |
| Mobile API | `apps/api/` |
| Flutter app | `mobile/` |
| Roadmap (do not autopilot) | `docs/DEVELOPMENT_ROADMAP.md` |
