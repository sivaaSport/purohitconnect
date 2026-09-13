# PurohitConnect Agent Definitions

This repository uses a set of agent-style documents to describe roles and responsibilities for working on the codebase.

## Core Agent
- Name: `PurohitConnect Core Agent`
- Purpose: Maintain the overall product, coordinate major fixes, preserve current project knowledge, and keep the application stable.
- Focus:
  - Project status and high-level handover
  - Key architectural decisions
  - Current working features and open risks
  - Deployment readiness and environment setup
- Primary files:
  - `agent_handover.md`
  - `config/settings/development.py`
  - `requirements.txt`
  - `apps/**`

## Testing Agent
- Name: `PurohitConnect Testing Agent`
- Purpose: Build, validate, and improve test coverage for core application flows.
- Focus:
  - Unit tests for accounts, bookings, notifications, and wallet flows
  - Integration tests for booking/payment workflows
  - Regression tests for payment, wallet, and route fixes
- Primary files:
  - `apps/accounts/tests.py`
  - `apps/bookings/tests.py`
  - `apps/core/tests.py`
  - `apps/accounts/utils.py`
  - `apps/bookings/payment_utils.py`

## Debugging Agent
- Name: `PurohitConnect Debugging Agent`
- Purpose: Diagnose runtime failures, dependency issues, and template or middleware errors.
- Focus:
  - Environment dependencies and missing packages
  - Middleware, template, and URL routing issues
  - Error handling and log analysis
  - Reproducing and fixing failing tests and payment route mismatches
- Primary files:
  - `templates/**/*.html`
  - `config/**/*.py`
  - `apps/**/*.py`
  - `agent_handover.md`

## Enhancement Agent
- Name: `PurohitConnect Feature Enhancement Agent`
- Purpose: Design and implement new features, refactor existing flows, and improve UX.
- Focus:
  - Payment security, wallet top-ups, and Razorpay integration
  - Wallet booking payments, transfers, and withdrawals
  - OTP and authentication workflows
  - Chat, notification, and booking lifecycle enhancements
  - Producing reusable, maintainable code
- Primary files:
  - `apps/bookings/views.py`
  - `apps/accounts/views.py`
  - `apps/accounts/utils.py`
  - `apps/accounts/payment_service.py`
  - `apps/bookings/payment_utils.py`
  - `apps/core/notification_service.py`
  - `templates/**/*.html`

## Usage
- Use `agent_handover.md` for overall project context and status.
- Use `AGENTS.md` to select the appropriate role for a task.
- Use the role-specific docs in the `agents/` folder when working on testing, debugging, or new features.
