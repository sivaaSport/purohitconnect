import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';

class ReviewScreen extends StatefulWidget {
  final BookingModel booking;
  const ReviewScreen({super.key, required this.booking});

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  int _rating = 5;
  final _title = TextEditingController();
  final _comment = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _title.dispose();
    _comment.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _saving = true);
    try {
      await ApiService().submitReview(
        widget.booking.bookingId,
        rating: _rating,
        title: _title.text.trim().isEmpty ? 'Blessed ceremony' : _title.text.trim(),
        comment: _comment.text.trim(),
      );
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Rate & review'),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(widget.booking.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          Text(widget.booking.purohitName, style: const TextStyle(color: AppTheme.textMuted)),
          const SizedBox(height: 16),
          Row(
            children: List.generate(5, (i) {
              final star = i + 1;
              return IconButton(
                onPressed: () => setState(() => _rating = star),
                icon: Icon(star <= _rating ? Icons.star_rounded : Icons.star_outline_rounded, color: AppTheme.sacredGold, size: 32),
              );
            }),
          ),
          TextField(controller: _title, decoration: const InputDecoration(labelText: 'Title')),
          const SizedBox(height: 12),
          TextField(controller: _comment, maxLines: 4, decoration: const InputDecoration(labelText: 'How was the vidhi?')),
          const SizedBox(height: 20),
          ElevatedButton(onPressed: _saving ? null : _submit, child: Text(_saving ? 'Saving…' : 'Submit review')),
        ],
      ),
    );
  }
}
