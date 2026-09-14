import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';
import '../../core/widgets/ui_kit.dart';

class PurohitPackagesScreen extends StatefulWidget {
  const PurohitPackagesScreen({super.key});

  @override
  State<PurohitPackagesScreen> createState() => _PurohitPackagesScreenState();
}

class _PurohitPackagesScreenState extends State<PurohitPackagesScreen> {
  List<PurohitPackageModel> _packages = [];
  List<PujaModel> _available = [];
  List<VenueOption> _venues = [];
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
      final data = await ApiService().fetchPurohitPackages();
      if (!mounted) return;
      setState(() {
        _packages = (data['packages'] as List? ?? [])
            .map((item) => PurohitPackageModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _available = (data['available_pujas'] as List? ?? [])
            .map((item) => PujaModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _venues = (data['venue_choices'] as List? ?? [])
            .map((item) => VenueOption.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
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

  Future<void> _openForm({PurohitPackageModel? package}) async {
    final changed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => PurohitPackageFormScreen(
          package: package,
          availablePujas: _available,
          venueChoices: _venues,
        ),
      ),
    );
    if (changed == true) _load();
  }

  Future<void> _remove(PurohitPackageModel package) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove offering'),
        content: Text('Remove ${package.pujaName} from your offerings?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Keep')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Remove')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      final res = await ApiService().savePurohitPackage({'action': 'delete', 'package_id': package.id});
      if (!mounted) return;
      showAppSnack(context, res['message']?.toString() ?? 'Removed');
      _load();
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('My pujas'),
      ),
      floatingActionButton: _available.isEmpty
          ? null
          : FloatingActionButton.extended(
              onPressed: () => _openForm(),
              backgroundColor: AppTheme.sacredGold,
              foregroundColor: Colors.white,
              icon: const Icon(CupertinoIcons.add),
              label: const Text('Add a ritual'),
            ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
          children: [
            const Text(
              'Each card is how devotees book you. Price, hours, venues, and samagri here are what they see before they pay.',
              style: TextStyle(color: AppTheme.textMuted, height: 1.35),
            ),
            const SizedBox(height: 16),
            if (_error != null) ErrorBanner(message: _error!, onRetry: _load),
            if (_loading)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
              )
            else if (_packages.isEmpty)
              EmptyState(
                title: 'No offerings yet',
                message: 'Add the rituals you actually perform. Your duration becomes the booking slot.',
                actionLabel: _available.isEmpty ? null : 'Add a ritual',
                onAction: _available.isEmpty ? null : () => _openForm(),
              )
            else
              ..._packages.map(_card),
          ],
        ),
      ),
    );
  }

  Widget _card(PurohitPackageModel package) {
    final venueLabel = package.venues.map((v) => v.label).where((v) => v.isNotEmpty).join(' · ');
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: SurfaceCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (package.categoryName.isNotEmpty)
              Text(
                package.categoryName,
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.sacredGold),
              ),
            Text(package.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
            const SizedBox(height: 4),
            Text(
              '₹${package.price.toInt()}',
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 20, color: AppTheme.sacredRust),
            ),
            const SizedBox(height: 8),
            Text(
              '${package.durationHours}h ritual · ${package.bufferMinutes}m rest after',
              style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
            ),
            if (venueLabel.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text('You perform at $venueLabel', style: const TextStyle(fontSize: 13, color: AppTheme.textDark)),
            ],
            if (package.venueNotes.isNotEmpty)
              Text(package.venueNotes, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            const SizedBox(height: 8),
            Text(
              package.includesSamagri
                  ? 'Samagri included${package.samagriPrice > 0 ? ' · +₹${package.samagriPrice.toInt()}' : ''}'
                  : 'Samagri not included',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.tulsiGreen),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _openForm(package: package),
                    child: const Text('Adjust offering'),
                  ),
                ),
                const SizedBox(width: 8),
                OutlinedButton(onPressed: () => _remove(package), child: const Text('Remove')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class PurohitPackageFormScreen extends StatefulWidget {
  final PurohitPackageModel? package;
  final List<PujaModel> availablePujas;
  final List<VenueOption> venueChoices;

  const PurohitPackageFormScreen({
    super.key,
    this.package,
    required this.availablePujas,
    required this.venueChoices,
  });

  @override
  State<PurohitPackageFormScreen> createState() => _PurohitPackageFormScreenState();
}

class _PurohitPackageFormScreenState extends State<PurohitPackageFormScreen> {
  final _price = TextEditingController();
  final _duration = TextEditingController();
  final _buffer = TextEditingController(text: '30');
  final _samagri = TextEditingController();
  final _notes = TextEditingController();
  PujaModel? _puja;
  bool _includesSamagri = false;
  final Set<String> _venues = {};
  bool _saving = false;

  bool get _editing => widget.package != null;

  @override
  void initState() {
    super.initState();
    final pkg = widget.package;
    if (pkg != null) {
      _price.text = pkg.price.toInt().toString();
      _duration.text = pkg.durationHours.toString();
      _buffer.text = pkg.bufferMinutes.toString();
      _samagri.text = pkg.samagriPrice > 0 ? pkg.samagriPrice.toInt().toString() : '';
      _notes.text = pkg.venueNotes;
      _includesSamagri = pkg.includesSamagri;
      _venues.addAll(pkg.venues.map((v) => v.code));
    } else if (widget.availablePujas.isNotEmpty) {
      _applyPuja(widget.availablePujas.first);
    }
  }

  void _applyPuja(PujaModel puja) {
    _puja = puja;
    _duration.text = puja.baseDurationHours.toString();
    _venues
      ..clear()
      ..addAll(puja.typicalVenues);
    if (_venues.isEmpty) _venues.add('home');
  }

  @override
  void dispose() {
    _price.dispose();
    _duration.dispose();
    _buffer.dispose();
    _samagri.dispose();
    _notes.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final price = double.tryParse(_price.text.trim()) ?? 0;
    if (price <= 0) {
      showAppSnack(context, 'Enter a valid price greater than zero.', error: true);
      return;
    }
    if (!_editing && _puja == null) {
      showAppSnack(context, 'Pick a ritual from the catalog.', error: true);
      return;
    }
    setState(() => _saving = true);
    try {
      final res = await ApiService().savePurohitPackage({
        'action': _editing ? 'update' : 'add',
        if (_editing) 'package_id': widget.package!.id,
        if (!_editing) 'puja_id': _puja!.id,
        'price': price,
        'duration_hours': double.tryParse(_duration.text.trim()) ?? 2,
        'buffer_minutes': int.tryParse(_buffer.text.trim()) ?? 30,
        'includes_samagri': _includesSamagri,
        'samagri_price': _samagri.text.trim(),
        'venues': _venues.toList(),
        'venue_notes': _notes.text.trim(),
      });
      if (!mounted) return;
      showAppSnack(context, res['message']?.toString() ?? 'Saved');
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        showAppSnack(context, e.toString(), error: true);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        leading: const AppBackButton(),
        title: Text(_editing ? 'Adjust offering' : 'Add a ritual'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          if (_editing)
            Text(widget.package!.pujaName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18))
          else ...[
            const Text('Ritual', style: TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            DropdownButton<int>(
              isExpanded: true,
              value: _puja?.id,
              items: widget.availablePujas
                  .map((p) => DropdownMenuItem(value: p.id, child: Text('${p.name} · ${p.baseDurationHours}h')))
                  .toList(),
              onChanged: (id) {
                PujaModel? next;
                for (final p in widget.availablePujas) {
                  if (p.id == id) next = p;
                }
                final chosen = next;
                if (chosen != null) setState(() => _applyPuja(chosen));
              },
            ),
          ],
          const SizedBox(height: 12),
          TextField(
            controller: _price,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Your price (₹)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _duration,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Ritual duration (hours)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _buffer,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Rest after ritual (minutes)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _samagri,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Samagri kit price (₹)'),
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Samagri is included in the base price'),
            value: _includesSamagri,
            activeThumbColor: AppTheme.sacredGold,
            onChanged: (value) => setState(() => _includesSamagri = value),
          ),
          const SizedBox(height: 8),
          const Text('You perform at', style: TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: widget.venueChoices.map((venue) {
              final selected = _venues.contains(venue.code);
              return AppSelectChip(
                label: venue.label,
                selected: selected,
                onTap: () => setState(() {
                  if (selected) {
                    _venues.remove(venue.code);
                  } else {
                    _venues.add(venue.code);
                  }
                }),
              );
            }).toList(),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _notes,
            maxLength: 240,
            decoration: const InputDecoration(labelText: 'Place note (optional)'),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _saving ? null : _save,
            child: Text(_saving ? 'Saving…' : 'Save changes'),
          ),
        ],
      ),
    );
  }
}
