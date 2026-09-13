import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiConstants {
  static const String appName = 'PurohitConnect';
  static const String appTagline = 'Sacred Rituals, Verified Purohits';
  static const String helplinePhone = '+91 98765 43210';

  /// Override with: flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
  static const String _envBase = String.fromEnvironment('API_BASE_URL');

  static String? resolvedBaseUrl;

  static List<String> get candidateBaseUrls {
    if (_envBase.isNotEmpty) {
      return [_envBase.replaceAll(RegExp(r'/$'), '')];
    }
    // 8001 is PurohitConnect. Port 8000 is often taken by another local app (F&O Pulse).
    const local = [
      'http://localhost:8001/api/v1',
      'http://127.0.0.1:8001/api/v1',
      'http://localhost:8000/api/v1',
      'http://127.0.0.1:8000/api/v1',
    ];
    if (kIsWeb) return local;
    try {
      if (Platform.isAndroid) {
        return const [
          'http://10.0.2.2:8001/api/v1',
          'http://10.0.2.2:8000/api/v1',
        ];
      }
    } catch (_) {}
    return local;
  }

  static String get baseUrl => resolvedBaseUrl ?? candidateBaseUrls.first;

  static String resolveMediaUrl(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty || trimmed == 'null' || trimmed == 'None') return '';
    final uri = Uri.tryParse(trimmed);
    final api = Uri.tryParse(baseUrl);
    if (uri == null || !uri.hasScheme || api == null) return trimmed;
    const localHosts = {'localhost', '127.0.0.1', '10.0.2.2'};
    if (localHosts.contains(uri.host) && api.host.isNotEmpty) {
      return uri
          .replace(
            host: api.host,
            port: api.hasPort ? api.port : uri.port,
          )
          .toString();
    }
    return trimmed;
  }

  static const sendOtp = '/auth/send-otp/';
  static const verifyOtp = '/auth/verify-otp/';
  static const me = '/auth/me/';
  static const logout = '/auth/logout/';
  static const categories = '/categories/';
  static const pujas = '/pujas/';
  static const cities = '/cities/';
  static const languages = '/languages/';
  static const purohits = '/purohits/';
  static const createBooking = '/bookings/create/';
  static const myBookings = '/bookings/my/';
  static const wallet = '/wallet/';
  static const walletTopup = '/wallet/topup/';
  static const walletVerify = '/wallet/verify-payment/';
  static const travelRequests = '/travel-requests/';
  static const notifications = '/notifications/';
  static const support = '/support/';
}
