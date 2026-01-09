import os
import time

import psycopg2
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            os.environ["POSTGRES_PASSWORD"]
        except KeyError:
            raise CommandError(
                "Please set the environment variable "
                "'POSTGRES_PASSWORD' before running the container"
            )

        user = os.environ.get("POSTGRES_USER", "postgres")
        for i in range(1, 21):
            self.stdout.write(f"Connecting to DB, try #{i} out of 20:")
            try:
                conn = psycopg2.connect(
                    f"user={user} "
                    f"password={os.environ['POSTGRES_PASSWORD']} "
                    f"dbname={os.environ.get('POSTGRES_DB', user)} "
                    f"host={os.environ.get('POSTGRES_HOST', 'db')} "
                    f"port={os.environ.get('POSTGRES_PORT', '5432')}"
                )
                conn.close()
                self.stdout.write("Connected to DB successfully")
                return
            except psycopg2.OperationalError:
                self.stdout.write(
                    "Connection to DB failed, trying again in 2 seconds..."
                )
                time.sleep(2)

        self.stderr.write("Connection to DB failed for 20 tries.")
