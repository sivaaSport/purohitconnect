import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/ui_kit.dart';

class PurohitTravelScreen extends StatefulWidget {
  const PurohitTravelScreen({super.key});

  @override
  State<PurohitTravelScreen> createState() => _PurohitTravelScreenState();
}

class _PurohitTravelScreenState extends State<PurohitTravelScreen> {
  List<TravelRequestModel> _items = [];
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
      final rows = await ApiService().fetchPurohitTravelRequests();
      if (!mounted) return;
      setState(() {
        _items = rows;
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

  Future<void> _respond(TravelRequestModel item, String decision) async {
    var fee = 0.0;
    if (decision == 'accept') {
      final controller = TextEditingController(text: '0');
      final ok = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Accept visit'),
          content: TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Travel fee (₹), 0 if none'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Accept')),
          ],
        ),
      );
      if (ok != true) return;
      fee = double.tryParse(controller.text.trim()) ?? 0;
    }
    try {
      final res = await ApiService().respondPurohitTravel(item.id, decision: decision, travelFee: fee);
      if (mounted) {
        showAppSnack(context, res['message']?.toString() ?? 'Updated');
        _load();
      }
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(title: const Text('Travel requests')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          children: [
            const Text(
              'Devotees ask first when you do not already offer their place. They pay only after they book.',
              style: TextStyle(color: AppTheme.textMuted, height: 1.35),
            ),
            const SizedBox(height: 16),
            if (_error != null) ErrorBanner(message: _error!, onRetry: _load),
            if (_loading)
              const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator(color: AppTheme.primary)))
            else if (_items.isEmpty)
              const EmptyState(title: 'No visit requests', message: 'New travel requests from devotees will show here.')
            else
              ..._items.map(_card),
          ],
        ),
      ),
    );
  }

  Widget _card(TravelRequestModel item) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: SurfaceCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.requestId, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.textLight)),
            Text(item.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            Text(item.customerName.isEmpty ? 'Devotee' : item.customerName, style: const TextStyle(color: AppTheme.textMuted)),
            const SizedBox(height: 6),
            Text('${item.area}, ${item.city}', style: const TextStyle(fontSize: 13)),
            Text('${item.preferredDate} · ${item.preferredTime}', style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            if (item.message.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(item.message, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
            ],
            const SizedBox(height: 8),
            Text(item.statusLabel, style: const TextStyle(fontWeight: FontWeight.w800, color: AppTheme.sacredGold)),
            if (item.status == 'pending') ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _respond(item, 'decline'),
                      child: const Text('Decline'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => _respond(item, 'accept'),
                      child: const Text('Accept'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
