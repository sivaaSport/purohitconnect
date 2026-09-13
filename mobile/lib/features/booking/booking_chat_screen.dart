import 'package:flutter/material.dart';
import '../../core/models/models.dart';
import '../../core/services/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/ui_kit.dart';

class BookingChatScreen extends StatefulWidget {
  final String bookingId;
  final String title;
  const BookingChatScreen({super.key, required this.bookingId, required this.title});

  @override
  State<BookingChatScreen> createState() => _BookingChatScreenState();
}

class _BookingChatScreenState extends State<BookingChatScreen> {
  final _controller = TextEditingController();
  List<ChatMessageModel> _messages = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final items = await ApiService().fetchChat(widget.bookingId);
      if (mounted) {
        setState(() {
          _messages = items;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        showAppSnack(context, e.toString(), error: true);
      }
    }
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    try {
      final items = await ApiService().sendChat(widget.bookingId, text);
      if (mounted) setState(() => _messages = items);
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surfaceCream,
      appBar: AppBar(
        title: Text(widget.title),
        leading: const AppBackButton(),
        automaticallyImplyLeading: false,
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (_, i) {
                      final m = _messages[i];
                      return Align(
                        alignment: m.isMine ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          decoration: BoxDecoration(
                            color: m.isMine ? AppTheme.primary : Colors.white,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(m.message, style: TextStyle(color: m.isMine ? Colors.white : AppTheme.textDark)),
                              Text(m.time, style: TextStyle(fontSize: 10, color: m.isMine ? Colors.white70 : AppTheme.textLight)),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Row(
                children: [
                  Expanded(child: TextField(controller: _controller, decoration: const InputDecoration(hintText: 'Message your purohit'))),
                  IconButton(onPressed: _send, icon: const Icon(Icons.send_rounded, color: AppTheme.primary)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
