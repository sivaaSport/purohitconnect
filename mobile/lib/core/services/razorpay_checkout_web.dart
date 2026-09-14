import 'dart:async';
import 'dart:js_interop';
import 'dart:js_interop_unsafe';

import 'razorpay_checkout_stub.dart' show PaymentCancelledException, RazorpayCheckoutResult;

export 'razorpay_checkout_stub.dart' show PaymentCancelledException, RazorpayCheckoutResult;

extension type _Razorpay._(JSObject _) implements JSObject {
  external factory _Razorpay(JSObject options);
  external void open();
  external void on(JSString event, JSFunction callback);
}

JSObject _jsMap(Map<String, Object?> values) {
  final object = JSObject();
  values.forEach((key, value) {
    if (value == null) {
      object.setProperty(key.toJS, null);
    } else if (value is String) {
      object.setProperty(key.toJS, value.toJS);
    } else if (value is num) {
      object.setProperty(key.toJS, value.toJS);
    } else if (value is JSObject) {
      object.setProperty(key.toJS, value);
    } else if (value is JSFunction) {
      object.setProperty(key.toJS, value);
    }
  });
  return object;
}

String _jsString(JSObject object, String key) {
  final value = object.getProperty(key.toJS);
  if (value == null) return '';
  return (value as JSAny?)?.dartify()?.toString() ?? '';
}

Future<void> _ensureCheckoutScript() async {
  if (globalContext.has('Razorpay')) return;
  final document = globalContext.getProperty('document'.toJS);
  if (document == null) {
    throw Exception('Razorpay Checkout is not available in this browser.');
  }
  final completer = Completer<void>();
  final doc = document as JSObject;
  final createElement = doc.getProperty('createElement'.toJS) as JSFunction;
  final script = createElement.callAsFunction(doc, 'script'.toJS) as JSObject;
  script.setProperty('src'.toJS, 'https://checkout.razorpay.com/v1/checkout.js'.toJS);
  script.setProperty('async'.toJS, true.toJS);
  script.setProperty(
    'onload'.toJS,
    (() {
      if (!completer.isCompleted) completer.complete();
    }).toJS,
  );
  script.setProperty(
    'onerror'.toJS,
    (() {
      if (!completer.isCompleted) {
        completer.completeError(Exception('Could not load Razorpay Checkout.'));
      }
    }).toJS,
  );
  final head = doc.getProperty('head'.toJS) as JSObject;
  final append = head.getProperty('appendChild'.toJS) as JSFunction;
  append.callAsFunction(head, script);
  await completer.future.timeout(const Duration(seconds: 20));
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
}) async {
  await _ensureCheckoutScript();
  if (!globalContext.has('Razorpay')) {
    throw Exception('Razorpay Checkout is not available in this browser.');
  }

  final completer = Completer<RazorpayCheckoutResult>();
  final prefill = _jsMap({
    'name': name,
    'email': email,
    'contact': contact,
  });
  final modal = JSObject();
  modal.setProperty(
    'ondismiss'.toJS,
    (() {
      if (!completer.isCompleted) completer.completeError(PaymentCancelledException());
    }).toJS,
  );
  final options = _jsMap({
    'key': key,
    'amount': amountPaise,
    'currency': currency,
    'name': 'PurohitConnect',
    'description': description,
    'order_id': orderId,
    'prefill': prefill,
    'theme': _jsMap({'color': '#D97706'}),
    'modal': modal,
  });
  options.setProperty(
    'handler'.toJS,
    ((JSObject response) {
      if (completer.isCompleted) return;
      completer.complete(RazorpayCheckoutResult(
        orderId: _jsString(response, 'razorpay_order_id').isEmpty
            ? orderId
            : _jsString(response, 'razorpay_order_id'),
        paymentId: _jsString(response, 'razorpay_payment_id'),
        signature: _jsString(response, 'razorpay_signature'),
      ));
    }).toJS,
  );

  final rzp = _Razorpay(options);
  rzp.on(
    'payment.failed'.toJS,
    ((JSObject response) {
      if (completer.isCompleted) return;
      var message = 'Payment failed';
      final error = response.getProperty('error'.toJS);
      if (error is JSObject) {
        final description = _jsString(error, 'description');
        if (description.isNotEmpty) message = description;
      }
      completer.completeError(Exception(message));
    }).toJS,
  );
  rzp.open();
  return completer.future;
}
