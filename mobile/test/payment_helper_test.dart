import 'package:flutter_test/flutter_test.dart';
import 'package:purohit_mobile/core/models/models.dart';
import 'package:purohit_mobile/core/services/payment_helper.dart';

void main() {
  test('mock orders settle in-app without opening Razorpay', () async {
    final paid = await PaymentHelper.collect(
      RazorpayOrder(
        id: 'order_mock_abc',
        amountPaise: 100,
        currency: 'INR',
        key: '',
        mock: true,
      ),
    );
    expect(paid.orderId, 'order_mock_abc');
    expect(paid.paymentId, startsWith('pay_mock_'));
    expect(paid.signature, 'mock_signature');
  });

  test('live orders without a key fail before checkout', () async {
    expect(
      () => PaymentHelper.collect(
        RazorpayOrder(
          id: 'order_live_abc',
          amountPaise: 100,
          currency: 'INR',
          key: '',
          mock: false,
        ),
      ),
      throwsA(isA<Exception>().having(
        (e) => e.toString(),
        'message',
        contains('Razorpay key is missing'),
      )),
    );
  });
}
