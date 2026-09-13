import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class DevoteeHomeBanner extends StatelessWidget {
  final String name;
  final String lead;
  final VoidCallback onBookPuja;
  final VoidCallback onFindPurohit;

  const DevoteeHomeBanner({
    super.key,
    required this.name,
    required this.lead,
    required this.onBookPuja,
    required this.onFindPurohit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0x24B45309)),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFF7ED), Color(0xFFFFFFFF)],
          stops: [0.0, 0.55],
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          Positioned(
            left: -30,
            top: -50,
            child: Container(
              width: 180,
              height: 180,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [Color(0x38F59E0B), Color(0x00F59E0B)],
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'YOUR HOME',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.6,
                    color: Color(0xFFB45309),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Namaste, $name',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.textDark,
                    height: 1.15,
                    letterSpacing: -0.4,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  lead,
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.45,
                    color: AppTheme.textMuted,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 18),
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    ElevatedButton(
                      onPressed: onBookPuja,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF59E0B),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                      ),
                      child: const Text('Book a puja', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
                    ),
                    OutlinedButton(
                      onPressed: onFindPurohit,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFFF59E0B),
                        backgroundColor: Colors.white,
                        side: const BorderSide(color: Color(0xFFF59E0B)),
                        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                      ),
                      child: const Text('Find a purohit', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class DevoteeStatStrip extends StatelessWidget {
  final int upcoming;
  final int awaitingPayment;
  final int travelWaiting;
  final int completed;
  final ValueChanged<String>? onTapStat;

  const DevoteeStatStrip({
    super.key,
    required this.upcoming,
    required this.awaitingPayment,
    required this.travelWaiting,
    required this.completed,
    this.onTapStat,
  });

  @override
  Widget build(BuildContext context) {
    final items = [
      ('upcoming', upcoming, 'Upcoming'),
      ('payment', awaitingPayment, 'Awaiting payment'),
      ('travel', travelWaiting, 'Travel waiting'),
      ('completed', completed, 'Completed'),
    ];
    return Row(
      children: [
        for (var i = 0; i < items.length; i++) ...[
          if (i > 0) const SizedBox(width: 8),
          Expanded(
            child: _StatCard(
              value: items[i].$2,
              label: items[i].$3,
              onTap: onTapStat == null ? null : () => onTapStat!(items[i].$1),
            ),
          ),
        ],
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final int value;
  final String label;
  final VoidCallback? onTap;

  const _StatCard({required this.value, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFE2E8F0)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          children: [
            Text(
              '$value',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w900,
                color: AppTheme.textDark,
                height: 1.05,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 2,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: AppTheme.textMuted,
                height: 1.2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class DevoteeJumpRow extends StatelessWidget {
  final VoidCallback onTravel;
  final VoidCallback onBrowse;

  const DevoteeJumpRow({
    super.key,
    required this.onTravel,
    required this.onBrowse,
  });

  @override
  Widget build(BuildContext context) {
    final items = [
      ('Travel', onTravel),
      ('Browse', onBrowse),
    ];
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: items.map((item) {
        return GestureDetector(
          onTap: item.$2,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Text(
              item.$1,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textDark),
            ),
          ),
        );
      }).toList(),
    );
  }
}
