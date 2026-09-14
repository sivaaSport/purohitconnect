import '../models/models.dart';
import 'api_service.dart';
import 'razorpay_checkout.dart';

export 'razorpay_checkout.dart' show PaymentCancelledException;

/// Opens Razorpay Checkout for live orders; mock orders settle locally.
class PaymentHelper {
  static Future<RazorpayCheckoutResult> collect(RazorpayOrder order, {
    String name = '',
    String email = '',
    String contact = '',
    String description = 'PurohitConnect payment',
  }) {
    if (order.mock) {
      return Future.value(RazorpayCheckoutResult(
        orderId: order.id,
        paymentId: 'pay_mock_${DateTime.now().millisecondsSinceEpoch}',
        signature: 'mock_signature',
      ));
    }
    if (order.key.isEmpty) {
      throw Exception('Razorpay key is missing. Add RAZORPAY_KEY_ID on the Django server.');
    }
    return openRazorpayCheckout(
      key: order.key,
      orderId: order.id,
      amountPaise: order.amountPaise,
      currency: order.currency,
      name: name,
      description: description,
      email: email,
      contact: contact,
    );
  }

  static Future<Map<String, dynamic>> settleBooking({
    required String bookingId,
    required RazorpayOrder order,
    String name = '',
    String email = '',
    String contact = '',
    String description = '',
  }) async {
    final paid = await collect(
      order,
      name: name,
      email: email,
      contact: contact,
      description: description.isNotEmpty ? description : 'Booking $bookingId',
    );
    return ApiService().verifyBookingPayment(
      bookingId: bookingId,
      orderId: paid.orderId,
      paymentId: paid.paymentId,
      signature: paid.signature,
    );
  }

  static Future<Map<String, dynamic>> settleWallet({
    required RazorpayOrder order,
    required double amount,
    String name = '',
    String email = '',
    String contact = '',
  }) async {
    final paid = await collect(
      order,
      name: name,
      email: email,
      contact: contact,
      description: 'Wallet top-up ₹${amount.toInt()}',
    );
    return ApiService().verifyWalletPayment(
      orderId: paid.orderId,
      paymentId: paid.paymentId,
      signature: paid.signature,
      amount: amount,
    );
  }
}
