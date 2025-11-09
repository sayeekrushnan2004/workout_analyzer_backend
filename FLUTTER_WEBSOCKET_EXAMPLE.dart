"""
Flutter WebSocket Integration for Real-Time Video Posture Analysis
Save as: lib/services/posture_websocket_service.dart
"""

# FILE: lib/services/posture_websocket_service.dart

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:image/image.dart' as img;

/// Real-time posture analysis using WebSocket
/// This allows continuous video frame analysis without HTTP overhead
class PostureWebSocketService {
  // IMPORTANT: Replace with your Render URL or local IP
  // For Render: wss://your-app.onrender.com/ws/posture-stream/
  // For Local: ws://192.168.1.X:8000/ws/posture-stream/
  static const String wsBaseUrl = 'wss://workout-analyzer-backend.onrender.com/ws/posture-stream';
  
  WebSocketChannel? _channel;
  String? _sessionId;
  bool _isConnected = false;
  
  // Stream controllers for real-time updates
  final StreamController<PostureResult> _postureResultController = 
      StreamController<PostureResult>.broadcast();
  final StreamController<SessionStats> _sessionStatsController = 
      StreamController<SessionStats>.broadcast();
  final StreamController<bool> _connectionStatusController = 
      StreamController<bool>.broadcast();
  
  // Public streams
  Stream<PostureResult> get postureResults => _postureResultController.stream;
  Stream<SessionStats> get sessionStats => _sessionStatsController.stream;
  Stream<bool> get connectionStatus => _connectionStatusController.stream;
  
  bool get isConnected => _isConnected;
  String? get sessionId => _sessionId;
  
  /// Connect to WebSocket server
  Future<bool> connect() async {
    try {
      // Generate unique session ID
      _sessionId = 'flutter-${DateTime.now().millisecondsSinceEpoch}';
      
      // Create WebSocket connection
      final wsUrl = '$wsBaseUrl/$_sessionId';
      print('Connecting to: $wsUrl');
      
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      // Listen for messages
      _channel!.stream.listen(
        (message) {
          _handleMessage(message);
        },
        onError: (error) {
          print('WebSocket error: $error');
          _isConnected = false;
          _connectionStatusController.add(false);
        },
        onDone: () {
          print('WebSocket connection closed');
          _isConnected = false;
          _connectionStatusController.add(false);
        },
      );
      
      _isConnected = true;
      _connectionStatusController.add(true);
      
      // Send initial ping to verify connection
      await Future.delayed(Duration(milliseconds: 500));
      sendPing();
      
      return true;
    } catch (e) {
      print('Error connecting to WebSocket: $e');
      _isConnected = false;
      _connectionStatusController.add(false);
      return false;
    }
  }
  
  /// Handle incoming messages from server
  void _handleMessage(dynamic message) {
    try {
      final data = jsonDecode(message);
      
      if (data['status'] == 'success') {
        // Parse posture result
        final result = PostureResult.fromJson(data);
        _postureResultController.add(result);
        
        // Parse session stats if available
        if (data['session_stats'] != null) {
          final stats = SessionStats.fromJson(data['session_stats']);
          _sessionStatsController.add(stats);
        }
      } else if (data['type'] == 'pong') {
        // Heartbeat response
        print('Pong received');
      } else if (data['message'] != null) {
        print('Server message: ${data['message']}');
      }
    } catch (e) {
      print('Error parsing message: $e');
    }
  }
  
  /// Send video frame for analysis
  Future<void> sendFrame(File imageFile) async {
    if (!_isConnected || _channel == null) {
      print('Not connected to WebSocket');
      return;
    }
    
    try {
      // Read image file
      final bytes = await imageFile.readAsBytes();
      
      // Convert to base64
      final base64Image = base64Encode(bytes);
      
      // Send frame
      final message = jsonEncode({
        'type': 'frame',
        'frame': base64Image,
      });
      
      _channel!.sink.add(message);
    } catch (e) {
      print('Error sending frame: $e');
    }
  }
  
  /// Send frame from bytes (for camera stream)
  Future<void> sendFrameBytes(Uint8List imageBytes) async {
    if (!_isConnected || _channel == null) {
      print('Not connected to WebSocket');
      return;
    }
    
    try {
      // Convert to base64
      final base64Image = base64Encode(imageBytes);
      
      // Send frame
      final message = jsonEncode({
        'type': 'frame',
        'frame': base64Image,
      });
      
      _channel!.sink.add(message);
    } catch (e) {
      print('Error sending frame: $e');
    }
  }
  
  /// Send compressed frame (recommended for real-time streaming)
  Future<void> sendCompressedFrame(Uint8List imageBytes, {int quality = 80}) async {
    if (!_isConnected || _channel == null) {
      print('Not connected to WebSocket');
      return;
    }
    
    try {
      // Decode image
      img.Image? image = img.decodeImage(imageBytes);
      
      if (image != null) {
        // Resize to 640x480 for faster processing
        img.Image resized = img.copyResize(image, width: 640, height: 480);
        
        // Compress as JPEG
        List<int> jpeg = img.encodeJpg(resized, quality: quality);
        
        // Convert to base64
        final base64Image = base64Encode(jpeg);
        
        // Send frame
        final message = jsonEncode({
          'type': 'frame',
          'frame': base64Image,
        });
        
        _channel!.sink.add(message);
      }
    } catch (e) {
      print('Error sending compressed frame: $e');
    }
  }
  
  /// Send ping (heartbeat)
  void sendPing() {
    if (!_isConnected || _channel == null) return;
    
    final message = jsonEncode({'type': 'ping'});
    _channel!.sink.add(message);
  }
  
  /// End session and disconnect
  Future<void> endSession() async {
    if (!_isConnected || _channel == null) return;
    
    try {
      // Send end session message
      final message = jsonEncode({'type': 'end_session'});
      _channel!.sink.add(message);
      
      // Wait for response
      await Future.delayed(Duration(seconds: 1));
    } catch (e) {
      print('Error ending session: $e');
    } finally {
      disconnect();
    }
  }
  
  /// Disconnect from WebSocket
  void disconnect() {
    _channel?.sink.close();
    _channel = null;
    _isConnected = false;
    _connectionStatusController.add(false);
  }
  
  /// Dispose resources
  void dispose() {
    disconnect();
    _postureResultController.close();
    _sessionStatsController.close();
    _connectionStatusController.close();
  }
}

/// Posture analysis result
class PostureResult {
  final String postureStatus;
  final int postureScore;
  final bool isGoodPosture;
  final String timestamp;
  final PostureMetrics? metrics;
  
  PostureResult({
    required this.postureStatus,
    required this.postureScore,
    required this.isGoodPosture,
    required this.timestamp,
    this.metrics,
  });
  
  factory PostureResult.fromJson(Map<String, dynamic> json) {
    return PostureResult(
      postureStatus: json['posture_status'] ?? 'Unknown',
      postureScore: json['posture_score'] ?? 0,
      isGoodPosture: json['is_good_posture'] ?? false,
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
      metrics: json['metrics'] != null 
          ? PostureMetrics.fromJson(json['metrics'])
          : null,
    );
  }
  
  int get statusColor {
    if (isGoodPosture) return 0xFF06D6A0; // Green
    if (postureScore > 70) return 0xFFFFA500; // Orange
    return 0xFFEF476F; // Red
  }
}

/// Posture metrics
class PostureMetrics {
  final double neckAngle;
  final double spineTilt;
  final double shoulderTilt;
  
  PostureMetrics({
    required this.neckAngle,
    required this.spineTilt,
    required this.shoulderTilt,
  });
  
  factory PostureMetrics.fromJson(Map<String, dynamic> json) {
    return PostureMetrics(
      neckAngle: (json['neck_angle'] as num?)?.toDouble() ?? 0.0,
      spineTilt: (json['spine_tilt'] as num?)?.toDouble() ?? 0.0,
      shoulderTilt: (json['shoulder_tilt'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

/// Session statistics
class SessionStats {
  final int totalFrames;
  final double goodPercent;
  final double badPercent;
  final double averageScore;
  final double currentBadDuration;
  
  SessionStats({
    required this.totalFrames,
    required this.goodPercent,
    required this.badPercent,
    required this.averageScore,
    required this.currentBadDuration,
  });
  
  factory SessionStats.fromJson(Map<String, dynamic> json) {
    return SessionStats(
      totalFrames: json['total_frames'] ?? 0,
      goodPercent: (json['good_percent'] as num?)?.toDouble() ?? 0.0,
      badPercent: (json['bad_percent'] as num?)?.toDouble() ?? 0.0,
      averageScore: (json['average_score'] as num?)?.toDouble() ?? 0.0,
      currentBadDuration: (json['current_bad_duration'] as num?)?.toDouble() ?? 0.0,
    );
  }
}


# ==============================================================
# USAGE EXAMPLE - Complete Flutter Widget with Camera
# ==============================================================

"""
// Add to pubspec.yaml:
dependencies:
  web_socket_channel: ^2.4.0
  camera: ^0.10.5
  image: ^4.1.3

// Complete example widget:

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'services/posture_websocket_service.dart';

class RealTimePostureScreen extends StatefulWidget {
  @override
  _RealTimePostureScreenState createState() => _RealTimePostureScreenState();
}

class _RealTimePostureScreenState extends State<RealTimePostureScreen> {
  final PostureWebSocketService wsService = PostureWebSocketService();
  
  CameraController? _cameraController;
  bool _isMonitoring = false;
  bool _isConnected = false;
  
  String _postureStatus = 'Not monitoring';
  int _postureScore = 0;
  Color _statusColor = Colors.grey;
  
  double _goodPercent = 0.0;
  double _badPercent = 0.0;
  int _totalFrames = 0;
  
  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _setupWebSocketListeners();
  }
  
  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;
    
    _cameraController = CameraController(
      cameras.first,
      ResolutionPreset.medium,
      enableAudio: false,
    );
    
    await _cameraController!.initialize();
    setState(() {});
  }
  
  void _setupWebSocketListeners() {
    // Listen to posture results
    wsService.postureResults.listen((result) {
      setState(() {
        _postureStatus = result.postureStatus;
        _postureScore = result.postureScore;
        _statusColor = Color(result.statusColor);
      });
      
      // Show alert for bad posture
      if (!result.isGoodPosture && result.postureScore < 50) {
        _showPostureAlert();
      }
    });
    
    // Listen to session stats
    wsService.sessionStats.listen((stats) {
      setState(() {
        _goodPercent = stats.goodPercent;
        _badPercent = stats.badPercent;
        _totalFrames = stats.totalFrames;
      });
    });
    
    // Listen to connection status
    wsService.connectionStatus.listen((connected) {
      setState(() {
        _isConnected = connected;
      });
    });
  }
  
  Future<void> _startMonitoring() async {
    // Connect to WebSocket
    final connected = await wsService.connect();
    
    if (!connected) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to connect to server')),
      );
      return;
    }
    
    setState(() {
      _isMonitoring = true;
    });
    
    // Start sending frames
    _sendFramesPeriodically();
  }
  
  Future<void> _sendFramesPeriodically() async {
    // Send frames at 3 FPS (every 333ms)
    while (_isMonitoring && _isConnected) {
      if (_cameraController != null && _cameraController!.value.isInitialized) {
        try {
          final image = await _cameraController!.takePicture();
          final bytes = await image.readAsBytes();
          
          // Send compressed frame
          await wsService.sendCompressedFrame(bytes, quality: 80);
        } catch (e) {
          print('Error capturing frame: $e');
        }
      }
      
      await Future.delayed(Duration(milliseconds: 333)); // 3 FPS
    }
  }
  
  Future<void> _stopMonitoring() async {
    setState(() {
      _isMonitoring = false;
    });
    
    await wsService.endSession();
    
    // Show summary
    _showSessionSummary();
  }
  
  void _showPostureAlert() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('⚠️ Please correct your posture!'),
        backgroundColor: Colors.red,
        duration: Duration(seconds: 2),
      ),
    );
  }
  
  void _showSessionSummary() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Session Complete'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Total Frames: $_totalFrames'),
            Text('Good Posture: ${_goodPercent.toStringAsFixed(1)}%'),
            Text('Bad Posture: ${_badPercent.toStringAsFixed(1)}%'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return Scaffold(
        appBar: AppBar(title: Text('Real-Time Posture Monitor')),
        body: Center(child: CircularProgressIndicator()),
      );
    }
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Real-Time Posture Monitor'),
        backgroundColor: _statusColor,
      ),
      body: Column(
        children: [
          // Camera preview
          Expanded(
            flex: 3,
            child: CameraPreview(_cameraController!),
          ),
          
          // Status display
          Expanded(
            flex: 2,
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.all(20),
              color: Colors.black87,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    _postureStatus,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: _statusColor,
                    ),
                  ),
                  SizedBox(height: 10),
                  Text(
                    'Score: $_postureScore',
                    style: TextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      Column(
                        children: [
                          Text(
                            'Good',
                            style: TextStyle(color: Colors.green, fontSize: 16),
                          ),
                          Text(
                            '${_goodPercent.toStringAsFixed(1)}%',
                            style: TextStyle(color: Colors.white, fontSize: 20),
                          ),
                        ],
                      ),
                      Column(
                        children: [
                          Text(
                            'Bad',
                            style: TextStyle(color: Colors.red, fontSize: 16),
                          ),
                          Text(
                            '${_badPercent.toStringAsFixed(1)}%',
                            style: TextStyle(color: Colors.white, fontSize: 20),
                          ),
                        ],
                      ),
                      Column(
                        children: [
                          Text(
                            'Frames',
                            style: TextStyle(color: Colors.blue, fontSize: 16),
                          ),
                          Text(
                            '$_totalFrames',
                            style: TextStyle(color: Colors.white, fontSize: 20),
                          ),
                        ],
                      ),
                    ],
                  ),
                  SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed: _isMonitoring ? _stopMonitoring : _startMonitoring,
                    icon: Icon(_isMonitoring ? Icons.stop : Icons.play_arrow),
                    label: Text(_isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _isMonitoring ? Colors.red : Colors.green,
                      padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  @override
  void dispose() {
    _cameraController?.dispose();
    wsService.dispose();
    super.dispose();
  }
}
"""
