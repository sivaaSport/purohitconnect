import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/state/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';
import 'login_screen.dart';
import 'otp_screen.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _phoneController = TextEditingController();
  final _nameController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  String _role = 'customer';

  @override
  void dispose() {
    _phoneController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (_role == 'purohit') {
      showAppSnack(context, 'Purohit workspace is on the website. Create a devotee account here to book rituals.');
    }
    final phone = '+91${_phoneController.text.trim()}';
    final auth = context.read<AuthProvider>();
    final sent = await auth.sendOtp(phone, action: 'signup');
    if (!mounted) return;
    if (sent) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => OtpScreen(phone: phone, displayName: _nameController.text.trim()),
        ),
      );
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
              constraints: const BoxConstraints(maxWidth: 500),
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
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Center(
                        child: Container(
                          width: 64,
                          height: 64,
                          decoration: const BoxDecoration(color: Color(0x24FACC15), shape: BoxShape.circle),
                          child: const Icon(CupertinoIcons.person_add_solid, color: Color(0xFFB45309), size: 28),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const Center(
                        child: Text('Create Your Account', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
                      ),
                      const SizedBox(height: 6),
                      const Center(
                        child: Text(
                          'Join the community of devotees and verified Purohits',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppTheme.textMuted),
                        ),
                      ),
                      const SizedBox(height: 22),
                      const Text('I am a:', style: TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(child: _roleCard('customer', 'Devotee', CupertinoIcons.person_fill)),
                          const SizedBox(width: 10),
                          Expanded(child: _roleCard('purohit', 'Purohit', CupertinoIcons.rosette)),
                        ],
                      ),
                      const SizedBox(height: 18),
                      const Text('Phone Number', style: TextStyle(fontWeight: FontWeight.w700)),
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
                      const Padding(
                        padding: EdgeInsets.only(top: 6),
                        child: Text('Enter 10-digit mobile number', style: TextStyle(fontSize: 12, color: AppTheme.textLight)),
                      ),
                      const SizedBox(height: 16),
                      const Text('Your name (Optional)', style: TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 8),
                      TextFormField(
                        controller: _nameController,
                        textCapitalization: TextCapitalization.words,
                        decoration: const InputDecoration(hintText: 'e.g. Ananda Bhakt'),
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
                      const SizedBox(height: 20),
                      const Divider(color: Color(0xFFE2E8F0)),
                      const SizedBox(height: 12),
                      Center(
                        child: Wrap(
                          alignment: WrapAlignment.center,
                          children: [
                            const Text('Already have an account? ', style: TextStyle(color: AppTheme.textMuted)),
                            GestureDetector(
                              onTap: () => Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen())),
                              child: const Text('Login here', style: TextStyle(color: Color(0xFFB45309), fontWeight: FontWeight.w800)),
                            ),
                          ],
                        ),
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

  Widget _roleCard(String value, String label, IconData icon) {
    final selected = _role == value;
    return GestureDetector(
      onTap: () => setState(() => _role = value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: selected ? const Color(0x1AF59E0B) : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: selected ? AppTheme.sacredGold : AppTheme.chipBorder, width: 2),
        ),
        child: Column(
          children: [
            Icon(icon, color: selected ? AppTheme.sacredRust : AppTheme.textDark),
            const SizedBox(height: 6),
            Text(label, style: TextStyle(fontWeight: FontWeight.w800, color: selected ? AppTheme.sacredRust : AppTheme.textDark)),
          ],
        ),
      ),
    );
  }
}
