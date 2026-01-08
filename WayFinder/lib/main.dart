import 'dart:convert';
import 'dart:io';
import 'dart:math';
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
import 'services/porcupine_service.dart';
import 'services/navigation_service.dart';
import 'services/chat_history_service.dart';
import 'screens/chat_screen.dart';
import 'screens/vision_mode.dart';
import 'widgets/glass_container.dart';

import 'services/auth_service.dart';
import 'screens/login_screen.dart';

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
      initialRoute: '/',
      routes: {
        '/': (context) => const AuthWrapper(),
        '/login': (context) => const LoginScreen(),
        '/home': (context) => MainNavScreen(onLocaleChange: setLocale),
      },
    );
  }
}

// Authentication Wrapper
class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: AuthService().isAuthenticated(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        
        // For now, skip auth and go directly to home
        // Change to: snapshot.data == true ? MainNavScreen(...) : LoginScreen()
        // when you want to enforce authentication
        return MainNavScreen(onLocaleChange: (Locale l) {
          // Access parent state through context if needed
        });
      },
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
  late PorcupineWakeWordService _porcupineService;
  final _navigationService = NavigationService();
  final _chatHistory = ChatHistoryService();
  CameraController? _cameraController;
  final _audioRecorder = AudioRecorder();
  final _audioPlayer = AudioPlayer();
  bool _wakeWordEnabled = true;
  bool _isNavigating = false;

  // State
  int _currentIndex = 0;
  bool _isRecording = false;
  bool _isProcessing = false;
  List<ChatMessage> _messages = [];
  String _visionStatus = "";
  
  static const int TAB_CHAT = 0;
  static const int TAB_VISION = 1;
  static const int TAB_SETTINGS = 2;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    
    _initHardware();
    _loadChatHistory();
    
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
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      _cameraController?.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initCamera();
      // Restart wake word on resume if enabled
      if (_wakeWordEnabled && !_isRecording && !_isProcessing) {
        _porcupineService.startListening();
      }
    } else if (state == AppLifecycleState.paused) {
      _porcupineService.stopListening();
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
        if (mounted) setState(() {});
      } catch (e) {
        print('Camera error: $e');
      }
    }
  }

  Future<void> _loadChatHistory() async {
    final history = await _chatHistory.loadHistory();
    if (history.isEmpty) {
      _addInitialMessage();
    } else {
      setState(() {
        _messages = history;
      });
    }
  }

  void _addInitialMessage() {
     final msg = ChatMessage(
       text: "Привет! Я WayFinder, ваш голосовой помощник. Скажите 'WayFinder' и задайте вопрос, или нажмите кнопку микрофона.", 
       isUser: false, 
       timestamp: DateTime.now()
     );
     setState(() {
       _messages.add(msg);
     });
     _chatHistory.saveHistory(_messages);
  }

  Future<void> _clearChatHistory() async {
    await _chatHistory.clearHistory();
    setState(() {
      _messages.clear();
    });
    _addInitialMessage();
  }

  Future<void> _initHardware() async {
    await [Permission.camera, Permission.microphone, Permission.location].request();
    // Re-init camera logic...
    await _initCamera();
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
      // 1. Stop Wake Word Listener
      await _porcupineService.stopListening();
      
      // 2. HAPTIC FEEDBACK - Premium vibration pattern
      try {
        // Triple vibration pattern for wake word confirmation
        await Future.delayed(Duration.zero);
        // Note: Add vibration package if needed: vibration: ^1.8.4
        // await Vibration.vibrate(duration: 50);
        // await Future.delayed(const Duration(milliseconds: 100));
        // await Vibration.vibrate(duration: 50);
      } catch (e) {
        print("Haptic not available: $e");
      }

      // 3. Visual Feedback - Show wake word detected animation
      setState(() { _isProcessing = true; });

      // 4. Start Recording immediately
      if (await _audioRecorder.hasPermission()) {
        final dir = await getTemporaryDirectory();
        final path = '${dir.path}/query.m4a';
        await _audioPlayer.stop();

        await _audioRecorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
        
        setState(() { 
          _isRecording = true; 
          _isProcessing = false;
        });
        
        // Auto-stop recording after 5 seconds
        Future.delayed(const Duration(seconds: 5), () {
           if (_isRecording) {
             _handleVoiceButton();
           }
        });
      }
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
      // STOP & SEND
      final path = await _audioRecorder.stop();
      setState(() { _isRecording = false; _isProcessing = true; });
      if (path != null) {
         // Analyze Request
         await _processRequest(audioPath: path, mode: 'chat');
      } else {
         setState(() { _isProcessing = false; });
      }
    } else {
      // START RECORDING MANUALLY
      if (await _audioRecorder.hasPermission()) {
        await _porcupineService.stopListening(); // Pause wake word
        final dir = await getTemporaryDirectory();
        final path = '${dir.path}/query.m4a';
        await _audioPlayer.stop();
        await _audioRecorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
        setState(() { _isRecording = true; });
      }
    }
  }

  Future<void> _handleTextSubmit(String text) async {
    final userMsg = ChatMessage(text: text, isUser: true, timestamp: DateTime.now());
    setState(() {
      _messages.add(userMsg);
      _isProcessing = true;
    });
    await _chatHistory.saveHistory(_messages);
    
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
      final position = await _navigationService.getCurrentLocation();
      final result = await _api.requestNavigation(
        audioPath,
        text,
        currentLat: position?.latitude,
        currentLon: position?.longitude,
      );
      
      final message = result['message'];
      final audioB64 = result['audio'];
      
      final aiMsg = ChatMessage(text: message, isUser: false, timestamp: DateTime.now());
      setState(() {
        _messages.add(aiMsg);
        _isProcessing = false;
      });
      await _chatHistory.saveHistory(_messages);

      if (audioB64 != null) {
         _playAudioResponse(audioB64);
      }
      
    } catch (e) {
      final errorMsg = ChatMessage(text: "Ошибка: $e", isUser: false, timestamp: DateTime.now());
      setState(() {
        _messages.add(errorMsg);
        _isProcessing = false;
      });
      await _chatHistory.saveHistory(_messages);
    }
  }

  Future<void> _buildAndStartNavigation(String destination) async {
      // ... existing nav logic ...
  }

  void _startTurnByTurnGuidance() {
     // ... existing nav logic ...
  }

  Future<List<int>?> _generateTTS(String text) async {
    return null;
  }

  Future<void> _processRequest({String? audioPath, String text = '', required String mode}) async {
    try {
      XFile? image;
      if (_cameraController != null && _cameraController!.value.isInitialized) {
        try {
          image = await _cameraController!.takePicture();
        } catch (_) {} 
      }

      final result = await _api.smartAnalyze(image, audioPath, mode: mode, text: text);
      
      final msg = result['message'];
      final audioB64 = result['audio'];
      final debugVision = result['debug_vision'];

      if (!mounted) return;

      final aiMsg = ChatMessage(text: msg, isUser: false, timestamp: DateTime.now());
      setState(() {
        if (mode == 'chat') {
           _messages.add(aiMsg);
        } else {
           _visionStatus = msg;
        }
        _isProcessing = false;
      });
      
      if (mode == 'chat') {
        await _chatHistory.saveHistory(_messages);
      }

      if (audioB64 != null) {
        await _playAudioResponse(audioB64);
      }

    } catch (e) {
      if (mounted) {
        final errorMsg = ChatMessage(text: "Ошибка: $e", isUser: false, timestamp: DateTime.now());
        setState(() {
          _messages.add(errorMsg);
          _isProcessing = false;
        });
        await _chatHistory.saveHistory(_messages);
      }
    } finally {
      if (mounted) {
          setState(() { _isProcessing = false; });
          if (_wakeWordEnabled && !_isRecording) {
            _porcupineService.startListening();
          }
      }
    }
  }
  
  Future<void> _playAudioResponse(String audioB64) async {
     try {
       final bytes = base64Decode(audioB64);
       final dir = await getTemporaryDirectory();
       final file = File('${dir.path}/response.mp3');
       await file.writeAsBytes(bytes);
       await _audioPlayer.play(DeviceFileSource(file.path));
     } catch (e) {
       print("Audio play error: $e");
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
          
          // Animated Wake Word Indicator
          if (_wakeWordEnabled && _currentIndex != TAB_SETTINGS)
            Positioned(
              top: 50,
              right: 20,
              child: TweenAnimationBuilder<double>(
                duration: const Duration(milliseconds: 1500),
                tween: Tween(begin: 0.0, end: 1.0),
                curve: Curves.easeInOut,
                builder: (context, value, child) {
                  final pulseValue = (value * 2 * 3.14159);
                  final scale = 1.0 + (0.1 * (1 + sin(pulseValue)));
                  final opacity = 0.6 + (0.4 * (1 + sin(pulseValue)));
                  
                  return Transform.scale(
                    scale: scale,
                    child: Opacity(
                      opacity: opacity,
                      child: child,
                    ),
                  );
                },
                onEnd: () {
                  // Repeat animation
                  if (mounted && _wakeWordEnabled) {
                    setState(() {});
                  }
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        const Color(0xFF00E676).withOpacity(0.3),
                        const Color(0xFF00E676).withOpacity(0.1),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF00E676), width: 2),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF00E676).withOpacity(0.5),
                        blurRadius: 12,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: Color(0xFF00E676),
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Color(0xFF00E676),
                              blurRadius: 8,
                              spreadRadius: 2,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Text(
                        'LISTENING',
                        style: TextStyle(
                          color: Color(0xFF00E676),
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ],
                  ),
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
            borderRadius: BorderRadius.circular(_isRecording ? 8 : 35), // Square when recording
            boxShadow: [
              BoxShadow(
                color: (_isRecording ? Colors.red : Theme.of(context).primaryColor).withOpacity(0.5),
                blurRadius: 20,
                spreadRadius: _isRecording ? 3 : 0
              )
            ]
          ),
          child: Icon(_isRecording ? Icons.stop_rounded : Icons.mic, color: Colors.white, size: 32),
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
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 50),
            Text(l10n.settings, style: Theme.of(context).textTheme.displayMedium),
            const SizedBox(height: 30),
            
            // User Profile Section
            FutureBuilder<Map<String, dynamic>?>(
              future: AuthService().getProfile(),
              builder: (context, snapshot) {
                if (snapshot.hasData && snapshot.data != null) {
                  final user = snapshot.data!;
                  return GlassContainer(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 30,
                            backgroundColor: const Color(0xFF00D4FF),
                            child: Text(
                              user['username']?.toString().substring(0, 1).toUpperCase() ?? 'U',
                              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  user['username'] ?? 'User',
                                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                                ),
                                Text(
                                  user['email'] ?? '',
                                  style: const TextStyle(fontSize: 14, color: Colors.white70),
                                ),
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF00E676).withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    (user['subscription_type'] ?? 'free').toString().toUpperCase(),
                                    style: const TextStyle(fontSize: 10, color: Color(0xFF00E676), fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.logout, color: Colors.redAccent),
                            onPressed: () async {
                              await AuthService().logout();
                              if (mounted) Navigator.of(context).pushReplacementNamed('/login');
                            },
                          ),
                        ],
                      ),
                    ),
                  );
                }
                return GlassContainer(
                  child: ListTile(
                    leading: const Icon(Icons.login, color: Color(0xFF00D4FF)),
                    title: const Text('Sign In'),
                    subtitle: const Text('Get unlimited access'),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                    onTap: () => Navigator.of(context).pushNamed('/login'),
                  ),
                );
              },
            ),
            
            const SizedBox(height: 30),
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
            ),
            
            const SizedBox(height: 30),
            Text("Chat History", style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 10),
            GlassContainer(
              child: ListTile(
                leading: const Icon(Icons.delete_outline, color: Colors.redAccent),
                title: const Text("Clear Chat History"),
                subtitle: Text("${_messages.length} messages stored"),
                trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                onTap: () async {
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (context) => AlertDialog(
                      backgroundColor: const Color(0xFF1E1E24),
                      title: const Text("Clear History?", style: TextStyle(color: Colors.white)),
                      content: const Text("This will delete all chat messages.", style: TextStyle(color: Colors.white70)),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text("Cancel"),
                        ),
                        TextButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const Text("Clear", style: TextStyle(color: Colors.redAccent)),
                        ),
                      ],
                    ),
                  );
                  if (confirm == true) {
                    await _clearChatHistory();
                  }
                },
              ),
            ),
            const SizedBox(height: 100), // Bottom padding for scroll
          ],
        ),
      ),
    );
  }
}
