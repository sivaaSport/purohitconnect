import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_exception.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  UserModel? _user;
  bool _ready = false;
  bool _isLoading = false;
  String? _errorMessage;
  String? _debugOtp;
  String? _pendingAction;

  UserModel? get user => _user ?? _api.currentUser;
  bool get isAuthenticated => user != null && _api.authToken != null;
  bool get isReady => _ready;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get debugOtp => _debugOtp;
  double get walletBalance => user?.walletBalance ?? 0.0;

  Future<void> bootstrap() async {
    try {
      await _api.restoreSession();
      _user = _api.currentUser;
    } catch (_) {
      _user = null;
    }
    _ready = true;
    notifyListeners();
  }

  Future<bool> sendOtp(String phone, {String action = 'auto'}) async {
    _isLoading = true;
    _errorMessage = null;
    _debugOtp = null;
    notifyListeners();
    try {
      final res = await _api.sendOtp(phone, action: action);
      _debugOtp = res['debug_otp']?.toString();
      _pendingAction = res['action']?.toString() ?? action;
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _errorMessage = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> verifyOtp(String phone, String otp, {String? name}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final res = await _api.verifyOtp(phone, otp, action: _pendingAction ?? 'auto', name: name);
      _user = UserModel.fromJson(res['user'] as Map<String, dynamic>);
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _errorMessage = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> refreshUser() async {
    try {
      _user = await _api.fetchMe();
      notifyListeners();
    } catch (_) {}
  }

  void applyWalletBalance(double balance) {
    if (_user != null) {
      _user = _user!.copyWith(walletBalance: balance);
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _api.logout();
    _user = null;
    notifyListeners();
  }
}
