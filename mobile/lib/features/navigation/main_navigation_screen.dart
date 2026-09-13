import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/state/auth_provider.dart';
import '../../core/state/notification_provider.dart';
import '../home/home_screen.dart';
import '../purohits/purohit_list_screen.dart';
import '../profile/my_bookings_screen.dart';
import '../profile/profile_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
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
    final userName = auth.user?.name ?? 'Devotee';
    final initial = userName.isNotEmpty ? userName[0].toUpperCase() : 'ॐ';
    final pages = const [HomeScreen(), PurohitListScreen(), MyBookingsScreen(), ProfileScreen()];

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
              boxShadow: [
                BoxShadow(color: const Color(0x1AF59E0B), blurRadius: 16, offset: const Offset(0, 6)),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _nav(0, CupertinoIcons.flame_fill, CupertinoIcons.flame, 'Home'),
                _nav(1, CupertinoIcons.person_2_fill, CupertinoIcons.person_2, 'Purohits'),
                _nav(2, CupertinoIcons.calendar_today, CupertinoIcons.calendar, 'Bookings'),
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
          color: selected ? const Color(0xFFF59E0B) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          children: [
            Icon(selected ? on : off, color: selected ? Colors.white : const Color(0xFFB45309), size: 22),
            if (selected) ...[
              const SizedBox(width: 8),
              Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _profile(int index, String initial, String fullName) {
    final selected = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        padding: EdgeInsets.symmetric(horizontal: selected ? 14 : 12, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFFF59E0B) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          children: [
            Container(
              width: 26,
              height: 26,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: selected
                    ? AppTheme.saffronGradient
                    : const LinearGradient(colors: [Color(0xFFF59E0B), Color(0xFFB45309)]),
              ),
              child: Center(child: Text(initial, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 11))),
            ),
            if (selected) ...[
              const SizedBox(width: 8),
              Text(fullName.split(' ').first, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }
}
