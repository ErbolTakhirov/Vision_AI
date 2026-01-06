import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:loading_animation_widget/loading_animation_widget.dart';
import '../widgets/glass_container.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class VisionModeScreen extends StatelessWidget {
  final CameraController? cameraController;
  final String statusText;
  final bool isProcessing;
  final VoidCallback onScanTap;

  const VisionModeScreen({
    super.key,
    required this.cameraController,
    required this.statusText,
    required this.isProcessing,
    required this.onScanTap,
  });

  @override
  Widget build(BuildContext context) {
    if (cameraController == null || !cameraController!.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }

    final l10n = AppLocalizations.of(context)!;

    return Stack(
      fit: StackFit.expand,
      children: [
        // 1. Camera Feed
        CameraPreview(cameraController!),

        // 2. HUD Overlay (Corners)
        _buildCorner(top: 40, left: 20),
        _buildCorner(top: 40, right: 20),
        _buildCorner(bottom: 120, left: 20),
        _buildCorner(bottom: 120, right: 20),

        // 3. Central Scanner Animation (Iron Man style)
        if (isProcessing)
          Center(
             child: LoadingAnimationWidget.twoRotatingArc(
                color: const Color(0xFF00E676), 
                size: 100
             ),
          ),
        
        // 4. Status Panel (Glassmorphism)
        Positioned(
          bottom: 140, 
          left: 20, 
          right: 20,
          child: GlassContainer(
            opacity: 0.15,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                 const Icon(Icons.remove_red_eye, color: Color(0xFF00E676), size: 30),
                 const SizedBox(height: 10),
                 Text(
                   statusText.isEmpty ? l10n.navigatorMode : statusText.toUpperCase(),
                   textAlign: TextAlign.center,
                   style: const TextStyle(
                     color: Colors.white, 
                     fontWeight: FontWeight.w600,
                     letterSpacing: 1.2
                   ),
                 ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCorner({double? top, double? bottom, double? left, double? right}) {
    return Positioned(
      top: top, bottom: bottom, left: left, right: right,
      child: Container(
        width: 40, height: 40,
        decoration: BoxDecoration(
          border: Border(
            top: top != null ? const BorderSide(color: Colors.white54, width: 3) : BorderSide.none,
            bottom: bottom != null ? const BorderSide(color: Colors.white54, width: 3) : BorderSide.none,
            left: left != null ? const BorderSide(color: Colors.white54, width: 3) : BorderSide.none,
            right: right != null ? const BorderSide(color: Colors.white54, width: 3) : BorderSide.none,
          )
        ),
      ),
    );
  }
}
