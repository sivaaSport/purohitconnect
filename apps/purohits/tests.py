from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import CustomUser, PurohitProfile
from apps.core.models import City, Area, Language
from apps.pujas.models import PujaCategory, Puja, PurohitPujaPackage
from apps.purohits.models import Purohit, PurohitAvailability, PurohitServiceOffer


class PurohitDiscoveryFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hyderabad = City.objects.create(name='Hyderabad', state='Telangana')
        self.bangalore = City.objects.create(name='Bangalore', state='Karnataka')
        self.hyd_area = Area.objects.create(city=self.hyderabad, name='Kukatpally', pincode='500072')
        self.blr_area = Area.objects.create(city=self.bangalore, name='Koramangala', pincode='560034')

        self.telugu = Language.objects.create(name='Telugu', native_name='తెలుగు')
        self.kannada = Language.objects.create(name='Kannada', native_name='ಕನ್ನಡ')

        category = PujaCategory.objects.create(name='Household')
        self.satyanarayan = Puja.objects.create(
            category=category,
            name='Satyanarayan Puja',
            description='Test',
            base_duration_hours=2.0,
        )
        self.griha = Puja.objects.create(
            category=category,
            name='Griha Pravesh',
            description='Test',
            base_duration_hours=3.0,
        )

        hyd_user = CustomUser.objects.create_user(
            username='purohit_hyd', phone='+919900000001', role='purohit', password='pass1234'
        )
        hyd_profile = PurohitProfile.objects.create(user=hyd_user, is_verified=True)
        hyd_profile.languages_spoken.add(self.telugu)
        self.hyd_purohit = Purohit.objects.create(
            profile=hyd_profile,
            name='Pt. Hyd Sharma',
            city=self.hyderabad,
            base_area=self.hyd_area,
            base_price=2100,
        )
        PurohitPujaPackage.objects.create(
            purohit=self.hyd_purohit, puja=self.satyanarayan, price=2100, includes_samagri=False
        )

        blr_user = CustomUser.objects.create_user(
            username='purohit_blr', phone='+919900000002', role='purohit', password='pass1234'
        )
        blr_profile = PurohitProfile.objects.create(user=blr_user, is_verified=True)
        blr_profile.languages_spoken.add(self.kannada)
        self.blr_purohit = Purohit.objects.create(
            profile=blr_profile,
            name='Pt. Blr Rao',
            city=self.bangalore,
            base_area=self.blr_area,
            base_price=2500,
        )
        PurohitPujaPackage.objects.create(
            purohit=self.blr_purohit, puja=self.griha, price=5100, includes_samagri=True
        )

    def test_list_renders_db_cities_and_languages(self):
        response = self.client.get(reverse('purohits:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hyderabad')
        self.assertContains(response, 'Bangalore')
        self.assertContains(response, 'Telugu')
        self.assertContains(response, 'Kannada')
        self.assertContains(response, f'value="{self.hyderabad.id}"')
        self.assertContains(response, f'value="{self.telugu.id}"')
        self.assertNotContains(response, 'value="1">Hyderabad</option>')

    def test_filter_by_city(self):
        response = self.client.get(reverse('purohits:list'), {'city': self.hyderabad.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hyd_purohit.name)
        self.assertNotContains(response, self.blr_purohit.name)
        self.assertEqual(response.context['selected_city'], self.hyderabad.id)

    def test_city_filter_includes_upcoming_visit(self):
        from datetime import date
        PurohitServiceOffer.objects.create(
            purohit=self.blr_purohit,
            city=self.hyderabad,
            area=self.hyd_area,
            kind=PurohitServiceOffer.KIND_VISIT,
            start_date=date(2026, 10, 12),
            end_date=date(2026, 10, 18),
        )
        response = self.client.get(reverse('purohits:list'), {'city': self.hyderabad.id})
        self.assertContains(response, self.hyd_purohit.name)
        self.assertContains(response, self.blr_purohit.name)
        self.assertContains(response, 'Visiting')

    def test_filter_by_language(self):
        response = self.client.get(reverse('purohits:list'), {'language': self.kannada.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.blr_purohit.name)
        self.assertNotContains(response, self.hyd_purohit.name)
        self.assertEqual(response.context['selected_language'], self.kannada.id)

    def test_filter_by_puja(self):
        response = self.client.get(reverse('purohits:list'), {'puja': self.griha.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.blr_purohit.name)
        self.assertNotContains(response, self.hyd_purohit.name)

    def test_puja_filter_keeps_ritual_on_cards_and_profile(self):
        response = self.client.get(reverse('purohits:list'), {'puja': self.satyanarayan.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['focus_puja'], self.satyanarayan)
        self.assertContains(response, 'Book Satyanarayan Puja')
        self.assertContains(response, f'{reverse("purohits:detail", args=[self.hyd_purohit.slug])}?puja={self.satyanarayan.id}')
        self.assertContains(response, reverse('bookings:book', args=[
            self.hyd_purohit.puja_packages.get(puja=self.satyanarayan).id
        ]))

        detail = self.client.get(
            reverse('purohits:detail', args=[self.hyd_purohit.slug]),
            {'puja': self.satyanarayan.id},
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.context['focus_package'].puja, self.satyanarayan)
        self.assertContains(detail, 'Ready to book')
        self.assertContains(detail, 'Your ritual')
        self.assertContains(detail, 'Satyanarayan Puja with')

    def test_search_query(self):
        response = self.client.get(reverse('purohits:list'), {'q': 'Hyd'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hyd_purohit.name)
        self.assertNotContains(response, self.blr_purohit.name)

    def test_invalid_filter_ids_ignored(self):
        response = self.client.get(reverse('purohits:list'), {'city': 'abc', 'language': '-1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hyd_purohit.name)
        self.assertContains(response, self.blr_purohit.name)


class PurohitWorkspaceSetupTests(TestCase):
    def setUp(self):
        self.city = City.objects.create(name='Hyderabad', state='Telangana')

    def test_ensure_purohit_listing_creates_missing_listing(self):
        from apps.purohits.services import ensure_purohit_listing

        user = CustomUser.objects.create_user(
            username='new_purohit', phone='+919911122233', role='purohit', password='pass1234'
        )
        PurohitProfile.objects.create(user=user)
        self.assertFalse(Purohit.objects.filter(profile__user=user).exists())

        listing = ensure_purohit_listing(user)
        self.assertIsNotNone(listing)
        self.assertEqual(listing.city, self.city)
        self.assertTrue(listing.name.startswith('Pt.'))
        self.assertEqual(Purohit.objects.filter(profile__user=user).count(), 1)

    def test_purohit_dashboard_opens_for_profile_without_listing(self):
        user = CustomUser.objects.create_user(
            username='dash_purohit', phone='+919911122244', role='purohit', password='pass1234'
        )
        PurohitProfile.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:purohit'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Service locations')
        self.assertContains(response, "Today's work")
        self.assertContains(response, 'Travel requests are on')
        self.assertTrue(Purohit.objects.filter(profile__user=user).exists())

    def test_purohit_can_update_service_locations(self):
        user = CustomUser.objects.create_user(
            username='loc_purohit', phone='+919911122266', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=user)
        area = Area.objects.create(city=self.city, name='Kukatpally', pincode='500072')
        other = Area.objects.create(city=self.city, name='Banjara Hills', pincode='500034')
        purohit = Purohit.objects.create(profile=profile, name='Pt. Areas', city=self.city, base_area=area)
        self.client.force_login(user)

        response = self.client.post(reverse('dashboard:update_travel_policy'), {
            'travel_note': 'I come if devotee covers train',
            'accepts_travel_requests': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('#travel-requests', response.url)
        purohit.refresh_from_db()
        self.assertEqual(purohit.travel_note, 'I come if devotee covers train')
        self.assertTrue(purohit.accepts_travel_requests)

        turned_off = self.client.post(reverse('dashboard:update_travel_policy'), {
            'travel_note': '',
            'accepts_travel_requests': 'off',
        })
        self.assertEqual(turned_off.status_code, 302)
        purohit.refresh_from_db()
        self.assertEqual(purohit.travel_note, '')
        self.assertFalse(purohit.accepts_travel_requests)

        citywide = self.client.post(reverse('dashboard:add_service_offer'), {
            'kind': 'permanent',
            'city': self.city.id,
            'area': '',
        })
        self.assertEqual(citywide.status_code, 302)
        self.assertTrue(
            PurohitServiceOffer.objects.filter(
                purohit=purohit, city=self.city, area__isnull=True, kind=PurohitServiceOffer.KIND_PERMANENT
            ).exists()
        )

        add = self.client.post(reverse('dashboard:add_service_offer'), {
            'kind': 'permanent',
            'city': self.city.id,
            'area': other.id,
        })
        self.assertEqual(add.status_code, 302)
        self.assertTrue(
            PurohitServiceOffer.objects.filter(
                purohit=purohit, area=other, kind=PurohitServiceOffer.KIND_PERMANENT
            ).exists()
        )

        visit = self.client.post(reverse('dashboard:add_service_offer'), {
            'kind': 'visit',
            'city': self.city.id,
            'area': other.id,
            'start_date': '2026-10-12',
            'end_date': '2026-10-18',
            'note': 'Family visit',
        })
        self.assertEqual(visit.status_code, 302)
        self.assertTrue(
            PurohitServiceOffer.objects.filter(
                purohit=purohit, kind=PurohitServiceOffer.KIND_VISIT, city=self.city
            ).exists()
        )

    def test_home_redirects_purohit_to_dashboard(self):
        user = CustomUser.objects.create_user(
            username='home_purohit', phone='+919911122255', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=user)
        Purohit.objects.create(profile=profile, name='Pt. Home', city=self.city)
        self.client.force_login(user)

        response = self.client.get(reverse('core:home'))
        self.assertRedirects(response, reverse('dashboard:purohit'))

    def test_purohit_can_add_package_and_block_date(self):
        from apps.pujas.models import PujaCategory
        from apps.purohits.models import PurohitAvailability
        from decimal import Decimal

        category = PujaCategory.objects.create(name='Household', icon='home')
        puja = Puja.objects.create(
            category=category, name='Satyanarayan Puja', description='Test', base_duration_hours=2
        )
        user = CustomUser.objects.create_user(
            username='pkg_purohit', phone='+919911122266', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=user)
        Purohit.objects.create(profile=profile, name='Pt. Package', city=self.city)
        self.client.force_login(user)

        response = self.client.post(reverse('dashboard:manage_package'), {
            'action': 'add',
            'puja_id': puja.id,
            'price': '2100',
            'includes_samagri': 'on',
            'samagri_price': '250',
            'venues': ['home', 'temple'],
            'venue_notes': 'I also go to the local mandir',
        })
        self.assertEqual(response.status_code, 302)
        package = PurohitPujaPackage.objects.get(purohit__profile__user=user, puja=puja)
        self.assertEqual(package.price, Decimal('2100'))
        self.assertEqual(package.get_venues(), ['home', 'temple'])
        self.assertEqual(package.venue_notes, 'I also go to the local mandir')

        response = self.client.post(reverse('dashboard:toggle_availability'), {
            'action': 'add_range',
            'date': '2026-09-20',
            'start_time': '10:00',
            'end_time': '12:00',
            'reason': 'Temple duty',
        })
        self.assertEqual(response.status_code, 302)
        block = PurohitAvailability.objects.get(purohit__profile__user=user, date='2026-09-20')
        self.assertEqual(block.start_time.strftime('%H:%M'), '10:00')
        self.assertEqual(block.end_time.strftime('%H:%M'), '12:00')
        self.assertFalse(block.is_available)

    def test_timed_slots_respect_blocks(self):
        from datetime import date, time
        from apps.purohits.utils import get_day_slots, check_purohit_availability, add_block

        user = CustomUser.objects.create_user(
            username='slot_purohit', phone='+919911122277', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=user)
        purohit = Purohit.objects.create(profile=profile, name='Pt. Slots', city=self.city)
        day = date(2026, 9, 22)
        add_block(purohit, day, time(10, 0), time(12, 0), 'Busy')

        slots = get_day_slots(purohit, day, duration_hours=2)
        ten = next(s for s in slots if s['value'] == '10:00')
        eight = next(s for s in slots if s['value'] == '08:00')
        self.assertFalse(ten['available'])
        self.assertTrue(eight['available'])
        ok, _ = check_purohit_availability(purohit, day, time_obj=time(8, 0), duration_hours=2)
        bad, _ = check_purohit_availability(purohit, day, time_obj=time(10, 0), duration_hours=2)
        self.assertTrue(ok)
        self.assertFalse(bad)