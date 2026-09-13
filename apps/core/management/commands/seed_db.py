from django.core.management.base import BaseCommand
from apps.core.models import City, Area, Language
from apps.accounts.models import CustomUser, PurohitProfile
from apps.purohits.models import Purohit, PurohitServiceOffer
from apps.pujas.models import Puja, PurohitPujaPackage
from apps.pujas.catalog import seed_hindu_pujas


CITIES = [
    {'name': 'Hyderabad', 'state': 'Telangana', 'latitude': 17.3850, 'longitude': 78.4867},
    {'name': 'Bangalore', 'state': 'Karnataka', 'latitude': 12.9716, 'longitude': 77.5946},
    {'name': 'Chennai', 'state': 'Tamil Nadu', 'latitude': 13.0827, 'longitude': 80.2707},
    {'name': 'Mumbai', 'state': 'Maharashtra', 'latitude': 19.0760, 'longitude': 72.8777},
    {'name': 'Pune', 'state': 'Maharashtra', 'latitude': 18.5204, 'longitude': 73.8567},
    {'name': 'Delhi', 'state': 'Delhi', 'latitude': 28.6139, 'longitude': 77.2090},
    {'name': 'Vijayawada', 'state': 'Andhra Pradesh', 'latitude': 16.5062, 'longitude': 80.6480},
    {'name': 'Visakhapatnam', 'state': 'Andhra Pradesh', 'latitude': 17.6868, 'longitude': 83.2185},
    {'name': 'Mysore', 'state': 'Karnataka', 'latitude': 12.2958, 'longitude': 76.6394},
    {'name': 'Ahmedabad', 'state': 'Gujarat', 'latitude': 23.0225, 'longitude': 72.5714},
]

AREAS = [
    ('Hyderabad', 'Banjara Hills', '500034'),
    ('Hyderabad', 'Kukatpally', '500072'),
    ('Hyderabad', 'Gachibowli', '500032'),
    ('Bangalore', 'Koramangala', '560034'),
    ('Bangalore', 'Whitefield', '560066'),
    ('Chennai', 'T Nagar', '600017'),
    ('Chennai', 'Adyar', '600020'),
    ('Mumbai', 'Andheri', '400053'),
    ('Pune', 'Kothrud', '411038'),
    ('Delhi', 'Dwarka', '110075'),
    ('Vijayawada', 'Benz Circle', '520010'),
    ('Visakhapatnam', 'MVP Colony', '530017'),
]

LANGUAGES = [
    ('Telugu', 'తెలుగు'),
    ('Hindi', 'हिन्दी'),
    ('Kannada', 'ಕನ್ನಡ'),
    ('Sanskrit', 'संस्कृतम्'),
    ('Tamil', 'தமிழ்'),
    ('Marathi', 'मराठी'),
    ('English', 'English'),
    ('Gujarati', 'ગુજરાતી'),
    ('Malayalam', 'മലയാളം'),
    ('Bengali', 'বাংলা'),
]


class Command(BaseCommand):
    help = 'Seeds cities, languages, areas, and optional MVP sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--core-only',
            action='store_true',
            help='Only seed cities, areas, and languages (no sample purohit/pujas)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        city_map = {}
        cities_created = 0
        for item in CITIES:
            city, created = City.objects.get_or_create(
                name=item['name'],
                defaults={
                    'state': item['state'],
                    'latitude': item['latitude'],
                    'longitude': item['longitude'],
                },
            )
            # Backfill coords/state if an older row exists without them
            updated = False
            if not city.state:
                city.state = item['state']
                updated = True
            if city.latitude is None:
                city.latitude = item['latitude']
                updated = True
            if city.longitude is None:
                city.longitude = item['longitude']
                updated = True
            if updated:
                city.save()
            city_map[city.name] = city
            if created:
                cities_created += 1

        areas_created = 0
        for city_name, area_name, pincode in AREAS:
            city = city_map.get(city_name)
            if not city:
                continue
            _, created = Area.objects.get_or_create(
                city=city,
                name=area_name,
                defaults={'pincode': pincode},
            )
            if created:
                areas_created += 1

        langs_created = 0
        language_map = {}
        for name, native_name in LANGUAGES:
            lang, created = Language.objects.get_or_create(
                name=name,
                defaults={'native_name': native_name},
            )
            if not lang.native_name and native_name:
                lang.native_name = native_name
                lang.save(update_fields=['native_name'])
            language_map[name] = lang
            if created:
                langs_created += 1

        self.stdout.write(
            f'Core data: +{cities_created} cities, +{areas_created} areas, +{langs_created} languages '
            f'(totals: {City.objects.count()} cities, {Area.objects.count()} areas, {Language.objects.count()} languages)'
        )

        if options['core_only']:
            self.stdout.write(self.style.SUCCESS('Core seed complete (--core-only).'))
            return

        puja_stats = seed_hindu_pujas()
        self.stdout.write(
            f'Hindu puja catalog: +{puja_stats["categories_created"]} categories, '
            f'+{puja_stats["pujas_created"]} pujas '
            f'(totals: {puja_stats["category_total"]} categories, {puja_stats["puja_total"]} pujas)'
        )
        satyanarayan = Puja.objects.get(name='Satyanarayan Puja')
        griha_pravesh = Puja.objects.get(name='Griha Pravesh')

        # Sample purohit (idempotent)
        hyderabad = city_map['Hyderabad']
        bangalore = city_map['Bangalore']
        kphb = Area.objects.get(city=hyderabad, name='Kukatpally')
        banjara = Area.objects.get(city=hyderabad, name='Banjara Hills')
        koramangala = Area.objects.get(city=bangalore, name='Koramangala')

        telugu = language_map['Telugu']
        hindi = language_map['Hindi']
        sanskrit = language_map['Sanskrit']
        kannada = language_map['Kannada']

        user1, created = CustomUser.objects.get_or_create(
            username='purohit_sharma',
            defaults={
                'role': 'purohit',
                'city': hyderabad,
                'is_phone_verified': True,
                'phone': '+919900112233',
            },
        )
        if created:
            user1.set_password('password123')
            user1.save()
            profile1 = PurohitProfile.objects.create(
                user=user1,
                experience_years=15,
                about='Expert in Vedic rituals and Griha Pravesh.',
                is_verified=True,
            )
            profile1.languages_spoken.add(telugu, hindi, sanskrit)
            purohit1 = Purohit.objects.create(
                profile=profile1,
                name='Pt. Ramakant Sharma',
                city=hyderabad,
                base_area=kphb,
                base_price=2100.00,
                avg_rating=4.8,
                total_reviews=124,
                travel_note='Open to travel if the devotee covers train and stay.',
            )
            purohit1.service_areas.add(kphb, banjara)
            for area in (kphb, banjara):
                PurohitServiceOffer.objects.get_or_create(
                    purohit=purohit1,
                    city=hyderabad,
                    area=area,
                    kind=PurohitServiceOffer.KIND_PERMANENT,
                    defaults={'is_active': True},
                )
            PurohitPujaPackage.objects.create(
                purohit=purohit1, puja=satyanarayan, price=2100.00,
                duration_hours=satyanarayan.base_duration_hours,
                buffer_minutes=30,
                includes_samagri=False, samagri_price=1500.00,
            )
            PurohitPujaPackage.objects.create(
                purohit=purohit1, puja=griha_pravesh, price=5100.00,
                duration_hours=griha_pravesh.base_duration_hours,
                buffer_minutes=45,
                includes_samagri=True,
            )
            self.stdout.write('Created sample purohit: purohit_sharma / password123')
        else:
            self.stdout.write('Sample purohit already exists (skipped).')
            purohit1 = Purohit.objects.filter(profile__user__username='purohit_sharma').first()

        if purohit1:
            from datetime import date
            pune = City.objects.filter(name='Pune').first()
            kothrud = Area.objects.filter(city=pune, name='Kothrud').first() if pune else None
            if pune:
                PurohitServiceOffer.objects.get_or_create(
                    purohit=purohit1,
                    city=pune,
                    area=kothrud,
                    kind=PurohitServiceOffer.KIND_VISIT,
                    start_date=date(2026, 10, 12),
                    end_date=date(2026, 10, 18),
                    defaults={'note': 'Family visit — taking work in Pune', 'is_active': True},
                )

        user2, created2 = CustomUser.objects.get_or_create(
            username='purohit_rao',
            defaults={
                'role': 'purohit',
                'city': bangalore,
                'is_phone_verified': True,
                'phone': '+919900445566',
            },
        )
        if created2:
            user2.set_password('password123')
            user2.save()
            profile2 = PurohitProfile.objects.create(
                user=user2,
                experience_years=10,
                about='Kannada and Sanskrit rituals across Bangalore.',
                is_verified=True,
            )
            profile2.languages_spoken.add(kannada, hindi, sanskrit)
            purohit2 = Purohit.objects.create(
                profile=profile2,
                name='Pt. Suresh Rao',
                city=bangalore,
                base_area=koramangala,
                base_price=2500.00,
                avg_rating=4.6,
                total_reviews=58,
            )
            purohit2.service_areas.add(koramangala)
            PurohitServiceOffer.objects.get_or_create(
                purohit=purohit2,
                city=bangalore,
                area=koramangala,
                kind=PurohitServiceOffer.KIND_PERMANENT,
                defaults={'is_active': True},
            )
            PurohitPujaPackage.objects.create(
                purohit=purohit2, puja=satyanarayan, price=2500.00,
                duration_hours=satyanarayan.base_duration_hours,
                buffer_minutes=30,
                includes_samagri=True, samagri_price=0,
            )
            self.stdout.write('Created sample purohit: purohit_rao / password123')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))
