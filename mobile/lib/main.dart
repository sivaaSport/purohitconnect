import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'core/state/auth_provider.dart';
import 'core/state/booking_provider.dart';
import 'core/state/notification_provider.dart';
import 'features/auth/welcome_screen.dart';
import 'features/navigation/workspace_home.dart';
import 'features/support/support_bot_overlay.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
    statusBarBrightness: Brightness.light,
  ));
  runApp(const PurohitConnectApp());
}

class PurohitConnectApp extends StatelessWidget {
  const PurohitConnectApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()..bootstrap()),
        ChangeNotifierProvider(create: (_) => BookingProvider()),
        ChangeNotifierProvider(create: (_) => NotificationProvider()),
      ],
      child: MaterialApp(
        title: 'PurohitConnect',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        builder: (context, child) => SupportBotHost(child: child ?? const SizedBox.shrink()),
        navigatorObservers: [modalStackObserver],
        home: const _AuthGate(),
      ),
    );
  }
}

class _AuthGate extends StatelessWidget {
  const _AuthGate();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isReady) {
      return Scaffold(
        backgroundColor: AppTheme.surfaceCream,
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 84,
                height: 84,
                decoration: const BoxDecoration(shape: BoxShape.circle, gradient: AppTheme.saffronGradient),
                child: const Center(child: Text('ॐ', style: TextStyle(color: Colors.white, fontSize: 40, fontWeight: FontWeight.bold))),
              ),
              const SizedBox(height: 18),
              const Text('PurohitConnect', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 22)),
              const SizedBox(height: 16),
              const CircularProgressIndicator(color: AppTheme.primary),
            ],
          ),
        ),
      );
    }
    if (!auth.isAuthenticated) return const WelcomeScreen();
    return const WorkspaceHome();
  }
}
