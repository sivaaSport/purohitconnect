import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/services/payment_helper.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  final _api = ApiService();
  double _balance = 0;
  List<WalletTransactionModel> _transactions = [];
  bool _loading = true;
  String? _error;

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
      final data = await _api.fetchWallet();
      final w = data['wallet'] as Map<String, dynamic>? ?? {};
      final raw = w['transactions'] as List? ?? [];
      if (!mounted) return;
      setState(() {
        _balance = (w['balance'] as num?)?.toDouble() ?? 0;
        _transactions = raw.map((t) => WalletTransactionModel.fromJson(Map<String, dynamic>.from(t as Map))).toList();
        _loading = false;
      });
      context.read<AuthProvider>().applyWalletBalance(_balance);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _topUp(double amount) async {
    try {
      final res = await _api.walletTopup(amount);
      final raw = res['razorpay'];
      if (raw is Map) {
        final order = RazorpayOrder.fromJson(Map<String, dynamic>.from(raw));
        await PaymentHelper.settleWallet(order: order, amount: amount);
      }
      await _load();
      if (!mounted) return;
      await context.read<AuthProvider>().refreshUser();
      if (!mounted) return;
      showAppSnack(context, '₹${amount.toInt()} added to wallet');
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Wallet'),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                gradient: AppTheme.creamHeroGradient,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppTheme.chipBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Available balance', style: TextStyle(color: AppTheme.sacredRust, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  Text('₹${_balance.toStringAsFixed(0)}', style: const TextStyle(color: AppTheme.textDark, fontSize: 36, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  const Text('Same ledger as the website wallet', style: TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                ],
              ),
            ),
            const SizedBox(height: 18),
            const Text('Quick top-up', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              children: [501.0, 1100.0, 2100.0, 5100.0].map((amt) {
                return ActionChip(
                  label: Text('₹${amt.toInt()}'),
                  onPressed: () => _topUp(amt),
                  backgroundColor: Colors.white,
                );
              }).toList(),
            ),
            const SizedBox(height: 22),
            const Text('Passbook', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 10),
            if (_loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator(color: AppTheme.primary))),
            if (_error != null) ErrorBanner(message: _error!, onRetry: _load),
            if (!_loading && _transactions.isEmpty && _error == null)
              const EmptyState(title: 'No transactions yet', message: 'Top-ups and booking payments will show here.', icon: CupertinoIcons.creditcard),
            ..._transactions.map((t) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: SurfaceCard(
                    child: Row(
                      children: [
                        Icon(t.type == 'credit' ? CupertinoIcons.arrow_down_left : CupertinoIcons.arrow_up_right, color: t.type == 'credit' ? AppTheme.tulsiGreen : AppTheme.sindoorRed),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(t.reason, style: const TextStyle(fontWeight: FontWeight.w700)),
                              Text(t.date, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                            ],
                          ),
                        ),
                        Text(
                          '${t.type == 'credit' ? '+' : '-'}₹${t.amount.toInt()}',
                          style: TextStyle(fontWeight: FontWeight.w800, color: t.type == 'credit' ? AppTheme.tulsiGreen : AppTheme.textDark),
                        ),
                      ],
                    ),
                  ),
                )),
          ],
        ),
      ),
    );
  }
}
