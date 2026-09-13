import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/state/booking_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';
import '../../core/widgets/devotee_avatar.dart';
import 'purohit_detail_screen.dart';

const _cityAliases = {
  'bangalore': ['bangalore', 'bengaluru'],
  'bengaluru': ['bangalore', 'bengaluru'],
  'mumbai': ['mumbai', 'bombay'],
  'bombay': ['mumbai', 'bombay'],
  'chennai': ['chennai', 'madras'],
  'madras': ['chennai', 'madras'],
};

class PurohitListScreen extends StatefulWidget {
  final int? pujaId;

  const PurohitListScreen({super.key, this.pujaId});

  @override
  State<PurohitListScreen> createState() => _PurohitListScreenState();
}

class _PurohitListScreenState extends State<PurohitListScreen> {
  final ApiService _api = ApiService();
  final TextEditingController _searchController = TextEditingController();
  List<PurohitModel> _allPurohits = [];
  List<PurohitModel> _filteredPurohits = [];
  List<CityModel> _cities = [];
  List<LanguageModel> _languages = [];
  bool _isLoading = true;
  String _selectedCity = 'All';
  int? _selectedLanguageId;
  Timer? _searchDebounce;

  List<String> get _cityChips {
    final names = _cities.map((c) => c.name).toList();
    if (names.isEmpty) {
      return const ['All', 'Hyderabad', 'Bangalore', 'Mumbai', 'Chennai', 'Pune'];
    }
    return ['All', ...names];
  }

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    try {
      final results = await Future.wait([
        _api.fetchCities(),
        _api.fetchLanguages(),
      ]);
      if (!mounted) return;
      setState(() {
        _cities = results[0] as List<CityModel>;
        _languages = results[1] as List<LanguageModel>;
      });
    } catch (_) {}
    await _loadPurohits();
  }

  Future<void> _loadPurohits() async {
    setState(() => _isLoading = true);
    try {
      final query = _searchController.text.trim();
      final list = await _api.fetchPurohits(
        pujaId: widget.pujaId,
        city: _selectedCity == 'All' ? null : _selectedCity,
        languageId: _selectedLanguageId,
        query: query.isEmpty ? null : query,
      );
      if (!mounted) return;
      _allPurohits = list;
      _filteredPurohits = _locallyMatched(list);
      setState(() => _isLoading = false);
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  bool _cityMatches(String purohitCity, String selected) {
    if (selected == 'All') return true;
    final city = purohitCity.toLowerCase().trim();
    final wanted = selected.toLowerCase().trim();
    final aliases = _cityAliases[wanted] ?? [wanted];
    return aliases.contains(city) || city == wanted;
  }

  List<PurohitModel> _locallyMatched(List<PurohitModel> source) {
    final query = _searchController.text.toLowerCase().trim();
    final languageName = _selectedLanguageId == null
        ? ''
        : _languages
            .where((lang) => lang.id == _selectedLanguageId)
            .map((lang) => lang.name.toLowerCase())
            .firstWhere((_) => true, orElse: () => '');
    return source.where((p) {
      final matchesCity = _cityMatches(p.city, _selectedCity);
      final matchesLanguage = languageName.isEmpty ||
          p.languages.any((lang) => lang.toLowerCase() == languageName || lang.toLowerCase().contains(languageName));
      final matchesQuery = query.isEmpty ||
          p.name.toLowerCase().contains(query) ||
          p.city.toLowerCase().contains(query) ||
          p.about.toLowerCase().contains(query) ||
          p.languages.any((l) => l.toLowerCase().contains(query)) ||
          p.offeredPujas.any((name) => name.toLowerCase().contains(query)) ||
          p.packages.any((pkg) => pkg.pujaName.toLowerCase().contains(query));
      return matchesCity && matchesLanguage && matchesQuery;
    }).toList();
  }

  void _applyLocalFilters() {
    setState(() => _filteredPurohits = _locallyMatched(_allPurohits));
  }

  void _onSearchChanged(String _) {
    _applyLocalFilters();
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 350), _loadPurohits);
  }

  void _selectCity(String city) {
    if (_selectedCity == city) return;
    setState(() => _selectedCity = city);
    _applyLocalFilters();
    _loadPurohits();
  }

  Future<void> _openFilterSheet() async {
    var draftCity = _selectedCity;
    var draftLanguageId = _selectedLanguageId;
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.white,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        final maxHeight = MediaQuery.sizeOf(context).height * 0.78;
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return SizedBox(
              height: maxHeight,
              child: Column(
                children: [
                  const SizedBox(height: 10),
                  Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFFE2E8F0),
                      borderRadius: BorderRadius.circular(99),
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.fromLTRB(20, 14, 20, 8),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text('Filter purohits', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
                    ),
                  ),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('City', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textMuted)),
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: _cityChips.map((city) {
                              return AppSelectChip(
                                label: city,
                                selected: draftCity == city,
                                onTap: () => setSheetState(() => draftCity = city),
                              );
                            }).toList(),
                          ),
                          if (_languages.isNotEmpty) ...[
                            const SizedBox(height: 18),
                            const Text('Language', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textMuted)),
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                AppSelectChip(
                                  label: 'Any',
                                  selected: draftLanguageId == null,
                                  onTap: () => setSheetState(() => draftLanguageId = null),
                                ),
                                ..._languages.map((lang) {
                                  final selected = draftLanguageId == lang.id;
                                  return AppSelectChip(
                                    label: lang.name,
                                    selected: selected,
                                    onTap: () => setSheetState(() => draftLanguageId = selected ? null : lang.id),
                                  );
                                }),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                  SafeArea(
                    top: false,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                      child: Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () {
                                setSheetState(() {
                                  draftCity = 'All';
                                  draftLanguageId = null;
                                });
                              },
                              child: const Text('Clear'),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: ElevatedButton(
                              onPressed: () {
                                Navigator.pop(context);
                                setState(() {
                                  _selectedCity = draftCity;
                                  _selectedLanguageId = draftLanguageId;
                                });
                                _applyLocalFilters();
                                _loadPurohits();
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.sacredGold,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text('Apply filters'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Find Vedic Purohit'),
        leading: AppBackButton.maybe(context),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: Icon(
              CupertinoIcons.slider_horizontal_3,
              color: _selectedLanguageId != null || _selectedCity != 'All' ? AppTheme.sacredGold : AppTheme.textDark,
            ),
            onPressed: _openFilterSheet,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: TextField(
              controller: _searchController,
              onChanged: _onSearchChanged,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _loadPurohits(),
              decoration: InputDecoration(
                hintText: 'Search by Purohit, language, or puja...',
                prefixIcon: const Icon(CupertinoIcons.search, color: AppTheme.textLight),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(CupertinoIcons.clear_circled_solid, size: 18),
                        onPressed: () {
                          _searchController.clear();
                          _applyLocalFilters();
                          _loadPurohits();
                        },
                      )
                    : null,
              ),
            ),
          ),
          SizedBox(
            height: 48,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 20),
              itemCount: _cityChips.length,
              itemBuilder: (context, index) {
                final city = _cityChips[index];
                final isSelected = _selectedCity == city;
                return AppSelectChip(
                  label: city,
                  selected: isSelected,
                  onTap: () => _selectCity(city),
                  margin: const EdgeInsets.only(right: 8, top: 4, bottom: 4),
                );
              },
            ),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                : _filteredPurohits.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(CupertinoIcons.person_crop_circle_badge_exclam, size: 48, color: AppTheme.textLight),
                            const SizedBox(height: 12),
                            Text(
                              _searchController.text.trim().isNotEmpty
                                  ? 'No purohits match “${_searchController.text.trim()}”'
                                  : 'No purohits found in $_selectedCity',
                              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: AppTheme.textMuted),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                        itemCount: _filteredPurohits.length,
                        itemBuilder: (context, index) {
                          final p = _filteredPurohits[index];
                          return _buildPurohitCard(context, p);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildPurohitCard(BuildContext context, PurohitModel purohit) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0x18FF6D00), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 15,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DevoteeAvatar(
                size: 58,
                name: purohit.name,
                imageUrl: purohit.avatarUrl,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            purohit.name,
                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppTheme.textDark),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Row(
                          children: [
                            const Icon(CupertinoIcons.star_fill, size: 14, color: AppTheme.sacredGold),
                            const SizedBox(width: 4),
                            Text(
                              purohit.avgRating.toStringAsFixed(1),
                              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${purohit.experienceYears}+ years exp • ${purohit.city}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, fontWeight: FontWeight.w500),
                    ),
                    if (purohit.verifiedByTemple != null && purohit.verifiedByTemple!.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.tulsiGreen.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          purohit.verifiedByTemple!,
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.tulsiGreen),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            purohit.about,
            style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.4),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            children: purohit.languages.map((l) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(l, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textMuted)),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          const Divider(height: 1, color: Color(0xFFF1F5F9)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('From', style: TextStyle(fontSize: 11, color: AppTheme.textLight)),
                  Text(
                    '₹${purohit.basePrice.toInt()}',
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.primary),
                  ),
                ],
              ),
              ElevatedButton(
                onPressed: () {
                  context.read<BookingProvider>().selectPurohit(purohit);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => PurohitDetailScreen(purohitId: purohit.id)),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text('View & Book', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
