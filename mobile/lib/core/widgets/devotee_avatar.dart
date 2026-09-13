import 'package:flutter/material.dart';
import '../constants/api_constants.dart';
import '../theme/app_theme.dart';

class DevoteeAvatar extends StatelessWidget {
  final double size;
  final VoidCallback? onTap;
  final bool showBorder;
  final String name;
  final String imageUrl;

  const DevoteeAvatar({
    super.key,
    this.size = 56,
    this.onTap,
    this.showBorder = true,
    this.name = '',
    this.imageUrl = '',
  });

  String get _initial {
    var trimmed = name.trim();
    if (trimmed.isEmpty) return 'D';
    final lower = trimmed.toLowerCase();
    const prefixes = ['pt.', 'pt ', 'pandit.', 'pandit ', 'purohit ', 'sri ', 'shri ', 'smt.'];
    for (final prefix in prefixes) {
      if (lower.startsWith(prefix)) {
        trimmed = trimmed.substring(prefix.length).trim();
        break;
      }
    }
    if (trimmed.isEmpty) return 'P';
    return String.fromCharCode(trimmed.runes.first).toUpperCase();
  }

  String get _resolvedUrl {
    final raw = imageUrl.trim();
    if (raw.isEmpty || raw == 'null' || raw == 'None') return '';
    final uri = Uri.tryParse(raw);
    final api = Uri.tryParse(ApiConstants.baseUrl);
    if (uri == null || !uri.hasScheme || api == null) return raw;
    final localHosts = {'localhost', '127.0.0.1', '10.0.2.2'};
    if (localHosts.contains(uri.host) && api.host.isNotEmpty) {
      return uri.replace(
        host: api.host,
        port: api.hasPort ? api.port : uri.port,
      ).toString();
    }
    return raw;
  }

  @override
  Widget build(BuildContext context) {
    final url = _resolvedUrl;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: showBorder ? Border.all(color: AppTheme.sacredGoldLight, width: 2) : null,
          boxShadow: [
            BoxShadow(
              color: AppTheme.primary.withOpacity(0.2),
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: ClipOval(
          child: url.isEmpty
              ? _InitialMark(initial: _initial, size: size)
              : Image.network(
                  url,
                  fit: BoxFit.cover,
                  width: size,
                  height: size,
                  errorBuilder: (context, error, stackTrace) {
                    return _InitialMark(initial: _initial, size: size);
                  },
                ),
        ),
      ),
    );
  }
}

class _InitialMark extends StatelessWidget {
  final String initial;
  final double size;

  const _InitialMark({required this.initial, required this.size});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.saffronGradient,
        shape: BoxShape.circle,
      ),
      child: Center(
        child: Text(
          initial,
          style: TextStyle(
            fontSize: size * 0.38,
            fontWeight: FontWeight.w800,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}
