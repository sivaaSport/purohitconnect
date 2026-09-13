from decimal import Decimal
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, OTP, PurohitProfile
from apps.accounts.utils import wallet_service
from apps.bookings.models import Booking
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

    def test_support_ticket(self):
        token = self._login()
        res = self.client.post(
            reverse('api:support'),
            data={'subject': 'Help', 'description': 'Need assistance', 'category': 'booking'},
            **self._auth_headers(token),
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(ServiceRequest.objects.filter(user=self.customer).exists())
