double _toDouble(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse('$value') ?? 0;
}

int _toInt(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse('$value') ?? 0;
}

bool _toBool(dynamic value) => value == true || value == 'true' || value == 1;

String _cleanMediaUrl(dynamic value) {
  final url = value?.toString().trim() ?? '';
  if (url.isEmpty || url == 'null' || url == 'None') return '';
  return url;
}

class UserModel {
  final int id;
  final String phone;
  final String username;
  final String name;
  final String role;
  final double walletBalance;
  final bool isPhoneVerified;
  final String email;
  final String city;
  final int? cityId;
  final String avatarUrl;

  UserModel({
    required this.id,
    required this.phone,
    required this.username,
    required this.name,
    required this.role,
    required this.walletBalance,
    required this.isPhoneVerified,
    this.email = '',
    this.city = '',
    this.cityId,
    this.avatarUrl = '',
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: _toInt(json['id']),
      phone: json['phone']?.toString() ?? '',
      username: json['username']?.toString() ?? '',
      name: (json['name'] ?? json['username'] ?? 'Devotee').toString(),
      role: json['role']?.toString() ?? 'customer',
      walletBalance: _toDouble(json['wallet_balance']),
      isPhoneVerified: _toBool(json['is_phone_verified']),
      email: json['email']?.toString() ?? '',
      city: json['city']?.toString() ?? '',
      cityId: json['city_id'] == null ? null : _toInt(json['city_id']),
      avatarUrl: _cleanMediaUrl(json['avatar_url']),
    );
  }

  UserModel copyWith({double? walletBalance, String? name}) {
    return UserModel(
      id: id,
      phone: phone,
      username: username,
      name: name ?? this.name,
      role: role,
      walletBalance: walletBalance ?? this.walletBalance,
      isPhoneVerified: isPhoneVerified,
      email: email,
      city: city,
      cityId: cityId,
      avatarUrl: avatarUrl,
    );
  }
}

class CityModel {
  final int id;
  final String name;
  final String state;
  final List<AreaModel> areas;

  CityModel({required this.id, required this.name, required this.state, this.areas = const []});

  factory CityModel.fromJson(Map<String, dynamic> json) {
    final raw = json['areas'] as List? ?? [];
    return CityModel(
      id: _toInt(json['id']),
      name: json['name']?.toString() ?? '',
      state: json['state']?.toString() ?? '',
      areas: raw.map((e) => AreaModel.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}

class AreaModel {
  final int id;
  final String name;
  final String pincode;

  AreaModel({required this.id, required this.name, this.pincode = ''});

  factory AreaModel.fromJson(Map<String, dynamic> json) {
    return AreaModel(
      id: _toInt(json['id']),
      name: json['name']?.toString() ?? '',
      pincode: json['pincode']?.toString() ?? '',
    );
  }
}

class LanguageModel {
  final int id;
  final String name;
  final String nativeName;

  LanguageModel({required this.id, required this.name, this.nativeName = ''});

  factory LanguageModel.fromJson(Map<String, dynamic> json) {
    return LanguageModel(
      id: _toInt(json['id']),
      name: json['name']?.toString() ?? '',
      nativeName: json['native_name']?.toString() ?? '',
    );
  }
}

class PujaCategoryModel {
  final int id;
  final String name;
  final String slug;
  final String icon;
  final String description;
  final int pujasCount;

  PujaCategoryModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.icon,
    required this.description,
    required this.pujasCount,
  });

  factory PujaCategoryModel.fromJson(Map<String, dynamic> json) {
    return PujaCategoryModel(
      id: _toInt(json['id']),
      name: json['name']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      icon: json['icon']?.toString() ?? 'home',
      description: json['description']?.toString() ?? '',
      pujasCount: _toInt(json['pujas_count']),
    );
  }
}

class PujaModel {
  final int id;
  final String name;
  final String slug;
  final int categoryId;
  final String categoryName;
  final String description;
  final double baseDurationHours;

  PujaModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.categoryId,
    required this.categoryName,
    required this.description,
    required this.baseDurationHours,
  });

  factory PujaModel.fromJson(Map<String, dynamic> json) {
    return PujaModel(
      id: _toInt(json['id']),
      name: json['name']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      categoryId: _toInt(json['category_id']),
      categoryName: json['category_name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      baseDurationHours: _toDouble(json['base_duration_hours'] ?? 2),
    );
  }
}

class VenueOption {
  final String code;
  final String label;
  VenueOption({required this.code, required this.label});
  factory VenueOption.fromJson(Map<String, dynamic> json) {
    return VenueOption(
      code: json['code']?.toString() ?? '',
      label: json['label']?.toString() ?? json['code']?.toString() ?? '',
    );
  }
}

class PurohitPackageModel {
  final int id;
  final int pujaId;
  final String pujaName;
  final String pujaDescription;
  final double price;
  final bool includesSamagri;
  final double samagriPrice;
  final String customDescription;
  final double durationHours;
  final List<VenueOption> venues;

  PurohitPackageModel({
    required this.id,
    required this.pujaId,
    required this.pujaName,
    required this.pujaDescription,
    required this.price,
    required this.includesSamagri,
    required this.samagriPrice,
    required this.customDescription,
    required this.durationHours,
    this.venues = const [],
  });

  factory PurohitPackageModel.fromJson(Map<String, dynamic> json) {
    final raw = json['venues'] as List? ?? [];
    return PurohitPackageModel(
      id: _toInt(json['id']),
      pujaId: _toInt(json['puja_id']),
      pujaName: json['puja_name']?.toString() ?? '',
      pujaDescription: json['puja_description']?.toString() ?? '',
      price: _toDouble(json['price']),
      includesSamagri: _toBool(json['includes_samagri']),
      samagriPrice: _toDouble(json['samagri_price']),
      customDescription: json['custom_description']?.toString() ?? '',
      durationHours: _toDouble(json['duration_hours'] ?? 2),
      venues: raw.map((e) => VenueOption.fromJson(Map<String, dynamic>.from(e as Map))).toList(),
    );
  }
}

class PurohitGalleryItem {
  final int id;
  final String mediaType;
  final String url;
  final String title;
  final String caption;
  final bool isFeatured;

  PurohitGalleryItem({
    required this.id,
    required this.mediaType,
    required this.url,
    required this.title,
    required this.caption,
    required this.isFeatured,
  });

  bool get isVideo => mediaType == 'video';

  factory PurohitGalleryItem.fromJson(Map<String, dynamic> json) {
    return PurohitGalleryItem(
      id: _toInt(json['id']),
      mediaType: json['media_type']?.toString() ?? 'photo',
      url: json['url']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      caption: json['caption']?.toString() ?? '',
      isFeatured: _toBool(json['is_featured']),
    );
  }
}

class PurohitModel {
  final int id;
  final String name;
  final String slug;
  final String city;
  final int? cityId;
  final double basePrice;
  final double avgRating;
  final int totalReviews;
  final int totalBookings;
  final bool isFeatured;
  final bool isVerified;
  final String? verifiedByTemple;
  final int experienceYears;
  final String about;
  final List<String> languages;
  final int packagesCount;
  final List<PurohitPackageModel> packages;
  final List<String> offeredPujas;
  final List<PurohitGalleryItem> gallery;
  final String avatarUrl;
  final bool acceptsTravelRequests;
  final String travelNote;

  PurohitModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.city,
    this.cityId,
    required this.basePrice,
    required this.avgRating,
    required this.totalReviews,
    required this.totalBookings,
    required this.isFeatured,
    required this.isVerified,
    this.verifiedByTemple,
    required this.experienceYears,
    required this.about,
    required this.languages,
    required this.packagesCount,
    this.packages = const [],
    this.offeredPujas = const [],
    this.gallery = const [],
    this.avatarUrl = '',
    this.acceptsTravelRequests = true,
    this.travelNote = '',
  });

  factory PurohitModel.fromJson(Map<String, dynamic> json) {
    final rawPackages = json['packages'] as List? ?? [];
    final pkgs = rawPackages.map((p) => PurohitPackageModel.fromJson(Map<String, dynamic>.from(p as Map))).toList();
    final rawGallery = json['gallery'] as List? ?? [];
    return PurohitModel(
      id: _toInt(json['id']),
      name: json['name']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      city: json['city']?.toString() ?? 'India',
      cityId: json['city_id'] == null ? null : _toInt(json['city_id']),
      basePrice: _toDouble(json['base_price'] ?? 1100),
      avgRating: _toDouble(json['avg_rating'] ?? 0),
      totalReviews: _toInt(json['total_reviews']),
      totalBookings: _toInt(json['total_bookings']),
      isFeatured: _toBool(json['is_featured']),
      isVerified: json['is_verified'] == false ? false : true,
      verifiedByTemple: json['verified_by_temple']?.toString(),
      experienceYears: _toInt(json['experience_years'] ?? 0),
      about: json['about']?.toString() ?? '',
      languages: (json['languages'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      packagesCount: _toInt(json['packages_count'] ?? pkgs.length),
      packages: pkgs,
      offeredPujas: (json['offered_pujas'] as List?)?.map((e) => e.toString()).toList()
          ?? pkgs.map((p) => p.pujaName).where((name) => name.isNotEmpty).toList(),
      gallery: rawGallery
          .map((item) => PurohitGalleryItem.fromJson(Map<String, dynamic>.from(item as Map)))
          .where((item) => item.url.isNotEmpty)
          .toList(),
      avatarUrl: _cleanMediaUrl(json['avatar_url']),
      acceptsTravelRequests: json['accepts_travel_requests'] == false ? false : true,
      travelNote: json['travel_note']?.toString() ?? '',
    );
  }
}

class TimeSlot {
  final String start;
  final String label;
  final bool available;

  TimeSlot({required this.start, required this.label, required this.available});

  factory TimeSlot.fromJson(Map<String, dynamic> json) {
    final start = json['value']?.toString() ?? json['start']?.toString() ?? json['time']?.toString() ?? '';
    return TimeSlot(
      start: start,
      label: json['label']?.toString() ?? start,
      available: json['available'] != false,
    );
  }
}

class BookingModel {
  final int id;
  final String bookingId;
  final int? purohitId;
  final String purohitName;
  final int? packageId;
  final String pujaName;
  final String eventDate;
  final String eventTime;
  final String timeWindow;
  final String address;
  final String city;
  final String area;
  final String venueLabel;
  final bool needsSamagri;
  final String specialRequests;
  final double totalAmount;
  final double advancePaid;
  final String status;
  final String paymentStatus;
  final String lifecycleKey;
  final String lifecycleLabel;
  final String rescheduleStatus;
  final String suggestedDate;
  final String rescheduleReason;
  final bool hasReview;
  final String createdAt;
  final String cancellationReason;

  BookingModel({
    required this.id,
    required this.bookingId,
    this.purohitId,
    required this.purohitName,
    this.packageId,
    required this.pujaName,
    required this.eventDate,
    required this.eventTime,
    this.timeWindow = '',
    required this.address,
    this.city = '',
    this.area = '',
    this.venueLabel = '',
    this.needsSamagri = false,
    this.specialRequests = '',
    required this.totalAmount,
    required this.advancePaid,
    required this.status,
    required this.paymentStatus,
    this.lifecycleKey = '',
    this.lifecycleLabel = '',
    this.rescheduleStatus = 'none',
    this.suggestedDate = '',
    this.rescheduleReason = '',
    this.hasReview = false,
    required this.createdAt,
    this.cancellationReason = '',
  });

  factory BookingModel.fromJson(Map<String, dynamic> json) {
    return BookingModel(
      id: _toInt(json['id']),
      bookingId: json['booking_id']?.toString() ?? '',
      purohitId: json['purohit_id'] == null ? null : _toInt(json['purohit_id']),
      purohitName: json['purohit_name']?.toString() ?? 'Vedic Purohit',
      packageId: json['package_id'] == null ? null : _toInt(json['package_id']),
      pujaName: json['puja_name']?.toString() ?? 'Puja Ceremony',
      eventDate: json['event_date']?.toString() ?? '',
      eventTime: json['event_time']?.toString() ?? 'Time TBD',
      timeWindow: json['time_window']?.toString() ?? '',
      address: json['address']?.toString() ?? '',
      city: json['city']?.toString() ?? '',
      area: json['area']?.toString() ?? '',
      venueLabel: json['venue_label']?.toString() ?? '',
      needsSamagri: _toBool(json['needs_samagri']),
      specialRequests: json['special_requests']?.toString() ?? '',
      totalAmount: _toDouble(json['total_amount']),
      advancePaid: _toDouble(json['advance_paid']),
      status: json['status']?.toString() ?? 'pending',
      paymentStatus: json['payment_status']?.toString() ?? 'pending',
      lifecycleKey: json['lifecycle_key']?.toString() ?? '',
      lifecycleLabel: json['lifecycle_label']?.toString() ?? '',
      rescheduleStatus: json['reschedule_status']?.toString() ?? 'none',
      suggestedDate: json['suggested_date']?.toString() ?? '',
      rescheduleReason: json['reschedule_reason']?.toString() ?? '',
      hasReview: _toBool(json['has_review']),
      createdAt: json['created_at']?.toString() ?? json['date']?.toString() ?? '',
      cancellationReason: json['cancellation_reason']?.toString() ?? '',
    );
  }

  bool get isPaid => paymentStatus == 'success';
  bool get canPay => !isPaid && status != 'cancelled';
  bool get canCancel => status != 'cancelled' && status != 'completed';
  bool get canReview => status == 'completed' && !hasReview;
}

class WalletTransactionModel {
  final int id;
  final String type;
  final double amount;
  final String reason;
  final String reference;
  final String status;
  final String date;

  WalletTransactionModel({
    required this.id,
    required this.type,
    required this.amount,
    required this.reason,
    required this.reference,
    required this.status,
    required this.date,
  });

  factory WalletTransactionModel.fromJson(Map<String, dynamic> json) {
    return WalletTransactionModel(
      id: _toInt(json['id']),
      type: json['type']?.toString() ?? 'credit',
      amount: _toDouble(json['amount']),
      reason: json['reason']?.toString() ?? '',
      reference: json['reference']?.toString() ?? '',
      status: json['status']?.toString() ?? 'completed',
      date: json['date']?.toString() ?? '',
    );
  }
}

class AppNotification {
  final int id;
  final String title;
  final String message;
  final bool isRead;
  final String date;

  AppNotification({
    required this.id,
    required this.title,
    required this.message,
    required this.isRead,
    required this.date,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: _toInt(json['id']),
      title: json['title']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      isRead: _toBool(json['is_read']),
      date: json['date']?.toString() ?? '',
    );
  }
}

class ChatMessageModel {
  final int id;
  final String message;
  final bool isMine;
  final String time;

  ChatMessageModel({required this.id, required this.message, required this.isMine, required this.time});

  factory ChatMessageModel.fromJson(Map<String, dynamic> json) {
    return ChatMessageModel(
      id: _toInt(json['id']),
      message: json['message']?.toString() ?? '',
      isMine: _toBool(json['is_mine']),
      time: json['time']?.toString() ?? '',
    );
  }
}

class TravelRequestModel {
  final int id;
  final String requestId;
  final String status;
  final String statusLabel;
  final int purohitId;
  final String purohitName;
  final int? packageId;
  final String pujaName;
  final String city;
  final String area;
  final String address;
  final String preferredDate;
  final String preferredTime;
  final String message;
  final String purohitResponse;
  final double travelFee;
  final String expiresAt;
  final bool canBook;

  TravelRequestModel({
    required this.id,
    required this.requestId,
    required this.status,
    required this.statusLabel,
    required this.purohitId,
    required this.purohitName,
    this.packageId,
    required this.pujaName,
    this.city = '',
    this.area = '',
    this.address = '',
    this.preferredDate = '',
    this.preferredTime = '',
    this.message = '',
    this.purohitResponse = '',
    this.travelFee = 0,
    this.expiresAt = '',
    this.canBook = false,
  });

  factory TravelRequestModel.fromJson(Map<String, dynamic> json) {
    return TravelRequestModel(
      id: _toInt(json['id']),
      requestId: json['request_id']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      statusLabel: json['status_label']?.toString() ?? json['status']?.toString() ?? '',
      purohitId: _toInt(json['purohit_id']),
      purohitName: json['purohit_name']?.toString() ?? '',
      packageId: json['package_id'] == null ? null : _toInt(json['package_id']),
      pujaName: json['puja_name']?.toString() ?? 'Visit request',
      city: json['city']?.toString() ?? '',
      area: json['area']?.toString() ?? '',
      address: json['address']?.toString() ?? '',
      preferredDate: json['preferred_date']?.toString() ?? '',
      preferredTime: json['preferred_time']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      purohitResponse: json['purohit_response']?.toString() ?? '',
      travelFee: _toDouble(json['travel_fee']),
      expiresAt: json['expires_at']?.toString() ?? '',
      canBook: _toBool(json['can_book']),
    );
  }
}

class SupportTicket {
  final String ticketId;
  final String subject;
  final String status;
  final String date;

  SupportTicket({required this.ticketId, required this.subject, required this.status, required this.date});

  factory SupportTicket.fromJson(Map<String, dynamic> json) {
    return SupportTicket(
      ticketId: json['ticket_id']?.toString() ?? '',
      subject: json['subject']?.toString() ?? '',
      status: json['status']?.toString() ?? 'open',
      date: json['date']?.toString() ?? '',
    );
  }
}

class RazorpayOrder {
  final String id;
  final int amountPaise;
  final String currency;
  final String key;
  final bool mock;

  RazorpayOrder({
    required this.id,
    required this.amountPaise,
    required this.currency,
    required this.key,
    required this.mock,
  });

  factory RazorpayOrder.fromJson(Map<String, dynamic> json) {
    return RazorpayOrder(
      id: json['id']?.toString() ?? '',
      amountPaise: _toInt(json['amount']),
      currency: json['currency']?.toString() ?? 'INR',
      key: json['key']?.toString() ?? '',
      mock: _toBool(json['mock']),
    );
  }
}

class PaymentOptions {
  final bool walletAvailable;
  final double walletBalance;
  final double walletShortfall;
  final bool mixedAvailable;
  final double mixedWallet;
  final double mixedRazorpay;

  PaymentOptions({
    this.walletAvailable = false,
    this.walletBalance = 0,
    this.walletShortfall = 0,
    this.mixedAvailable = false,
    this.mixedWallet = 0,
    this.mixedRazorpay = 0,
  });

  factory PaymentOptions.fromJson(Map<String, dynamic>? json) {
    if (json == null) return PaymentOptions();
    final wallet = json['wallet'] as Map<String, dynamic>? ?? {};
    final mixed = json['mixed'] as Map<String, dynamic>? ?? {};
    return PaymentOptions(
      walletAvailable: _toBool(wallet['available']),
      walletBalance: _toDouble(wallet['balance']),
      walletShortfall: _toDouble(wallet['shortfall']),
      mixedAvailable: _toBool(mixed['available']),
      mixedWallet: _toDouble(mixed['wallet_amount']),
      mixedRazorpay: _toDouble(mixed['razorpay_amount']),
    );
  }
}
