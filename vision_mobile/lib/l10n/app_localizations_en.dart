// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Vision AI';

  @override
  String get startListening => 'Tap to Speak';

  @override
  String get stopListening => 'Stop';

  @override
  String get processing => 'Thinking...';

  @override
  String get navigatorMode => 'Navigator Mode';

  @override
  String get chatMode => 'Chat Mode';

  @override
  String get settings => 'Settings';

  @override
  String get serverUrl => 'Server URL';

  @override
  String get save => 'Save';

  @override
  String get error => 'Error';

  @override
  String get welcome => 'Hello! I am your Vision AI.';

  @override
  String get cameraPermission => 'Camera permission is required';

  @override
  String get micPermission => 'Microphone permission is required';
}
