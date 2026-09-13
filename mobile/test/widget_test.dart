import 'package:flutter_test/flutter_test.dart';
import 'package:purohit_mobile/core/theme/app_theme.dart';

void main() {
  test('brand palette is defined', () {
    expect(AppTheme.primary, isNotNull);
    expect(AppTheme.templeMidnight, isNotNull);
  });
}
