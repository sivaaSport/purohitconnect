import 'package:flutter/cupertino.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/models/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_back_button.dart';

class RitualGallerySection extends StatelessWidget {
  final String purohitName;
  final List<PurohitGalleryItem> gallery;

  const RitualGallerySection({
    super.key,
    required this.purohitName,
    required this.gallery,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Past pujas & moments',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textDark),
        ),
        const SizedBox(height: 6),
        Text(
          'Photos and videos shared by $purohitName.',
          style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.4),
        ),
        const SizedBox(height: 14),
        if (gallery.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 22),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: const Text(
              'No gallery items yet. This purohit has not uploaded past puja photos or videos.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.45),
            ),
          )
        else
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: gallery.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              childAspectRatio: 0.86,
            ),
            itemBuilder: (context, index) {
              final item = gallery[index];
              return _GalleryTile(
                item: item,
                onTap: () => _openViewer(context, index),
              );
            },
          ),
      ],
    );
  }

  void _openViewer(BuildContext context, int index) {
    Navigator.of(context).push(
      PageRouteBuilder(
        opaque: false,
        pageBuilder: (_, __, ___) => _GalleryViewer(
          items: gallery,
          initialIndex: index,
        ),
      ),
    );
  }
}

class _GalleryTile extends StatelessWidget {
  final PurohitGalleryItem item;
  final VoidCallback onTap;

  const _GalleryTile({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Stack(
                fit: StackFit.expand,
                children: [
                  ColoredBox(
                    color: const Color(0xFF0B1020),
                    child: item.isVideo
                        ? const SizedBox.expand()
                        : _GalleryPhoto(item: item, fit: BoxFit.cover),
                  ),
                  if (item.isVideo)
                    const Center(
                      child: CircleAvatar(
                        radius: 18,
                        backgroundColor: Color(0xCCFFFFFF),
                        child: Icon(CupertinoIcons.play_fill, size: 18, color: AppTheme.textDark),
                      ),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title.isEmpty ? (item.isVideo ? 'Video' : 'Puja photo') : item.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppTheme.textDark),
                  ),
                  if (item.caption.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      item.caption,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GalleryPhoto extends StatelessWidget {
  final PurohitGalleryItem item;
  final BoxFit fit;

  const _GalleryPhoto({required this.item, this.fit = BoxFit.cover});

  @override
  Widget build(BuildContext context) {
    final url = ApiConstants.resolveMediaUrl(item.url);
    if (url.isEmpty) {
      return const ColoredBox(color: Color(0xFF0B1020));
    }
    return Image.network(
      url,
      fit: fit,
      width: double.infinity,
      height: double.infinity,
      errorBuilder: (_, __, ___) => const ColoredBox(
        color: Color(0xFF0B1020),
        child: Center(child: Icon(CupertinoIcons.photo, color: Colors.white54, size: 28)),
      ),
    );
  }
}

class _GalleryVideo extends StatelessWidget {
  final PurohitGalleryItem item;

  const _GalleryVideo({required this.item});

  @override
  Widget build(BuildContext context) {
    final url = ApiConstants.resolveMediaUrl(item.url);
    if (url.isEmpty) {
      return const ColoredBox(color: Color(0xFF0B1020));
    }
    if (kIsWeb) {
      return HtmlElementView.fromTagName(
        tagName: 'video',
        onElementCreated: (element) {
          final video = element as dynamic;
          video.src = url;
          video.controls = true;
          video.setAttribute('playsinline', 'true');
          video.setAttribute('preload', 'metadata');
          try {
            video.style.width = '100%';
            video.style.height = '100%';
            video.style.objectFit = 'contain';
            video.style.background = '#0b1020';
          } catch (_) {}
        },
      );
    }
    return const ColoredBox(
      color: Color(0xFF0B1020),
      child: Center(
        child: Icon(CupertinoIcons.play_circle, color: Colors.white70, size: 42),
      ),
    );
  }
}

class _GalleryViewer extends StatefulWidget {
  final List<PurohitGalleryItem> items;
  final int initialIndex;

  const _GalleryViewer({required this.items, required this.initialIndex});

  @override
  State<_GalleryViewer> createState() => _GalleryViewerState();
}

class _GalleryViewerState extends State<_GalleryViewer> {
  late final PageController _controller;
  late int _index;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
    _controller = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.items[_index];
    return Scaffold(
      backgroundColor: const Color(0xF20B1020),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        leading: const AppBackButton(color: Colors.white),
        automaticallyImplyLeading: false,
        title: Text(
          item.title.isEmpty ? (item.isVideo ? 'Video' : 'Puja photo') : item.title,
          style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: PageView.builder(
              controller: _controller,
              itemCount: widget.items.length,
              onPageChanged: (value) => setState(() => _index = value),
              itemBuilder: (context, index) {
                final current = widget.items[index];
                return InteractiveViewer(
                  minScale: 1,
                  maxScale: 4,
                  child: Center(
                    child: AspectRatio(
                      aspectRatio: 4 / 3,
                      child: current.isVideo
                          ? _GalleryVideo(item: current)
                          : _GalleryPhoto(item: current, fit: BoxFit.contain),
                    ),
                  ),
                );
              },
            ),
          ),
          if (item.caption.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
              child: Text(
                item.caption,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
              ),
            ),
        ],
      ),
    );
  }
}
