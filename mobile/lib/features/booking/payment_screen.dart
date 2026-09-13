import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/services/payment_helper.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';
import 'booking_success_screen.dart';

class PaymentScreen extends StatefulWidget {
  final BookingModel booking;
  const PaymentScreen({super.key, required this.booking});

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  late BookingModel _booking;
  PaymentOptions _options = PaymentOptions();
  bool _loading = false;
  String _method = 'wallet';

  @override
  void initState() {
    super.initState();
    _booking = widget.booking;
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ApiService().fetchBooking(_booking.bookingId);
      if (!mounted) return;
      setState(() {
        _booking = BookingModel.fromJson(Map<String, dynamic>.from(data['booking'] as Map));
        _options = PaymentOptions.fromJson(data['payment_options'] as Map<String, dynamic>?);
        if (!_options.walletAvailable) _method = _options.mixedAvailable ? 'mixed' : 'razorpay';
      });
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  Future<void> _pay() async {
    setState(() => _loading = true);
    try {
      final res = await ApiService().payBooking(_booking.bookingId, _method);
      if (res['paid'] == true || res['already_paid'] == true) {
        _goSuccess(BookingModel.fromJson(Map<String, dynamic>.from(res['booking'] as Map)));
        return;
      }
      final raw = res['razorpay'];
      if (raw is Map) {
        final order = RazorpayOrder.fromJson(Map<String, dynamic>.from(raw));
        final verified = await PaymentHelper.settleBooking(bookingId: _booking.bookingId, order: order);
        _goSuccess(BookingModel.fromJson(Map<String, dynamic>.from(verified['booking'] as Map)));
        return;
      }
      throw Exception(res['error'] ?? 'Payment could not start');
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _goSuccess(BookingModel booking) {
    context.read<AuthProvider>().refreshUser();
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => BookingSuccessScreen(booking: booking)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Pay for ceremony'),
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
                Text(_booking.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                const SizedBox(height: 4),
                Text(_booking.purohitName, style: const TextStyle(color: AppTheme.textMuted)),
                const SizedBox(height: 12),
                Text('₹${_booking.totalAmount.toInt()}', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: AppTheme.primary)),
                Text('${_booking.eventDate} · ${_booking.eventTime}', style: const TextStyle(color: AppTheme.textMuted)),
              ],
            ),
          ),
          const SizedBox(height: 18),
          _methodTile('wallet', 'Pay from wallet', 'Balance ₹${_options.walletBalance.toInt()}', enabled: _options.walletAvailable),
          _methodTile('mixed', 'Wallet + Razorpay', _options.mixedAvailable ? '₹${_options.mixedWallet.toInt()} wallet + ₹${_options.mixedRazorpay.toInt()} card' : 'Not needed', enabled: _options.mixedAvailable),
          _methodTile('razorpay', 'Razorpay / UPI / card', 'Secure checkout (mock in local dev)', enabled: true),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _loading ? null : _pay,
            child: _loading
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.4))
                : Text('Pay ₹${_booking.totalAmount.toInt()}'),
          ),
        ],
      ),
    );
  }

  Widget _methodTile(String id, String title, String subtitle, {required bool enabled}) {
    return RadioListTile<String>(
      value: id,
      groupValue: _method,
      onChanged: enabled ? (v) => setState(() => _method = v!) : null,
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
      activeColor: AppTheme.primary,
    );
  }
}
