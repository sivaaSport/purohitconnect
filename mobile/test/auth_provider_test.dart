import 'package:flutter_test/flutter_test.dart';
import 'package:purohit_mobile/core/models/models.dart';
import 'package:purohit_mobile/core/state/auth_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

UserModel _user({required String role, bool canActAsPurohit = false}) {
  return UserModel(
    id: 1,
    phone: '+919876543210',
    username: 'user',
    name: 'Test User',
    role: role,
    walletBalance: 0,
    isPhoneVerified: true,
    canActAsPurohit: canActAsPurohit,
  );
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('devotee cannot open purohit workspace', () {
    final auth = AuthProvider();
    auth.hydrateForTest(user: _user(role: 'customer'), workspace: 'purohit');
    expect(auth.canActAsPurohit, isFalse);
    expect(auth.isPurohitWorkspace, isFalse);
    expect(auth.workspace, 'devotee');
  });

  test('purohit role can switch into purohit workspace', () async {
    final auth = AuthProvider();
    auth.hydrateForTest(user: _user(role: 'purohit'), workspace: 'devotee');
    expect(auth.canActAsPurohit, isTrue);
    expect(auth.isPurohitWorkspace, isFalse);

    await auth.setWorkspace('purohit');
    expect(auth.workspace, 'purohit');
    expect(auth.isPurohitWorkspace, isTrue);
  });

  test('dual-flag devotee can act as purohit', () {
    final auth = AuthProvider();
    auth.hydrateForTest(
      user: _user(role: 'customer', canActAsPurohit: true),
      workspace: 'purohit',
    );
    expect(auth.canActAsPurohit, isTrue);
    expect(auth.isPurohitWorkspace, isTrue);
  });
}
