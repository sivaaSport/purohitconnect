import 'dart:async';

import 'package:razorpay_flutter/razorpay_flutter.dart';

import 'razorpay_checkout_stub.dart' show PaymentCancelledException, RazorpayCheckoutResult;

export 'razorpay_checkout_stub.dart' show PaymentCancelledException, RazorpayCheckoutResult;

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
  final razorpay = Razorpay();
  final completer = Completer<RazorpayCheckoutResult>();

  void finish() {
    razorpay.clear();
  }

  razorpay.on(Razorpay.EVENT_PAYMENT_SUCCESS, (PaymentSuccessResponse response) {
    if (completer.isCompleted) return;
    completer.complete(RazorpayCheckoutResult(
      orderId: (response.orderId ?? '').isNotEmpty ? response.orderId! : orderId,
      paymentId: response.paymentId ?? '',
      signature: response.signature ?? '',
    ));
    finish();
  });
  razorpay.on(Razorpay.EVENT_PAYMENT_ERROR, (PaymentFailureResponse response) {
    if (completer.isCompleted) return;
    if (response.code == Razorpay.PAYMENT_CANCELLED) {
      completer.completeError(PaymentCancelledException());
    } else {
      completer.completeError(Exception(response.message ?? 'Payment failed'));
    }
    finish();
  });
  razorpay.on(Razorpay.EVENT_EXTERNAL_WALLET, (_) {});

  razorpay.open({
    'key': key,
    'amount': amountPaise,
    'currency': currency,
    'name': 'PurohitConnect',
    'description': description,
    'order_id': orderId,
    'prefill': {
      'name': name,
      'email': email,
      'contact': contact,
    },
    'theme': {'color': '#D97706'},
  });
  return completer.future;
}
