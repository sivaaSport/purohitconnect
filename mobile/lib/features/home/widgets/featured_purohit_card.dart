import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../../../core/models/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/devotee_avatar.dart';

class FeaturedPurohitCard extends StatelessWidget {
  final PurohitModel purohit;
  final VoidCallback onTap;

  const FeaturedPurohitCard({
    super.key,
    required this.purohit,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 280,
        margin: const EdgeInsets.only(right: 16),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: const Color(0x18FF6D00), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 15,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Avatar with sacred aura ring
                DevoteeAvatar(
                  size: 52,
                  name: purohit.name,
                  imageUrl: purohit.avatarUrl,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        purohit.name,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.textDark,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          const Icon(CupertinoIcons.location_solid, size: 12, color: AppTheme.primary),
                          const SizedBox(width: 4),
                          Text(
                            purohit.city,
                            style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Verified Temple Badge
            if (purohit.isVerified)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.tulsiGreen.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(CupertinoIcons.checkmark_seal_fill, size: 12, color: AppTheme.tulsiGreen),
                    const SizedBox(width: 4),
                    Text(
                      purohit.verifiedByTemple ?? 'Vedic Verified Purohit',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.tulsiGreen,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 10),
            // Languages
            Wrap(
              spacing: 6,
              children: purohit.languages.take(3).map((lang) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    lang,
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                  ),
                );
              }).toList(),
            ),
            const Spacer(),
            const Divider(height: 16, color: Color(0xFFF1F5F9)),
            // Rating and Pricing
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(CupertinoIcons.star_fill, size: 14, color: AppTheme.sacredGold),
                    const SizedBox(width: 4),
                    Text(
                      purohit.avgRating.toStringAsFixed(1),
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppTheme.textDark),
                    ),
                    Text(
                      ' (${purohit.totalReviews})',
                      style: const TextStyle(fontSize: 11, color: AppTheme.textLight),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text('Dakshina from', style: TextStyle(fontSize: 10, color: AppTheme.textLight)),
                    Text(
                      '₹${purohit.basePrice.toInt()}',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.primary,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
