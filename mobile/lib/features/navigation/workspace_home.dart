import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/state/auth_provider.dart';
import '../navigation/main_navigation_screen.dart';
import '../purohit/purohit_navigation_screen.dart';

class WorkspaceHome extends StatelessWidget {
  const WorkspaceHome({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (auth.isPurohitWorkspace) return const PurohitNavigationScreen();
    return const MainNavigationScreen();
  }
}
