import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_exception.dart';
import '../services/api_service.dart';

enum CoverageMode { covered, ask, closed, unknown }

class CoverageStatus {
  final CoverageMode mode;
  final String title;
  final String body;

  const CoverageStatus(this.mode, this.title, this.body);
}

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
  int _travelRevision = 0;

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
  int get travelRevision => _travelRevision;

  String get dateStr =>
      '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}';

  double get baseAmount => _selectedPackage?.price ?? _selectedPurohit?.basePrice ?? 0;
  double get samagriAmount {
    if (!_needsSamagri) return 0;
    return _selectedPackage?.samagriPrice ?? 0;
  }
  double get totalAmount => baseAmount + samagriAmount;

  CoverageStatus get coverageStatus {
    if (_venueType == 'purohit') {
      return const CoverageStatus(
        CoverageMode.covered,
        'This ritual is at their place',
        'Location is already set. You can book and pay now.',
      );
    }
    final coverage = _selectedPurohit?.coverage;
    if (coverage == null) {
      return const CoverageStatus(CoverageMode.unknown, '', '');
    }
    final cityId = _city?.id;
    final areaId = _area?.id;
    final cityName = _city?.name ?? 'this city';
    final areaName = _area?.name ?? 'this area';
    if (cityId == null) {
      return const CoverageStatus(CoverageMode.ask, 'Choose a city', 'Pick the city and area for the ceremony.');
    }
    for (final offer in coverage.permanent) {
      if (offer.matches(cityId, areaId)) {
        return CoverageStatus(
          CoverageMode.covered,
          'They already offer this place',
          '$cityName / $areaName is on their list. You can book and pay now.',
        );
      }
    }
    final visitMatches = coverage.places.where((offer) => offer.kind == 'visit' && offer.matches(cityId, areaId)).toList();
    if (visitMatches.isNotEmpty) {
      final inWindow = visitMatches.where((offer) {
        return offer.start.isNotEmpty &&
            offer.end.isNotEmpty &&
            dateStr.compareTo(offer.start) >= 0 &&
            dateStr.compareTo(offer.end) <= 0;
      });
      if (inWindow.isNotEmpty) {
        return CoverageStatus(
          CoverageMode.covered,
          'They are visiting then',
          '${inWindow.first.label}. You can book this date.',
        );
      }
      if (!coverage.acceptsTravel) {
        return CoverageStatus(
          CoverageMode.closed,
          'That date is outside their visit',
          'They visit here on: ${visitMatches.map((o) => o.label).join('; ')}.',
        );
      }
      return CoverageStatus(
        CoverageMode.ask,
        'That date is outside their visit',
        'They visit here on: ${visitMatches.map((o) => o.label).join('; ')}. Pick one of those dates to book, or request this date.',
      );
    }
    if (!coverage.acceptsTravel) {
      return CoverageStatus(
        CoverageMode.closed,
        'They do not offer this place',
        '$areaName, $cityName is not on their list, and they are not taking travel requests.',
      );
    }
    return CoverageStatus(
      CoverageMode.ask,
      'Ask them to visit this place',
      'They do not already offer $areaName, $cityName on that date. Send a request first. They decide, and you pay only after they accept and you book.',
    );
  }

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

  void selectOfferedPlace(CoveragePlace place) {
    CityModel? city;
    for (final item in _cities) {
      if (item.id == place.cityId) city = item;
    }
    if (city == null) return;
    _city = city;
    if (place.areaId != null) {
      AreaModel? area;
      for (final item in city.areas) {
        if (item.id == place.areaId) area = item;
      }
      _area = area;
    } else {
      _area = city.areas.isNotEmpty ? city.areas.first : null;
    }
    notifyListeners();
  }

  Future<void> loadCities() async {
    _cities = await _api.fetchCities();
    if (_city == null && _cities.isNotEmpty) {
      final homeId = _selectedPurohit?.cityId;
      CityModel? home;
      if (homeId != null) {
        for (final item in _cities) {
          if (item.id == homeId) home = item;
        }
      }
      _city = home ?? _cities.first;
      if (_city!.areas.isNotEmpty) _area = _city!.areas.first;
    }
    notifyListeners();
  }

  Future<void> loadSlots() async {
    if (_selectedPurohit == null) return;
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
    } on ApiException catch (e) {
      _isLoading = false;
      notifyListeners();
      return {'success': false, 'error': e.message, 'code': e.code};
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> sendTravelRequest() async {
    if (_selectedPackage == null) {
      return {'success': false, 'error': 'Select a purohit package first'};
    }
    if (_city == null || _area == null) {
      return {'success': false, 'error': 'Choose city and area'};
    }
    _isLoading = true;
    notifyListeners();
    try {
      final res = await _api.createTravelRequest(
        packageId: _selectedPackage!.id,
        eventDate: dateStr,
        eventTime: _selectedTime,
        address: _address.isNotEmpty ? _address : 'Ceremony venue',
        cityId: _city!.id,
        areaId: _area!.id,
        venueType: _venueType,
        message: _specialRequests,
      );
      _travelRevision++;
      _isLoading = false;
      notifyListeners();
      return res;
    } on ApiException catch (e) {
      _isLoading = false;
      notifyListeners();
      return {'success': false, 'error': e.message, 'code': e.code};
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
