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

Web / Chrome: `http://127.0.0.1:8000/api/v1`.

## Auth

Phone OTP matches the website. New numbers are signed up automatically. In DEBUG + mock SMS, the OTP is shown on the verify screen.

Local Razorpay mock orders (`order_mock_*`) complete in-app. Live Razorpay checkout needs the official Android/iOS SDK later.

## Customer flows included

- OTP login / signup with persisted session
- Categories, pujas, cities, languages, purohit discovery
- Real availability slots
- Booking create with city, area, venue, samagri
- Wallet / Razorpay / mixed pay
- Booking detail, cancel, reschedule, chat, review
- Wallet top-up + passbook
- Notifications
- Support tickets (`ServiceRequest`)
