import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants/api_constants.dart';
import '../models/models.dart';
import 'api_exception.dart';
import 'session_store.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _authToken;
  UserModel? _currentUser;

  String? get authToken => _authToken;
  UserModel? get currentUser => _currentUser;

  void setAuth(String token, UserModel? user) {
    _authToken = token;
    _currentUser = user;
  }

  void clearAuth() {
    _authToken = null;
    _currentUser = null;
  }

  Future<void> restoreSession() async {
    final token = await SessionStore.readToken();
    if (token == null || token.isEmpty) return;
    _authToken = token;
    try {
      final data = await _get(ApiConstants.me);
      _currentUser = UserModel.fromJson(data['user'] as Map<String, dynamic>);
    } catch (_) {
      _authToken = null;
      _currentUser = null;
      await SessionStore.clear();
    }
  }

  Map<String, String> _headers() {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (_authToken != null && _authToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  Uri _uri(String base, String path, [Map<String, String>? query]) {
    final url = Uri.parse('$base$path');
    if (query == null || query.isEmpty) return url;
    return url.replace(queryParameters: {...url.queryParameters, ...query});
  }

  List<String> get _bases {
    final resolved = ApiConstants.resolvedBaseUrl;
    if (resolved != null) return [resolved];
    return ApiConstants.candidateBaseUrls;
  }

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, String>? query,
    Map<String, dynamic>? body,
  }) async {
    Object? lastError;
    for (final base in _bases) {
      try {
        final uri = _uri(base, path, query);
        final payload = body == null ? null : jsonEncode(body);
        late http.Response res;
        if (method == 'POST') {
          res = await http.post(uri, headers: _headers(), body: payload).timeout(const Duration(seconds: 12));
        } else if (method == 'PATCH') {
          res = await http.patch(uri, headers: _headers(), body: payload).timeout(const Duration(seconds: 12));
        } else {
          res = await http.get(uri, headers: _headers()).timeout(const Duration(seconds: 12));
        }
        final data = _decode(res);
        ApiConstants.resolvedBaseUrl = base;
        return data;
      } on ApiException {
        rethrow;
      } catch (e) {
        lastError = e;
      }
    }
    throw ApiException(
      'Cannot reach Django at ${ApiConstants.candidateBaseUrls.join(' or ')}. '
      'Keep `python manage.py runserver 0.0.0.0:8000` running, then hot-restart the app. ($lastError)',
    );
  }

  Future<Map<String, dynamic>> _get(String path, [Map<String, String>? query]) {
    return _request('GET', path, query: query);
  }

  Future<Map<String, dynamic>> _send(String method, String path, [Map<String, dynamic>? body]) {
    return _request(method, path, body: body);
  }

  Map<String, dynamic> _decode(http.Response res) {
    Map<String, dynamic> data = {};
    if (res.body.isNotEmpty) {
      try {
        final parsed = jsonDecode(res.body);
        if (parsed is Map<String, dynamic>) data = parsed;
      } catch (_) {
        throw ApiException('Unexpected server response (${res.statusCode})');
      }
    }
    if (res.statusCode >= 400 || data['success'] == false) {
      throw ApiException(
        (data['error'] ?? data['message'] ?? 'Request failed (${res.statusCode})').toString(),
        statusCode: res.statusCode,
        code: data['code']?.toString(),
      );
    }
    return data;
  }

  Future<Map<String, dynamic>> sendOtp(String phone, {String action = 'auto'}) {
    return _send('POST', ApiConstants.sendOtp, {'phone': phone, 'action': action});
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otpCode, {String action = 'auto', String? name, String? role}) async {
    final data = await _send('POST', ApiConstants.verifyOtp, {
      'phone': phone,
      'otp_code': otpCode,
      'action': action,
      if (name != null && name.isNotEmpty) 'name': name,
      if (role != null && role.isNotEmpty) 'role': role,
    });
    final token = data['token']?.toString();
    if (token != null && data['user'] != null) {
      _authToken = token;
      _currentUser = UserModel.fromJson(data['user'] as Map<String, dynamic>);
      await SessionStore.saveToken(token);
    }
    return data;
  }

  Future<UserModel> fetchMe() async {
    final data = await _get(ApiConstants.me);
    _currentUser = UserModel.fromJson(data['user'] as Map<String, dynamic>);
    return _currentUser!;
  }

  Future<void> logout() async {
    try {
      await _send('POST', ApiConstants.logout);
    } catch (_) {}
    clearAuth();
    await SessionStore.clear();
  }

  Future<List<PujaCategoryModel>> fetchCategories() async {
    final data = await _get(ApiConstants.categories);
    return (data['categories'] as List? ?? [])
        .map((c) => PujaCategoryModel.fromJson(Map<String, dynamic>.from(c as Map)))
        .toList();
  }

  Future<List<PujaModel>> fetchPujas({String? categorySlug, bool featured = false}) async {
    final data = await _get(ApiConstants.pujas, {
      if (categorySlug != null && categorySlug.isNotEmpty) 'category': categorySlug,
      if (featured) 'featured': 'true',
    });
    return (data['pujas'] as List? ?? [])
        .map((p) => PujaModel.fromJson(Map<String, dynamic>.from(p as Map)))
        .toList();
  }

  Future<List<CityModel>> fetchCities() async {
    final data = await _get(ApiConstants.cities);
    return (data['cities'] as List? ?? [])
        .map((c) => CityModel.fromJson(Map<String, dynamic>.from(c as Map)))
        .toList();
  }

  Future<List<LanguageModel>> fetchLanguages() async {
    final data = await _get(ApiConstants.languages);
    return (data['languages'] as List? ?? [])
        .map((c) => LanguageModel.fromJson(Map<String, dynamic>.from(c as Map)))
        .toList();
  }

  Future<List<PurohitModel>> fetchPurohits({
    String? city,
    int? cityId,
    int? languageId,
    int? pujaId,
    bool featured = false,
    String? query,
  }) async {
    final data = await _get(ApiConstants.purohits, {
      if (cityId != null) 'city': '$cityId',
      if (city != null && city.isNotEmpty && cityId == null) 'city': city,
      if (languageId != null) 'language': '$languageId',
      if (pujaId != null) 'puja': '$pujaId',
      if (featured) 'featured': 'true',
      if (query != null && query.isNotEmpty) 'q': query,
    });
    return (data['purohits'] as List? ?? [])
        .map((p) => PurohitModel.fromJson(Map<String, dynamic>.from(p as Map)))
        .toList();
  }

  Future<PurohitModel> fetchPurohitDetail(int id) async {
    final data = await _get('${ApiConstants.purohits}$id/');
    return PurohitModel.fromJson(Map<String, dynamic>.from(data['purohit'] as Map));
  }

  Future<List<TimeSlot>> fetchSlots(int purohitId, String date, {int? packageId}) async {
    final data = await _get('${ApiConstants.purohits}$purohitId/slots/', {
      'date': date,
      if (packageId != null) 'package_id': '$packageId',
    });
    return (data['slots'] as List? ?? [])
        .map((s) => TimeSlot.fromJson(Map<String, dynamic>.from(s as Map)))
        .toList();
  }

  Future<Map<String, dynamic>> createBooking({
    required int packageId,
    required String eventDate,
    required String eventTime,
    required String address,
    required int cityId,
    required int areaId,
    String venueType = 'home',
    bool needsSamagri = false,
    String specialRequests = '',
  }) {
    return _send('POST', ApiConstants.createBooking, {
      'package_id': packageId,
      'event_date': eventDate,
      'event_time': eventTime,
      'address': address,
      'city_id': cityId,
      'area_id': areaId,
      'venue_type': venueType,
      'needs_samagri': needsSamagri,
      'special_requests': specialRequests,
    });
  }

  Future<List<BookingModel>> fetchMyBookings({String status = 'all'}) async {
    final data = await _get(ApiConstants.myBookings, {'status': status});
    return (data['bookings'] as List? ?? [])
        .map((b) => BookingModel.fromJson(Map<String, dynamic>.from(b as Map)))
        .toList();
  }

  Future<Map<String, dynamic>> fetchBooking(String bookingId) {
    return _get('/bookings/$bookingId/');
  }

  Future<Map<String, dynamic>> payBooking(String bookingId, String method) {
    return _send('POST', '/bookings/$bookingId/pay/', {'method': method});
  }

  Future<Map<String, dynamic>> verifyBookingPayment({
    required String bookingId,
    required String orderId,
    required String paymentId,
    required String signature,
  }) {
    return _send('POST', '/bookings/$bookingId/verify-payment/', {
      'razorpay_order_id': orderId,
      'razorpay_payment_id': paymentId,
      'razorpay_signature': signature,
    });
  }

  Future<Map<String, dynamic>> cancelBooking(String bookingId, String reason) {
    return _send('POST', '/bookings/$bookingId/cancel/', {'reason': reason});
  }

  Future<Map<String, dynamic>> requestReschedule(String bookingId, String date, String time, String reason) {
    return _send('POST', '/bookings/$bookingId/reschedule/', {
      'date': date,
      'time': time,
      'reason': reason,
    });
  }

  Future<Map<String, dynamic>> handleReschedule(String bookingId, String action) {
    return _send('POST', '/bookings/$bookingId/reschedule/handle/', {'action': action});
  }

  Future<List<ChatMessageModel>> fetchChat(String bookingId) async {
    final data = await _get('/bookings/$bookingId/chat/');
    return (data['messages'] as List? ?? [])
        .map((m) => ChatMessageModel.fromJson(Map<String, dynamic>.from(m as Map)))
        .toList();
  }

  Future<List<ChatMessageModel>> sendChat(String bookingId, String message) async {
    final data = await _send('POST', '/bookings/$bookingId/chat/', {'message': message});
    return (data['messages'] as List? ?? [])
        .map((m) => ChatMessageModel.fromJson(Map<String, dynamic>.from(m as Map)))
        .toList();
  }

  Future<void> submitReview(String bookingId, {required int rating, required String title, required String comment}) {
    return _send('POST', '/bookings/$bookingId/review/', {
      'rating': rating,
      'title': title,
      'comment': comment,
    });
  }

  Future<Map<String, dynamic>> fetchWallet() => _get(ApiConstants.wallet);

  Future<Map<String, dynamic>> walletTopup(double amount) {
    return _send('POST', ApiConstants.walletTopup, {'amount': amount});
  }

  Future<Map<String, dynamic>> verifyWalletPayment({
    required String orderId,
    required String paymentId,
    required String signature,
    required double amount,
  }) {
    return _send('POST', ApiConstants.walletVerify, {
      'razorpay_order_id': orderId,
      'razorpay_payment_id': paymentId,
      'razorpay_signature': signature,
      'amount': amount,
    });
  }

  Future<List<TravelRequestModel>> fetchTravelRequests() async {
    final data = await _get(ApiConstants.travelRequests);
    return (data['travel_requests'] as List? ?? [])
        .map((item) => TravelRequestModel.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList();
  }

  Future<Map<String, dynamic>> createTravelRequest({
    required int packageId,
    required String eventDate,
    required String eventTime,
    required String address,
    required int cityId,
    required int areaId,
    String venueType = 'home',
    String message = '',
  }) {
    return _send('POST', ApiConstants.travelRequests, {
      'package_id': packageId,
      'event_date': eventDate,
      'event_time': eventTime,
      'address': address,
      'city_id': cityId,
      'area_id': areaId,
      'venue_type': venueType,
      'message': message,
    });
  }

  Future<Map<String, dynamic>> fetchNotifications() => _get(ApiConstants.notifications);

  Future<void> markNotificationRead(int id) => _send('POST', '/notifications/$id/read/');

  Future<void> markAllNotificationsRead() => _send('POST', '/notifications/read-all/');

  Future<List<SupportTicket>> fetchTickets() async {
    final data = await _get(ApiConstants.support);
    return (data['tickets'] as List? ?? [])
        .map((t) => SupportTicket.fromJson(Map<String, dynamic>.from(t as Map)))
        .toList();
  }

  Future<SupportTicket> createTicket({required String subject, required String description, required String category}) async {
    final data = await _send('POST', ApiConstants.support, {
      'subject': subject,
      'description': description,
      'category': category,
    });
    return SupportTicket.fromJson(Map<String, dynamic>.from(data['ticket'] as Map));
  }

  Future<Map<String, dynamic>> enablePurohitWorkspace() {
    return _send('POST', ApiConstants.purohitEnable);
  }

  Future<Map<String, dynamic>> fetchPurohitDashboard() => _get(ApiConstants.purohitDashboard);

  Future<List<BookingModel>> fetchPurohitBookings({String bucket = 'all'}) async {
    final data = await _get(ApiConstants.purohitBookings, {'bucket': bucket});
    return (data['bookings'] as List? ?? [])
        .map((item) => BookingModel.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList();
  }

  Future<Map<String, dynamic>> updatePurohitBookingStatus(
    String bookingId, {
    required String status,
    String code = '',
  }) {
    return _send('POST', '/workspace/purohit/bookings/$bookingId/status/', {
      'status': status,
      if (code.isNotEmpty) 'verification_code': code,
    });
  }

  Future<List<TravelRequestModel>> fetchPurohitTravelRequests() async {
    final data = await _get(ApiConstants.purohitTravel);
    return (data['travel_requests'] as List? ?? [])
        .map((item) => TravelRequestModel.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList();
  }

  Future<Map<String, dynamic>> respondPurohitTravel(
    int requestId, {
    required String decision,
    double travelFee = 0,
    String response = '',
  }) {
    return _send('POST', '/workspace/purohit/travel-requests/$requestId/respond/', {
      'decision': decision,
      'travel_fee': travelFee,
      'purohit_response': response,
    });
  }

  Future<Map<String, dynamic>> fetchPurohitPackages() => _get(ApiConstants.purohitPackages);

  Future<Map<String, dynamic>> savePurohitPackage(Map<String, dynamic> body) {
    return _send('POST', ApiConstants.purohitPackages, body);
  }

  Future<PurohitCalendarState> fetchPurohitCalendar({
    required int year,
    required int month,
    String day = '',
    int? previewPackageId,
  }) async {
    final query = <String, String>{
      'year': '$year',
      'month': '$month',
      if (day.isNotEmpty) 'day': day,
      if (previewPackageId != null) 'preview_package': '$previewPackageId',
    };
    final data = await _get(ApiConstants.purohitCalendar, query);
    return PurohitCalendarState.fromJson(data);
  }

  Future<PurohitCalendarState> updatePurohitCalendar(Map<String, dynamic> body) async {
    final data = await _send('POST', ApiConstants.purohitCalendar, body);
    return PurohitCalendarState.fromJson(data);
  }
}
