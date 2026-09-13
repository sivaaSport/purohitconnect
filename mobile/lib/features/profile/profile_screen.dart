import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../../core/state/auth_provider.dart';
import '../../core/state/booking_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/devotee_avatar.dart';
import 'wallet_screen.dart';
import 'my_bookings_screen.dart';
import 'support_center_screen.dart';
import 'notifications_screen.dart';
import '../auth/welcome_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthProvider>().refreshUser();
      context.read<BookingProvider>().loadMyBookings(status: 'all');
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final bookings = context.watch<BookingProvider>().myBookings;
    final completedCount = bookings.where((booking) => booking.status == 'completed').length;
    final user = auth.user;
    final name = user?.name ?? 'Devotee';
    final phone = user?.phone ?? '';

    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Devotee Profile'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        child: Column(
          children: [
            // Profile Card Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: const Color(0x18FF6D00), width: 1.2),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 15,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: Row(
                children: [
                  DevoteeAvatar(
                    size: 68,
                    showBorder: true,
                    name: name,
                    imageUrl: user?.avatarUrl ?? '',
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          name,
                          style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: AppTheme.textDark),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          phone,
                          style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.tulsiGreen.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Text(
                            '✓ Phone Verified',
                            style: TextStyle(color: AppTheme.tulsiGreen, fontSize: 10, fontWeight: FontWeight.w700),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Quick Stats Row
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                Expanded(
                  child: _buildStatTile(
                    '₹${auth.walletBalance.toInt()}',
                    'Wallet Balance',
                    CupertinoIcons.creditcard_fill,
                    AppTheme.sacredGold,
                    () => Navigator.push(context, MaterialPageRoute(builder: (_) => const WalletScreen())),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatTile(
                    '$completedCount',
                    'Bookings Done',
                    CupertinoIcons.flame_fill,
                    AppTheme.primary,
                    () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyBookingsScreen())),
                  ),
                ),
              ],
              ),
            ),
            const SizedBox(height: 24),

            // Menu Section
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                children: [
                  _buildMenuItem(
                    context,
                    'Wallet & Passbook',
                    'Manage funds, top-up & transaction logs',
                    CupertinoIcons.creditcard,
                    () => Navigator.push(context, MaterialPageRoute(builder: (_) => const WalletScreen())),
                  ),
                  const Divider(height: 1, color: Color(0xFFF1F5F9)),
                  _buildMenuItem(
                    context,
                    'My Sacred Bookings',
                    'Upcoming pujas, muhurat & receipts',
                    CupertinoIcons.calendar,
                    () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyBookingsScreen())),
                  ),
                  const Divider(height: 1, color: Color(0xFFF1F5F9)),
                  _buildMenuItem(
                    context,
                    'Notifications',
                    'Booking, chat, and payment updates',
                    CupertinoIcons.bell,
                    () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationsScreen())),
                  ),
                  const Divider(height: 1, color: Color(0xFFF1F5F9)),
                  _buildMenuItem(
                    context,
                    '24x7 Vedic Helpline',
                    'Connect with spiritual counselors on WhatsApp',
                    CupertinoIcons.phone_circle_fill,
                    () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Helpline: +91 98765 43210 available 24x7')),
                      );
                    },
                  ),
                  const Divider(height: 1, color: Color(0xFFF1F5F9)),
                  _buildMenuItem(
                    context,
                    'Help & Support Center',
                    'FAQs, raise a ticket, contact helpline',
                    CupertinoIcons.question_circle,
                    () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SupportCenterScreen())),
                  ),
                  const Divider(height: 1, color: Color(0xFFF1F5F9)),
                  _buildMenuItem(
                    context,
                    'Sign Out / Switch User',
                    'Log out of current session',
                    CupertinoIcons.square_arrow_left,
                    () async {
                      await auth.logout();
                      if (!context.mounted) return;
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const WelcomeScreen()),
                        (route) => false,
                      );
                    },
                    isDestructive: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),

            const Text(
              'PurohitConnect v1.0.0 (Vedic Cross-Platform Edition)',
              style: TextStyle(fontSize: 12, color: AppTheme.textLight, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildStatTile(String value, String label, IconData icon, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14, color: AppTheme.textDark),
                  ),
                  Text(
                    label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11, color: AppTheme.textLight, fontWeight: FontWeight.w600),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem(BuildContext context, String title, String subtitle, IconData icon, VoidCallback onTap, {bool isDestructive = false}) {
    return ListTile(
      onTap: onTap,
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: isDestructive ? AppTheme.sindoorRed.withOpacity(0.1) : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: isDestructive ? AppTheme.sindoorRed : AppTheme.primary, size: 20),
      ),
      title: Text(
        title,
        style: TextStyle(
          fontWeight: FontWeight.w700,
          fontSize: 14,
          color: isDestructive ? AppTheme.sindoorRed : AppTheme.textDark,
        ),
      ),
      subtitle: Text(
        subtitle,
        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
      ),
      trailing: const Icon(CupertinoIcons.chevron_right, size: 14, color: AppTheme.textLight),
    );
  }
}
