// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get appTitle => 'Vision AI';

  @override
  String get startListening => 'Нажмите, чтобы сказать';

  @override
  String get stopListening => 'Стоп';

  @override
  String get processing => 'Думаю...';

  @override
  String get navigatorMode => 'Режим Навигатора';

  @override
  String get chatMode => 'Режим Чата';

  @override
  String get settings => 'Настройки';

  @override
  String get serverUrl => 'Адрес сервера';

  @override
  String get save => 'Сохранить';

  @override
  String get error => 'Ошибка';

  @override
  String get welcome => 'Привет! Я твой Vision AI.';

  @override
  String get cameraPermission => 'Нужен доступ к камере';

  @override
  String get micPermission => 'Нужен доступ к микрофону';
}
