import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';

import 'theme/app_theme.dart';
import 'services/vision_api.dart';
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
      title: 'Vision AI Pro',
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

class _MainNavScreenState extends State<MainNavScreen> {
  // Services
  final _api = VisionApiService();
  CameraController? _cameraController;
  final _audioRecorder = AudioRecorder();
  final _audioPlayer = AudioPlayer();

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
    _initHardware();
    _addInitialMessage();
  }

  void _addInitialMessage() {
     _messages.add(ChatMessage(
       text: "Ready to help. Press the mic to speak or use Vison Mode.", 
       isUser: false, 
       timestamp: DateTime.now()
     ));
  }

  Future<void> _initHardware() async {
    await [Permission.camera, Permission.microphone].request();
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      _cameraController = CameraController(cameras.first, ResolutionPreset.medium, enableAudio: false);
      await _cameraController!.initialize();
      setState(() {});
    }
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
        await _audioRecorder.start(const RecordConfig(), path: path);
        setState(() { _isRecording = true; });
      }
    }
  }

  Future<void> _handleTextSubmit(String text) async {
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true, timestamp: DateTime.now()));
      _isProcessing = true;
    });
    await _processRequest(text: text, mode: 'chat');
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
         final bytes = base64Decode(audioB64);
         final dir = await getTemporaryDirectory();
         final file = File('${dir.path}/response.mp3');
         await file.writeAsBytes(bytes);
         await _audioPlayer.play(DeviceFileSource(file.path));
      }

    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: "Error: $e", isUser: false, timestamp: DateTime.now()));
      });
    } finally {
      setState(() { _isProcessing = false; });
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
      body: IndexedStack(
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
      
      // Floating Recording Button (only on Chat & Vision)
      floatingActionButton: _currentIndex != TAB_SETTINGS ? GestureDetector(
        onTap: _handleVoiceButton,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          height: 70, width: 70,
          decoration: BoxDecoration(
            color: _isRecording ? Colors.redAccent : Theme.of(context).primaryColor,
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
        color: const Color(0xFF1E1E24),
        shape: const CircularNotchedRectangle(),
        notchMargin: 8.0,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            IconButton(
              icon: Icon(Icons.chat_bubble_outline, color: _currentIndex == 0 ? Colors.white : Colors.grey),
              onPressed: () => setState(() => _currentIndex = 0),
              tooltip: l10n.chatMode,
            ),
            const SizedBox(width: 20), // Spacer for FAB
            IconButton(
              icon: Icon(Icons.remove_red_eye_outlined, color: _currentIndex == 1 ? const Color(0xFF00E676) : Colors.grey),
              onPressed: () => setState(() => _currentIndex = 1),
              tooltip: l10n.navigatorMode,
            ),
             IconButton(
              icon: Icon(Icons.settings_outlined, color: _currentIndex == 2 ? Colors.white : Colors.grey),
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
           )
        ],
      ),
    );
  }
}
