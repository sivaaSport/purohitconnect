import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/state/booking_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';
import '../booking/booking_detail_screen.dart';
import '../booking/widgets/sacred_month_calendar.dart';

class MyBookingsScreen extends StatefulWidget {
  const MyBookingsScreen({super.key});

  @override
  State<MyBookingsScreen> createState() => _MyBookingsScreenState();
}

class _MyBookingsScreenState extends State<MyBookingsScreen> {
  String _selectedTab = 'all';
  DateTime _visibleMonth = DateTime(DateTime.now().year, DateTime.now().month);
  DateTime? _selectedDay;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<BookingProvider>().loadMyBookings(status: 'all');
    });
  }

  List<BookingModel> _filteredBookings(List<BookingModel> all) {
    return all.where((booking) {
      if (_selectedTab == 'upcoming' && booking.status != 'confirmed' && booking.status != 'pending') {
        return false;
      }
      if (_selectedTab == 'completed' && booking.status != 'completed') {
        return false;
      }
      if (_selectedDay != null) {
        final date = SacredMonthCalendar.parseBookingDate(booking.eventDate);
        if (date == null || date != _selectedDay) return false;
      }
      return true;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final booking = context.watch<BookingProvider>();

    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('My Sacred Bookings'),
        leading: AppBackButton.maybe(context),
        automaticallyImplyLeading: false,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              children: [
                SacredMonthCalendar(
                  visibleMonth: _visibleMonth,
                  selectedDay: _selectedDay,
                  bookings: booking.myBookings,
                  onMonthChanged: (month) => setState(() {
                    _visibleMonth = DateTime(month.year, month.month);
                  }),
                  onDaySelected: (day) => setState(() => _selectedDay = day),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    _buildFilterPill('All Ceremonies', 'all'),
                    const SizedBox(width: 8),
                    _buildFilterPill('Upcoming', 'upcoming'),
                    const SizedBox(width: 8),
                    _buildFilterPill('Completed', 'completed'),
                  ],
                ),
                if (_selectedDay != null) ...[
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: ActionChip(
                      onPressed: () => setState(() => _selectedDay = null),
                      backgroundColor: const Color(0xFFFFF7ED),
                      side: const BorderSide(color: Color(0xFFFDBA74)),
                      label: Text(
                        'Showing ${_selectedDay!.day} · tap to clear',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFFB45309)),
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                if (booking.isLoading)
                  const Padding(
                    padding: EdgeInsets.only(top: 40),
                    child: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
                  )
                else
                  ..._bookingList(context, _filteredBookings(booking.myBookings)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _bookingList(BuildContext context, List<BookingModel> filtered) {
    if (filtered.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.only(top: 28),
          child: Column(
            children: [
              const Icon(CupertinoIcons.calendar_badge_plus, size: 46, color: AppTheme.textLight),
              const SizedBox(height: 12),
              Text(
                _selectedDay != null
                    ? 'No ceremony on this day'
                    : _selectedTab == 'upcoming'
                        ? 'No upcoming ceremonies scheduled'
                        : _selectedTab == 'completed'
                            ? 'No completed ceremonies yet'
                            : 'No ceremonies scheduled yet',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.textMuted),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              const Text(
                'Book a Vedic Purohit for your next auspicious puja',
                style: TextStyle(fontSize: 13, color: AppTheme.textLight),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ];
    }
    return filtered.map((b) => _buildBookingCard(context, b)).toList();
  }

  Widget _buildFilterPill(String title, String value) {
    final isSelected = _selectedTab == value;
    return Expanded(
      child: AppSelectChip(
        label: title,
        selected: isSelected,
        expand: true,
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        onTap: () => setState(() => _selectedTab = value),
      ),
    );
  }

  Widget _buildBookingCard(BuildContext context, BookingModel b) {
    Color statusColor;
    String statusText;

    if (b.status == 'confirmed') {
      statusColor = AppTheme.tulsiGreen;
      statusText = 'Confirmed';
    } else if (b.status == 'completed') {
      statusColor = const Color(0xFF3B82F6);
      statusText = 'Completed';
    } else {
      statusColor = AppTheme.sacredGold;
      statusText = 'Pending Approval';
    }

    return GestureDetector(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => BookingDetailScreen(bookingId: b.bookingId)),
      ).then((_) => context.read<BookingProvider>().loadMyBookings(status: 'all')),
      child: Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 15,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: ID and Status Pill
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                b.bookingId,
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, color: AppTheme.primary),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  statusText,
                  style: TextStyle(color: statusColor, fontWeight: FontWeight.w800, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Puja Name
          Text(
            b.pujaName,
            style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: AppTheme.textDark),
          ),
          const SizedBox(height: 4),
          Text(
            'With ${b.purohitName}',
            style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),

          // Date & Time
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(CupertinoIcons.calendar, size: 14, color: AppTheme.primary),
                const SizedBox(width: 6),
                Text(
                  b.eventDate,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                ),
                const SizedBox(width: 14),
                const Icon(CupertinoIcons.clock, size: 14, color: AppTheme.sacredGold),
                const SizedBox(width: 6),
                Text(
                  b.eventTime,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Address
          Row(
            children: [
              const Icon(CupertinoIcons.location_solid, size: 14, color: AppTheme.textLight),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  b.address,
                  style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Divider(height: 1, color: Color(0xFFF1F5F9)),
          const SizedBox(height: 12),

          // Bottom Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '₹${b.totalAmount.toInt()} Total',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: AppTheme.textDark),
              ),
              OutlinedButton.icon(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Contacting ${b.purohitName}...')),
                  );
                },
                icon: const Icon(CupertinoIcons.phone_fill, size: 13, color: AppTheme.primary),
                label: const Text('Contact Purohit', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.primary,
                  side: const BorderSide(color: AppTheme.primary),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
    );
  }
}
