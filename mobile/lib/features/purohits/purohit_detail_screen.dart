import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/state/booking_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/devotee_avatar.dart';
import '../booking/booking_screen.dart';
import 'widgets/ritual_gallery_section.dart';

class PurohitDetailScreen extends StatefulWidget {
  final int purohitId;

  const PurohitDetailScreen({super.key, required this.purohitId});

  @override
  State<PurohitDetailScreen> createState() => _PurohitDetailScreenState();
}

class _PurohitDetailScreenState extends State<PurohitDetailScreen> {
  final ApiService _api = ApiService();
  PurohitModel? _purohit;
  bool _isLoading = true;
  PurohitPackageModel? _selectedPackage;

  @override
  void initState() {
    super.initState();
    _fetchDetail();
  }

  Future<void> _fetchDetail() async {
    try {
      final detail = await _api.fetchPurohitDetail(widget.purohitId);
      if (!mounted) return;
      setState(() {
        _purohit = detail;
        if (detail.packages.isNotEmpty) {
          _selectedPackage = detail.packages.first;
        }
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.surfaceCream,
        body: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
      );
    }
    if (_purohit == null) {
      return Scaffold(
        appBar: AppBar(leading: const AppBackButton(), automaticallyImplyLeading: false),
        body: const Center(child: Text('Could not load this purohit.')),
      );
    }

    final p = _purohit!;

    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      body: CustomScrollView(
        slivers: [
          // Elegant Sliver App Bar with spiritual header
          SliverAppBar(
            expandedHeight: 220,
            pinned: true,
            backgroundColor: const Color(0xFFFFF7ED),
            surfaceTintColor: Colors.transparent,
            leading: const AppBackButton(),
            automaticallyImplyLeading: false,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: const BoxDecoration(
                  gradient: AppTheme.creamHeroGradient,
                ),
                child: Stack(
                  children: [
                    Positioned(
                      right: -40,
                      top: -30,
                      child: Container(
                        width: 180,
                        height: 180,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: RadialGradient(
                            colors: [Color(0x38F59E0B), Color(0x00F59E0B)],
                          ),
                        ),
                      ),
                    ),
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const SizedBox(height: 30),
                          DevoteeAvatar(
                            size: 80,
                            name: p.name,
                            imageUrl: p.avatarUrl,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            p.name,
                            style: const TextStyle(
                              color: AppTheme.textDark,
                              fontWeight: FontWeight.w900,
                              fontSize: 20,
                              letterSpacing: -0.3,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${p.city} • ${p.experienceYears}+ Years Vedic Service',
                            style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Content body
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Badges Row
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: AppTheme.tulsiGreen.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(CupertinoIcons.checkmark_seal_fill, size: 14, color: AppTheme.tulsiGreen),
                            const SizedBox(width: 6),
                            Text(
                              p.verifiedByTemple ?? 'Vedic Verified',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.tulsiGreen,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Spacer(),
                      Row(
                        children: [
                          const Icon(CupertinoIcons.star_fill, size: 16, color: AppTheme.sacredGold),
                          const SizedBox(width: 4),
                          Text(
                            p.avgRating.toStringAsFixed(2),
                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: AppTheme.textDark),
                          ),
                          Text(
                            ' (${p.totalReviews} reviews)',
                            style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // About Purohit
                  const Text(
                    'About Purohit Ji',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textDark),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    p.about,
                    style: const TextStyle(fontSize: 14, color: AppTheme.textMuted, height: 1.5),
                  ),
                  const SizedBox(height: 20),

                  // Languages
                  const Text(
                    'Languages Spoken for Rituals',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: p.languages.map((l) {
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xFFE2E8F0)),
                        ),
                        child: Text(
                          l,
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 28),

                  RitualGallerySection(
                    purohitName: p.name,
                    gallery: p.gallery,
                  ),
                  const SizedBox(height: 28),

                  // Packages Section
                  const Text(
                    'Select Puja Package',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.textDark),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Choose a ritual vidhi to customize your muhurat booking',
                    style: TextStyle(fontSize: 13, color: AppTheme.textLight),
                  ),
                  const SizedBox(height: 14),

                  if (p.packages.isEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text('Direct Vedic Booking with customized samagri available.'),
                    )
                  else
                    ...p.packages.map((pkg) {
                      final isSelected = _selectedPackage?.id == pkg.id;
                      return GestureDetector(
                        onTap: () => setState(() => _selectedPackage = pkg),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(
                              color: isSelected ? AppTheme.sacredGold : const Color(0xFFE2E8F0),
                              width: isSelected ? 2 : 1,
                            ),
                            boxShadow: isSelected
                                ? [
                                    BoxShadow(
                                      color: AppTheme.sacredGold.withOpacity(0.18),
                                      blurRadius: 10,
                                      offset: const Offset(0, 4),
                                    )
                                  ]
                                : null,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Text(
                                      pkg.pujaName,
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w800,
                                        color: isSelected ? AppTheme.sacredRust : AppTheme.textDark,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    '₹${pkg.price.toInt()}',
                                    style: const TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w900,
                                      color: AppTheme.textDark,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(
                                pkg.pujaDescription,
                                style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
                              ),
                              const SizedBox(height: 10),
                              Row(
                                children: [
                                  const Icon(CupertinoIcons.clock, size: 13, color: AppTheme.textLight),
                                  const SizedBox(width: 4),
                                  Text('${pkg.durationHours} Hours', style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                                  const SizedBox(width: 14),
                                  Icon(
                                    pkg.includesSamagri ? CupertinoIcons.checkmark_circle_fill : CupertinoIcons.circle,
                                    size: 13,
                                    color: pkg.includesSamagri ? AppTheme.tulsiGreen : AppTheme.textLight,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    pkg.includesSamagri ? 'Samagri Included' : 'Samagri Optional (+₹${pkg.samagriPrice.toInt()})',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: pkg.includesSamagri ? AppTheme.tulsiGreen : AppTheme.textMuted,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                  const SizedBox(height: 100),
                ],
              ),
            ),
          ),
        ],
      ),

      // Bottom Sticky Booking Button
      bottomSheet: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.06),
              blurRadius: 20,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: SafeArea(
          child: Row(
            children: [
              Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Total Dakshina', style: TextStyle(fontSize: 11, color: AppTheme.textLight)),
                  Text(
                    '₹${(_selectedPackage?.price ?? p.basePrice).toInt()}',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.primary,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 20),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    final bookingProv = context.read<BookingProvider>();
                    bookingProv.selectPurohit(p, package: _selectedPackage);
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const BookingScreen()),
                    );
                  },
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('Proceed to Book'),
                      SizedBox(width: 8),
                      Icon(CupertinoIcons.arrow_right, size: 18),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
