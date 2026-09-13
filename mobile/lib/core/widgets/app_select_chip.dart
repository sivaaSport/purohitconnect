import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class AppSelectChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback? onTap;
  final IconData? icon;
  final double fontSize;
  final bool expand;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry margin;

  const AppSelectChip({
    super.key,
    required this.label,
    required this.selected,
    this.onTap,
    this.icon,
    this.fontSize = 12,
    this.expand = false,
    this.padding = const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    this.margin = EdgeInsets.zero,
  });

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return Padding(
      padding: margin,
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: expand ? double.infinity : null,
          padding: padding,
          alignment: expand ? Alignment.center : null,
          decoration: AppTheme.selectChipDecoration(selected),
          child: Row(
            mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min,
            mainAxisAlignment: expand ? MainAxisAlignment.center : MainAxisAlignment.start,
            children: [
              if (icon != null) ...[
                Icon(
                  icon,
                  size: 16,
                  color: selected ? Colors.white : AppTheme.sacredGold,
                ),
                const SizedBox(width: 8),
              ],
              Text(
                label,
                style: AppTheme.selectChipText(selected, fontSize: fontSize).copyWith(
                  color: selected
                      ? Colors.white
                      : (enabled ? AppTheme.textDark : AppTheme.textLight),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
