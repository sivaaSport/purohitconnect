# Hourly reschedule expiry + maintenance jobs (Linux/macOS cron)
#
# Install:
#   crontab -e
# Add (adjust paths):
#   15 * * * * /path/to/purohitconnect/scripts/expire_pending_reschedules.sh >> /var/log/purohitconnect-cron.log 2>&1

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f "$ROOT/venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/venv/bin/activate"
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"
python manage.py run_scheduled_jobs
