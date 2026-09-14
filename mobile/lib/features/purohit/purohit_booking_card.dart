import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/ui_kit.dart';
import '../booking/booking_chat_screen.dart';

class PurohitBookingCard extends StatelessWidget {
  final BookingModel booking;
  final VoidCallback onChanged;

  const PurohitBookingCard({super.key, required this.booking, required this.onChanged});

  Future<String?> _askCode(BuildContext context, String title) async {
    final controller = TextEditingController();
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          maxLength: 4,
          decoration: const InputDecoration(labelText: '4-digit code from the devotee'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('Verify')),
        ],
      ),
    );
    return value;
  }

  Future<void> _act(BuildContext context, {required String status, bool needsCode = false, required String title}) async {
    var code = '';
    if (needsCode) {
      final entered = await _askCode(context, title);
      if (entered == null || entered.isEmpty) return;
      code = entered;
    }
    try {
      final res = await ApiService().updatePurohitBookingStatus(booking.bookingId, status: status, code: code);
      if (context.mounted) {
        showAppSnack(context, res['message']?.toString() ?? 'Updated');
        onChanged();
      }
    } catch (e) {
      if (context.mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(booking.bookingId, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.textLight)),
          const SizedBox(height: 2),
          Text(booking.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          Text(booking.customerName.isEmpty ? 'Devotee' : booking.customerName, style: const TextStyle(color: AppTheme.textMuted)),
          const SizedBox(height: 6),
          Text('${booking.eventDate} · ${booking.eventTime}', style: const TextStyle(fontSize: 13, color: AppTheme.textDark)),
          if (booking.address.isNotEmpty)
            Text(booking.address, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
          const SizedBox(height: 8),
          Text(
            booking.paymentStatus == 'success' ? 'Paid ₹${booking.totalAmount.toInt()}' : 'Payment ${booking.paymentStatus}',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: booking.paymentStatus == 'success' ? AppTheme.tulsiGreen : AppTheme.sacredGold,
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (booking.canConfirm)
                ElevatedButton(
                  onPressed: () => _act(context, status: 'confirmed', title: 'Confirm booking'),
                  child: const Text('Confirm'),
                ),
              if (booking.canStart)
                ElevatedButton(
                  onPressed: () => _act(context, status: 'confirmed', needsCode: true, title: 'Start ritual'),
                  child: const Text('Start ritual'),
                ),
              if (booking.canComplete)
                ElevatedButton(
                  onPressed: () => _act(context, status: 'completed', needsCode: true, title: 'Complete ritual'),
                  child: const Text('Mark done'),
                ),
              OutlinedButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => BookingChatScreen(bookingId: booking.bookingId, title: booking.customerName)),
                ),
                icon: const Icon(CupertinoIcons.chat_bubble, size: 16),
                label: const Text('Chat'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
