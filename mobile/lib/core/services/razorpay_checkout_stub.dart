class PaymentCancelledException implements Exception {
  @override
  String toString() => 'Payment cancelled';
}

class RazorpayCheckoutResult {
  final String orderId;
  final String paymentId;
  final String signature;

  const RazorpayCheckoutResult({
    required this.orderId,
    required this.paymentId,
    required this.signature,
  });
}

Future<RazorpayCheckoutResult> openRazorpayCheckout({
  required String key,
  required String orderId,
  required int amountPaise,
  required String currency,
  required String name,
  required String description,
  String email = '',
  String contact = '',
}) {
  throw UnsupportedError('Razorpay checkout is only available on web, Android, and iOS.');
}
