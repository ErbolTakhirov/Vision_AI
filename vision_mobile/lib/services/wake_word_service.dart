import 'package:speech_to_text/speech_to_text.dart' as stt;

class WakeWordService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  Function(String command)? onWakeWordDetected;
  
  // Wake words in different languages
  final List<String> _wakeWords = [
    'эй вижион', 'эй вижен', 'хей вижион', 'hey vision', 'эй vision',
    'эй вижу', 'хей вижу', 'привет вижион', 'вижион', 'vision',
    'слушай вижион', 'ok vision'
  ];

  bool _isRestarting = false;

  Future<bool> initialize() async {
    return await _speech.initialize(
      onError: (error) {
        print('Speech error: $error');
        // Filter out permanent errors that shouldn't restart immediately
        // But for wake word, we generally want to keep trying
        _restartListening();
      },
      onStatus: (status) {
        print('Speech status: $status');
        if (status == 'done' || status == 'notListening') {
          _restartListening();
        }
      },
      debugLogging: false, 
    );
  }

  void _restartListening() {
    if (!_isListening || _isRestarting) return;
    
    _isRestarting = true;
    Future.delayed(const Duration(milliseconds: 2000), () {
      _isRestarting = false;
      _listenContinuously();
    });
  }

  Future<void> startListening() async {
    if (_isListening) return;
    
    // Initialize if needed, then listen
    bool available = await _speech.initialize(); 
    if (available) {
      _isListening = true;
      _listenContinuously();
    } else {
      print('Speech recognition turned off or not available');
    }
  }

  void _listenContinuously() async {
    if (!_isListening) return;

    // Force Russian locale if available
    var locales = await _speech.locales();
    var selectedLocale = locales.firstWhere(
      (element) => element.localeId.startsWith('ru'), 
      orElse: () => locales.first
    );

    print('Listening with locale: ${selectedLocale.localeId} (Mode: Search)');

    _speech.listen(
      onResult: (result) {
        final text = result.recognizedWords.toLowerCase();
        
        // BROAD MATCHING (Широкий поиск)
        final hasVision = text.contains('виж') || text.contains('vision') || text.contains('веж');
        final hasHey = text.contains('эй') || text.contains('хей') || text.contains('привет') || text.contains('hey') || text.contains('hi');
        
        // Trigger logic
        bool detected = false;
        
        if (hasVision && hasHey) {
          detected = true;
        } else {
           for (final w in _wakeWords) {
            if (text.contains(w)) {
              detected = true;
              break;
            }
          }
        }

        if (detected) {
          print('🚀 WAKE WORD DETECTED in: "$text"');
          
          String command = text.replaceAll(RegExp(r'(эй|хей|привет|hey|hi|vision|вижион|вижен|вижу|виж)'), '').trim();
          if (command.isEmpty || command.length < 3) {
             command = "что передо мной?";
          }
          
          if (_isListening) {
             onWakeWordDetected?.call(command);
             stopListening(); // Stop clean
          }
        }
      },
      localeId: selectedLocale.localeId, 
      listenFor: const Duration(seconds: 60), // Try max duration
      pauseFor: const Duration(seconds: 30),
      partialResults: true,
      listenMode: stt.ListenMode.search, // Better for commands
      cancelOnError: false,
    );
  }

  void stopListening() {
    _isListening = false;
    _speech.stop();
  }

  void dispose() {
    stopListening();
    _speech.cancel();
  }

  bool get isListening => _isListening;
}
