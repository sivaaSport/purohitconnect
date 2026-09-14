import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';
import '../../core/widgets/ui_kit.dart';

class PurohitCalendarScreen extends StatefulWidget {
  const PurohitCalendarScreen({super.key});

  @override
  State<PurohitCalendarScreen> createState() => _PurohitCalendarScreenState();
}

class _PurohitCalendarScreenState extends State<PurohitCalendarScreen> {
  late int _year;
  late int _month;
  String _day = '';
  int? _previewPackageId;
  PurohitCalendarState? _state;
  bool _loading = true;
  String? _error;
  String _rangeStart = '10:00';
  String _rangeEnd = '12:00';
  final _reason = TextEditingController();

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _year = now.year;
    _month = now.month;
    _load();
  }

  @override
  void dispose() {
    _reason.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final state = await ApiService().fetchPurohitCalendar(
        year: _year,
        month: _month,
        day: _day,
        previewPackageId: _previewPackageId,
      );
      if (!mounted) return;
      setState(() {
        _state = state;
        _year = state.year;
        _month = state.month;
        _previewPackageId = state.previewPackageId;
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

  Future<void> _act(Map<String, dynamic> body) async {
    try {
      final state = await ApiService().updatePurohitCalendar({
        ...body,
        'year': _year,
        'month': _month,
        if (_day.isNotEmpty) 'date': _day,
        if (_previewPackageId != null) 'preview_package': _previewPackageId,
      });
      if (!mounted) return;
      setState(() {
        _state = state;
        _year = state.year;
        _month = state.month;
        if (state.selectedDay.isNotEmpty) _day = state.selectedDay;
        _previewPackageId = state.previewPackageId;
      });
      if (state.message.isNotEmpty) showAppSnack(context, state.message);
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  Future<String?> _pickTime(String current) async {
    final parts = current.split(':');
    final initial = TimeOfDay(
      hour: int.tryParse(parts.isNotEmpty ? parts[0] : '10') ?? 10,
      minute: int.tryParse(parts.length > 1 ? parts[1] : '0') ?? 0,
    );
    final picked = await showTimePicker(context: context, initialTime: initial);
    if (picked == null) return null;
    return '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final state = _state;
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('Availability'),
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            const Text(
              'Block busy times, set working hours, and preview slots using your ritual durations.',
              style: TextStyle(color: AppTheme.textMuted, height: 1.35),
            ),
            const SizedBox(height: 16),
            if (_error != null) ErrorBanner(message: _error!, onRetry: _load),
            if (_loading && state == null)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
              )
            else if (state != null) ...[
              _hours(state),
              const SizedBox(height: 16),
              _monthCard(state),
              if (_day.isNotEmpty) ...[
                const SizedBox(height: 16),
                _dayPanel(state),
              ],
            ],
          ],
        ),
      ),
    );
  }

  Widget _hours(PurohitCalendarState state) {
    return SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Working hours', style: TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          const Text(
            'Accept 06:00–21:00, or extend so long rituals still fit.',
            style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _timeButton('Day start', state.workStart, (value) => _act({'action': 'set_work_hours', 'work_start': value, 'work_end': state.workEnd}))),
              const SizedBox(width: 10),
              Expanded(child: _timeButton('Day end', state.workEnd, (value) => _act({'action': 'set_work_hours', 'work_start': state.workStart, 'work_end': value}))),
            ],
          ),
        ],
      ),
    );
  }

  Widget _timeButton(String label, String value, ValueChanged<String> onPicked) {
    return InkWell(
      onTap: () async {
        final next = await _pickTime(value);
        if (next != null) onPicked(next);
      },
      child: InputDecorator(
        decoration: InputDecoration(labelText: label),
        child: Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
      ),
    );
  }

  Widget _monthCard(PurohitCalendarState state) {
    return SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(state.monthLabel, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18))),
              IconButton(
                onPressed: () {
                  final prev = DateTime(_year, _month - 1, 1);
                  setState(() {
                    _year = prev.year;
                    _month = prev.month;
                  });
                  _load();
                },
                icon: const Icon(CupertinoIcons.chevron_left, color: AppTheme.sacredRust),
              ),
              IconButton(
                onPressed: () {
                  final next = DateTime(_year, _month + 1, 1);
                  setState(() {
                    _year = next.year;
                    _month = next.month;
                  });
                  _load();
                },
                icon: const Icon(CupertinoIcons.chevron_right, color: AppTheme.sacredRust),
              ),
            ],
          ),
          if (state.packages.isNotEmpty) ...[
            const Text('PREVIEW SLOTS FOR', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)),
            const SizedBox(height: 6),
            DropdownButton<int>(
              isExpanded: true,
              value: _previewPackageId,
              items: state.packages
                  .map((p) => DropdownMenuItem(value: p.id, child: Text('${p.pujaName} · ${p.durationHours}h')))
                  .toList(),
              onChanged: (id) {
                setState(() => _previewPackageId = id);
                _load();
              },
            ),
            const SizedBox(height: 12),
          ],
          const Row(
            children: [
              Expanded(child: Center(child: Text('Mo', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
              Expanded(child: Center(child: Text('Tu', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
              Expanded(child: Center(child: Text('We', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
              Expanded(child: Center(child: Text('Th', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
              Expanded(child: Center(child: Text('Fr', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
              Expanded(child: Center(child: Text('Sa', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
              Expanded(child: Center(child: Text('Su', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)))),
            ],
          ),
          const SizedBox(height: 6),
          ...state.weeks.map((week) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(children: week.map(_cell).toList()),
              )),
          const SizedBox(height: 10),
          const Wrap(
            spacing: 12,
            children: [
              _Legend(color: Color(0x7310B981), label: 'Open'),
              _Legend(color: Color(0x8CF59E0B), label: 'Timed blocks'),
              _Legend(color: Color(0x73EF4444), label: 'Full day'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _cell(CalendarDayCell cell) {
    if (!cell.inMonth) {
      return const Expanded(child: SizedBox(height: 40));
    }
    Color bg = Colors.transparent;
    if (cell.status == 'full') bg = const Color(0x22EF4444);
    if (cell.status == 'partial') bg = const Color(0x33F59E0B);
    if (cell.status == 'free') bg = const Color(0x2210B981);
    final selected = cell.date == _day;
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.all(2),
        child: InkWell(
          onTap: cell.isPast
              ? null
              : () {
                  setState(() => _day = cell.date);
                  _load();
                },
          borderRadius: BorderRadius.circular(10),
          child: Container(
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: selected ? AppTheme.sacredGold.withValues(alpha: 0.28) : bg,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: cell.isToday ? AppTheme.sacredRust : (selected ? AppTheme.sacredGold : Colors.transparent),
              ),
            ),
            child: Text(
              '${cell.day}',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                color: cell.isPast ? AppTheme.textLight : AppTheme.textDark,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _dayPanel(PurohitCalendarState state) {
    return SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(state.selectedDay.isEmpty ? _day : state.selectedDay, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
          if (state.selectedBookings.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text('BOOKINGS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)),
            const SizedBox(height: 6),
            ...state.selectedBookings.map((row) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text(
                    '${row['time_label'] ?? ''} · ${row['puja_name'] ?? ''} · ${row['customer_name'] ?? ''}',
                    style: const TextStyle(fontSize: 13),
                  ),
                )),
          ],
          const SizedBox(height: 12),
          const Text('YOUR BLOCKS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)),
          const SizedBox(height: 6),
          if (state.selectedBlocks.isEmpty)
            const Text('No blocks — day is open for bookings.', style: TextStyle(color: AppTheme.textMuted, fontSize: 13))
          else
            ...state.selectedBlocks.map((block) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(block.label, style: const TextStyle(fontWeight: FontWeight.w800)),
                            if (block.reason.isNotEmpty)
                              Text(block.reason, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: () => _act({'action': 'delete_block', 'block_id': block.id}),
                        child: const Text('Remove', style: TextStyle(color: AppTheme.sindoorRed)),
                      ),
                    ],
                  ),
                )),
          const SizedBox(height: 12),
          const Text('QUICK BLOCK', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              AppSelectChip(label: 'All day', selected: false, onTap: () => _act({'action': 'preset', 'preset': 'fullday'})),
              AppSelectChip(label: 'Morning', selected: false, onTap: () => _act({'action': 'preset', 'preset': 'morning'})),
              AppSelectChip(label: 'Afternoon', selected: false, onTap: () => _act({'action': 'preset', 'preset': 'afternoon'})),
              AppSelectChip(label: 'Evening', selected: false, onTap: () => _act({'action': 'preset', 'preset': 'evening'})),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _timeButton('Start', _rangeStart, (v) => setState(() => _rangeStart = v))),
              const SizedBox(width: 10),
              Expanded(child: _timeButton('End', _rangeEnd, (v) => setState(() => _rangeEnd = v))),
            ],
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _reason,
            decoration: const InputDecoration(labelText: 'Reason (optional)'),
          ),
          const SizedBox(height: 10),
          ElevatedButton(
            onPressed: () => _act({
              'action': 'add_range',
              'start_time': _rangeStart,
              'end_time': _rangeEnd,
              'reason': _reason.text.trim(),
            }),
            child: const Text('Block custom time'),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: () => _act({'action': 'clear_day'}),
            child: const Text('Clear all blocks this day'),
          ),
          if (state.selectedSlots.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              'SLOT PREVIEW · ${state.calendarDuration}h windows',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: state.selectedSlots
                  .map((slot) => Chip(
                        label: Text(slot.label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
                        backgroundColor: slot.available ? const Color(0x2210B981) : const Color(0x22EF4444),
                        side: BorderSide.none,
                      ))
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  final Color color;
  final String label;
  const _Legend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted, fontWeight: FontWeight.w700)),
      ],
    );
  }
}
