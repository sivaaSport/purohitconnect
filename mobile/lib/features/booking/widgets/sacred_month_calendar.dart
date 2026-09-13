import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/models/models.dart';
import '../../../core/theme/app_theme.dart';

class SacredMonthCalendar extends StatelessWidget {
  final DateTime visibleMonth;
  final DateTime? selectedDay;
  final List<BookingModel> bookings;
  final ValueChanged<DateTime> onMonthChanged;
  final ValueChanged<DateTime?> onDaySelected;

  const SacredMonthCalendar({
    super.key,
    required this.visibleMonth,
    required this.bookings,
    required this.onMonthChanged,
    required this.onDaySelected,
    this.selectedDay,
  });

  static DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);

  static DateTime? parseBookingDate(String raw) {
    final parsed = DateTime.tryParse(raw.split('T').first.trim());
    if (parsed == null) return null;
    return _dateOnly(parsed);
  }

  Map<DateTime, List<BookingModel>> get _byDate {
    final map = <DateTime, List<BookingModel>>{};
    for (final booking in bookings) {
      if (booking.status == 'cancelled') continue;
      final date = parseBookingDate(booking.eventDate);
      if (date == null) continue;
      map.putIfAbsent(date, () => []).add(booking);
    }
    return map;
  }

  List<DateTime?> get _cells {
    final first = DateTime(visibleMonth.year, visibleMonth.month, 1);
    final daysInMonth = DateTime(visibleMonth.year, visibleMonth.month + 1, 0).day;
    final leading = first.weekday - 1;
    return [
      ...List<DateTime?>.filled(leading, null),
      ...List<DateTime>.generate(daysInMonth, (index) => DateTime(visibleMonth.year, visibleMonth.month, index + 1)),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final today = _dateOnly(DateTime.now());
    final booked = _byDate;
    final cells = _cells;
    final label = DateFormat('MMMM yyyy').format(visibleMonth);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
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
                      'YOUR TIME',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.8,
                        color: AppTheme.textLight,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Your month',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.textDark),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Gold days are booked rituals.',
                      style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              Row(
                children: [
                  _NavButton(
                    icon: CupertinoIcons.chevron_left,
                    onTap: () => onMonthChanged(DateTime(visibleMonth.year, visibleMonth.month - 1)),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Text(
                      label,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppTheme.textDark),
                    ),
                  ),
                  _NavButton(
                    icon: CupertinoIcons.chevron_right,
                    onTap: () => onMonthChanged(DateTime(visibleMonth.year, visibleMonth.month + 1)),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Row(
            children: [
              _Dow('Mo'),
              _Dow('Tu'),
              _Dow('We'),
              _Dow('Th'),
              _Dow('Fr'),
              _Dow('Sa'),
              _Dow('Su'),
            ],
          ),
          const SizedBox(height: 6),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: cells.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              mainAxisSpacing: 4,
              crossAxisSpacing: 4,
              childAspectRatio: 0.92,
            ),
            itemBuilder: (context, index) {
              final day = cells[index];
              if (day == null) return const SizedBox.shrink();
              final dayBookings = booked[day] ?? const <BookingModel>[];
              final hasBooking = dayBookings.isNotEmpty;
              final isToday = day == today;
              final isPast = day.isBefore(today);
              final isSelected = selectedDay != null && day == _dateOnly(selectedDay!);
              final timeLabel = hasBooking ? _shortTime(dayBookings.first.eventTime) : '';

              return GestureDetector(
                onTap: () => onDaySelected(isSelected ? null : day),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 160),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? const Color(0xFFB45309)
                        : hasBooking
                            ? const Color(0x24F59E0B)
                            : Colors.transparent,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: isSelected
                          ? const Color(0xFF7C2D12)
                          : hasBooking
                              ? const Color(0x66F59E0B)
                              : isToday
                                  ? const Color(0xB3F59E0B)
                                  : Colors.transparent,
                    ),
                    boxShadow: isSelected
                        ? [
                            BoxShadow(
                              color: const Color(0x61B45309),
                              blurRadius: 0,
                              spreadRadius: 3,
                            ),
                          ]
                        : isToday && !hasBooking
                            ? [
                                const BoxShadow(
                                  color: Color(0x40F59E0B),
                                  blurRadius: 0,
                                  spreadRadius: 1,
                                ),
                              ]
                            : null,
                  ),
                  transform: isSelected ? (Matrix4.identity()..scale(1.04)) : Matrix4.identity(),
                  transformAlignment: Alignment.center,
                  child: Opacity(
                    opacity: !hasBooking && isPast && !isSelected && !isToday ? 0.38 : 1,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '${day.day}',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            color: isSelected ? const Color(0xFFFFFBEB) : AppTheme.textDark,
                          ),
                        ),
                        if (hasBooking)
                          Text(
                            timeLabel,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 8,
                              fontWeight: FontWeight.w700,
                              color: isSelected ? const Color(0xFFFFFBEB) : const Color(0xFFB45309),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 12),
          const Row(
            children: [
              _LegendSwatch(color: Color(0x24F59E0B), border: Color(0x66F59E0B)),
              SizedBox(width: 6),
              Text('Booked ritual', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textMuted)),
              SizedBox(width: 14),
              _LegendSwatch(color: Colors.transparent, border: Color(0xB3F59E0B)),
              SizedBox(width: 6),
              Text('Today', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textMuted)),
            ],
          ),
        ],
      ),
    );
  }

  static String _shortTime(String raw) {
    final value = raw.trim();
    if (value.isEmpty || value.toLowerCase().contains('tbd')) return 'Puja';
    return value.replaceFirst(RegExp(r'\s+'), ' ');
  }
}

class _Dow extends StatelessWidget {
  final String label;
  const _Dow(this.label);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Text(
        label,
        textAlign: TextAlign.center,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textLight),
      ),
    );
  }
}

class _NavButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _NavButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Icon(icon, size: 14, color: AppTheme.textDark),
      ),
    );
  }
}

class _LegendSwatch extends StatelessWidget {
  final Color color;
  final Color border;
  const _LegendSwatch({required this.color, required this.border});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 12,
      height: 12,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: border),
      ),
    );
  }
}
