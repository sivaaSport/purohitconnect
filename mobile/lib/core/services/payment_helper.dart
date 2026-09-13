import '../models/models.dart';
import 'api_service.dart';

/// Completes Razorpay checkout. Live keys open later via the official SDK;
/// local mock orders (order_mock_*) settle immediately against the API.
class PaymentHelper {
  static Future<Map<String, dynamic>> settleBooking({
    required String bookingId,
    required RazorpayOrder order,
  }) {
    if (!order.mock) {
      throw Exception('Live Razorpay checkout needs the Android/iOS Razorpay SDK. Use mock mode locally.');
    }
    return ApiService().verifyBookingPayment(
      bookingId: bookingId,
      orderId: order.id,
      paymentId: 'pay_mock_${DateTime.now().millisecondsSinceEpoch}',
      signature: 'mock_signature',
    );
  }

  static Future<Map<String, dynamic>> settleWallet({
    required RazorpayOrder order,
    required double amount,
  }) {
    if (!order.mock) {
      throw Exception('Live Razorpay checkout needs the Android/iOS Razorpay SDK. Use mock mode locally.');
    }
    return ApiService().verifyWalletPayment(
      orderId: order.id,
      paymentId: 'pay_mock_${DateTime.now().millisecondsSinceEpoch}',
      signature: 'mock_signature',
      amount: amount,
    );
  }
}
