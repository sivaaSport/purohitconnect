import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../home/all_categories_screen.dart';
import '../purohits/purohit_list_screen.dart';
import 'login_screen.dart';
import 'signup_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
              child: Row(
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: const BoxDecoration(shape: BoxShape.circle, gradient: AppTheme.saffronGradient),
                    child: const Icon(CupertinoIcons.flame_fill, color: Colors.white, size: 16),
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'PurohitConnect',
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: AppTheme.textDark),
                    ),
                  ),
                  TextButton(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen())),
                    child: const Text('Login', style: TextStyle(fontWeight: FontWeight.w800, color: AppTheme.textDark)),
                  ),
                  const SizedBox(width: 4),
                  ElevatedButton(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SignupScreen())),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF59E0B),
                      foregroundColor: const Color(0xFF111827),
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                    ),
                    child: const Text('Sign Up', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.only(bottom: 28),
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.fromLTRB(22, 36, 22, 32),
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [Color(0xFF7C2D12), Color(0xFFB45309), Color(0xFFF59E0B)],
                        stops: [0.0, 0.4, 1.0],
                      ),
                      borderRadius: BorderRadius.vertical(bottom: Radius.circular(28)),
                    ),
                    child: Column(
                      children: [
                        const Text(
                          'Sacred Ceremonies, Simplified.',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 30, fontWeight: FontWeight.w900, color: Colors.white, height: 1.15),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Book verified, experienced Purohits & Pandits for your household pujas, festivals, and life events.',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 15, color: Color(0xF0FFFFFF), height: 1.4, fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 22),
                        Container(
                          padding: const EdgeInsets.fromLTRB(6, 6, 6, 6),
                          decoration: BoxDecoration(
                            color: const Color(0xE60F172A),
                            borderRadius: BorderRadius.circular(999),
                            border: Border.all(color: const Color(0x40FACC15)),
                          ),
                          child: Row(
                            children: [
                              const SizedBox(width: 12),
                              const Expanded(
                                child: Text(
                                  'Search pujas, e.g. Satyanarayan Puja...',
                                  style: TextStyle(color: Color(0xB3FFFFFF), fontSize: 13),
                                ),
                              ),
                              ElevatedButton(
                                onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AllCategoriesScreen())),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFFF59E0B),
                                  foregroundColor: const Color(0xFF111827),
                                  elevation: 0,
                                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                                ),
                                child: const Text('Search', style: TextStyle(fontWeight: FontWeight.w800)),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 22),
                        const Wrap(
                          alignment: WrapAlignment.center,
                          spacing: 16,
                          runSpacing: 8,
                          children: [
                            _HeroTrust(icon: CupertinoIcons.checkmark_seal_fill, label: 'Verified Profiles'),
                            _HeroTrust(icon: CupertinoIcons.money_dollar_circle_fill, label: 'Transparent Pricing'),
                            _HeroTrust(icon: CupertinoIcons.calendar_badge_plus, label: 'Instant Booking'),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Popular Categories', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
                                  SizedBox(height: 4),
                                  Text('Find the right rituals for your occasion.', style: TextStyle(color: AppTheme.textMuted)),
                                ],
                              ),
                            ),
                            GestureDetector(
                              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AllCategoriesScreen())),
                              child: const Text('View all pujas >', style: TextStyle(color: Color(0xFFB45309), fontWeight: FontWeight.w800, fontSize: 13)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        const _CategoryCard(icon: CupertinoIcons.house_fill, title: 'Household Pujas', subtitle: 'Vastu Shanti, Satyanarayan Puja, Griha Pravesh'),
                        const _CategoryCard(icon: CupertinoIcons.heart_fill, title: 'Life Events', subtitle: 'Namkaran, Annaprasana, Upanayanam'),
                        const _CategoryCard(icon: CupertinoIcons.heart_circle_fill, title: 'Weddings', subtitle: 'Engagement, Vivah, Post-wedding rituals'),
                        const _CategoryCard(icon: CupertinoIcons.sparkles, title: 'Special Rituals', subtitle: 'Navagraha Shanti, Havan, Yagna'),
                        const SizedBox(height: 28),
                        const Text('How It Works', textAlign: TextAlign.center, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
                        const SizedBox(height: 4),
                        const Center(child: Text('Your sacred journey in 3 simple steps', style: TextStyle(color: AppTheme.textMuted))),
                        const SizedBox(height: 18),
                        const _StepCard(number: '1', title: 'Search', body: 'Search for the puja you need, then choose a verified purohit.'),
                        const _StepCard(number: '2', title: 'Choose & Book', body: 'Review verified purohit profiles, prices, and book your slot.'),
                        const _StepCard(number: '3', title: 'Perform Puja', body: 'The Purohit arrives on time to conduct the authentic ritual.'),
                        const SizedBox(height: 22),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(22),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(22),
                            gradient: const LinearGradient(
                              colors: [Color(0xFFF59E0B), Color(0xFFB45309)],
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Are you a Purohit or Pandit?', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                              const SizedBox(height: 8),
                              const Text(
                                'Join our platform to connect with devotees across your city. Manage bookings and focus on what you do best.',
                                style: TextStyle(color: Color(0xF0FFFFFF), height: 1.4),
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SignupScreen())),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.white,
                                  foregroundColor: const Color(0xFFB45309),
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                ),
                                child: const Text('Register as Purohit', style: TextStyle(fontWeight: FontWeight.w800)),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        Center(
                          child: TextButton(
                            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PurohitListScreen())),
                            child: const Text('Find a Purohit', style: TextStyle(fontWeight: FontWeight.w800, color: Color(0xFFB45309))),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeroTrust extends StatelessWidget {
  final IconData icon;
  final String label;
  const _HeroTrust({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: Colors.white, size: 16),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12)),
      ],
    );
  }
}

class _CategoryCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  const _CategoryCard({required this.icon, required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AllCategoriesScreen())),
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(color: const Color(0x1AFF9933), shape: BoxShape.circle),
              child: Icon(icon, color: const Color(0xFFB45309), size: 24),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppTheme.textDark)),
                  const SizedBox(height: 4),
                  Text(subtitle, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.3)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepCard extends StatelessWidget {
  final String number;
  final String title;
  final String body;
  const _StepCard({required this.number, required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.surfaceCream,
              border: Border.all(color: const Color(0xFFF59E0B), width: 2),
            ),
            child: Center(
              child: Text(number, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Color(0xFFB45309))),
            ),
          ),
          const SizedBox(height: 10),
          Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(body, textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textMuted, height: 1.4)),
        ],
      ),
    );
  }
}
