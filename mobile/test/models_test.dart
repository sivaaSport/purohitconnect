import 'package:flutter_test/flutter_test.dart';
import 'package:purohit_mobile/core/models/models.dart';

void main() {
  group('UserModel.fromJson', () {
    test('treats purohit role as canActAsPurohit', () {
      final user = UserModel.fromJson({
        'id': 7,
        'phone': '+919876543210',
        'username': 'pandit',
        'name': 'Pandit Rao',
        'role': 'purohit',
        'wallet_balance': '150.50',
        'is_phone_verified': true,
      });
      expect(user.canActAsPurohit, isTrue);
      expect(user.walletBalance, 150.5);
    });

    test('keeps devotee role from acting as purohit unless flagged', () {
      final user = UserModel.fromJson({
        'id': 1,
        'phone': '+919111111111',
        'username': 'devotee',
        'role': 'customer',
        'wallet_balance': 0,
        'is_phone_verified': 1,
        'can_act_as_purohit': false,
      });
      expect(user.canActAsPurohit, isFalse);
      expect(user.name, 'devotee');
    });
  });

  group('BookingModel', () {
    test('maps confirm flags, start code, and started_at', () {
      final booking = BookingModel.fromJson({
        'id': 12,
        'booking_id': 'BK-12',
        'purohit_name': 'Pt Test',
        'puja_name': 'Satyanarayan',
        'event_date': '2026-09-20',
        'event_time': '09:00',
        'address': 'Hyderabad',
        'total_amount': 2100,
        'advance_paid': 0,
        'status': 'confirmed',
        'payment_status': 'pending',
        'created_at': '2026-09-14',
        'can_confirm': true,
        'start_code': '4821',
        'started_at': '2026-09-20 09:05',
      });
      expect(booking.canConfirm, isTrue);
      expect(booking.startCode, '4821');
      expect(booking.started, isTrue);
      expect(booking.canPay, isTrue);
    });

    test('blocks pay after cancel or success', () {
      final paid = BookingModel.fromJson({
        'id': 1,
        'booking_id': 'BK-1',
        'purohit_name': 'Pt Test',
        'puja_name': 'Ganesh',
        'event_date': '2026-09-20',
        'event_time': '10:00',
        'address': 'Home',
        'total_amount': 1100,
        'advance_paid': 1100,
        'status': 'confirmed',
        'payment_status': 'success',
        'created_at': '2026-09-14',
      });
      final cancelled = BookingModel.fromJson({
        'id': 2,
        'booking_id': 'BK-2',
        'purohit_name': 'Pt Test',
        'puja_name': 'Ganesh',
        'event_date': '2026-09-20',
        'event_time': '10:00',
        'address': 'Home',
        'total_amount': 1100,
        'advance_paid': 0,
        'status': 'cancelled',
        'payment_status': 'pending',
        'created_at': '2026-09-14',
      });
      expect(paid.canPay, isFalse);
      expect(cancelled.canPay, isFalse);
      expect(cancelled.canCancel, isFalse);
    });
  });

  group('RazorpayOrder.fromJson', () {
    test('marks mock orders', () {
      final order = RazorpayOrder.fromJson({
        'id': 'order_mock_abc',
        'amount': 100,
        'currency': 'INR',
        'key': '',
        'mock': true,
      });
      expect(order.mock, isTrue);
      expect(order.amountPaise, 100);
    });
  });

  group('CoveragePlace.matches', () {
    test('city-wide offer matches any area', () {
      final place = CoveragePlace(cityId: 3, kind: 'permanent');
      expect(place.matches(3, 9), isTrue);
      expect(place.matches(4, 9), isFalse);
    });

    test('area offer matches only that area', () {
      final place = CoveragePlace(cityId: 3, areaId: 9, kind: 'permanent');
      expect(place.matches(3, 9), isTrue);
      expect(place.matches(3, 8), isFalse);
    });

    test('parses snake_case city and area ids', () {
      final place = CoveragePlace.fromJson({
        'city_id': '3',
        'area_id': '9',
        'kind': 'visit',
        'start': '2026-09-20',
        'end': '2026-09-22',
        'label': 'Jubilee Hills visit',
      });
      expect(place.cityId, 3);
      expect(place.areaId, 9);
      expect(place.kind, 'visit');
    });
  });

  group('TravelRequestModel.fromJson', () {
    test('maps can_book and travel fee', () {
      final request = TravelRequestModel.fromJson({
        'id': 4,
        'request_id': 'TR-4',
        'status': 'accepted',
        'status_label': 'Accepted',
        'purohit_id': 2,
        'purohit_name': 'Pt Test',
        'puja_name': 'Satyanarayan',
        'travel_fee': '250',
        'can_book': true,
      });
      expect(request.canBook, isTrue);
      expect(request.travelFee, 250);
    });
  });

  group('PurohitPackageModel.fromJson', () {
    test('reads buffer minutes and venues', () {
      final pkg = PurohitPackageModel.fromJson({
        'id': 8,
        'puja_id': 1,
        'puja_name': 'Satyanarayan',
        'price': 2100,
        'includes_samagri': true,
        'samagri_price': 400,
        'buffer_minutes': 45,
        'venues': [
          {'code': 'home', 'label': 'At home'},
          {'code': 'purohit', 'label': 'At purohit place'},
        ],
      });
      expect(pkg.bufferMinutes, 45);
      expect(pkg.venues.map((v) => v.code), ['home', 'purohit']);
    });
  });

  group('PurohitCalendarState.fromJson', () {
    test('parses month grid and selected day', () {
      final calendar = PurohitCalendarState.fromJson({
        'year': 2026,
        'month': 9,
        'month_label': 'September 2026',
        'work_start': '07:00',
        'work_end': '20:00',
        'weeks': [
          [
            {
              'date': '2026-09-01',
              'day': 1,
              'in_month': true,
              'is_today': false,
              'is_past': true,
              'status': 'open',
              'block_count': 0,
            },
          ],
        ],
        'selected_day': '2026-09-14',
        'selected_blocks': [
          {'id': 1, 'date': '2026-09-14', 'is_all_day': true, 'label': 'Off'},
        ],
      });
      expect(calendar.monthLabel, 'September 2026');
      expect(calendar.weeks.first.first.day, 1);
      expect(calendar.selectedBlocks.single.isAllDay, isTrue);
    });
  });

  group('PaymentOptions.fromJson', () {
    test('reads wallet and mixed splits', () {
      final options = PaymentOptions.fromJson({
        'wallet': {'available': true, 'balance': 500, 'shortfall': 200},
        'mixed': {'available': true, 'wallet_amount': 500, 'razorpay_amount': 200},
      });
      expect(options.walletAvailable, isTrue);
      expect(options.mixedRazorpay, 200);
    });
  });
}
