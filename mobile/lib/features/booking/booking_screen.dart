import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/models/models.dart';
import '../../core/state/booking_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';
import '../../core/widgets/devotee_avatar.dart';
import '../../core/widgets/ui_kit.dart';
import 'payment_screen.dart';

class BookingScreen extends StatefulWidget {
  const BookingScreen({super.key});

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  final _addressController = TextEditingController();
  final _notesController = TextEditingController();
  String? _error;

  @override
  void initState() {
    super.initState();
    final booking = context.read<BookingProvider>();
    _addressController.text = booking.address;
    _notesController.text = booking.specialRequests;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      try {
        await booking.loadCities();
        await booking.loadSlots();
      } catch (e) {
        if (mounted) setState(() => _error = e.toString());
      }
    });
  }

  @override
  void dispose() {
    _addressController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final booking = context.read<BookingProvider>();
    final picked = await showDatePicker(
      context: context,
      initialDate: booking.selectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 180)),
    );
    if (picked != null) {
      booking.setDate(picked);
      booking.setTime('');
      try {
        await booking.loadSlots();
      } catch (e) {
        if (mounted) setState(() => _error = e.toString());
      }
    }
  }

  void _syncFields(BookingProvider booking) {
    booking.setAddress(_addressController.text.trim());
    booking.setSpecialRequests(_notesController.text.trim());
  }

  Future<void> _submit() async {
    final booking = context.read<BookingProvider>();
    _syncFields(booking);
    if (booking.coverageStatus.mode == CoverageMode.ask) {
      await _sendTravelRequest();
      return;
    }
    final res = await booking.confirmBooking();
    if (!mounted) return;
    if (res['code'] == 'travel_request_required') {
      showAppSnack(context, res['error']?.toString() ?? 'Request a visit first.', error: true);
      return;
    }
    if (res['success'] == true && res['booking'] != null) {
      final created = BookingModel.fromJson(Map<String, dynamic>.from(res['booking'] as Map));
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => PaymentScreen(booking: created)),
      );
    } else {
      showAppSnack(context, res['error']?.toString() ?? 'Could not create booking', error: true);
    }
  }

  Future<void> _sendTravelRequest() async {
    final booking = context.read<BookingProvider>();
    _syncFields(booking);
    final res = await booking.sendTravelRequest();
    if (!mounted) return;
    if (res['success'] == true) {
      final messenger = ScaffoldMessenger.of(context);
      Navigator.of(context).popUntil((route) => route.isFirst);
      messenger.showSnackBar(SnackBar(
        content: Text(res['message']?.toString() ?? 'Visit request sent. You pay only if they accept and you book.'),
      ));
    } else {
      showAppSnack(context, res['error']?.toString() ?? 'Could not send visit request', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final booking = context.watch<BookingProvider>();
    final p = booking.selectedPurohit;
    final pkg = booking.selectedPackage;
    if (p == null || pkg == null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Schedule ceremony'),
          leading: const AppBackButton(),
          automaticallyImplyLeading: false,
        ),
        body: const EmptyState(title: 'No package selected', message: 'Open a purohit profile and choose a puja first.'),
      );
    }

    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Schedule ceremony'),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 120),
        children: [
          SurfaceCard(
            child: Row(
              children: [
                DevoteeAvatar(
                  size: 48,
                  name: p.name,
                  imageUrl: p.avatarUrl,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(pkg.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                      Text(p.name, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                    ],
                  ),
                ),
                Text('₹${booking.baseAmount.toInt()}', style: const TextStyle(fontWeight: FontWeight.w900, color: AppTheme.primary, fontSize: 16)),
              ],
            ),
          ),
          if (_error != null) ...[const SizedBox(height: 12), ErrorBanner(message: _error!, onRetry: () => booking.loadSlots())],
          const SizedBox(height: 20),
          const Text('Auspicious date', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 10),
          SurfaceCard(
            onTap: _pickDate,
            child: Row(
              children: [
                const Icon(CupertinoIcons.calendar, color: AppTheme.primary),
                const SizedBox(width: 10),
                Text(DateFormat('EEE, d MMM yyyy').format(booking.selectedDate), style: const TextStyle(fontWeight: FontWeight.w700)),
                const Spacer(),
                const Icon(CupertinoIcons.chevron_right, size: 16, color: AppTheme.textLight),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const Text('Open time slots', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 10),
          if (booking.slots.isEmpty)
            const Text('No slots loaded yet. Pick a date.', style: TextStyle(color: AppTheme.textMuted))
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: booking.slots.map((slot) {
                final selected = booking.selectedTime == slot.start;
                return AppSelectChip(
                  label: slot.label,
                  selected: selected,
                  onTap: slot.available ? () => booking.setTime(slot.start) : null,
                );
              }).toList(),
            ),
          const SizedBox(height: 20),
          const Text('Venue', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 10),
          if (pkg.venues.isNotEmpty)
            Wrap(
              spacing: 8,
              children: pkg.venues.map((v) {
                return AppSelectChip(
                  label: v.label,
                  selected: booking.venueType == v.code,
                  onTap: () => booking.setVenueType(v.code),
                );
              }).toList(),
            )
          else
            const Text('Home ceremony', style: TextStyle(color: AppTheme.textMuted)),
          if ((booking.selectedPurohit?.coverage?.places ?? []).isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('Places they already offer', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: booking.selectedPurohit!.coverage!.places.map((place) {
                final selected = booking.city?.id == place.cityId &&
                    (place.areaId == null || booking.area?.id == place.areaId);
                return AppSelectChip(
                  label: place.label.isNotEmpty ? place.label : '${place.cityId}',
                  selected: selected,
                  onTap: () => booking.selectOfferedPlace(place),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 16),
          DropdownButtonFormField<CityModel>(
            value: booking.city,
            decoration: const InputDecoration(labelText: 'City'),
            items: booking.cities.map((c) => DropdownMenuItem(value: c, child: Text(c.name))).toList(),
            onChanged: booking.setCity,
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<AreaModel>(
            value: booking.area,
            decoration: const InputDecoration(labelText: 'Area'),
            items: (booking.city?.areas ?? []).map((a) => DropdownMenuItem(value: a, child: Text(a.name))).toList(),
            onChanged: booking.setArea,
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _addressController,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Full address / temple name'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _notesController,
            maxLines: 2,
            decoration: InputDecoration(
              labelText: booking.coverageStatus.mode == CoverageMode.ask
                  ? 'Message to the purohit (optional)'
                  : 'Sankalpam / special requests',
            ),
          ),
          if (booking.coverageStatus.title.isNotEmpty) ...[
            const SizedBox(height: 16),
            SurfaceCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    booking.coverageStatus.title,
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 15,
                      color: booking.coverageStatus.mode == CoverageMode.covered
                          ? AppTheme.tulsiGreen
                          : booking.coverageStatus.mode == CoverageMode.closed
                              ? AppTheme.sindoorRed
                              : AppTheme.sacredGold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    booking.coverageStatus.body,
                    style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.35),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          SwitchListTile.adaptive(
            contentPadding: EdgeInsets.zero,
            title: const Text('Include samagri kit', style: TextStyle(fontWeight: FontWeight.w700)),
            subtitle: Text(pkg.samagriPrice > 0 ? '₹${pkg.samagriPrice.toInt()} extra' : 'Included by purohit'),
            value: booking.needsSamagri,
            activeColor: AppTheme.primary,
            onChanged: booking.toggleSamagri,
          ),
          SurfaceCard(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Estimated total', style: TextStyle(fontWeight: FontWeight.w700)),
                Text('₹${booking.totalAmount.toInt()}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 20, color: AppTheme.primary)),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
          child: ElevatedButton(
            onPressed: booking.isLoading || booking.coverageStatus.mode == CoverageMode.closed ? null : _submit,
            child: booking.isLoading
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.4))
                : Text(booking.coverageStatus.mode == CoverageMode.ask ? 'Send travel request' : 'Create booking & pay'),
          ),
        ),
      ),
    );
  }
}
