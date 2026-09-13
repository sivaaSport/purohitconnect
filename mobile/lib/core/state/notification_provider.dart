import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class NotificationProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  List<AppNotification> items = [];
  int unreadCount = 0;
  bool loading = false;

  Future<void> refresh() async {
    loading = true;
    notifyListeners();
    try {
      final data = await _api.fetchNotifications();
      items = (data['notifications'] as List? ?? [])
          .map((n) => AppNotification.fromJson(Map<String, dynamic>.from(n as Map)))
          .toList();
      unreadCount = (data['unread_count'] as num?)?.toInt() ?? items.where((n) => !n.isRead).length;
    } catch (_) {}
    loading = false;
    notifyListeners();
  }

  Future<void> markAll() async {
    await _api.markAllNotificationsRead();
    await refresh();
  }
}
