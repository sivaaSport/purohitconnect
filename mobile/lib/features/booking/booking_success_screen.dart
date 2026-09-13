import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import '../../core/models/models.dart';
import '../../core/theme/app_theme.dart';
import '../navigation/main_navigation_screen.dart';

class BookingSuccessScreen extends StatelessWidget {
  final BookingModel booking;

  const BookingSuccessScreen({super.key, required this.booking});

  @override
  Widget build(BuildContext context) {
    final bookingId = booking.bookingId;
    final purohitName = booking.purohitName;
    final pujaName = booking.pujaName;
    final eventDate = booking.eventDate;
    final eventTime = booking.eventTime;
    final address = booking.address;
    final totalAmount = booking.totalAmount;

    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 20),
              // Celebratory Glowing Mandala Badge
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: AppTheme.saffronGradient,
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primary.withOpacity(0.35),
                      blurRadius: 30,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: const Center(
                  child: Icon(CupertinoIcons.checkmark_alt, size: 54, color: Colors.white),
                ),
              ),
              const SizedBox(height: 24),

              const Text(
                '🙏 Shubham Bhavatu!',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.textDark,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your sacred ritual has been booked with auspicious blessings.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: AppTheme.textMuted, height: 1.4),
              ),
              const SizedBox(height: 24),

              // Booking ID Chip
              GestureDetector(
                onTap: () {
                  Clipboard.setData(ClipboardData(text: bookingId));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Booking ID copied to clipboard!')),
                  );
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: const Color(0x22FF6D00)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Booking Ref: $bookingId',
                        style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, color: AppTheme.primary),
                      ),
                      const SizedBox(width: 8),
                      const Icon(CupertinoIcons.doc_on_clipboard, size: 16, color: AppTheme.primary),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Booking Details Card
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 20,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    _buildDetailRow('Ceremony', pujaName, CupertinoIcons.flame_fill),
                    const Divider(height: 24, color: Color(0xFFF1F5F9)),
                    _buildDetailRow('Vedic Purohit', purohitName, CupertinoIcons.person_fill),
                    const Divider(height: 24, color: Color(0xFFF1F5F9)),
                    _buildDetailRow('Muhurat Date & Time', '$eventDate at $eventTime', CupertinoIcons.calendar),
                    const Divider(height: 24, color: Color(0xFFF1F5F9)),
                    _buildDetailRow('Location', address, CupertinoIcons.location_solid),
                    const Divider(height: 24, color: Color(0xFFF1F5F9)),
                    _buildDetailRow('Total Dakshina', '₹${totalAmount.toInt()}', CupertinoIcons.money_dollar_circle_fill, isHighlight: true),
                  ],
                ),
              ),
              const SizedBox(height: 30),

              // Share on WhatsApp button
              OutlinedButton.icon(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Ceremony invitation details shared with family!')),
                  );
                },
                icon: const Icon(CupertinoIcons.share, color: AppTheme.tulsiGreen, size: 18),
                label: const Text(
                  'Share Muhurat with Family',
                  style: TextStyle(color: AppTheme.tulsiGreen, fontWeight: FontWeight.w700),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppTheme.tulsiGreen, width: 1.5),
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
              ),
              const SizedBox(height: 14),

              // Home Button
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pushAndRemoveUntil(
                      context,
                      MaterialPageRoute(builder: (_) => const MainNavigationScreen()),
                      (route) => false,
                    );
                  },
                  child: const Text('Return to Home', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                ),
              ),
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, IconData icon, {bool isHighlight = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: isHighlight ? AppTheme.primary : AppTheme.sacredGold),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textLight, fontWeight: FontWeight.w600)),
              const SizedBox(height: 2),
              Text(
                value,
                style: TextStyle(
                  fontSize: isHighlight ? 16 : 14,
                  fontWeight: isHighlight ? FontWeight.w900 : FontWeight.w700,
                  color: isHighlight ? AppTheme.primary : AppTheme.textDark,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
