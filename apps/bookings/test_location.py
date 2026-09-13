from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, PurohitProfile
from apps.bookings.location import covers, coverage_payload, served_areas, validate_booking_location
from apps.bookings.models import Booking, TravelRequest
from apps.core.models import Area, City
from apps.pujas.models import Puja, PujaCategory, PurohitPujaPackage
from apps.purohits.models import Purohit, PurohitServiceOffer


class LocationMatchingTests(TestCase):
    def setUp(self):
        self.hyderabad = City.objects.create(name='Hyderabad', state='Telangana')
        self.gaya = City.objects.create(name='Gaya', state='Bihar')
        self.kphb = Area.objects.create(city=self.hyderabad, name='Kukatpally', pincode='500072')
        self.banjara = Area.objects.create(city=self.hyderabad, name='Banjara Hills', pincode='500034')
        self.secunderabad = Area.objects.create(city=self.hyderabad, name='Secunderabad', pincode='500003')
        self.gaya_area = Area.objects.create(city=self.gaya, name='Vishnupad', pincode='823001')

        self.customer = CustomUser.objects.create_user(
            username='devotee_loc', phone='+919900000111', role='customer', password='pass1234'
        )
        purohit_user = CustomUser.objects.create_user(
            username='purohit_loc', phone='+919900000112', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=purohit_user, is_verified=True)
        self.purohit = Purohit.objects.create(
            profile=profile,
            name='Pt. Location',
            city=self.hyderabad,
            base_area=self.kphb,
            base_price=2100,
        )
        self.purohit.service_areas.add(self.kphb, self.banjara)
        for area in (self.kphb, self.banjara):
            PurohitServiceOffer.objects.create(
                purohit=self.purohit,
                city=self.hyderabad,
                area=area,
                kind=PurohitServiceOffer.KIND_PERMANENT,
            )
        self.day = date(2026, 5, 10)

        category = PujaCategory.objects.create(name='Weddings', slug='weddings')
        self.haldi = Puja.objects.create(
            category=category, name='Haldi Ceremony', description='Test', base_duration_hours=1.5
        )
        self.pind = Puja.objects.create(
            category=category, name='Pind Daan', description='Test', base_duration_hours=2.0
        )
        self.home_package = PurohitPujaPackage.objects.create(
            purohit=self.purohit, puja=self.haldi, price=2998, venues='home,other'
        )
        self.teerth_package = PurohitPujaPackage.objects.create(
            purohit=self.purohit,
            puja=self.pind,
            price=5100,
            venues='teerth,temple',
            venue_notes='I travel to Gaya',
        )
        self.place_package = PurohitPujaPackage.objects.create(
            purohit=self.purohit,
            puja=Puja.objects.create(
                category=category, name='Satyanarayan Puja', description='Test', base_duration_hours=2
            ),
            price=2100,
            venues='purohit',
        )

    def test_served_areas_use_permanent_offers(self):
        names = [area.name for area in served_areas(self.purohit)]
        self.assertEqual(names, ['Banjara Hills', 'Kukatpally'])

    def test_coverage_payload_lists_places_for_devotee_ui(self):
        payload = coverage_payload(self.purohit)
        labels = [item['label'] for item in payload['places']]
        self.assertTrue(any('Kukatpally' in label for label in labels))
        self.assertIn('acceptsTravel', payload)
        self.assertIn('purohitName', payload)

    def test_home_in_offered_area_is_accepted(self):
        ok, error, data = validate_booking_location(
            self.home_package, 'home', self.hyderabad, self.banjara, '12 Road No. 1', on_date=self.day
        )
        self.assertTrue(ok, error)
        self.assertEqual(data['venue_type'], 'home')
        self.assertEqual(data['area'], self.banjara)

    def test_home_outside_offer_is_rejected(self):
        ok, error, data = validate_booking_location(
            self.home_package, 'home', self.hyderabad, self.secunderabad, 'Somewhere else', on_date=self.day
        )
        self.assertFalse(ok)
        self.assertIsNone(data)
        self.assertIn('does not offer', error)
        self.assertIn('request a visit', error)

    def test_purohit_place_locks_base_area(self):
        ok, error, data = validate_booking_location(
            self.place_package, 'purohit', self.gaya, self.gaya_area, 'ignored', on_date=self.day
        )
        self.assertTrue(ok, error)
        self.assertEqual(data['city'], self.hyderabad)
        self.assertEqual(data['area'], self.kphb)
        self.assertIn("purohit's place", data['address'])

    def test_teerth_note_does_not_unlock_destination(self):
        ok, error, data = validate_booking_location(
            self.teerth_package, 'teerth', self.gaya, self.gaya_area, 'Vishnupad Ghat', on_date=self.day
        )
        self.assertFalse(ok)
        self.assertIn('does not offer', error)

    def test_visit_offer_unlocks_destination_on_those_dates(self):
        PurohitServiceOffer.objects.create(
            purohit=self.purohit,
            city=self.gaya,
            area=self.gaya_area,
            kind=PurohitServiceOffer.KIND_VISIT,
            start_date=date(2026, 10, 12),
            end_date=date(2026, 10, 18),
        )
        ok, error, data = validate_booking_location(
            self.teerth_package, 'teerth', self.gaya, self.gaya_area, 'Vishnupad Ghat',
            on_date=date(2026, 10, 15),
        )
        self.assertTrue(ok, error)
        self.assertEqual(data['city'], self.gaya)
        self.assertFalse(covers(self.purohit, self.gaya, self.gaya_area, date(2026, 10, 20)))

    def test_accepted_travel_request_unlocks_and_adds_fee(self):
        travel = TravelRequest.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.home_package,
            city=self.gaya,
            area=self.gaya_area,
            address='A hall in Gaya',
            venue_type='other',
            preferred_date=self.day,
            status='accepted',
            travel_fee=1500,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        ok, error, data = validate_booking_location(
            self.home_package, 'other', self.gaya, self.gaya_area, 'A hall in Gaya',
            on_date=self.day, devotee=self.customer,
        )
        self.assertTrue(ok, error)
        self.assertEqual(data['travel_request'], travel)
        self.assertEqual(data['travel_fee'], travel.travel_fee)

    def test_invalid_venue_is_rejected(self):
        ok, error, data = validate_booking_location(
            self.place_package, 'home', self.hyderabad, self.kphb, 'My house', on_date=self.day
        )
        self.assertFalse(ok)
        self.assertIsNone(data)
        self.assertIn('choose a place', error)

    def test_area_must_belong_to_city(self):
        ok, error, _data = validate_booking_location(
            self.home_package, 'home', self.hyderabad, self.gaya_area, 'Mismatch', on_date=self.day
        )
        self.assertFalse(ok)
        self.assertIn('not in the selected city', error)


class BookingLocationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.city = City.objects.create(name='Hyderabad', state='Telangana')
        self.area = Area.objects.create(city=self.city, name='Kukatpally', pincode='500072')
        self.outside = Area.objects.create(city=self.city, name='Secunderabad', pincode='500003')
        self.customer = CustomUser.objects.create_user(
            username='book_loc', phone='+919900000211', role='customer', password='pass1234'
        )
        purohit_user = CustomUser.objects.create_user(
            username='book_purohit', phone='+919900000212', role='purohit', password='pass1234'
        )
        profile = PurohitProfile.objects.create(user=purohit_user, is_verified=True)
        self.purohit = Purohit.objects.create(
            profile=profile, name='Pt. Book Loc', city=self.city, base_area=self.area, base_price=2100
        )
        self.purohit.service_areas.add(self.area)
        PurohitServiceOffer.objects.create(
            purohit=self.purohit, city=self.city, area=self.area, kind=PurohitServiceOffer.KIND_PERMANENT
        )
        category = PujaCategory.objects.create(name='Household')
        puja = Puja.objects.create(category=category, name='Haldi Ceremony', description='Test', base_duration_hours=1)
        self.package = PurohitPujaPackage.objects.create(
            purohit=self.purohit, puja=puja, price=2000, venues='home'
        )
        self.client.force_login(self.customer)

    def test_book_page_shows_coverage_and_all_areas(self):
        response = self.client.get(reverse('bookings:book', args=[self.package.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kukatpally')
        self.assertContains(response, 'Where will the ritual happen?')
        self.assertContains(response, 'Request a visit')
        self.assertContains(response, 'Places they already offer')
        self.assertContains(response, 'Other cities — request a visit first')
        served_names = [area.name for area in response.context['served_areas']]
        self.assertEqual(served_names, ['Kukatpally'])
        payload = response.context['areas_by_city']
        self.assertIn(self.area.id, [item['id'] for item in payload[self.city.id]])
        self.assertIn(self.outside.id, [item['id'] for item in payload[self.city.id]])

    def test_post_rejects_unserved_home_area(self):
        response = self.client.post(reverse('bookings:book', args=[self.package.id]), {
            'date': '2026-05-10',
            'time': '09:00',
            'venue_type': 'home',
            'address': 'Far away',
            'city': self.city.id,
            'area': self.outside.id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 0)
        self.assertEqual(response.url, reverse('bookings:book', args=[self.package.id]))

    def test_devotee_can_request_travel_instead_of_booking(self):
        response = self.client.post(reverse('bookings:request_travel', args=[self.package.id]), {
            'date': '2026-05-10',
            'time': '09:00',
            'venue_type': 'home',
            'address': 'Far away',
            'city': self.city.id,
            'area': self.outside.id,
            'message': 'Family house is here',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 0)
        request = TravelRequest.objects.get()
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.area, self.outside)
        self.assertEqual(request.purohit, self.purohit)

    def test_accepted_request_can_be_booked_with_fee(self):
        travel = TravelRequest.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            city=self.city,
            area=self.outside,
            address='Far away',
            venue_type='home',
            preferred_date=date(2026, 5, 10),
            status='accepted',
            travel_fee=800,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        response = self.client.post(reverse('bookings:book', args=[self.package.id]), {
            'date': '2026-05-10',
            'time': '09:00',
            'venue_type': 'home',
            'address': 'Far away',
            'city': self.city.id,
            'area': self.outside.id,
        })
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get()
        self.assertEqual(booking.travel_fee, travel.travel_fee)
        self.assertEqual(booking.total_amount, 2800)
        travel.refresh_from_db()
        self.assertEqual(travel.status, 'booked')
