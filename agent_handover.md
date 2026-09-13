# Agent Handover: PurohitConnect Booking, Wallet & Notification Platform

## Current Project Status
The application is in active development with core booking, OTP, notification, and wallet support now integrated. Targeted tests for apps.accounts and apps.bookings are passing, and wallet functionality has been added to booking payment flows.

## What Is Working
- OTP generation and verification with expiry and attempt tracking
- Booking lifecycle and payment workflow with pending/confirmed status
- Wallet ledger model, balance field, and transaction history
- Wallet operations: top-up, debit, transfer, and withdrawal request support
- Booking payment via wallet or Razorpay order creation
- Notification infrastructure for in-app messages and SMS fallback
- Admin visibility for wallet transactions and user wallet balances
- Mock SMS fallback for development when Twilio is not configured

## Fixed Issues
- Resolved booking payment route signature mismatch for verify_booking_payment
- Added wallet withdrawal validation and balance reservation
- Registered WalletTransaction admin and surfaced wallet balances in user admin
- Added wallet test coverage for credit, debit, transfer, and booking wallet payments
- Verified python manage.py test apps.accounts and python manage.py test apps.bookings both pass
- Implemented real Razorpay signature verification for wallet top-ups and booking payments (removed mock mode)
- Extended Razorpay webhook handling to support refund and payout events

## Current Strengths
- Strong wallet service layer for account-level transactions
- Booking checkout supports wallet payments and Razorpay fallback
- Clear separation between wallet utilities and booking payment logic
- Admin and UI flow support for wallet dashboards and transaction history
- Test coverage protecting wallet and booking payment changes

## Remaining Work
- Production settings module (`config/settings/production.py`) is now in place.
- Purohit payout flow now uses structured bank accounts + RazorpayX payout creation (falls back to queued pending if RazorpayX is not configured).
- Booking flow now routes to wallet/mixed/Razorpay checkout; success page is confirmation-only.
- Support bot creates real ServiceRequest tickets.
- Twilio SMS/WhatsApp delivery hardened (dedicated SMS + WhatsApp senders; production fails closed unless TWILIO_ALLOW_MOCK=True).
- Reschedule hardened: max 2 attempts, 48h notice, 24h auto-expire (`expire_pending_reschedules`), customer or purohit can request, reason stored.
- Discovery filters (city/language/puja) now load from `City` / `Language` / `Puja` models instead of hardcoded IDs.
- Reviews list/count removed from purohit listing + detail booking path (post-booking Rate & Review on dashboard remains).
- Payment test coverage expanded: mixed verify/complete, mixed rollback, invalid signatures, full Razorpay order create, payment options, already-paid redirect.
- Payout polish: `WithdrawalRequest` + bank verification fields; admin approve/reject/retry; failed payout idempotent restore; default admin-gated (`WITHDRAWAL_AUTO_PAYOUT=False`).
- Scheduled jobs: `run_scheduled_jobs` + `scripts/expire_pending_reschedules.(sh|ps1)` documented in production deploy guide.
- Docker: Compose stack with Postgres + Gunicorn (`docs/DOCKER.md`).

## Notes
- apps.accounts and apps.bookings tests are green.
- Staticfiles warnings remain a development environment issue, not a functional failure.

## Recommended Next Steps
1. Paste Twilio credentials into `.env`, set `TWILIO_ALLOW_MOCK=False`, verify with `python manage.py check_twilio --send-sms +91...`.
2. ~~Install hourly Task Scheduler/cron~~ — Windows task `PurohitConnect\ExpirePendingReschedules` installed (scripts + `logs/scheduled_jobs.log`).
3. Configure RazorpayX + verify bank accounts in admin before live payouts.
4. ~~Seed cities/languages~~ — `seed_db` expanded (10 languages, 10+ cities/areas); re-run anytime with `python manage.py seed_db` or `--core-only`.
5. ~~Docker / deploy stack~~ — `Dockerfile` + `docker-compose.yml` (web + Postgres); see `docs/DOCKER.md`.

## Complete Development Roadmap
See [docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) for the comprehensive development plan with all remaining features, priorities, and implementation phases.
