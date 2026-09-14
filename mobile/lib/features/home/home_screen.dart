import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../../core/constants/catalog_order.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/state/auth_provider.dart';
import '../../core/state/booking_provider.dart';
import '../../core/theme/app_theme.dart';
import 'widgets/muhurat_card.dart';
import 'widgets/featured_purohit_card.dart';
import 'widgets/travel_requests_section.dart';
import 'widgets/popular_season_section.dart';
import 'widgets/devotee_home_banner.dart';
import '../profile/my_bookings_screen.dart';
import 'all_categories_screen.dart';
import '../../core/widgets/devotee_avatar.dart';
import '../purohits/purohit_detail_screen.dart';
import '../purohits/purohit_list_screen.dart';
import '../profile/wallet_screen.dart';
import '../profile/profile_screen.dart';
import '../profile/notifications_screen.dart';
import '../../core/state/notification_provider.dart';
import '../../core/widgets/ui_kit.dart';
import '../../core/widgets/app_select_chip.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _api = ApiService();
  List<PujaCategoryModel> _categories = [];
  List<PurohitModel> _purohits = [];
  List<PujaModel> _pujas = [];
  List<PujaModel> _featuredPujas = [];
  List<TravelRequestModel> _travelRequests = [];
  List<BookingModel> _bookings = [];
  bool _isLoading = true;
  String? _error;
  int _selectedCategoryIndex = 0;
  final ScrollController _scrollController = ScrollController();
  final GlobalKey _travelKey = GlobalKey();
  final GlobalKey _browseKey = GlobalKey();

  int _seenTravelRevision = 0;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final revision = context.watch<BookingProvider>().travelRevision;
    if (revision != _seenTravelRevision) {
      _seenTravelRevision = revision;
      if (revision > 0) _loadData();
    }
  }

  PujaCategoryModel? get _selectedCategory {
    if (_categories.isEmpty) return null;
    return _categories[_selectedCategoryIndex.clamp(0, _categories.length - 1)];
  }

  List<PujaModel> get _selectedRituals {
    final cat = _selectedCategory;
    if (cat == null) return _pujas;
    return _pujas.where((p) {
      return p.categoryId == cat.id || p.categoryName.toLowerCase() == cat.name.toLowerCase();
    }).toList();
  }

  Future<void> _loadData() async {
    setState(() {
      _error = null;
      if (_categories.isEmpty && _pujas.isEmpty) _isLoading = true;
    });
    try {
      final catalog = await Future.wait([
        _api.fetchCategories(),
        _api.fetchPujas(),
        _api.fetchPujas(featured: true),
      ]);
      if (!mounted) return;
      final cats = sortByCatalogCategory(
        catalog[0] as List<PujaCategoryModel>,
        (c) => c.name,
      );
      final allPujas = catalog[1] as List<PujaModel>;
      final featuredIncoming = catalog[2] as List<PujaModel>;
      final byName = {for (final puja in [...featuredIncoming, ...allPujas]) puja.name: puja};
      var featured = [
        for (final name in kFeaturedPujaNames)
          if (byName.containsKey(name)) byName[name]!,
      ];
      if (featured.isEmpty) {
        featured = featuredIncoming.take(4).toList();
      }
      setState(() {
        _categories = cats;
        _pujas = allPujas;
        _featuredPujas = featured;
        if (_selectedCategoryIndex >= cats.length) _selectedCategoryIndex = 0;
        _isLoading = false;
      });
      try {
        final extras = await Future.wait([
          _api.fetchTravelRequests(),
          _api.fetchMyBookings(),
        ]);
        if (mounted) {
          setState(() {
            _travelRequests = extras[0] as List<TravelRequestModel>;
            _bookings = extras[1] as List<BookingModel>;
          });
        }
      } catch (_) {}

      var purohits = await _api.fetchPurohits(featured: true);
      if (purohits.isEmpty) {
        purohits = await _api.fetchPurohits();
      }
      if (!mounted) return;
      setState(() => _purohits = purohits);
      context.read<NotificationProvider>().refresh();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  DateTime get _today {
    final now = DateTime.now();
    return DateTime(now.year, now.month, now.day);
  }

  DateTime? _eventDate(BookingModel booking) {
    return DateTime.tryParse(booking.eventDate.split('T').first);
  }

  int get _upcomingCount => _bookings.where((booking) {
        if (booking.status == 'cancelled' || booking.status == 'completed') return false;
        final date = _eventDate(booking);
        return date != null && !date.isBefore(_today);
      }).length;

  int get _awaitingPaymentCount => _bookings
      .where((booking) => booking.status != 'cancelled' && booking.paymentStatus == 'pending')
      .length;

  int get _completedCount => _bookings.where((booking) => booking.status == 'completed').length;

  int get _travelWaitingCount => _travelRequests.where((item) => item.status == 'pending').length;

  String _heroLead() {
    final next = _bookings.where((booking) {
      if (booking.status == 'cancelled' || booking.status == 'completed') return false;
      final date = _eventDate(booking);
      return date != null && !date.isBefore(_today);
    }).toList()
      ..sort((a, b) => (a.eventDate).compareTo(b.eventDate));
    if (next.isEmpty) {
      return 'Book a verified purohit for your next ceremony. Price and time stay clear before you pay.';
    }
    final booking = next.first;
    final date = _eventDate(booking)!;
    final days = date.difference(_today).inDays;
    if (days == 0) return 'Today: ${booking.pujaName}${booking.eventTime.isNotEmpty ? ' at ${booking.eventTime}' : ''}.';
    if (days == 1) return 'Tomorrow: ${booking.pujaName} with ${booking.purohitName}.';
    return 'Next ritual in $days days — ${booking.pujaName}.';
  }

  void _scrollTo(GlobalKey key) {
    final context = key.currentContext;
    if (context == null) return;
    Scrollable.ensureVisible(context, duration: const Duration(milliseconds: 380), curve: Curves.easeOut);
  }

  void _openBookings() {
    Navigator.push(context, MaterialPageRoute(builder: (_) => const MyBookingsScreen()));
  }

  void _openRituals({int? categoryIndex}) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => AllCategoriesScreen(
          initialCategoryIndex: categoryIndex ?? _selectedCategoryIndex,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final userName = auth.user?.name ?? 'Devotee';
    final firstName = userName.split(' ').first;

    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.primary,
          onRefresh: _loadData,
          child: SingleChildScrollView(
            controller: _scrollController,
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Header Row
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        DevoteeAvatar(
                          size: 48,
                          name: userName,
                          imageUrl: auth.user?.avatarUrl ?? '',
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const ProfileScreen()),
                            );
                          },
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              '🙏 Shubh Prabhat',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.primary,
                                letterSpacing: 0.3,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Namaste, $firstName 🙏',
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w900,
                                color: AppTheme.textDark,
                                letterSpacing: -0.4,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    Row(
                      children: [
                    GestureDetector(
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen()));
                      },
                      child: Stack(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
                            child: const Icon(CupertinoIcons.bell, color: AppTheme.textDark, size: 20),
                          ),
                          if (context.watch<NotificationProvider>().unreadCount > 0)
                            Positioned(
                              right: 4,
                              top: 4,
                              child: Container(
                                width: 8,
                                height: 8,
                                decoration: const BoxDecoration(color: AppTheme.sindoorRed, shape: BoxShape.circle),
                              ),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const WalletScreen()),
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0x15FF6D00), width: 1.2),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.03),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            const Icon(CupertinoIcons.creditcard, size: 16, color: AppTheme.sacredGold),
                            const SizedBox(width: 6),
                            Text(
                              '₹${auth.walletBalance.toInt()}',
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.textDark,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                DevoteeHomeBanner(
                  name: firstName,
                  lead: _heroLead(),
                  onBookPuja: _openRituals,
                  onFindPurohit: () {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const PurohitListScreen()));
                  },
                ),
                const SizedBox(height: 12),
                DevoteeStatStrip(
                  upcoming: _upcomingCount,
                  awaitingPayment: _awaitingPaymentCount,
                  travelWaiting: _travelWaitingCount,
                  completed: _completedCount,
                  onTapStat: (key) {
                    if (key == 'travel') {
                      _scrollTo(_travelKey);
                    } else {
                      _openBookings();
                    }
                  },
                ),
                const SizedBox(height: 12),
                DevoteeJumpRow(
                  onTravel: () => _scrollTo(_travelKey),
                  onBrowse: () => _scrollTo(_browseKey),
                ),
                const SizedBox(height: 20),

                // Auspicious Muhurat Card
                const MuhuratCard(),
                if (_error != null) ...[
                  const SizedBox(height: 16),
                  ErrorBanner(message: _error!, onRetry: _loadData),
                ],
                const SizedBox(height: 28),
                KeyedSubtree(
                  key: _travelKey,
                  child: TravelRequestsSection(
                  requests: _travelRequests,
                  onBook: (item) {
                    if (item.purohitId <= 0) return;
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => PurohitDetailScreen(purohitId: item.purohitId),
                      ),
                    );
                  },
                ),
                ),
                const SizedBox(height: 28),
                KeyedSubtree(
                  key: _browseKey,
                  child: PopularSeasonSection(
                  pujas: _featuredPujas,
                  onSeeAll: _openRituals,
                  onTapPuja: (puja) {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => PurohitListScreen(pujaId: puja.id)),
                    );
                  },
                ),
                ),
                const SizedBox(height: 28),

                // Categories Section Header with View All
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Sacred Rituals',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textDark,
                      ),
                    ),
                    GestureDetector(
                      onTap: _openRituals,
                      child: const Row(
                        children: [
                          Text(
                            'View All',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppTheme.primary,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          SizedBox(width: 4),
                          Icon(CupertinoIcons.chevron_right, size: 14, color: AppTheme.primary),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                // Categories Horizontal List
                SizedBox(
                  height: 42,
                  child: _isLoading && _categories.isEmpty
                      ? ListView(
                          scrollDirection: Axis.horizontal,
                          children: List.generate(
                            4,
                            (index) => Container(
                              width: 120,
                              margin: const EdgeInsets.only(right: 10),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: const Color(0xFFE2E8F0)),
                              ),
                            ),
                          ),
                        )
                      : ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: _categories.length,
                    itemBuilder: (context, index) {
                      final cat = _categories[index];
                      final isSelected = _selectedCategoryIndex == index;
                      return AppSelectChip(
                        label: cat.name,
                        selected: isSelected,
                        fontSize: 13,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        margin: const EdgeInsets.only(right: 10),
                        onTap: () => setState(() => _selectedCategoryIndex = index),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 22),

                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _selectedCategory != null
                          ? '${_selectedCategory!.name} Packages'
                          : 'Popular Puja Packages',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textDark,
                      ),
                    ),
                    GestureDetector(
                      onTap: _openRituals,
                      child: const Text(
                        'See All',
                        style: TextStyle(fontSize: 13, color: AppTheme.primary, fontWeight: FontWeight.w800),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                if (_isLoading && _pujas.isEmpty)
                  ...List.generate(3, (_) => const _RitualCardSkeleton())
                else if (_selectedRituals.isEmpty)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 22),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: const Color(0xFFF1F5F9)),
                    ),
                    child: const Text(
                      'No rituals in this category yet.',
                      style: TextStyle(fontSize: 13, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                    ),
                  )
                else
                  ..._selectedRituals.map((puja) => _buildPujaCard(context, puja)),

                if (_purohits.isNotEmpty) ...[
                  const SizedBox(height: 28),
                  const Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Verified Purohits',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.textDark,
                        ),
                      ),
                      Row(
                        children: [
                          Icon(CupertinoIcons.checkmark_shield_fill, size: 14, color: AppTheme.tulsiGreen),
                          SizedBox(width: 4),
                          Text(
                            '100% Vedic Vetted',
                            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.tulsiGreen),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    height: 230,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: _purohits.length,
                      itemBuilder: (context, index) {
                        final p = _purohits[index];
                        return FeaturedPurohitCard(
                          purohit: p,
                          onTap: () {
                            context.read<BookingProvider>().selectPurohit(p);
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => PurohitDetailScreen(purohitId: p.id),
                              ),
                            );
                          },
                        );
                      },
                    ),
                  ),
                ],
                const SizedBox(height: 20),

                // Trust Badge Banner
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF7ED),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFFFFEDD5)),
                  ),
                  child: const Row(
                    children: [
                      Icon(CupertinoIcons.shield_lefthalf_fill, color: AppTheme.primary, size: 32),
                      SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'PurohitConnect Guarantee',
                              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: AppTheme.textDark),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'Authentic vidhi, pure organic samagri, and punctual purohits guaranteed.',
                              style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 30),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPujaCard(BuildContext context, PujaModel puja) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFF1F5F9), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Center(
              child: Icon(CupertinoIcons.flame_fill, color: AppTheme.primary, size: 24),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  puja.name,
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppTheme.textDark),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(CupertinoIcons.clock, size: 12, color: AppTheme.textLight),
                    const SizedBox(width: 4),
                    Text(
                      '${puja.baseDurationHours} Hours',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      puja.categoryName,
                      style: const TextStyle(fontSize: 12, color: AppTheme.primary, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ],
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => PurohitListScreen(pujaId: puja.id)),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('Book', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }
}

class _RitualCardSkeleton extends StatelessWidget {
  const _RitualCardSkeleton();

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      height: 80,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFF1F5F9)),
      ),
    );
  }
}
