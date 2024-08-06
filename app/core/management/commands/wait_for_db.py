"""
Django commands to wait for database to be available
"""

import time
from django.core.management.base import BaseCommand

# When database is not available, Psycopg2 raises OperationalError
from psycopg2 import OperationalError as Psycopg2OperationalError

# When database is not available, Django raises OperationalError
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        """Handle the command"""
        self.stdout.write("Waiting for database...")
        db_up = False
        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except (Psycopg2OperationalError, OperationalError):
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("Database available!"))
