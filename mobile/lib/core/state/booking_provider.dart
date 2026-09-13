import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class BookingProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  PurohitModel? _selectedPurohit;
  PurohitPackageModel? _selectedPackage;
  DateTime _selectedDate = DateTime.now().add(const Duration(days: 2));
  String _selectedTime = '';
  bool _needsSamagri = true;
  String _address = '';
  String _specialRequests = '';
  CityModel? _city;
  AreaModel? _area;
  String _venueType = 'home';
  List<CityModel> _cities = [];
  List<TimeSlot> _slots = [];
  bool _isLoading = false;
  List<BookingModel> _myBookings = [];

  PurohitModel? get selectedPurohit => _selectedPurohit;
  PurohitPackageModel? get selectedPackage => _selectedPackage;
  DateTime get selectedDate => _selectedDate;
  String get selectedTime => _selectedTime;
  bool get needsSamagri => _needsSamagri;
  String get address => _address;
  String get specialRequests => _specialRequests;
  CityModel? get city => _city;
  AreaModel? get area => _area;
  String get venueType => _venueType;
  List<CityModel> get cities => _cities;
  List<TimeSlot> get slots => _slots;
  bool get isLoading => _isLoading;
  List<BookingModel> get myBookings => _myBookings;

  double get baseAmount => _selectedPackage?.price ?? _selectedPurohit?.basePrice ?? 0;
  double get samagriAmount {
    if (!_needsSamagri) return 0;
    return _selectedPackage?.samagriPrice ?? 0;
  }
  double get totalAmount => baseAmount + samagriAmount;

  void selectPurohit(PurohitModel purohit, {PurohitPackageModel? package}) {
    _selectedPurohit = purohit;
    _selectedPackage = package ?? (purohit.packages.isNotEmpty ? purohit.packages.first : null);
    final venues = _selectedPackage?.venues ?? [];
    if (venues.isNotEmpty) _venueType = venues.first.code;
    notifyListeners();
  }

  void selectPackage(PurohitPackageModel package) {
    _selectedPackage = package;
    if (package.venues.isNotEmpty) _venueType = package.venues.first.code;
    notifyListeners();
  }

  void setDate(DateTime date) {
    _selectedDate = date;
    notifyListeners();
  }

  void setTime(String time) {
    _selectedTime = time;
    notifyListeners();
  }

  void toggleSamagri(bool value) {
    _needsSamagri = value;
    notifyListeners();
  }

  void setAddress(String address) {
    _address = address;
    notifyListeners();
  }

  void setSpecialRequests(String requests) {
    _specialRequests = requests;
    notifyListeners();
  }

  void setCity(CityModel? city) {
    _city = city;
    _area = null;
    notifyListeners();
  }

  void setArea(AreaModel? area) {
    _area = area;
    notifyListeners();
  }

  void setVenueType(String venue) {
    _venueType = venue;
    notifyListeners();
  }

  Future<void> loadCities() async {
    _cities = await _api.fetchCities();
    if (_city == null && _cities.isNotEmpty) {
      _city = _cities.first;
      if (_city!.areas.isNotEmpty) _area = _city!.areas.first;
    }
    notifyListeners();
  }

  Future<void> loadSlots() async {
    if (_selectedPurohit == null) return;
    final dateStr =
        '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}';
    _slots = await _api.fetchSlots(_selectedPurohit!.id, dateStr, packageId: _selectedPackage?.id);
    if (_selectedTime.isEmpty) {
      final open = _slots.where((s) => s.available);
      if (open.isNotEmpty) _selectedTime = open.first.start;
    }
    notifyListeners();
  }

  Future<Map<String, dynamic>> confirmBooking() async {
    if (_selectedPurohit == null || _selectedPackage == null) {
      return {'success': false, 'error': 'Select a purohit package first'};
    }
    if (_city == null || _area == null) {
      return {'success': false, 'error': 'Choose city and area'};
    }
    if (_selectedTime.isEmpty) {
      return {'success': false, 'error': 'Choose a time slot'};
    }
    _isLoading = true;
    notifyListeners();
    final dateStr =
        '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}';
    try {
      final res = await _api.createBooking(
        packageId: _selectedPackage!.id,
        eventDate: dateStr,
        eventTime: _selectedTime,
        address: _address.isNotEmpty ? _address : 'Ceremony venue',
        cityId: _city!.id,
        areaId: _area!.id,
        venueType: _venueType,
        needsSamagri: _needsSamagri,
        specialRequests: _specialRequests,
      );
      _isLoading = false;
      notifyListeners();
      return res;
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<void> loadMyBookings({String status = 'all'}) async {
    _isLoading = true;
    notifyListeners();
    try {
      _myBookings = await _api.fetchMyBookings(status: status);
    } catch (_) {
      _myBookings = [];
    }
    _isLoading = false;
    notifyListeners();
  }
}
