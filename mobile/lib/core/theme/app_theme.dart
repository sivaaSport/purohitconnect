import 'package:flutter/material.dart';

class AppTheme {
  static const Color primary = Color(0xFFFF6D00);
  static const Color primaryLight = Color(0xFFFF8A50);
  static const Color primaryDark = Color(0xFFC43E00);
  static const Color sacredGold = Color(0xFFF59E0B);
  static const Color sacredGoldLight = Color(0xFFFDE68A);
  static const Color sacredRust = Color(0xFFB45309);
  static const Color chipBorder = Color(0x24B45309);
  static const Color templeMidnight = Color(0xFF0F172A);
  static const Color surfaceCream = Color(0xFFFBF8F2);
  static const Color cardWhite = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF0F172A);
  static const Color textMuted = Color(0xFF64748B);
  static const Color textLight = Color(0xFF94A3B8);
  static const Color tulsiGreen = Color(0xFF059669);
  static const Color sindoorRed = Color(0xFFDC2626);

  static const LinearGradient saffronGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFFF8533), Color(0xFFFF5200)],
  );

  static const LinearGradient goldGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFFBBF24), Color(0xFFD97706)],
  );

  static const LinearGradient divineHeroGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF1E1B4B), Color(0xFF0F172A)],
  );

  static const LinearGradient creamHeroGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFFFF7ED), Color(0xFFFFFFFF)],
    stops: [0.0, 0.55],
  );

  static BoxDecoration selectChipDecoration(bool selected, {double radius = 20}) {
    return BoxDecoration(
      color: selected ? sacredGold : Colors.white,
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(color: selected ? sacredGold : chipBorder),
    );
  }

  static TextStyle selectChipText(bool selected, {double fontSize = 12}) {
    return TextStyle(
      color: selected ? Colors.white : textDark,
      fontWeight: FontWeight.w700,
      fontSize: fontSize,
    );
  }

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      fontFamily: 'AppSans',
      scaffoldBackgroundColor: surfaceCream,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        primary: primary,
        secondary: sacredGold,
        surface: cardWhite,
      ),
      textTheme: ThemeData.light().textTheme.apply(
        fontFamily: 'AppSans',
        bodyColor: textDark,
        displayColor: textDark,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: surfaceCream,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: sacredRust),
        titleTextStyle: TextStyle(
          color: textDark,
          fontSize: 20,
          fontWeight: FontWeight.w800,
        ),
      ),
      chipTheme: ChipThemeData(
        selectedColor: sacredGold,
        backgroundColor: Colors.white,
        disabledColor: const Color(0xFFF8FAFC),
        checkmarkColor: Colors.white,
        side: const BorderSide(color: chipBorder),
        labelStyle: const TextStyle(fontWeight: FontWeight.w700, color: textDark, fontSize: 12),
        secondaryLabelStyle: const TextStyle(fontWeight: FontWeight.w700, color: Colors.white, fontSize: 12),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      cardTheme: CardThemeData(
        color: cardWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0x14FF6D00), width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: Color(0xFFE2E8F0))),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: Color(0xFFE2E8F0))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: primary, width: 2)),
        hintStyle: const TextStyle(color: textLight, fontSize: 15),
      ),
    );
  }
}
