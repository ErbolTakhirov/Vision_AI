import 'dart:convert';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'package:http/http.dart' as http;
import '../secrets.dart';

class NavigationService {
  Position? _currentPosition;
  List<NavigationStep> _currentRoute = [];
  int _currentStepIndex = 0;
  
  // Get current location
  Future<Position?> getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    // Check if location services are enabled
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      print('Location services are disabled.');
      return null;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        print('Location permissions are denied');
        return null;
      }
    }
    
    if (permission == LocationPermission.deniedForever) {
      print('Location permissions are permanently denied');
      return null;
    }

    _currentPosition = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high
    );
    return _currentPosition;
  }

  // Geocode address to coordinates
  Future<Location?> geocodeAddress(String address) async {
    try {
      List<Location> locations = await locationFromAddress(address);
      if (locations.isNotEmpty) {
        return locations.first;
      }
    } catch (e) {
      print('Geocoding error: $e');
    }
    return null;
  }

  // Build route using OpenRouteService (free alternative to Google)
  // You can also use 2GIS API if you have access
  Future<List<NavigationStep>> buildRoute(String destinationAddress) async {
    try {
      // Get current location
      final currentPos = await getCurrentLocation();
      if (currentPos == null) {
        throw Exception('Cannot get current location');
      }

      // Geocode destination
      final destination = await geocodeAddress(destinationAddress);
      if (destination == null) {
        throw Exception('Cannot find destination: $destinationAddress');
      }

      // For now, we'll use OpenRouteService API (you need to get a free API key)
      // Alternative: Use 2GIS API or Google Directions API
      final apiKey = Secrets.openRouteServiceApiKey;
      
      final url = Uri.parse('https://api.openrouteservice.org/v2/directions/foot-walking');
      
      final response = await http.post(
        url,
        headers: {
          'Authorization': apiKey,
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'coordinates': [
            [currentPos.longitude, currentPos.latitude],
            [destination.longitude, destination.latitude],
          ],
          'instructions': true,
          'language': 'ru',
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final steps = _parseRouteSteps(data);
        _currentRoute = steps;
        _currentStepIndex = 0;
        return steps;
      } else {
        throw Exception('Failed to build route: ${response.statusCode}');
      }
    } catch (e) {
      print('Route building error: $e');
      rethrow;
    }
  }

  List<NavigationStep> _parseRouteSteps(Map<String, dynamic> data) {
    final steps = <NavigationStep>[];
    
    try {
      final route = data['routes'][0];
      final segments = route['segments'] as List;
      
      for (var segment in segments) {
        final stepsList = segment['steps'] as List;
        for (var step in stepsList) {
          steps.add(NavigationStep(
            instruction: step['instruction'] ?? '',
            distance: (step['distance'] ?? 0).toDouble(),
            duration: (step['duration'] ?? 0).toDouble(),
            type: step['type']?.toString() ?? 'straight',
          ));
        }
      }
    } catch (e) {
      print('Error parsing route steps: $e');
    }
    
    return steps;
  }

  // Get current navigation instruction
  String getCurrentInstruction() {
    if (_currentRoute.isEmpty || _currentStepIndex >= _currentRoute.length) {
      return 'Вы прибыли к месту назначения';
    }
    
    final step = _currentRoute[_currentStepIndex];
    return _formatInstruction(step);
  }

  String _formatInstruction(NavigationStep step) {
    final distanceText = step.distance < 100 
      ? '${step.distance.toInt()} метров'
      : '${(step.distance / 1000).toStringAsFixed(1)} километров';
    
    return '${step.instruction}. Расстояние: $distanceText';
  }

  // Move to next step
  void nextStep() {
    if (_currentStepIndex < _currentRoute.length - 1) {
      _currentStepIndex++;
    }
  }

  // Check if we should move to next step based on location
  Future<bool> checkStepProgress() async {
    final currentPos = await getCurrentLocation();
    if (currentPos == null || _currentRoute.isEmpty) return false;
    
    // Simple distance-based check
    // In production, you'd want more sophisticated logic
    final step = _currentRoute[_currentStepIndex];
    
    // If we've traveled the step distance, move to next
    // This is simplified - you'd want to track actual progress
    return false; // Implement proper logic here
  }

  // Listen to location updates for turn-by-turn navigation
  Stream<Position> getLocationStream() {
    return Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    );
  }

  void reset() {
    _currentRoute = [];
    _currentStepIndex = 0;
  }

  List<NavigationStep> get currentRoute => _currentRoute;
  int get currentStepIndex => _currentStepIndex;
}

class NavigationStep {
  final String instruction;
  final double distance;
  final double duration;
  final String type;

  NavigationStep({
    required this.instruction,
    required this.distance,
    required this.duration,
    required this.type,
  });
}
