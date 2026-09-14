import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_select_chip.dart';
import '../../core/widgets/ui_kit.dart';
import 'purohit_booking_card.dart';

class PurohitBookingsScreen extends StatefulWidget {
  const PurohitBookingsScreen({super.key});

  @override
  State<PurohitBookingsScreen> createState() => _PurohitBookingsScreenState();
}

class _PurohitBookingsScreenState extends State<PurohitBookingsScreen> {
  String _bucket = 'need_you';
  List<BookingModel> _bookings = [];
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
      final rows = await ApiService().fetchPurohitBookings(bucket: _bucket);
      if (!mounted) return;
      setState(() {
        _bookings = rows;
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
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(title: const Text('Bookings')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          children: [
            Wrap(
              spacing: 8,
              children: [
                AppSelectChip(label: 'Need you', selected: _bucket == 'need_you', onTap: () => _setBucket('need_you')),
                AppSelectChip(label: 'Upcoming', selected: _bucket == 'upcoming', onTap: () => _setBucket('upcoming')),
                AppSelectChip(label: 'Past', selected: _bucket == 'past', onTap: () => _setBucket('past')),
              ],
            ),
            const SizedBox(height: 16),
            if (_error != null) ErrorBanner(message: _error!, onRetry: _load),
            if (_loading)
              const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator(color: AppTheme.primary)))
            else if (_bookings.isEmpty)
              const EmptyState(title: 'No bookings here', message: 'When devotees book and pay, they appear in Need you.')
            else
              ..._bookings.map((b) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: PurohitBookingCard(booking: b, onChanged: _load),
                  )),
          ],
        ),
      ),
    );
  }

  void _setBucket(String bucket) {
    setState(() => _bucket = bucket);
    _load();
  }
}
