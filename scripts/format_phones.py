#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huevoreal.settings')
django.setup()

from django.core.management import call_command

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    call_command('format_customer_phones', dry_run=dry_run)
