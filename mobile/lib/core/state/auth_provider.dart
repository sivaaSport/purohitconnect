import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_exception.dart';
import '../services/api_service.dart';
import '../services/session_store.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  UserModel? _user;
  bool _ready = false;
  bool _isLoading = false;
  String? _errorMessage;
  String? _debugOtp;
  String? _pendingAction;
  String? _pendingRole;
  String _workspace = 'devotee';

  UserModel? get user => _user ?? _api.currentUser;
  bool get isAuthenticated => user != null && _api.authToken != null;
  bool get isReady => _ready;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get debugOtp => _debugOtp;
  double get walletBalance => user?.walletBalance ?? 0.0;
  String get workspace => _workspace;
  bool get canActAsPurohit => user?.canActAsPurohit == true || user?.role == 'purohit';
  bool get isPurohitWorkspace => _workspace == 'purohit' && canActAsPurohit;

  @visibleForTesting
  void hydrateForTest({UserModel? user, String workspace = 'devotee'}) {
    _user = user;
    _ready = true;
    _workspace = user == null ? 'devotee' : _resolveWorkspace(workspace);
    notifyListeners();
  }

  Future<void> bootstrap() async {
    try {
      await _api.restoreSession();
      _user = _api.currentUser;
      final stored = await SessionStore.readWorkspace();
      _workspace = _resolveWorkspace(stored);
    } catch (_) {
      _user = null;
      _workspace = 'devotee';
    }
    _ready = true;
    notifyListeners();
  }

  String _resolveWorkspace(String? stored) {
    if (!canActAsPurohit) return 'devotee';
    if (stored == 'purohit' || stored == 'devotee') return stored!;
    return user?.role == 'purohit' ? 'purohit' : 'devotee';
  }

  Future<void> setWorkspace(String value) async {
    _workspace = value == 'purohit' && canActAsPurohit ? 'purohit' : 'devotee';
    await SessionStore.saveWorkspace(_workspace);
    notifyListeners();
  }

  Future<bool> sendOtp(String phone, {String action = 'auto', String? role}) async {
    _isLoading = true;
    _errorMessage = null;
    _debugOtp = null;
    _pendingRole = role;
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
      final res = await _api.verifyOtp(
        phone,
        otp,
        action: _pendingAction ?? 'auto',
        name: name,
        role: _pendingRole,
      );
      _user = UserModel.fromJson(res['user'] as Map<String, dynamic>);
      await setWorkspace(_resolveWorkspace(null));
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
      if (!canActAsPurohit && _workspace == 'purohit') {
        await setWorkspace('devotee');
      } else {
        notifyListeners();
      }
    } catch (_) {}
  }

  Future<bool> enablePurohitWorkspace() async {
    try {
      await _api.enablePurohitWorkspace();
      await refreshUser();
      await setWorkspace('purohit');
      return true;
    } on ApiException catch (e) {
      _errorMessage = e.message;
      notifyListeners();
      return false;
    }
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
    _workspace = 'devotee';
    notifyListeners();
  }
}
