import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_select_chip.dart';

class SupportCenterScreen extends StatefulWidget {
  const SupportCenterScreen({super.key});

  @override
  State<SupportCenterScreen> createState() => _SupportCenterScreenState();
}

class _SupportCenterScreenState extends State<SupportCenterScreen> {
  final TextEditingController _subjectController = TextEditingController();
  final TextEditingController _descController = TextEditingController();
  String _selectedCategory = 'general';
  bool _isSubmitting = false;

  final List<Map<String, String>> _categories = [
    {'id': 'general', 'label': 'General Inquiry'},
    {'id': 'booking', 'label': 'Booking Issue'},
    {'id': 'payment', 'label': 'Payment Issue'},
    {'id': 'technical', 'label': 'Technical Glitch'},
  ];

  final List<Map<String, String>> _faqs = [
    {
      'q': 'How are Purohits verified on PurohitConnect?',
      'a': 'Every Purohit undergoes rigorous background verification, Veda Patasala certification check (Shukla Yajurveda, Rigveda, Samaveda), and temple endorsement before onboarding.'
    },
    {
      'q': 'How does Sacred Samagri delivery work?',
      'a': 'If you opt for Samagri kit, our temple-grade organic samagri (pure cow ghee, 108 havan herbs, Gangajal, sacred kalash, coconuts) is delivered to your venue 2 hours prior to the muhurat.'
    },
    {
      'q': 'Can I reschedule my ceremony if muhurat changes?',
      'a': 'Yes! You can reschedule your booking date or time up to 24 hours before the ceremony directly from the Bookings tab or by contacting your Purohit.'
    },
    {
      'q': 'What if my payment fails or need a refund?',
      'a': 'All cancelled bookings eligible for refund are instantly credited back to your PurohitConnect Wallet with zero processing delay.'
    },
  ];

  void _submitTicket() async {
    final subject = _subjectController.text.trim();
    final desc = _descController.text.trim();

    if (subject.isEmpty || desc.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill in both subject and description.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final ticket = await ApiService().createTicket(
        subject: subject,
        description: desc,
        category: _selectedCategory,
      );
      if (!mounted) return;
      _subjectController.clear();
      _descController.clear();
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          backgroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(
            children: [
              Icon(CupertinoIcons.checkmark_circle_fill, color: AppTheme.tulsiGreen),
              SizedBox(width: 8),
              Text('Ticket raised', style: TextStyle(fontWeight: FontWeight.w800)),
            ],
          ),
          content: Text(
            'Your request ${ticket.ticketId} is with the support team.',
            style: const TextStyle(height: 1.4, color: AppTheme.textMuted),
          ),
          actions: [
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx),
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
              child: const Text('OK'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Help & Support Center'),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Quick Contact Options Card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: AppTheme.creamHeroGradient,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppTheme.chipBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '24x7 Dedicated Vedic Helpline',
                    style: TextStyle(color: AppTheme.textDark, fontSize: 18, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'We are here to assist with muhurat guidance, bookings, and samagri requirements.',
                    style: TextStyle(color: AppTheme.textMuted, fontSize: 13, height: 1.4),
                  ),
                  const SizedBox(height: 18),

                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Opening WhatsApp Support (+91 98765 43210)...')),
                            );
                          },
                          icon: const Icon(CupertinoIcons.chat_bubble_2_fill, color: Colors.white, size: 16),
                          label: const Text('WhatsApp', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.tulsiGreen,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Calling Helpline: +91 98765 43210')),
                            );
                          },
                          icon: const Icon(CupertinoIcons.phone_fill, color: Colors.white, size: 16),
                          label: const Text('Call Us', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // Raise a Ticket Section
            const Text(
              'Raise a Service Request',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.textDark),
            ),
            const SizedBox(height: 4),
            const Text(
              'Have an issue with a booking, payment, or purohit? Tell us below.',
              style: TextStyle(fontSize: 13, color: AppTheme.textLight),
            ),
            const SizedBox(height: 14),

            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Category', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textMuted)),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _categories.map((c) {
                      return AppSelectChip(
                        label: c['label']!,
                        selected: _selectedCategory == c['id'],
                        onTap: () => setState(() => _selectedCategory = c['id']!),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 14),

                  const Text('Subject', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textMuted)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: _subjectController,
                    decoration: const InputDecoration(
                      hintText: 'e.g., Reschedule booking BK-7C3F9C39',
                    ),
                  ),
                  const SizedBox(height: 14),

                  const Text('Description', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textMuted)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: _descController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      hintText: 'Please provide details so we can resolve this quickly...',
                    ),
                  ),
                  const SizedBox(height: 18),

                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _isSubmitting ? null : _submitTicket,
                      child: _isSubmitting
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text('Submit Request', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // FAQs Section
            const Text(
              'Frequently Asked Questions',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.textDark),
            ),
            const SizedBox(height: 12),

            ..._faqs.map((faq) {
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                child: ExpansionTile(
                  title: Text(
                    faq['q']!,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                  ),
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      child: Text(
                        faq['a']!,
                        style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.5),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }
}
