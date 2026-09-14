import 'package:shared_preferences/shared_preferences.dart';

class SessionStore {
  static const _tokenKey = 'pc_auth_token';
  static const _workspaceKey = 'pc_workspace';

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<String?> readToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> saveWorkspace(String workspace) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_workspaceKey, workspace);
  }

  static Future<String?> readWorkspace() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_workspaceKey);
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_workspaceKey);
  }
}
