import 'package:porcupine_flutter/porcupine_manager.dart';
import 'package:porcupine_flutter/porcupine_error.dart';
import 'package:porcupine_flutter/porcupine.dart';
import '../secrets.dart'; // Нужно убедиться, что там есть picovoiceAccessKey

class PorcupineWakeWordService {
  PorcupineManager? _porcupineManager;
  final Function() onWakeWordDetected;
  final Function(String error)? onError;
  
  bool _isListening = false;

  PorcupineWakeWordService({
    required this.onWakeWordDetected,
    this.onError,
  });

  Future<void> initialize() async {
    try {
      // Используем кастомное слово "WayFinder" из файла .ppn
      _porcupineManager = await PorcupineManager.fromKeywordPaths(
        Secrets.picovoiceAccessKey,
        ['assets/words/way_finder_android.ppn'], 
        _wakeWordCallback,
        errorCallback: _errorCallback
      );
      print("✅ Porcupine (WayFinder) initialized");
    } on PorcupineException catch (err) {
      print("❌ Porcupine init error: $err");
      onError?.call(err.toString());
    } catch (err) {
      print("❌ Generic error: $err");
      onError?.call(err.toString());
    }
  }

  void _wakeWordCallback(int keywordIndex) {
    if (keywordIndex == 0) {
      print("🚀 WAYFINDER DETECTED!");
      onWakeWordDetected();
    }
  }

  void _errorCallback(PorcupineException error) {
    print("❌ Porcupine error: $error");
    onError?.call(error.message ?? "Unknown error");
  }

  Future<void> startListening() async {
    if (_isListening) return;
    try {
      await _porcupineManager?.start();
      _isListening = true;
      print("👂 Porcupine started listening...");
    } on PorcupineException catch (ex) {
      print("❌ Failed to start Porcupine: $ex");
    }
  }

  Future<void> stopListening() async {
    if (!_isListening) return;
    try {
      await _porcupineManager?.stop();
      _isListening = false;
      print("🛑 Porcupine stopped.");
    } on PorcupineException catch (ex) {
      print("❌ Failed to stop Porcupine: $ex");
    }
  }

  Future<void> dispose() async {
    await _porcupineManager?.delete();
  }
}
