import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:purohit_mobile/core/state/auth_provider.dart';
import 'package:purohit_mobile/core/theme/app_theme.dart';
import 'package:purohit_mobile/core/widgets/app_back_button.dart';
import 'package:purohit_mobile/core/widgets/app_select_chip.dart';
import 'package:purohit_mobile/core/widgets/ui_kit.dart';
import 'package:purohit_mobile/features/auth/login_screen.dart';
import 'package:purohit_mobile/features/auth/welcome_screen.dart';

void main() {
  test('brand palette is defined', () {
    expect(AppTheme.primary, isNotNull);
    expect(AppTheme.templeMidnight, isNotNull);
    expect(AppTheme.sacredGold, const Color(0xFFF59E0B));
  });

  testWidgets('AppSelectChip calls onTap', (tester) async {
    var taps = 0;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: AppSelectChip(
          label: 'Hyderabad',
          selected: false,
          onTap: () => taps += 1,
        ),
      ),
    ));
    await tester.tap(find.text('Hyderabad'));
    expect(taps, 1);
  });

  testWidgets('EmptyState shows title, message, and action', (tester) async {
    var acted = false;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: EmptyState(
          title: 'No bookings yet',
          message: 'Book a puja to see it here.',
          actionLabel: 'Browse pujas',
          onAction: () => acted = true,
        ),
      ),
    ));
    expect(find.text('No bookings yet'), findsOneWidget);
    await tester.tap(find.text('Browse pujas'));
    expect(acted, isTrue);
  });

  testWidgets('AppBackButton.maybe hides on the root route', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Builder(builder: (context) {
        return Scaffold(
          appBar: AppBar(leading: AppBackButton.maybe(context)),
          body: const Text('root'),
        );
      }),
    ));
    expect(find.byType(AppBackButton), findsNothing);
  });

  testWidgets('AppBackButton.maybe shows when the route can pop', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Builder(builder: (context) {
        return Scaffold(
          body: TextButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (inner) {
                  return Scaffold(
                    appBar: AppBar(leading: AppBackButton.maybe(inner)),
                    body: const Text('inner'),
                  );
                }),
              );
            },
            child: const Text('go'),
          ),
        );
      }),
    ));
    await tester.tap(find.text('go'));
    await tester.pumpAndSettle();
    expect(find.byType(AppBackButton), findsOneWidget);
  });

  testWidgets('WelcomeScreen shows brand copy without hitting the API', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
    expect(find.text('PurohitConnect'), findsOneWidget);
    expect(find.text('Sacred Ceremonies, Simplified.'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
    expect(find.text('Sign Up'), findsOneWidget);
    expect(find.text('Find a Purohit'), findsOneWidget);
  });

  testWidgets('LoginScreen asks for a phone number', (tester) async {
    await tester.pumpWidget(ChangeNotifierProvider(
      create: (_) => AuthProvider()..hydrateForTest(),
      child: const MaterialApp(home: LoginScreen()),
    ));
    expect(find.text('Welcome Back'), findsOneWidget);
    expect(find.text('Send OTP'), findsOneWidget);
    expect(find.textContaining('10-digit'), findsWidgets);
  });
}
