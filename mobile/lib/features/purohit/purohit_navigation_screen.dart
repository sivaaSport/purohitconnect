import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/state/auth_provider.dart';
import '../../core/state/notification_provider.dart';
import '../../core/theme/app_theme.dart';
import '../profile/profile_screen.dart';
import 'purohit_bookings_screen.dart';
import 'purohit_home_screen.dart';
import 'purohit_travel_screen.dart';

class PurohitNavigationScreen extends StatefulWidget {
  const PurohitNavigationScreen({super.key});

  @override
  State<PurohitNavigationScreen> createState() => _PurohitNavigationScreenState();
}

class _PurohitNavigationScreenState extends State<PurohitNavigationScreen> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotificationProvider>().refresh();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final userName = auth.user?.name ?? 'Purohit';
    final initial = userName.isNotEmpty ? userName[0].toUpperCase() : 'ॐ';
    const pages = [
      PurohitHomeScreen(),
      PurohitBookingsScreen(),
      PurohitTravelScreen(),
      ProfileScreen(purohitMode: true),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: pages),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(28),
          child: Container(
            height: 68,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFFFFF7ED), Color(0xFFFFFFFF)],
              ),
              borderRadius: BorderRadius.circular(28),
              border: Border.all(color: const Color(0x24B45309)),
              boxShadow: const [
                BoxShadow(color: Color(0x1AF59E0B), blurRadius: 16, offset: Offset(0, 6)),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _nav(0, CupertinoIcons.square_grid_2x2_fill, CupertinoIcons.square_grid_2x2, 'Home'),
                _nav(1, CupertinoIcons.calendar, CupertinoIcons.calendar, 'Bookings'),
                _nav(2, CupertinoIcons.location_solid, CupertinoIcons.location, 'Travel'),
                _profile(3, initial, userName),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _nav(int index, IconData on, IconData off, String label) {
    final selected = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        padding: EdgeInsets.symmetric(horizontal: selected ? 14 : 12, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? AppTheme.sacredGold.withValues(alpha: 0.16) : Colors.transparent,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(selected ? on : off, size: 20, color: selected ? AppTheme.sacredRust : AppTheme.textMuted),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: selected ? AppTheme.sacredRust : AppTheme.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _profile(int index, String initial, String name) {
    final selected = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircleAvatar(
            radius: 12,
            backgroundColor: selected ? AppTheme.sacredGold : const Color(0xFFF1F5F9),
            child: Text(initial, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
          ),
          const SizedBox(height: 2),
          Text(
            'You',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: selected ? AppTheme.sacredRust : AppTheme.textMuted,
            ),
          ),
        ],
      ),
    );
  }
}
