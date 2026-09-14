import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/ui_kit.dart';
import 'purohit_booking_card.dart';
import 'purohit_calendar_screen.dart';
import 'purohit_packages_screen.dart';

class PurohitHomeScreen extends StatefulWidget {
  const PurohitHomeScreen({super.key});

  @override
  State<PurohitHomeScreen> createState() => _PurohitHomeScreenState();
}

class _PurohitHomeScreenState extends State<PurohitHomeScreen> {
  Map<String, dynamic>? _stats;
  List<BookingModel> _needYou = [];
  List<TravelRequestModel> _travel = [];
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
      final data = await ApiService().fetchPurohitDashboard();
      if (!mounted) return;
      setState(() {
        _stats = Map<String, dynamic>.from(data['stats'] as Map? ?? {});
        _needYou = (data['need_you'] as List? ?? [])
            .map((item) => BookingModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _travel = (data['travel_requests'] as List? ?? [])
            .map((item) => TravelRequestModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .where((item) => item.status == 'pending')
            .toList();
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

  @override
  Widget build(BuildContext context) {
    final name = context.watch<AuthProvider>().user?.name ?? 'Purohit';
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(title: const Text('Purohit workspace')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          children: [
            Text('Namaste, $name', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 22)),
            const SizedBox(height: 4),
            const Text(
              'Incoming bookings and visit requests. Confirm only after the devotee has paid.',
              style: TextStyle(color: AppTheme.textMuted, height: 1.35),
            ),
            if (_error != null) ...[const SizedBox(height: 12), ErrorBanner(message: _error!, onRetry: _load)],
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: SurfaceCard(
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PurohitPackagesScreen())),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('My pujas', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                        SizedBox(height: 4),
                        Text('Price, hours, venues', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SurfaceCard(
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PurohitCalendarScreen())),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Calendar', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                        SizedBox(height: 4),
                        Text('Hours and blocked time', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _stat('Need you', '${_stats?['pending_requests'] ?? _needYou.length}'),
                const SizedBox(width: 10),
                _stat('Upcoming', '${_stats?['upcoming_bookings'] ?? 0}'),
                const SizedBox(width: 10),
                _stat('Travel', '${_stats?['pending_travel_count'] ?? _travel.length}'),
              ],
            ),
            const SizedBox(height: 24),
            const Text('Needs your action', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 10),
            if (_loading)
              const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator(color: AppTheme.primary)))
            else if (_needYou.isEmpty)
              const EmptyState(title: 'All clear', message: 'Paid bookings waiting for confirmation will show here.')
            else
              ..._needYou.map((b) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: PurohitBookingCard(booking: b, onChanged: _load),
                  )),
            if (_travel.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                '${_travel.length} travel request${_travel.length == 1 ? '' : 's'} waiting on the Travel tab.',
                style: const TextStyle(color: AppTheme.sacredGold, fontWeight: FontWeight.w700),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _stat(String label, String value) {
    return Expanded(
      child: SurfaceCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 22, color: AppTheme.sacredRust)),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }
}
