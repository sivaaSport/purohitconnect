import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../../core/models/models.dart';
import '../../../core/theme/app_theme.dart';

class TravelRequestsSection extends StatelessWidget {
  final List<TravelRequestModel> requests;
  final ValueChanged<TravelRequestModel>? onBook;

  const TravelRequestsSection({
    super.key,
    required this.requests,
    this.onBook,
  });

  int get _waitingCount => requests.where((item) => item.status == 'pending').length;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'EXCEPTIONS',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                      color: AppTheme.textLight,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Travel requests',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.textDark,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'If a purohit does not already offer your place, you ask first. Book and pay only after they accept.',
                    style: TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.35),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Text(
                '$_waitingCount waiting',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        if (requests.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFF1F5F9)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'No travel requests',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppTheme.textDark),
                ),
                SizedBox(height: 4),
                Text(
                  'When you ask a purohit to visit a place they do not already offer, it will show here.',
                  style: TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.4),
                ),
              ],
            ),
          )
        else
          ...requests.map((item) => _TravelRequestCard(item: item, onBook: onBook)),
      ],
    );
  }
}

class _TravelRequestCard extends StatelessWidget {
  final TravelRequestModel item;
  final ValueChanged<TravelRequestModel>? onBook;

  const _TravelRequestCard({required this.item, this.onBook});

  Color get _statusColor {
    switch (item.status) {
      case 'accepted':
        return AppTheme.tulsiGreen;
      case 'declined':
        return AppTheme.sindoorRed;
      case 'expired':
        return AppTheme.textLight;
      default:
        return AppTheme.sacredGold;
    }
  }

  String get _place {
    final parts = [item.area, item.city].where((part) => part.trim().isNotEmpty);
    return parts.join(', ');
  }

  String get _when {
    final parts = [item.preferredDate, item.preferredTime].where((part) => part.trim().isNotEmpty);
    return parts.join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFF1F5F9)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.requestId,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.textLight),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item.pujaName,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppTheme.textDark),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  item.statusLabel,
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: _statusColor),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            item.purohitName,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textDark),
          ),
          if (_when.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(_when, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
          ],
          if (_place.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(_place, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
          ],
          if (item.travelFee > 0) ...[
            const SizedBox(height: 2),
            Text(
              'Travel fee ₹${item.travelFee.toInt()}',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
            ),
          ],
          if (item.status == 'pending') ...[
            const SizedBox(height: 8),
            Text(
              'Waiting for ${item.purohitName} to accept or decline. You have not paid yet.',
              style: const TextStyle(fontSize: 12, color: AppTheme.sacredGold, height: 1.35),
            ),
          ],
          if (item.status == 'accepted') ...[
            const SizedBox(height: 8),
            Text(
              item.travelFee > 0
                  ? 'They accepted with a ₹${item.travelFee.toInt()} travel fee. Book within 48 hours. You have not paid yet.'
                  : 'They accepted. Book within 48 hours to keep this unlock. You have not paid yet.',
              style: const TextStyle(fontSize: 12, color: AppTheme.tulsiGreen, height: 1.35),
            ),
          ],
          if (item.canBook && onBook != null) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => onBook!(item),
                icon: const Icon(CupertinoIcons.calendar, size: 16),
                label: const Text('Book this visit', style: TextStyle(fontWeight: FontWeight.w800)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
