import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/state/notification_provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotificationProvider>().refresh();
    });
  }

  @override
  Widget build(BuildContext context) {
    final store = context.watch<NotificationProvider>();
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: const Text('Notifications'),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
        actions: [
          if (store.unreadCount > 0)
            TextButton(onPressed: store.markAll, child: const Text('Mark all read')),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: store.refresh,
        child: store.loading && store.items.isEmpty
            ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
            : store.items.isEmpty
                ? const EmptyState(title: 'All quiet', message: 'Ceremony updates and chat messages will appear here.', icon: CupertinoIcons.bell)
                : ListView.separated(
                    padding: const EdgeInsets.all(20),
                    itemCount: store.items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (_, i) {
                      final n = store.items[i];
                      return SurfaceCard(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(n.isRead ? CupertinoIcons.bell : CupertinoIcons.bell_fill, color: AppTheme.primary, size: 20),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(n.title, style: TextStyle(fontWeight: n.isRead ? FontWeight.w600 : FontWeight.w800, fontSize: 15)),
                                  const SizedBox(height: 4),
                                  Text(n.message, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                                  const SizedBox(height: 6),
                                  Text(n.date, style: const TextStyle(color: AppTheme.textLight, fontSize: 11)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}
