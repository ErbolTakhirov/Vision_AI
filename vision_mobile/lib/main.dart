import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'l10n/app_localizations.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';

import 'theme/app_theme.dart';
import 'services/vision_api.dart';
// import 'services/wake_word_service.dart'; // Old service
import 'services/porcupine_service.dart';
import 'services/navigation_service.dart';
import 'screens/chat_screen.dart';
import 'screens/vision_mode.dart';
import 'widgets/glass_container.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VisionApp());
}

class VisionApp extends StatefulWidget {
  const VisionApp({super.key});

  @override
  State<VisionApp> createState() => _VisionAppState();
}

class _VisionAppState extends State<VisionApp> {
  // Locale State
  Locale? _locale;

  void setLocale(Locale l) {
    setState(() {
      _locale = l;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WayFinder',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      locale: _locale,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('en'),
        Locale('ru'),
        Locale('ky'),
      ],
      home: MainNavScreen(onLocaleChange: setLocale),
    );
  }
}

class MainNavScreen extends StatefulWidget {
  final Function(Locale) onLocaleChange;
  const MainNavScreen({super.key, required this.onLocaleChange});

  @override
  State<MainNavScreen> createState() => _MainNavScreenState();
}

class _MainNavScreenState extends State<MainNavScreen> with WidgetsBindingObserver {
  // Services
  final _api = VisionApiService();
  // final _wakeWordService = WakeWordService();
  late PorcupineWakeWordService _porcupineService;
  final _navigationService = NavigationService();
  CameraController? _cameraController;
  final _audioRecorder = AudioRecorder();
  final _audioPlayer = AudioPlayer();
  bool _wakeWordEnabled = false;
  bool _isNavigating = false;

  // State
  int _currentIndex = 0;
  bool _isRecording = false;
  bool _isProcessing = false;
  List<ChatMessage> _messages = [];
  String _visionStatus = "";
  
  // Tabs
  static const int TAB_CHAT = 0;
  static const int TAB_VISION = 1;
  static const int TAB_SETTINGS = 2;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    
    // Resume listening listener removed for manual control stability
    // _audioPlayer.onPlayerComplete.listen((event) { ... });

    _initHardware();
    _addInitialMessage();
    // Init Porcupine
    _porcupineService = PorcupineWakeWordService(
      onWakeWordDetected: _handlePorcupineWake,
      onError: (err) => print("Porcupine Error: $err")
    );
    _initWakeWord();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cameraController?.dispose();
    _audioRecorder.dispose();
    _audioPlayer.dispose();
    _porcupineService.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Handle camera resource management
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      _cameraController?.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initCamera();
    }
  }

  Future<void> _initCamera() async {
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      try {
        _cameraController = CameraController(
          cameras.first, 
          ResolutionPreset.medium, 
          enableAudio: false,
          imageFormatGroup: ImageFormatGroup.jpeg,
        );
        await _cameraController!.initialize();
        setState(() {});
      } catch (e) {
        print('Camera error: $e');
      }
    }
  }

  void _addInitialMessage() {
     _messages.add(ChatMessage(
       text: "Я WayFinder. Нажмите кнопку или скажите 'WayFinder'.", 
       isUser: false, 
       timestamp: DateTime.now()
     ));
  }

  Future<void> _initHardware() async {
    await [Permission.camera, Permission.microphone].request();
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      try {
        // Use medium resolution for better compatibility
        // High resolution can cause issues on some devices
        _cameraController = CameraController(
          cameras.first, 
          ResolutionPreset.medium, 
          enableAudio: false,
          imageFormatGroup: ImageFormatGroup.jpeg,
        );
        
        await _cameraController!.initialize();
        
        // Enable auto-focus if available
        try {
          await _cameraController!.setFocusMode(FocusMode.auto);
        } catch (e) {
          print('Auto-focus not available: $e');
        }
        
        setState(() {});
      } catch (e) {
        print('Camera initialization error: $e');
        // Try with lower resolution as fallback
        try {
          _cameraController = CameraController(
            cameras.first,
            ResolutionPreset.low,
            enableAudio: false,
          );
          await _cameraController!.initialize();
          setState(() {});
        } catch (e2) {
          print('Camera fallback failed: $e2');
        }
      }
    }
  }

  Future<void> _initWakeWord() async {
    await _porcupineService.initialize();
    if (_wakeWordEnabled) {
      await _porcupineService.startListening();
    }
  }

  void _handlePorcupineWake() async {
    print("⚡ WAYFINDER DETECTED! Starting recording...");
    if (!_isRecording && !_isProcessing) {
      await _porcupineService.stopListening();
      // Start recording user query
      _handleVoiceButton();
    }
  }

  void _toggleWakeWord() {
    setState(() {
      _wakeWordEnabled = !_wakeWordEnabled;
      if (_wakeWordEnabled) {
        _porcupineService.startListening();
      } else {
        _porcupineService.stopListening();
      }
    });
  }

  // --- ACTIONS ---

  Future<void> _handleVoiceButton() async {
    if (_isProcessing) return;

    if (_isRecording) {
      // STOP
      final path = await _audioRecorder.stop();
      setState(() { _isRecording = false; _isProcessing = true; });
      if (path != null) {
        await _processRequest(audioPath: path, mode: 'chat');
      }
    } else {
      // START
      if (await _audioRecorder.hasPermission()) {
        final dir = await getTemporaryDirectory();
        final path = '${dir.path}/query.m4a';
        await _audioPlayer.stop();
        await _audioRecorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
        setState(() { _isRecording = true; });
      }
    }
  }

  Future<void> _handleTextSubmit(String text) async {
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true, timestamp: DateTime.now()));
      _isProcessing = true;
    });
    
    // Check if this is a navigation request
    if (_isNavigationRequest(text)) {
      await _handleNavigationRequest(text: text);
    } else {
      await _processRequest(text: text, mode: 'chat');
    }
  }

  bool _isNavigationRequest(String text) {
    final navKeywords = ['как дойти', 'как доехать', 'маршрут', 'навигация', 'проведи', 'как пройти'];
    final lowerText = text.toLowerCase();
    return navKeywords.any((keyword) => lowerText.contains(keyword));
  }

  Future<void> _handleNavigationRequest({String? audioPath, String text = ''}) async {
    try {
      // Get current location
      final position = await _navigationService.getCurrentLocation();
      
      // Request navigation from backend
      final result = await _api.requestNavigation(
        audioPath,
        text,
        currentLat: position?.latitude,
        currentLon: position?.longitude,
      );
      
      final message = result['message'];
      final audioB64 = result['audio'];
      final destination = result['destination'];
      final action = result['action'];
      
      setState(() {
        _messages.add(ChatMessage(text: message, isUser: false, timestamp: DateTime.now()));
      });
      
      // Play audio response
      if (audioB64 != null) {
        // Pause listening so AI doesn't hear itself
        await _porcupineService.stopListening();
        
        final bytes = base64Decode(audioB64);
        final dir = await getTemporaryDirectory();
        final file = File('${dir.path}/response.mp3');
        await file.writeAsBytes(bytes);
        await _audioPlayer.play(DeviceFileSource(file.path));
      }
      
      // Build route if destination found
      if (action == 'build_route' && destination != null) {
        await _buildAndStartNavigation(destination);
      }
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: "Ошибка навигации: $e", isUser: false, timestamp: DateTime.now()));
      });
    } finally {
      setState(() { _isProcessing = false; });
    }
  }

  Future<void> _buildAndStartNavigation(String destination) async {
    try {
      final steps = await _navigationService.buildRoute(destination);
      
      if (steps.isEmpty) {
        throw Exception('Не удалось построить маршрут');
      }
      
      setState(() {
        _isNavigating = true;
        _currentIndex = TAB_VISION; // Switch to vision mode for navigation
      });
      
      // Start turn-by-turn navigation
      _startTurnByTurnGuidance();
      
    } catch (e) {
      final errorMsg = 'Ошибка построения маршрута: $e';
      setState(() {
        _messages.add(ChatMessage(text: errorMsg, isUser: false, timestamp: DateTime.now()));
      });
      
      // Speak error
      final ttsBytes = await _generateTTS(errorMsg);
      if (ttsBytes != null) {
        final dir = await getTemporaryDirectory();
        final file = File('${dir.path}/nav_error.mp3');
        await file.writeAsBytes(ttsBytes);
        await _audioPlayer.play(DeviceFileSource(file.path));
      }
    }
  }

  void _startTurnByTurnGuidance() {
    // Listen to location updates
    _navigationService.getLocationStream().listen((position) async {
      if (!_isNavigating) return;
      
      // Get current instruction
      final instruction = _navigationService.getCurrentInstruction();
      
      setState(() {
        _visionStatus = instruction;
      });
      
      // Check if we should move to next step
      final shouldProgress = await _navigationService.checkStepProgress();
      if (shouldProgress) {
        _navigationService.nextStep();
        final nextInstruction = _navigationService.getCurrentInstruction();
        
        // Speak next instruction
        final ttsBytes = await _generateTTS(nextInstruction);
        if (ttsBytes != null) {
          final dir = await getTemporaryDirectory();
          final file = File('${dir.path}/nav_step.mp3');
          await file.writeAsBytes(ttsBytes);
          await _audioPlayer.play(DeviceFileSource(file.path));
        }
      }
    });
  }

  Future<List<int>?> _generateTTS(String text) async {
    // Simple TTS generation - in production, use backend TTS
    // For now, return null and rely on backend
    return null;
  }

  Future<void> _processRequest({String? audioPath, String text = '', required String mode}) async {
    try {
      XFile? image;
      // Capture image if camera is ready (context aware)
      if (_cameraController != null && _cameraController!.value.isInitialized) {
        try {
          image = await _cameraController!.takePicture();
        } catch (_) {} 
      }

      final result = await _api.smartAnalyze(image, audioPath, mode: mode, text: text);
      
      final msg = result['message'];
      final audioB64 = result['audio'];
      final debugVision = result['debug_vision'];

      // Update UI
      setState(() {
        if (mode == 'chat') {
           _messages.add(ChatMessage(text: msg, isUser: false, timestamp: DateTime.now()));
           if (debugVision != null) {
              // Optionally show what AI saw
           }
        } else {
           _visionStatus = msg;
        }
      });

      // Play Audio
      if (audioB64 != null) {
         // Pause listening so AI doesn't hear itself
         await _porcupineService.stopListening();
         
         final bytes = base64Decode(audioB64);
         final dir = await getTemporaryDirectory();
         final file = File('${dir.path}/response.mp3');
         await file.writeAsBytes(bytes);
         await _audioPlayer.play(DeviceFileSource(file.path));
      }
      
      // Wait for TTS to finish before listening again
      if (audioB64 != null) {
        try {
           await _audioPlayer.onPlayerComplete.first.timeout(const Duration(seconds: 30));
        } catch (_) {}
      }

    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: "Error: $e", isUser: false, timestamp: DateTime.now()));
      });
    } finally {
      setState(() { _isProcessing = false; });
      if (_wakeWordEnabled) {
        _porcupineService.startListening();
      }
    }
  }

  // --- UI BUILDING ---
  
  @override
  Widget build(BuildContext context) {
    if (_cameraController == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      extendBody: true, // For transparency behind navbar
      body: Stack(
        children: [
          IndexedStack(
            index: _currentIndex,
            children: [
              // TAB 0: CHAT
              SafeArea(
                child: ChatScreen(
                  messages: _messages,
                  isProcessing: _isProcessing,
                  onSendMessage: _handleTextSubmit,
                ),
              ),

              // TAB 1: VISION
              VisionModeScreen(
                cameraController: _cameraController,
                statusText: _visionStatus,
                isProcessing: _isProcessing,
                onScanTap: () => {}, // Continuous scan usually
              ),

              // TAB 2: SETTINGS (Inline simplified)
              _buildSettingsScreen(l10n),
            ],
          ),
          
          // Wake Word Indicator
          if (_wakeWordEnabled && _currentIndex != TAB_SETTINGS)
            Positioned(
              top: 50,
              right: 20,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFF00E676), width: 1),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.mic,
                      color: const Color(0xFF00E676),
                      size: 16,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'Listening',
                      style: TextStyle(
                        color: const Color(0xFF00E676),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
      
      // Floating Recording Button (only on Chat & Vision)
      floatingActionButton: _currentIndex != TAB_SETTINGS ? GestureDetector(
        onTap: _handleVoiceButton,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          height: 70, width: 70,
          decoration: BoxDecoration(
            color: _isRecording ? const Color(0xFFFF2E63) : const Color(0xFF00D4FF),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: (_isRecording ? Colors.red : Theme.of(context).primaryColor).withOpacity(0.5),
                blurRadius: 20
              )
            ]
          ),
          child: Icon(_isRecording ? Icons.stop : Icons.mic, color: Colors.white, size: 32),
        ),
      ) : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,

      bottomNavigationBar: BottomAppBar(
        color: const Color(0xFF121426),
        shape: const CircularNotchedRectangle(),
        notchMargin: 8.0,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            IconButton(
              icon: Icon(Icons.chat_bubble_outline, color: _currentIndex == 0 ? const Color(0xFF00D4FF) : Colors.white38),
              onPressed: () => setState(() => _currentIndex = 0),
              tooltip: l10n.chatMode,
            ),
            const SizedBox(width: 20), // Spacer for FAB
            IconButton(
              icon: Icon(Icons.remove_red_eye_outlined, color: _currentIndex == 1 ? const Color(0xFF00D4FF) : Colors.white38),
              onPressed: () => setState(() => _currentIndex = 1),
              tooltip: l10n.navigatorMode,
            ),
             IconButton(
              icon: Icon(Icons.settings_outlined, color: _currentIndex == 2 ? const Color(0xFF00D4FF) : Colors.white38),
              onPressed: () => setState(() => _currentIndex = 2),
              tooltip: l10n.settings,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingsScreen(AppLocalizations l10n) {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 50),
          Text(l10n.settings, style: Theme.of(context).textTheme.displayMedium),
          const SizedBox(height: 30),
          
          // Language Selector
          Text("Language / Язык", style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: 10),
          GlassContainer(
            child: Column(
              children: [
                ListTile(title: const Text("🇺🇸 English"), onTap: () => widget.onLocaleChange(const Locale('en'))),
                const Divider(height: 1, color: Colors.white24),
                ListTile(title: const Text("🇷🇺 Русский"), onTap: () => widget.onLocaleChange(const Locale('ru'))),
                const Divider(height: 1, color: Colors.white24),
                ListTile(title: const Text("🇰🇬 Кыргызча"), onTap: () => widget.onLocaleChange(const Locale('ky'))),
              ],
            ),
          ),
          
          const SizedBox(height: 30),
          Text(l10n.serverUrl, style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: 10),
          // Server URL Edit logic would go here
           GlassContainer(
             child: ListTile(
               leading: const Icon(Icons.link),
               title: const Text("Server Connection"),
               subtitle: const Text("Configure backend URL"),
               trailing: const Icon(Icons.arrow_forward_ios, size: 16),
               onTap: () {
                 // Add dialog here
               },
             ),
           ),
           
           const SizedBox(height: 30),
           Text("Voice Activation", style: Theme.of(context).textTheme.bodyLarge),
           const SizedBox(height: 10),
           GlassContainer(
             child: SwitchListTile(
               secondary: const Icon(Icons.mic_none),
               title: const Text("\"WayFinder\" Activation"),
               subtitle: Text(_wakeWordEnabled 
                 ? "Listening for 'WayFinder'..." 
                 : "Voice activation disabled"),
               value: _wakeWordEnabled,
               onChanged: (value) => _toggleWakeWord(),
               activeColor: const Color(0xFF00E676),
             ),
           )
        ],
      ),
    );
  }
}
