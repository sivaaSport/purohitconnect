import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class AppBackButton extends StatelessWidget {
  final Color color;

  const AppBackButton({super.key, this.color = AppTheme.sacredRust});

  static Widget? maybe(BuildContext context, {Color color = AppTheme.sacredRust}) {
    if (!Navigator.canPop(context)) return null;
    return AppBackButton(color: color);
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(CupertinoIcons.back, color: color),
      tooltip: 'Back',
      onPressed: () => Navigator.maybePop(context),
    );
  }
}
