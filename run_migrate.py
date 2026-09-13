import os
import sys

# Add purohitconnect to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.core.management import call_command
import traceback

try:
    print("Running migrations...")
    call_command('migrate', interactive=False)
    print("Migrations completed successfully.")
except Exception as e:
    print("Error running migrations:")
    traceback.print_exc()
