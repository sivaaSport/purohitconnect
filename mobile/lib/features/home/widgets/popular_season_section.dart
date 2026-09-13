import 'package:flutter/material.dart';
import '../../../core/models/models.dart';
import '../../../core/theme/app_theme.dart';

class PopularSeasonSection extends StatelessWidget {
  final List<PujaModel> pujas;
  final VoidCallback onSeeAll;
  final ValueChanged<PujaModel> onTapPuja;

  const PopularSeasonSection({
    super.key,
    required this.pujas,
    required this.onSeeAll,
    required this.onTapPuja,
  });

  @override
  Widget build(BuildContext context) {
    if (pujas.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'DISCOVER',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                      color: AppTheme.textLight,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Popular this season',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.textDark,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Start from a ritual, then choose your purohit. Price and time stay clear before you pay.',
                    style: TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.35),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: onSeeAll,
              child: const Padding(
                padding: EdgeInsets.only(top: 4, left: 8),
                child: Text(
                  'See all pujas',
                  style: TextStyle(fontSize: 13, color: AppTheme.primary, fontWeight: FontWeight.w800),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        SizedBox(
          height: 118,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: pujas.length,
            separatorBuilder: (_, __) => const SizedBox(width: 10),
            itemBuilder: (context, index) {
              final puja = pujas[index];
              return GestureDetector(
                onTap: () => onTapPuja(puja),
                child: Container(
                  width: 168,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: const Color(0xFFF1F5F9)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        puja.categoryName.toUpperCase(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.4,
                          color: AppTheme.primary,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        puja.name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 14,
                          color: AppTheme.textDark,
                          height: 1.2,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        'About ${puja.baseDurationHours}h',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
