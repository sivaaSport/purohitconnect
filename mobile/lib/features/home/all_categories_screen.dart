import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../../core/constants/catalog_order.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';
import '../purohits/purohit_list_screen.dart';

class AllCategoriesScreen extends StatefulWidget {
  final int initialCategoryIndex;

  const AllCategoriesScreen({super.key, this.initialCategoryIndex = 0});

  @override
  State<AllCategoriesScreen> createState() => _AllCategoriesScreenState();
}

class _AllCategoriesScreenState extends State<AllCategoriesScreen> {
  final ApiService _api = ApiService();
  List<PujaCategoryModel> _categories = [];
  List<PujaModel> _pujas = [];
  bool _isLoading = true;
  int _selectedCategoryIndex = 0;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _selectedCategoryIndex = widget.initialCategoryIndex;
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
    final cats = sortByCatalogCategory(await _api.fetchCategories(), (c) => c.name);
    final pujas = await _api.fetchPujas();
    if (mounted) {
      setState(() {
        _categories = cats;
        _pujas = pujas;
        if (_selectedCategoryIndex >= cats.length) _selectedCategoryIndex = 0;
        _isLoading = false;
      });
    }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  List<PujaModel> get _filteredPujas {
    if (_categories.isEmpty) return _pujas;
    final selectedCat = _categories[_selectedCategoryIndex.clamp(0, _categories.length - 1)];
    final query = _searchController.text.toLowerCase().trim();

    return _pujas.where((p) {
      final matchesCategory = p.categoryId == selectedCat.id || p.categoryName.toLowerCase() == selectedCat.name.toLowerCase();
      final matchesQuery = query.isEmpty ||
          p.name.toLowerCase().contains(query) ||
          p.description.toLowerCase().contains(query);
      return matchesCategory && matchesQuery;
    }).toList();
  }

  IconData _getCategoryIcon(String iconName) {
    switch (iconName.toLowerCase()) {
      case 'home':
        return CupertinoIcons.house_fill;
      case 'baby':
        return CupertinoIcons.heart_fill;
      case 'sparkles':
        return CupertinoIcons.sparkles;
      case 'shield':
        return CupertinoIcons.shield_fill;
      default:
        return CupertinoIcons.flame_fill;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('All Sacred Categories'),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : Column(
              children: [
                // Search Bar
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  child: TextField(
                    controller: _searchController,
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(
                      hintText: 'Search rituals, havans, and pujas...',
                      prefixIcon: const Icon(CupertinoIcons.search, color: AppTheme.textLight),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(CupertinoIcons.clear_circled_solid, size: 18),
                              onPressed: () {
                                _searchController.clear();
                                setState(() {});
                              },
                            )
                          : null,
                    ),
                  ),
                ),

                // Category Tabs Selector
                SizedBox(
                  height: 52,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    itemCount: _categories.length,
                    itemBuilder: (context, index) {
                      final cat = _categories[index];
                      final isSelected = _selectedCategoryIndex == index;
                      return AppSelectChip(
                        label: cat.name,
                        selected: isSelected,
                        icon: _getCategoryIcon(cat.icon),
                        fontSize: 13,
                        margin: const EdgeInsets.only(right: 10, top: 4, bottom: 4),
                        onTap: () => setState(() => _selectedCategoryIndex = index),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 12),

                // Category Description Banner
                if (_categories.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFF1F5F9)),
                      ),
                      child: Text(
                        _categories[_selectedCategoryIndex.clamp(0, _categories.length - 1)].description,
                        style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.4),
                      ),
                    ),
                  ),
                const SizedBox(height: 12),

                // Ceremonies List
                Expanded(
                  child: _filteredPujas.isEmpty
                      ? const Center(
                          child: Text(
                            'No pujas found in this category',
                            style: TextStyle(fontSize: 14, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                          itemCount: _filteredPujas.length,
                          itemBuilder: (context, index) {
                            final puja = _filteredPujas[index];
                            return _buildPujaItem(context, puja);
                          },
                        ),
                ),
              ],
            ),
    );
  }

  Widget _buildPujaItem(BuildContext context, PujaModel puja) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  gradient: AppTheme.saffronGradient,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Center(
                  child: Text('ॐ', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      puja.name,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppTheme.textDark),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      puja.description,
                      style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.4),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(height: 1, color: Color(0xFFF1F5F9)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(CupertinoIcons.clock, size: 14, color: AppTheme.textLight),
                  const SizedBox(width: 6),
                  Text(
                    '${puja.baseDurationHours} Hours Vidhi',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                  ),
                ],
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
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text('Book with Purohit', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
