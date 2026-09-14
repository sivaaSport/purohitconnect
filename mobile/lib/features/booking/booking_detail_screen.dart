import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';
import 'booking_chat_screen.dart';
import 'payment_screen.dart';
import 'review_screen.dart';

class BookingDetailScreen extends StatefulWidget {
  final String bookingId;
  const BookingDetailScreen({super.key, required this.bookingId});

  @override
  State<BookingDetailScreen> createState() => _BookingDetailScreenState();
}

class _BookingDetailScreenState extends State<BookingDetailScreen> {
  BookingModel? _booking;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ApiService().fetchBooking(widget.bookingId);
      if (!mounted) return;
      setState(() {
        _booking = BookingModel.fromJson(Map<String, dynamic>.from(data['booking'] as Map));
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _cancel() async {
    final reason = await _ask('Cancel ceremony', 'Why are you cancelling?');
    if (reason == null || reason.isEmpty) return;
    try {
      await ApiService().cancelBooking(widget.bookingId, reason);
      await _load();
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  Future<void> _reschedule() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 3)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 180)),
    );
    if (date == null || !mounted) return;
    final reason = await _ask('Reschedule', 'Reason for the new date');
    try {
      await ApiService().requestReschedule(
        widget.bookingId,
        '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}',
        '09:00',
        reason ?? '',
      );
      await _load();
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  Future<void> _handleReschedule(String action) async {
    try {
      await ApiService().handleReschedule(widget.bookingId, action);
      await _load();
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  Future<String?> _ask(String title, String hint) async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: TextField(controller: controller, decoration: InputDecoration(hintText: hint)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, controller.text.trim()), child: const Text('Submit')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator(color: AppTheme.primary)));
    }
    if (_error != null || _booking == null) {
      return Scaffold(
        appBar: AppBar(leading: const AppBackButton(), automaticallyImplyLeading: false),
        body: ErrorBanner(message: _error ?? 'Not found', onRetry: _load),
      );
    }
    final b = _booking!;
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: Text(b.bookingId),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SurfaceCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(b.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18))),
                    StatusChip.lifecycle(b.lifecycleKey, b.lifecycleLabel),
                  ],
                ),
                const SizedBox(height: 8),
                Text(b.purohitName, style: const TextStyle(color: AppTheme.textMuted)),
                const SizedBox(height: 12),
                Text('${b.eventDate} · ${b.timeWindow.isNotEmpty ? b.timeWindow : b.eventTime}'),
                Text(b.address, style: const TextStyle(color: AppTheme.textMuted)),
                if (b.venueLabel.isNotEmpty) Text(b.venueLabel, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                const SizedBox(height: 12),
                Text('₹${b.totalAmount.toInt()}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 22, color: AppTheme.primary)),
                if (b.startCode.isNotEmpty || b.completeCode.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text(
                    b.started ? 'Share the done code with your purohit when the ritual finishes.' : 'Share the start code when the purohit arrives.',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.35),
                  ),
                  const SizedBox(height: 8),
                  if (!b.started && b.startCode.isNotEmpty)
                    Text('Start code  ${b.startCode}', style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 18)),
                  if (b.completeCode.isNotEmpty)
                    Text('Done code  ${b.completeCode}', style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 18)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (b.canPay)
            ElevatedButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => PaymentScreen(booking: b))).then((_) => _load()),
              child: const Text('Complete payment'),
            ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => BookingChatScreen(bookingId: b.bookingId, title: b.purohitName))),
            icon: const Icon(CupertinoIcons.chat_bubble_2),
            label: const Text('Chat with purohit'),
          ),
          if (b.canCancel) TextButton(onPressed: _reschedule, child: const Text('Request reschedule')),
          if (b.rescheduleStatus == 'pending')
            Row(
              children: [
                Expanded(child: OutlinedButton(onPressed: () => _handleReschedule('accept'), child: const Text('Accept new date'))),
                const SizedBox(width: 8),
                Expanded(child: TextButton(onPressed: () => _handleReschedule('reject'), child: const Text('Decline'))),
              ],
            ),
          if (b.canReview)
            ElevatedButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ReviewScreen(booking: b))).then((_) => _load()),
              child: const Text('Rate & review'),
            ),
          if (b.canCancel)
            TextButton(onPressed: _cancel, child: const Text('Cancel booking', style: TextStyle(color: AppTheme.sindoorRed))),
        ],
      ),
    );
  }
}
