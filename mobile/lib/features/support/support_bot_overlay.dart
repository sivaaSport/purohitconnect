import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/api_service.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';

class ModalStackObserver extends NavigatorObserver {
  final ValueNotifier<bool> hasPopup = ValueNotifier(false);
  int _popups = 0;

  void _bump(Route<dynamic> route, int delta) {
    if (route is! PopupRoute) return;
    _popups = (_popups + delta).clamp(0, 20);
    hasPopup.value = _popups > 0;
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) => _bump(route, 1);

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) => _bump(route, -1);

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) => _bump(route, -1);

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    if (oldRoute != null) _bump(oldRoute, -1);
    if (newRoute != null) _bump(newRoute, 1);
  }
}

final modalStackObserver = ModalStackObserver();

const _supportCategories = [
  ('general', 'General Inquiry'),
  ('booking', 'Booking Issue'),
  ('payment', 'Payment Issue'),
  ('technical', 'Technical Glitch'),
];

class SupportBotHost extends StatelessWidget {
  final Widget child;

  const SupportBotHost({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final authed = context.watch<AuthProvider>().isAuthenticated;
    return Stack(
      children: [
        child,
        if (authed)
          ValueListenableBuilder<bool>(
            valueListenable: modalStackObserver.hasPopup,
            builder: (context, hasPopup, _) {
              if (hasPopup) return const SizedBox.shrink();
              return const SupportBotOverlay();
            },
          ),
      ],
    );
  }
}

class SupportBotOverlay extends StatefulWidget {
  const SupportBotOverlay({super.key});

  @override
  State<SupportBotOverlay> createState() => _SupportBotOverlayState();
}

class _SupportBotOverlayState extends State<SupportBotOverlay> {
  final _subject = TextEditingController();
  final _description = TextEditingController();
  String _category = 'general';
  bool _open = false;
  bool _submitting = false;
  String? _ticketId;
  String? _error;

  @override
  void dispose() {
    _subject.dispose();
    _description.dispose();
    super.dispose();
  }

  void _toggle() {
    setState(() => _open = !_open);
  }

  void _resetForm() {
    _subject.clear();
    _description.clear();
    setState(() {
      _category = 'general';
      _ticketId = null;
      _error = null;
    });
  }

  Future<void> _submit() async {
    final subject = _subject.text.trim();
    final description = _description.text.trim();
    if (subject.isEmpty || description.isEmpty) {
      setState(() => _error = 'Please provide both a subject and description.');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final ticket = await ApiService().createTicket(
        subject: subject,
        description: description,
        category: _category,
      );
      if (!mounted) return;
      _subject.clear();
      _description.clear();
      setState(() => _ticketId = ticket.ticketId);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final width = size.width;
    final panelWidth = width < 400 ? width - 32 : 350.0;
    final panelMaxHeight = (size.height - 180).clamp(280.0, 480.0);
    return Align(
      alignment: Alignment.bottomRight,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 20, 96),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (_open) ...[
              _SupportWindow(
                width: panelWidth,
                maxHeight: panelMaxHeight,
                category: _category,
                subject: _subject,
                description: _description,
                submitting: _submitting,
                ticketId: _ticketId,
                error: _error,
                onCategory: (value) => setState(() => _category = value),
                onSubmit: _submitting ? null : _submit,
                onAnother: _resetForm,
              ),
              const SizedBox(height: 12),
            ],
            _SupportFab(open: _open, onTap: _toggle),
          ],
        ),
      ),
    );
  }
}

class _SupportFab extends StatelessWidget {
  final bool open;
  final VoidCallback onTap;

  const _SupportFab({required this.open, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFFF59E0B), Color(0xFFD97706)],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0x66B45309),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Icon(
            open ? CupertinoIcons.xmark : CupertinoIcons.chat_bubble_text_fill,
            color: const Color(0xFF111827),
            size: open ? 22 : 26,
          ),
        ),
      ),
    );
  }
}

class _SupportWindow extends StatelessWidget {
  final double width;
  final double maxHeight;
  final String category;
  final TextEditingController subject;
  final TextEditingController description;
  final bool submitting;
  final String? ticketId;
  final String? error;
  final ValueChanged<String> onCategory;
  final VoidCallback? onSubmit;
  final VoidCallback onAnother;

  const _SupportWindow({
    required this.width,
    required this.maxHeight,
    required this.category,
    required this.subject,
    required this.description,
    required this.submitting,
    required this.ticketId,
    required this.error,
    required this.onCategory,
    required this.onSubmit,
    required this.onAnother,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Container(
        width: width,
        constraints: BoxConstraints(maxHeight: maxHeight),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFFE2E8F0)),
          boxShadow: const [
            BoxShadow(color: Color(0x33000000), blurRadius: 28, offset: Offset(0, 12)),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFFF59E0B), Color(0xFFD97706)],
                ),
              ),
              child: const Row(
                children: [
                  CircleAvatar(
                    radius: 16,
                    backgroundColor: Color(0x33FFFFFF),
                    child: Icon(CupertinoIcons.flame_fill, color: Colors.white, size: 16),
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Support Center',
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 15),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'We typically reply in 10 mins',
                          style: TextStyle(color: Color(0xE6FFFFFF), fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Flexible(
              child: Container(
                width: double.infinity,
                color: const Color(0xFFF1F5F9),
                padding: const EdgeInsets.fromLTRB(14, 14, 14, 16),
                child: SingleChildScrollView(
                  child: ticketId == null ? _TicketForm(
                    category: category,
                    subject: subject,
                    description: description,
                    submitting: submitting,
                    error: error,
                    onCategory: onCategory,
                    onSubmit: onSubmit,
                  ) : _SuccessNote(ticketId: ticketId!, onAnother: onAnother),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TicketForm extends StatelessWidget {
  final String category;
  final TextEditingController subject;
  final TextEditingController description;
  final bool submitting;
  final String? error;
  final ValueChanged<String> onCategory;
  final VoidCallback? onSubmit;

  const _TicketForm({
    required this.category,
    required this.subject,
    required this.description,
    required this.submitting,
    required this.error,
    required this.onCategory,
    required this.onSubmit,
  });

  InputDecoration _field(String hint) {
    return InputDecoration(
      hintText: hint,
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE2E8F0))),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE2E8F0))),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppTheme.sacredGold, width: 1.5)),
      hintStyle: const TextStyle(fontSize: 13, color: AppTheme.textLight),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const CircleAvatar(
              radius: 14,
              backgroundColor: Colors.white,
              child: Icon(Icons.smart_toy_outlined, color: AppTheme.sacredGold, size: 16),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: const BoxDecoration(
                  color: Color(0x2694A3B8),
                  borderRadius: BorderRadius.only(
                    topRight: Radius.circular(12),
                    bottomLeft: Radius.circular(12),
                    bottomRight: Radius.circular(12),
                  ),
                ),
                child: const Text(
                  'Namaste! 🙏 How can we help you today? You can raise a service request below and our admins will get back to you.',
                  style: TextStyle(fontSize: 13, height: 1.4, color: AppTheme.textDark),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        DropdownButtonFormField<String>(
          value: category,
          decoration: _field('Category'),
          items: _supportCategories
              .map((item) => DropdownMenuItem(value: item.$1, child: Text(item.$2, style: const TextStyle(fontSize: 13))))
              .toList(),
          onChanged: submitting ? null : (value) {
            if (value != null) onCategory(value);
          },
        ),
        const SizedBox(height: 10),
        TextField(
          controller: subject,
          enabled: !submitting,
          decoration: _field('Subject / Summary'),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: description,
          enabled: !submitting,
          maxLines: 3,
          decoration: _field('Describe your issue...'),
        ),
        if (error != null) ...[
          const SizedBox(height: 8),
          Text(error!, style: const TextStyle(color: AppTheme.sindoorRed, fontSize: 12)),
        ],
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: ElevatedButton(
            onPressed: onSubmit,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.sacredGold,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: submitting
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Send Request', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),
          ),
        ),
      ],
    );
  }
}

class _SuccessNote extends StatelessWidget {
  final String ticketId;
  final VoidCallback onAnother;

  const _SuccessNote({required this.ticketId, required this.onAnother});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: AppTheme.tulsiGreen.withOpacity(0.15),
              child: const Icon(CupertinoIcons.checkmark_alt, color: AppTheme.tulsiGreen, size: 14),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.tulsiGreen.withOpacity(0.12),
                  borderRadius: const BorderRadius.only(
                    topRight: Radius.circular(12),
                    bottomLeft: Radius.circular(12),
                    bottomRight: Radius.circular(12),
                  ),
                ),
                child: Text(
                  'Thanks! Your request $ticketId has been created. Our team will get back to you shortly.',
                  style: const TextStyle(fontSize: 13, height: 1.4, color: AppTheme.textDark),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: onAnother,
            style: OutlinedButton.styleFrom(
              foregroundColor: AppTheme.sacredGold,
              side: const BorderSide(color: AppTheme.sacredGold),
            ),
            child: const Text('Raise Another Request', style: TextStyle(fontWeight: FontWeight.w800)),
          ),
        ),
      ],
    );
  }
}
