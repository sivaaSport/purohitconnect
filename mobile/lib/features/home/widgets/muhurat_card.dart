import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_theme.dart';

class MuhuratCard extends StatefulWidget {
  const MuhuratCard({super.key});

  @override
  State<MuhuratCard> createState() => _MuhuratCardState();
}

class _MuhuratCardState extends State<MuhuratCard> {
  int _dayOffset = 0;

  DateTime get _currentDate => DateTime.now().add(Duration(days: _dayOffset));

  @override
  Widget build(BuildContext context) {
    final dateStr = DateFormat('EEEE, d MMMM yyyy').format(_currentDate);
    final isToday = _dayOffset == 0;

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
        boxShadow: [
          BoxShadow(
            color: const Color(0x14B45309),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          Positioned(
            left: -24,
            top: -40,
            child: Container(
              width: 160,
              height: 160,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [Color(0x38F59E0B), Color(0x00F59E0B)],
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: const Color(0x1AF59E0B),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0x40F59E0B)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(CupertinoIcons.sparkles, color: Color(0xFFB45309), size: 14),
                          const SizedBox(width: 6),
                          Text(
                            isToday ? "TODAY'S PANCHANG" : "TOMORROW'S PANCHANG",
                            style: const TextStyle(
                              color: Color(0xFFB45309),
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Row(
                      children: [
                        _DayChip(label: 'Today', selected: isToday, onTap: () => setState(() => _dayOffset = 0)),
                        const SizedBox(width: 6),
                        _DayChip(label: 'Tomorrow', selected: !isToday, onTap: () => setState(() => _dayOffset = 1)),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    const Icon(CupertinoIcons.calendar, color: Color(0xFFB45309), size: 16),
                    const SizedBox(width: 8),
                    Text(
                      dateStr,
                      style: const TextStyle(
                        color: AppTheme.textDark,
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  isToday
                      ? 'Abhijit Muhurat: 11:48 AM – 12:38 PM'
                      : 'Abhijit Muhurat: 11:46 AM – 12:36 PM',
                  style: const TextStyle(
                    color: Color(0xFFB45309),
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Shukla Paksha • Rohini Nakshatra • Amrit Kaal',
                  style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0x24B45309)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const _MuhuratItem(label: 'Sunrise', value: '06:08 AM', icon: CupertinoIcons.sun_max_fill),
                      _MuhuratItem(
                        label: 'Rahu Kaal',
                        value: isToday ? '04:30 – 06:00 PM' : '03:00 – 04:30 PM',
                        icon: CupertinoIcons.moon_fill,
                      ),
                      const _MuhuratItem(label: 'Brahma Muhurat', value: '04:35 AM', icon: CupertinoIcons.sparkles),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DayChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _DayChip({required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: AppTheme.selectChipDecoration(selected, radius: 8),
        child: Text(
          label,
          style: AppTheme.selectChipText(selected, fontSize: 11),
        ),
      ),
    );
  }
}

class _MuhuratItem extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _MuhuratItem({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFFF59E0B), size: 14),
        const SizedBox(width: 6),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: const TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.w500),
            ),
            Text(
              value,
              style: const TextStyle(color: AppTheme.textDark, fontSize: 11, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ],
    );
  }
}
