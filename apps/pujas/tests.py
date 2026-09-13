from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import CustomUser, PurohitProfile
from apps.core.models import City
from apps.pujas.catalog import PUJAS, seed_hindu_pujas
from apps.pujas.models import PujaCategory, Puja, PurohitPujaPackage
from apps.purohits.models import Purohit


class PujaListSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.household = PujaCategory.objects.create(
            name='Household Pujas', slug='household-pujas', icon='home'
        )
        self.weddings = PujaCategory.objects.create(
            name='Weddings', slug='weddings', icon='heart-handshake'
        )
        self.satya = Puja.objects.create(
            category=self.household,
            name='Satyanarayan Puja',
            description='Vishnu ritual',
            base_duration_hours=2.5,
        )
        self.vivah = Puja.objects.create(
            category=self.weddings,
            name='Vivah',
            description='Wedding ceremony',
            base_duration_hours=6.0,
        )

    def test_home_search_points_to_pujas(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('pujas:list'))
        self.assertContains(response, 'View all pujas')

    def test_search_filters_by_name(self):
        response = self.client.get(reverse('pujas:list'), {'q': 'Satyanarayan'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result_count'], 1)
        names = [p.name for pujas in response.context['categories'].values() for p in pujas]
        self.assertEqual(names, ['Satyanarayan Puja'])

    def test_category_filter(self):
        response = self.client.get(reverse('pujas:list'), {'category': 'weddings'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result_count'], 1)
        names = [p.name for pujas in response.context['categories'].values() for p in pujas]
        self.assertEqual(names, ['Vivah'])

    def test_catalog_and_purohit_venues_are_labeled_separately(self):
        self.vivah.typical_venues = 'home'
        self.vivah.save()
        user = CustomUser.objects.create_user(
            username='purohit_venue', phone='+919900000099', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=user, is_verified=True)
        city = City.objects.create(name='Hyderabad', state='Telangana')
        purohit = Purohit.objects.create(profile=profile, name='Pt. Venue', city=city, base_price=2100)
        PurohitPujaPackage.objects.create(
            purohit=purohit,
            puja=self.vivah,
            price=2998,
            venues='home,other',
        )

        response = self.client.get(reverse('pujas:list'), {'q': 'Vivah'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usually at')
        self.assertContains(response, 'Some purohits also')
        self.assertContains(response, 'Other arranged venue')
        vivah = [p for pujas in response.context['categories'].values() for p in pujas][0]
        self.assertEqual([item['code'] for item in vivah.get_typical_venue_items()], ['home'])
        self.assertEqual([item['code'] for item in vivah.extra_offered_venue_items], ['other'])

        filtered = self.client.get(reverse('pujas:list'), {'venue': 'other'})
        names = [p.name for pujas in filtered.context['categories'].values() for p in pujas]
        self.assertIn('Vivah', names)


class HinduCatalogTests(TestCase):
    def test_catalog_names_are_unique(self):
        names = [row[1] for row in PUJAS]
        self.assertEqual(len(names), len(set(n.lower() for n in names)))
        self.assertGreaterEqual(len(names), 80)

    def test_seed_is_idempotent(self):
        first = seed_hindu_pujas()
        second = seed_hindu_pujas()
        self.assertGreaterEqual(first['puja_total'], 80)
        self.assertEqual(second['pujas_created'], 0)
        self.assertEqual(first['puja_total'], second['puja_total'])
        self.assertTrue(Puja.objects.filter(name='Rudrabhishek').exists())
        self.assertTrue(PujaCategory.objects.filter(name='Festivals').exists())
        rudra = Puja.objects.get(name='Rudrabhishek')
        self.assertIn('temple', rudra.get_typical_venues())
        pind = Puja.objects.get(name='Pind Daan')
        self.assertIn('teerth', pind.get_typical_venues())
