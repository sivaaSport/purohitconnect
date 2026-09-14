from decimal import Decimal
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, OTP, PurohitProfile
from apps.accounts.utils import wallet_service
from apps.bookings.models import Booking, TravelRequest
from apps.core.models import Area, City, ServiceRequest
from apps.pujas.models import Puja, PujaCategory, PurohitPujaPackage
from apps.purohits.models import Purohit, PurohitMedia


class MobileApiTests(TestCase):
    def setUp(self):
        self.city = City.objects.create(name='Hyderabad', state='TG')
        self.area = Area.objects.create(city=self.city, name='Jubilee Hills', pincode='500033')
        self.phone = '+919876543210'
        self.customer = CustomUser.objects.create_user(
            username='devotee1',
            phone=self.phone,
            role='customer',
            first_name='Ananda',
            last_name='Bhakt',
        )
        self.purohit_user = CustomUser.objects.create_user(
            username='purohit1',
            phone='+919876543211',
            role='purohit',
        )
        profile = PurohitProfile.objects.create(
            user=self.purohit_user,
            experience_years=12,
            about='Vedic priest',
            is_verified=True,
        )
        self.purohit = Purohit.objects.create(
            profile=profile,
            name='Pt. Test Sharma',
            city=self.city,
            base_area=self.area,
            base_price=2100,
            is_featured=True,
        )
        category = PujaCategory.objects.create(name='Household Pujas', slug='household-pujas', icon='home')
        self.puja = Puja.objects.create(
            category=category,
            name='Satyanarayan Katha',
            description='Prosperity katha',
            base_duration_hours=2,
        )
        self.package = PurohitPujaPackage.objects.create(
            purohit=self.purohit,
            puja=self.puja,
            price=2100,
            samagri_price=400,
            duration_hours=2,
        )

    def _auth_headers(self, token):
        return {'HTTP_AUTHORIZATION': f'Bearer {token}', 'content_type': 'application/json'}

    def _login(self, phone=None):
        phone = phone or self.phone
        send = self.client.post(
            reverse('api:send_otp'),
            data={'phone': phone, 'action': 'login'},
            content_type='application/json',
        )
        self.assertEqual(send.status_code, 200)
        otp = OTP.objects.filter(phone=phone).latest('created_at')
        verify = self.client.post(
            reverse('api:verify_otp'),
            data={'phone': phone, 'otp_code': otp.otp_code, 'action': 'login'},
            content_type='application/json',
        )
        self.assertEqual(verify.status_code, 200)
        body = verify.json()
        self.assertTrue(body['success'])
        return body['token']

    def test_otp_login_returns_token(self):
        token = self._login()
        me = self.client.get(reverse('api:me'), **self._auth_headers(token))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['user']['phone'], self.phone)
        self.assertEqual(me.json()['user']['avatar_url'], '')

    def test_otp_resend_is_rate_limited(self):
        first = self.client.post(
            reverse('api:send_otp'),
            data={'phone': self.phone, 'action': 'login'},
            content_type='application/json',
        )
        self.assertEqual(first.status_code, 200, first.content)
        second = self.client.post(
            reverse('api:send_otp'),
            data={'phone': self.phone, 'action': 'login'},
            content_type='application/json',
        )
        self.assertEqual(second.status_code, 429)

    def test_cors_allows_local_flutter_origin(self):
        ok = self.client.get(reverse('api:categories'), HTTP_ORIGIN='http://localhost:5173')
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok['Access-Control-Allow-Origin'], 'http://localhost:5173')
        blocked = self.client.get(reverse('api:categories'), HTTP_ORIGIN='https://evil.example')
        self.assertEqual(blocked.status_code, 200)
        self.assertNotEqual(blocked.get('Access-Control-Allow-Origin'), 'https://evil.example')

    def test_signup_creates_customer(self):
        phone = '+919111122222'
        send = self.client.post(
            reverse('api:send_otp'),
            data={'phone': phone, 'action': 'signup'},
            content_type='application/json',
        )
        self.assertEqual(send.status_code, 200)
        otp = OTP.objects.filter(phone=phone).latest('created_at')
        verify = self.client.post(
            reverse('api:verify_otp'),
            data={'phone': phone, 'otp_code': otp.otp_code, 'action': 'signup', 'name': 'New Devotee'},
            content_type='application/json',
        )
        self.assertEqual(verify.status_code, 200)
        user = CustomUser.objects.get(phone=phone)
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.role, 'customer')

    def test_catalog_endpoints(self):
        cats = self.client.get(reverse('api:categories'))
        self.assertEqual(cats.status_code, 200)
        self.assertEqual(len(cats.json()['categories']), 1)
        purohits = self.client.get(reverse('api:purohits') + '?featured=true')
        self.assertEqual(purohits.status_code, 200)
        self.assertEqual(purohits.json()['purohits'][0]['name'], 'Pt. Test Sharma')
        detail = self.client.get(reverse('api:purohit_detail', args=[self.purohit.id]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.json()['purohit']['packages']), 1)
        self.assertEqual(detail.json()['purohit']['gallery'], [])

    def test_purohit_detail_includes_ritual_gallery(self):
        PurohitMedia.objects.create(
            purohit=self.purohit,
            media_type='photo',
            file=SimpleUploadedFile('satyanarayan.jpg', b'fake-image-bytes', content_type='image/jpeg'),
            title='Satyanarayan Puja',
            caption='Home ceremony in Jubilee Hills',
            is_featured=True,
        )
        detail = self.client.get(reverse('api:purohit_detail', args=[self.purohit.id]))
        self.assertEqual(detail.status_code, 200)
        gallery = detail.json()['purohit']['gallery']
        self.assertEqual(len(gallery), 1)
        self.assertEqual(gallery[0]['title'], 'Satyanarayan Puja')
        self.assertEqual(gallery[0]['caption'], 'Home ceremony in Jubilee Hills')
        self.assertEqual(gallery[0]['media_type'], 'photo')
        self.assertTrue(gallery[0]['url'])
        listed = self.client.get(reverse('api:purohits'))
        self.assertEqual(listed.json()['purohits'][0]['gallery'], [])
        self.assertIsNone(listed.json()['purohits'][0].get('coverage'))
        self.assertIn('coverage', detail.json()['purohit'])
        self.assertTrue(detail.json()['purohit']['coverage']['acceptsTravel'])

    def test_catalog_follows_sacred_ritual_order(self):
        household = PujaCategory.objects.get(name='Household Pujas')
        PujaCategory.objects.create(name='Ancestral Rites', slug='ancestral-rites')
        PujaCategory.objects.create(name='Festivals', slug='festivals')
        Puja.objects.create(
            category=household,
            name='Bhoomi Puja',
            description='Plot puja',
            base_duration_hours=2,
        )
        Puja.objects.create(
            category=household,
            name='Griha Pravesh',
            description='Housewarming',
            base_duration_hours=4,
        )
        cats = self.client.get(reverse('api:categories'))
        self.assertEqual(
            [c['name'] for c in cats.json()['categories']],
            ['Household Pujas', 'Festivals', 'Ancestral Rites'],
        )
        pujas = self.client.get(reverse('api:pujas'))
        self.assertEqual(pujas.status_code, 200)
        names = [p['name'] for p in pujas.json()['pujas']]
        self.assertLess(names.index('Griha Pravesh'), names.index('Bhoomi Puja'))

    def test_featured_pujas_and_empty_travel_requests(self):
        household = PujaCategory.objects.get(name='Household Pujas')
        Puja.objects.create(
            category=household,
            name='Satyanarayan Puja',
            description='Prosperity katha',
            base_duration_hours=2,
        )
        featured = self.client.get(reverse('api:pujas'), {'featured': 'true'})
        self.assertEqual(featured.status_code, 200)
        names = [p['name'] for p in featured.json()['pujas']]
        self.assertEqual(names[0], 'Satyanarayan Puja')
        self.assertLessEqual(len(names), 4)
        token = self._login()
        travel = self.client.get(reverse('api:travel_requests'), **self._auth_headers(token))
        self.assertEqual(travel.status_code, 200)
        self.assertEqual(travel.json()['travel_requests'], [])
        self.assertEqual(travel.json()['pending_count'], 0)

    def test_create_booking_and_wallet_pay(self):
        wallet_service.credit_wallet(self.customer, Decimal('5000'), 'top_up', 'seed')
        token = self._login()
        event_date = (timezone.localdate() + timedelta(days=5)).isoformat()
        create = self.client.post(
            reverse('api:create_booking'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '09:00',
                'address': 'Plot 42, Jubilee Hills',
                'city_id': self.city.id,
                'area_id': self.area.id,
                'venue_type': 'home',
                'needs_samagri': True,
            },
            **self._auth_headers(token),
        )
        self.assertEqual(create.status_code, 200, create.content)
        booking_id = create.json()['booking']['booking_id']
        pay = self.client.post(
            reverse('api:booking_pay', args=[booking_id]),
            data={'method': 'wallet'},
            **self._auth_headers(token),
        )
        self.assertEqual(pay.status_code, 200, pay.content)
        self.assertTrue(pay.json()['paid'])
        booking = Booking.objects.get(booking_id=booking_id)
        self.assertEqual(booking.payment_status, 'success')
        self.assertEqual(booking.total_amount, Decimal('2500.00'))

    def test_razorpay_pay_returns_checkout_payload(self):
        token = self._login()
        event_date = (timezone.localdate() + timedelta(days=5)).isoformat()
        create = self.client.post(
            reverse('api:create_booking'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '09:00',
                'address': 'Plot 42, Jubilee Hills',
                'city_id': self.city.id,
                'area_id': self.area.id,
                'venue_type': 'home',
            },
            **self._auth_headers(token),
        )
        self.assertEqual(create.status_code, 200, create.content)
        booking_id = create.json()['booking']['booking_id']
        pay = self.client.post(
            reverse('api:booking_pay', args=[booking_id]),
            data={'method': 'razorpay'},
            **self._auth_headers(token),
        )
        self.assertEqual(pay.status_code, 200, pay.content)
        order = pay.json()['razorpay']
        self.assertTrue(order['id'])
        self.assertIn('key', order)
        self.assertTrue(order['mock'] or str(order['id']).startswith('order_mock_') or str(order['id']).startswith('order_'))
        verify = self.client.post(
            reverse('api:verify_booking_payment', args=[booking_id]),
            data={
                'razorpay_order_id': order['id'],
                'razorpay_payment_id': 'pay_mock_1',
                'razorpay_signature': 'mock_signature',
            },
            **self._auth_headers(token),
        )
        if order.get('mock'):
            self.assertEqual(verify.status_code, 200, verify.content)
            self.assertTrue(verify.json()['paid'])
        else:
            self.assertEqual(verify.status_code, 400)

    def test_support_ticket(self):
        token = self._login()
        res = self.client.post(
            reverse('api:support'),
            data={'subject': 'Help', 'description': 'Need assistance', 'category': 'booking'},
            **self._auth_headers(token),
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(ServiceRequest.objects.filter(user=self.customer).exists())

    def test_travel_request_for_unserved_area(self):
        outside = Area.objects.create(city=self.city, name='Gachibowli', pincode='500032')
        token = self._login()
        event_date = (timezone.localdate() + timedelta(days=5)).isoformat()
        blocked = self.client.post(
            reverse('api:create_booking'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '09:00',
                'address': 'Far away',
                'city_id': self.city.id,
                'area_id': outside.id,
                'venue_type': 'home',
            },
            **self._auth_headers(token),
        )
        self.assertEqual(blocked.status_code, 400)
        self.assertEqual(blocked.json()['code'], 'travel_request_required')

        created = self.client.post(
            reverse('api:travel_requests'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '09:00',
                'address': 'Far away',
                'city_id': self.city.id,
                'area_id': outside.id,
                'venue_type': 'home',
                'message': 'Family house is here',
            },
            **self._auth_headers(token),
        )
        self.assertEqual(created.status_code, 200, created.content)
        self.assertEqual(created.json()['code'], 'created')
        travel = TravelRequest.objects.get()
        self.assertEqual(travel.status, 'pending')
        self.assertEqual(travel.area, outside)
        listed = self.client.get(reverse('api:travel_requests'), **self._auth_headers(token))
        self.assertEqual(listed.json()['pending_count'], 1)

        again = self.client.post(
            reverse('api:travel_requests'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '09:00',
                'address': 'Far away',
                'city_id': self.city.id,
                'area_id': outside.id,
                'venue_type': 'home',
            },
            **self._auth_headers(token),
        )
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()['code'], 'already_open')
        self.assertEqual(TravelRequest.objects.count(), 1)

    def test_customer_cannot_open_purohit_workspace(self):
        token = self._login()
        res = self.client.get(reverse('api:purohit_dashboard'), **self._auth_headers(token))
        self.assertEqual(res.status_code, 403)

    def test_purohit_confirms_paid_booking_and_handles_travel(self):
        from apps.core.models import Notification

        wallet_service.credit_wallet(self.customer, Decimal('5000'), 'top_up', 'seed')
        devotee = self._login()
        event_date = (timezone.localdate() + timedelta(days=5)).isoformat()
        create = self.client.post(
            reverse('api:create_booking'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '09:00',
                'address': 'Plot 42, Jubilee Hills',
                'city_id': self.city.id,
                'area_id': self.area.id,
                'venue_type': 'home',
            },
            **self._auth_headers(devotee),
        )
        booking_id = create.json()['booking']['booking_id']
        self.client.post(
            reverse('api:booking_pay', args=[booking_id]),
            data={'method': 'wallet'},
            **self._auth_headers(devotee),
        )
        priest = self._login(self.purohit_user.phone)
        dash = self.client.get(reverse('api:purohit_dashboard'), **self._auth_headers(priest))
        self.assertEqual(dash.status_code, 200, dash.content)
        self.assertEqual(dash.json()['stats']['pending_requests'], 1)
        confirm = self.client.post(
            reverse('api:purohit_booking_status', args=[booking_id]),
            data={'status': 'confirmed'},
            **self._auth_headers(priest),
        )
        self.assertEqual(confirm.status_code, 200, confirm.content)
        self.assertEqual(confirm.json()['code'], 'confirmed')
        detail = self.client.get(reverse('api:booking_detail', args=[booking_id]), **self._auth_headers(devotee))
        self.assertTrue(detail.json()['booking']['start_code'])
        self.assertNotIn('start_code', confirm.json()['booking'])

        outside = Area.objects.create(city=self.city, name='Madhapur', pincode='500081')
        travel = self.client.post(
            reverse('api:travel_requests'),
            data={
                'package_id': self.package.id,
                'event_date': event_date,
                'event_time': '11:00',
                'address': 'Far house',
                'city_id': self.city.id,
                'area_id': outside.id,
                'venue_type': 'home',
            },
            **self._auth_headers(devotee),
        )
        request_pk = travel.json()['travel_request']['id']
        accept = self.client.post(
            reverse('api:purohit_travel_respond', args=[request_pk]),
            data={'decision': 'accept', 'travel_fee': 400},
            **self._auth_headers(priest),
        )
        self.assertEqual(accept.status_code, 200, accept.content)
        self.assertEqual(accept.json()['code'], 'accepted')
        self.assertTrue(Notification.objects.filter(title='Travel request accepted').exists())

    def test_purohit_manages_packages_and_calendar(self):
        extra = Puja.objects.create(
            category=self.puja.category,
            name='Griha Pravesh',
            description='Housewarming',
            base_duration_hours=4,
        )
        priest = self._login(self.purohit_user.phone)
        listed = self.client.get(reverse('api:purohit_packages'), **self._auth_headers(priest))
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(len(listed.json()['packages']), 1)
        names = {item['name'] for item in listed.json()['available_pujas']}
        self.assertIn('Griha Pravesh', names)

        added = self.client.post(
            reverse('api:purohit_packages'),
            data={
                'action': 'add',
                'puja_id': extra.id,
                'price': 4500,
                'duration_hours': 4,
                'buffer_minutes': 45,
                'includes_samagri': True,
                'samagri_price': 300,
                'venues': ['home', 'temple'],
                'venue_notes': 'I also go to the local mandir',
            },
            **self._auth_headers(priest),
        )
        self.assertEqual(added.status_code, 200, added.content)
        self.assertEqual(added.json()['code'], 'added')
        self.assertEqual(len(added.json()['packages']), 2)
        new_pkg = next(item for item in added.json()['packages'] if item['puja_id'] == extra.id)
        self.assertEqual(new_pkg['price'], 4500)
        self.assertEqual([v['code'] for v in new_pkg['venues']], ['home', 'temple'])

        updated = self.client.post(
            reverse('api:purohit_packages'),
            data={'action': 'update', 'package_id': self.package.id, 'price': 2500, 'duration_hours': 2, 'buffer_minutes': 30},
            **self._auth_headers(priest),
        )
        self.assertEqual(updated.status_code, 200, updated.content)
        satya = next(item for item in updated.json()['packages'] if item['id'] == self.package.id)
        self.assertEqual(satya['price'], 2500)

        blocked = self.client.post(
            reverse('api:purohit_calendar'),
            data={
                'action': 'add_range',
                'date': '2026-10-20',
                'start_time': '10:00',
                'end_time': '12:00',
                'reason': 'Temple duty',
            },
            **self._auth_headers(priest),
        )
        self.assertEqual(blocked.status_code, 200, blocked.content)
        self.assertEqual(blocked.json()['code'], 'range_blocked')
        self.assertEqual(blocked.json()['selected_day'], '2026-10-20')
        self.assertEqual(blocked.json()['selected_blocks'][0]['start_time'], '10:00')

        month = self.client.get(
            reverse('api:purohit_calendar') + '?year=2026&month=10&day=2026-10-20',
            **self._auth_headers(priest),
        )
        self.assertEqual(month.status_code, 200)
        self.assertEqual(month.json()['month'], 10)
        day = next(
            cell
            for week in month.json()['weeks']
            for cell in week
            if cell['date'] == '2026-10-20'
        )
        self.assertEqual(day['status'], 'partial')

        hours = self.client.post(
            reverse('api:purohit_calendar'),
            data={'action': 'set_work_hours', 'work_start': '07:00', 'work_end': '20:00', 'date': '2026-10-20'},
            **self._auth_headers(priest),
        )
        self.assertEqual(hours.status_code, 200, hours.content)
        self.assertEqual(hours.json()['work_start'], '07:00')
        self.assertEqual(hours.json()['work_end'], '20:00')

        devotee = self._login()
        denied = self.client.get(reverse('api:purohit_packages'), **self._auth_headers(devotee))
        self.assertEqual(denied.status_code, 403)
