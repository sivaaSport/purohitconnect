import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';
import 'otp_screen.dart';
import 'signup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final phone = '+91${_phoneController.text.trim()}';
    final auth = context.read<AuthProvider>();
    final sent = await auth.sendOtp(phone, action: 'login');
    if (!mounted) return;
    if (sent) {
      Navigator.push(context, MaterialPageRoute(builder: (_) => OtpScreen(phone: phone)));
    } else {
      showAppSnack(context, auth.errorMessage ?? 'Could not send OTP', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        backgroundColor: AppTheme.surfaceCream,
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 450),
              child: Form(
                key: _formKey,
                child: Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(color: const Color(0x1A0F172A)),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0x140F172A),
                        blurRadius: 24,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      Container(
                        width: 64,
                        height: 64,
                        decoration: const BoxDecoration(color: Color(0x24FACC15), shape: BoxShape.circle),
                        child: const Icon(CupertinoIcons.phone_fill, color: Color(0xFFB45309), size: 28),
                      ),
                      const SizedBox(height: 16),
                      const Text('Welcome Back', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
                      const SizedBox(height: 6),
                      const Text('Enter your phone number to receive OTP', style: TextStyle(color: AppTheme.textMuted)),
                      const SizedBox(height: 24),
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Text('Phone Number', style: TextStyle(fontWeight: FontWeight.w700)),
                      ),
                      const SizedBox(height: 8),
                      TextFormField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        maxLength: 10,
                        decoration: const InputDecoration(
                          hintText: '9876543210',
                          counterText: '',
                          prefixText: '+91  ',
                        ),
                        validator: (val) => (val == null || val.length < 10) ? 'Enter 10-digit mobile number' : null,
                      ),
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Padding(
                          padding: EdgeInsets.only(top: 6),
                          child: Text('Enter 10-digit mobile number', style: TextStyle(fontSize: 12, color: AppTheme.textLight)),
                        ),
                      ),
                      const SizedBox(height: 22),
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: auth.isLoading ? null : _submit,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF59E0B),
                            foregroundColor: const Color(0xFF111827),
                          ),
                          child: auth.isLoading
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.2, color: Color(0xFF111827)))
                              : const Text('Send OTP', style: TextStyle(fontWeight: FontWeight.w800)),
                        ),
                      ),
                      const SizedBox(height: 22),
                      const Divider(color: Color(0xFFE2E8F0)),
                      const SizedBox(height: 16),
                      const Text('New to PurohitConnect?', style: TextStyle(color: AppTheme.textMuted)),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: () {
                          Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const SignupScreen()));
                        },
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFB45309),
                          side: const BorderSide(color: Color(0xFFF59E0B)),
                          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                        ),
                        child: const Text('Create Account', style: TextStyle(fontWeight: FontWeight.w800)),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
