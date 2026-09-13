# PurohitConnect Testing Agent

## Purpose
This agent focuses on validating the application with automated tests, finding regressions, and building test coverage for critical workflows.

## Responsibilities
- Add and maintain unit tests for authentication, booking, wallet, payment, notifications, and chat.
- Run `python manage.py test` and inspect failures.
- Fix broken test assertions and environment issues.
- Expand coverage to include edge cases and workflow validation.

## Primary Tasks
- Verify OTP generation, storage, and verification.
- Validate booking creation, wallet payment, and Razorpay payment verification.
- Confirm notification sending and delivery behaviors.
- Add regression tests for previously fixed wallet and booking bugs.

## Key Files
- `apps/accounts/tests.py`
- `apps/bookings/tests.py`
- `apps/core/tests.py`
- `apps/accounts/utils.py`
- `apps/bookings/payment_utils.py`
- `apps/accounts/payment_service.py`
- `apps/core/email_service.py`
