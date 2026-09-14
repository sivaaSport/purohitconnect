# PurohitConnect Mobile

Flutter client for the PurohitConnect Django backend. Lives at `purohitconnect/mobile`.

## What it talks to

The app calls `/api/v1/` on the Django server (token auth). Demo fallbacks are gone — if Django is down, the UI shows an error.

## Run

1. From `purohitconnect`:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

2. From `purohitconnect/mobile`:

```bash
flutter pub get
flutter run
```

Android emulator uses `http://10.0.2.2:8000/api/v1`. A physical phone needs your LAN IP:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
```

Web / Chrome: `http://127.0.0.1:8001/api/v1`.

## Tests

These stay off the network (no running Django):

```bash
cd mobile
flutter test
```

## Auth

Phone OTP matches the website. New numbers are signed up automatically. In DEBUG + mock SMS, the OTP is shown on the verify screen.

Local Razorpay mock orders (`order_mock_*`) complete in-app when Django has no keys. Live orders open Razorpay Checkout (web Checkout.js, Android/iOS SDK) and Django verifies the signature. Glance at a test-key payment before production.

## Customer flows included

- OTP login / signup with persisted session
- Categories, pujas, cities, languages, purohit discovery
- Real availability slots
- Booking create with city, area, venue, samagri
- Travel request when the purohit does not already offer that place
- Wallet / Razorpay / mixed pay
- Booking detail, cancel, reschedule, chat, review
- Wallet top-up + passbook
- Notifications
- Support tickets (`ServiceRequest`)
- Purohit workspace: confirm/start/complete bookings, travel-request replies, switch from devotee profile, My pujas, availability calendar
