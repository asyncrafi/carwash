"""
Management command to seed initial database data.
Usage: python manage.py seed_database
"""
from django.core.management.base import BaseCommand
from apps.services.seed_data import seed_all_data


class Command(BaseCommand):
    help = 'Populates the database with initial seed data for vehicle types, engine types, services, and dirt levels'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting database seeding...\n')
        )

        try:
            result = seed_all_data()

            self.stdout.write(
                self.style.SUCCESS(f"✅ {result['vehicle_types']['message']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ {result['engine_types']['message']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ {result['dirt_levels']['message']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ {result['services']['message']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ {result['platform_config']['message']}")
            )

            total_created = sum([
                result['vehicle_types']['created'],
                result['engine_types']['created'],
                result['dirt_levels']['created'],
                result['services']['created'],
                result['platform_config']['created'],
            ])

            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Database seeding completed! {total_created} total records created.")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during seeding: {str(e)}')
            )
            raise
