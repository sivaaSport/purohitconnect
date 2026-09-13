import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';
import '../navigation/main_navigation_screen.dart';

class OtpScreen extends StatefulWidget {
  final String phone;
  final String? displayName;
  const OtpScreen({super.key, required this.phone, this.displayName});

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final _controllers = List.generate(6, (_) => TextEditingController());
  final _nodes = List.generate(6, (_) => FocusNode());
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    for (final node in _nodes) {
      node.addListener(() => setState(() {}));
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final debug = context.read<AuthProvider>().debugOtp;
      if (debug != null && debug.length == 6) {
        _fillOtp(debug);
      } else {
        _nodes.first.requestFocus();
      }
    });
  }

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    for (final n in _nodes) {
      n.dispose();
    }
    super.dispose();
  }

  String get _otp => _controllers.map((c) => c.text).join();

  void _fillOtp(String value) {
    final digits = value.replaceAll(RegExp(r'\D'), '');
    for (var i = 0; i < 6; i++) {
      _controllers[i].text = i < digits.length ? digits[i] : '';
    }
    setState(() {});
    if (digits.length >= 6) {
      _nodes.last.requestFocus();
      _verify();
    } else if (digits.isNotEmpty) {
      _nodes[digits.length.clamp(0, 5)].requestFocus();
    }
  }

  Future<void> _verify() async {
    if (_submitting || _otp.length < 6) return;
    _submitting = true;
    final auth = context.read<AuthProvider>();
    final ok = await auth.verifyOtp(widget.phone, _otp, name: widget.displayName);
    _submitting = false;
    if (!mounted) return;
    if (ok) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const MainNavigationScreen()),
        (_) => false,
      );
    } else {
      showAppSnack(context, auth.errorMessage ?? 'Invalid OTP', error: true);
    }
  }

  void _onChanged(int index, String value) {
    final cleaned = value.replaceAll(RegExp(r'\D'), '');
    if (cleaned.length > 1) {
      _fillOtp(cleaned);
      return;
    }
    _controllers[index].text = cleaned;
    _controllers[index].selection = TextSelection.collapsed(offset: cleaned.length);
    setState(() {});
    if (cleaned.isNotEmpty && index < 5) {
      _nodes[index + 1].requestFocus();
    } else if (cleaned.isEmpty && index > 0) {
      _nodes[index - 1].requestFocus();
    }
    if (_otp.length == 6) _verify();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(leading: const AppBackButton(), automaticallyImplyLeading: false),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const SizedBox(height: 12),
              Container(
                width: 70,
                height: 70,
                decoration: BoxDecoration(color: AppTheme.primary.withValues(alpha: 0.12), shape: BoxShape.circle),
                child: const Icon(CupertinoIcons.chat_bubble_2_fill, color: AppTheme.primary, size: 32),
              ),
              const SizedBox(height: 18),
              const Text('Enter verification code', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Text('Sent to ${widget.phone}', style: const TextStyle(color: AppTheme.textMuted)),
              if (auth.debugOtp != null) ...[
                const SizedBox(height: 10),
                Text('Dev mock OTP: ${auth.debugOtp}', style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w700)),
              ],
              const SizedBox(height: 28),
              LayoutBuilder(
                builder: (context, constraints) {
                  final gap = 8.0;
                  final box = ((constraints.maxWidth - gap * 5) / 6).clamp(40.0, 56.0);
                  return Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(6, (i) {
                      final focused = _nodes[i].hasFocus;
                      final filled = _controllers[i].text.isNotEmpty;
                      return Padding(
                        padding: EdgeInsets.only(right: i == 5 ? 0 : gap),
                        child: SizedBox(
                          width: box,
                          height: box + 4,
                          child: TextField(
                            controller: _controllers[i],
                            focusNode: _nodes[i],
                            textAlign: TextAlign.center,
                            textAlignVertical: TextAlignVertical.center,
                            keyboardType: TextInputType.number,
                            maxLength: 6,
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w800,
                              height: 1.0,
                              color: AppTheme.textDark,
                            ),
                            cursorColor: AppTheme.primary,
                            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                            decoration: InputDecoration(
                              counterText: '',
                              isCollapsed: false,
                              isDense: true,
                              filled: true,
                              fillColor: Colors.white,
                              contentPadding: EdgeInsets.zero,
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(14),
                                borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(14),
                                borderSide: BorderSide(
                                  color: filled ? const Color(0xFFF59E0B) : const Color(0xFFE2E8F0),
                                ),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(14),
                                borderSide: BorderSide(
                                  color: focused ? AppTheme.primary : const Color(0xFFE2E8F0),
                                  width: 2,
                                ),
                              ),
                            ),
                            onChanged: (v) => _onChanged(i, v),
                          ),
                        ),
                      );
                    }),
                  );
                },
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: auth.isLoading || _otp.length < 6 ? null : _verify,
                  child: auth.isLoading
                      ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.4))
                      : const Text('Verify & continue'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
