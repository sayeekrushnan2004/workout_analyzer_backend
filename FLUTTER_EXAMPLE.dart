"""
Example Flutter Integration Code
Save this in your Flutter project as: lib/services/posture_api.dart
"""

# FILE: lib/services/posture_api.dart

import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Main API service for posture analysis
class PostureAPI {
  // IMPORTANT: Replace with your actual server IP address
  // Use ipconfig (Windows) or ifconfig (Mac/Linux) to find your IP
  static const String baseUrl = 'http://192.168.1.X:8000';  // Change X to your actual IP
  
  String? _currentSessionId;
  
  /// Check if API server is reachable
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (e) {
      print('Health check failed: $e');
      return false;
    }
  }
  
  /// Start a new posture monitoring session
  Future<String?> startSession() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/posture/start-session'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _currentSessionId = data['session_id'];
        print('Session started: $_currentSessionId');
        return _currentSessionId;
      }
    } catch (e) {
      print('Error starting session: $e');
    }
    return null;
  }
  
  /// Analyze a single frame from the camera
  Future<PostureResult?> analyzeFrame(File imageFile) async {
    if (_currentSessionId == null) {
      print('No active session. Call startSession() first.');
      return null;
    }
    
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/posture/analyze-frame?session_id=$_currentSessionId'),
      );
      
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );
      
      var streamedResponse = await request.send();
      
      if (streamedResponse.statusCode == 200) {
        final responseData = await streamedResponse.stream.bytesToString();
        final data = jsonDecode(responseData);
        return PostureResult.fromJson(data);
      }
    } catch (e) {
      print('Error analyzing frame: $e');
    }
    return null;
  }
  
  /// Quick analysis without session tracking
  Future<PostureResult?> quickAnalyze(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/posture/quick-analyze'),
      );
      
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );
      
      var streamedResponse = await request.send();
      
      if (streamedResponse.statusCode == 200) {
        final responseData = await streamedResponse.stream.bytesToString();
        final data = jsonDecode(responseData);
        return PostureResult.fromJson(data);
      }
    } catch (e) {
      print('Error in quick analyze: $e');
    }
    return null;
  }
  
  /// Get current session statistics
  Future<SessionStats?> getSessionStatus() async {
    if (_currentSessionId == null) return null;
    
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/posture/session-status/$_currentSessionId'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return SessionStats.fromJson(data['statistics']);
      }
    } catch (e) {
      print('Error getting session status: $e');
    }
    return null;
  }
  
  /// End the current session and save to database
  Future<SessionStats?> endSession() async {
    if (_currentSessionId == null) return null;
    
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/posture/end-session?session_id=$_currentSessionId'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final stats = SessionStats.fromJson(data['session_statistics']);
        _currentSessionId = null;
        return stats;
      }
    } catch (e) {
      print('Error ending session: $e');
    }
    return null;
  }
  
  /// Get posture session history
  Future<List<SessionHistory>> getHistory({int limit = 10}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/posture/history?limit=$limit'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final sessions = data['sessions'] as List;
        return sessions.map((s) => SessionHistory.fromJson(s)).toList();
      }
    } catch (e) {
      print('Error getting history: $e');
    }
    return [];
  }
  
  /// Get overall posture statistics
  Future<OverallStats?> getOverallStatistics() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/posture/statistics'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return OverallStats.fromJson(data['statistics']);
      }
    } catch (e) {
      print('Error getting statistics: $e');
    }
    return null;
  }
  
  bool get hasActiveSession => _currentSessionId != null;
  String? get currentSessionId => _currentSessionId;
}

/// Result from posture analysis
class PostureResult {
  final String postureStatus;
  final int postureScore;
  final bool isGoodPosture;
  final String? annotatedImageBase64;
  final PostureMetrics? metrics;
  final SessionStats? sessionStats;
  
  PostureResult({
    required this.postureStatus,
    required this.postureScore,
    required this.isGoodPosture,
    this.annotatedImageBase64,
    this.metrics,
    this.sessionStats,
  });
  
  factory PostureResult.fromJson(Map<String, dynamic> json) {
    return PostureResult(
      postureStatus: json['posture_status'],
      postureScore: json['posture_score'],
      isGoodPosture: json['is_good_posture'],
      annotatedImageBase64: json['annotated_image'],
      metrics: json['metrics'] != null 
          ? PostureMetrics.fromJson(json['metrics']) 
          : null,
      sessionStats: json['session_stats'] != null 
          ? SessionStats.fromJson(json['session_stats']) 
          : null,
    );
  }
  
  /// Get color for posture status
  int get statusColor {
    if (isGoodPosture) return 0xFF06D6A0; // Green
    if (postureScore > 70) return 0xFFFFA500; // Orange
    return 0xFFEF476F; // Red
  }
}

/// Posture metrics details
class PostureMetrics {
  final double neckAngle;
  final double spineTilt;
  final double shoulderTilt;
  final double noseShoulderDistance;
  
  PostureMetrics({
    required this.neckAngle,
    required this.spineTilt,
    required this.shoulderTilt,
    required this.noseShoulderDistance,
  });
  
  factory PostureMetrics.fromJson(Map<String, dynamic> json) {
    return PostureMetrics(
      neckAngle: (json['neck_angle'] as num).toDouble(),
      spineTilt: (json['spine_tilt'] as num).toDouble(),
      shoulderTilt: (json['shoulder_tilt'] as num).toDouble(),
      noseShoulderDistance: (json['nose_shoulder_distance'] as num).toDouble(),
    );
  }
}

/// Session statistics
class SessionStats {
  final String sessionId;
  final String startTime;
  final double durationSeconds;
  final int totalFrames;
  final int goodFrames;
  final int badFrames;
  final double goodPercent;
  final double badPercent;
  final double averageScore;
  final double longestBadDuration;
  final double currentBadDuration;
  
  SessionStats({
    required this.sessionId,
    required this.startTime,
    required this.durationSeconds,
    required this.totalFrames,
    required this.goodFrames,
    required this.badFrames,
    required this.goodPercent,
    required this.badPercent,
    required this.averageScore,
    required this.longestBadDuration,
    required this.currentBadDuration,
  });
  
  factory SessionStats.fromJson(Map<String, dynamic> json) {
    return SessionStats(
      sessionId: json['session_id'],
      startTime: json['start_time'],
      durationSeconds: (json['duration_seconds'] as num).toDouble(),
      totalFrames: json['total_frames'],
      goodFrames: json['good_frames'],
      badFrames: json['bad_frames'],
      goodPercent: (json['good_percent'] as num).toDouble(),
      badPercent: (json['bad_percent'] as num).toDouble(),
      averageScore: (json['average_score'] as num).toDouble(),
      longestBadDuration: (json['longest_bad_duration'] as num).toDouble(),
      currentBadDuration: (json['current_bad_duration'] as num).toDouble(),
    );
  }
  
  String get formattedDuration {
    final minutes = (durationSeconds / 60).floor();
    final seconds = (durationSeconds % 60).floor();
    return '${minutes}m ${seconds}s';
  }
}

/// Session history item
class SessionHistory {
  final String timestamp;
  final String sessionId;
  final String sessionSeconds;
  final String totalFrames;
  final String goodFrames;
  final String badFrames;
  final String goodPercent;
  final String badPercent;
  final String averageScore;
  final String longestBadSecs;
  
  SessionHistory({
    required this.timestamp,
    required this.sessionId,
    required this.sessionSeconds,
    required this.totalFrames,
    required this.goodFrames,
    required this.badFrames,
    required this.goodPercent,
    required this.badPercent,
    required this.averageScore,
    required this.longestBadSecs,
  });
  
  factory SessionHistory.fromJson(Map<String, dynamic> json) {
    return SessionHistory(
      timestamp: json['timestamp'],
      sessionId: json['session_id'] ?? '',
      sessionSeconds: json['session_seconds'] ?? '0',
      totalFrames: json['total_frames'] ?? '0',
      goodFrames: json['good_frames'] ?? '0',
      badFrames: json['bad_frames'] ?? '0',
      goodPercent: json['good_percent'] ?? '0',
      badPercent: json['bad_percent'] ?? '0',
      averageScore: json['average_score'] ?? '0',
      longestBadSecs: json['longest_bad_secs'] ?? '0',
    );
  }
}

/// Overall statistics
class OverallStats {
  final int totalSessions;
  final double totalDurationSeconds;
  final double averageGoodPercent;
  final double averageBadPercent;
  final double averageScore;
  
  OverallStats({
    required this.totalSessions,
    required this.totalDurationSeconds,
    required this.averageGoodPercent,
    required this.averageBadPercent,
    required this.averageScore,
  });
  
  factory OverallStats.fromJson(Map<String, dynamic> json) {
    return OverallStats(
      totalSessions: json['total_sessions'],
      totalDurationSeconds: (json['total_duration_seconds'] as num).toDouble(),
      averageGoodPercent: (json['average_good_percent'] as num).toDouble(),
      averageBadPercent: (json['average_bad_percent'] as num).toDouble(),
      averageScore: (json['average_score'] as num).toDouble(),
    );
  }
}


# ==============================================================
# USAGE EXAMPLE - Copy to your Flutter widget
# ==============================================================

"""
import 'package:flutter/material.dart';
import 'services/posture_api.dart';
import 'dart:io';

class PostureMonitorScreen extends StatefulWidget {
  @override
  _PostureMonitorScreenState createState() => _PostureMonitorScreenState();
}

class _PostureMonitorScreenState extends State<PostureMonitorScreen> {
  final PostureAPI api = PostureAPI();
  
  String postureStatus = 'Not monitoring';
  int postureScore = 0;
  bool isMonitoring = false;
  SessionStats? currentStats;
  
  @override
  void initState() {
    super.initState();
    checkAPIConnection();
  }
  
  Future<void> checkAPIConnection() async {
    final isHealthy = await api.healthCheck();
    if (!isHealthy) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Cannot connect to API server')),
      );
    }
  }
  
  Future<void> startMonitoring() async {
    final sessionId = await api.startSession();
    if (sessionId != null) {
      setState(() {
        isMonitoring = true;
        postureStatus = 'Monitoring started';
      });
      
      // Start analyzing frames from camera
      // You would integrate with camera package here
    }
  }
  
  Future<void> analyzeFrame(File imageFile) async {
    final result = await api.analyzeFrame(imageFile);
    
    if (result != null) {
      setState(() {
        postureStatus = result.postureStatus;
        postureScore = result.postureScore;
        currentStats = result.sessionStats;
      });
      
      // Show alert if bad posture
      if (!result.isGoodPosture && result.postureScore < 50) {
        _showPostureAlert();
      }
    }
  }
  
  Future<void> stopMonitoring() async {
    final finalStats = await api.endSession();
    
    if (finalStats != null) {
      setState(() {
        isMonitoring = false;
        postureStatus = 'Session ended';
      });
      
      // Show summary
      _showSessionSummary(finalStats);
    }
  }
  
  void _showPostureAlert() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('⚠️ Please correct your posture!'),
        backgroundColor: Colors.red,
      ),
    );
  }
  
  void _showSessionSummary(SessionStats stats) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Session Complete'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Duration: ${stats.formattedDuration}'),
            Text('Good Posture: ${stats.goodPercent.toStringAsFixed(1)}%'),
            Text('Bad Posture: ${stats.badPercent.toStringAsFixed(1)}%'),
            Text('Average Score: ${stats.averageScore.toStringAsFixed(0)}'),
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
    return Scaffold(
      appBar: AppBar(title: Text('Posture Monitor')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              postureStatus,
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 20),
            Text(
              'Score: $postureScore',
              style: TextStyle(fontSize: 48),
            ),
            SizedBox(height: 40),
            if (currentStats != null) ...[
              Text('Good: ${currentStats!.goodPercent.toStringAsFixed(1)}%'),
              Text('Bad: ${currentStats!.badPercent.toStringAsFixed(1)}%'),
            ],
            SizedBox(height: 40),
            ElevatedButton(
              onPressed: isMonitoring ? stopMonitoring : startMonitoring,
              child: Text(isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'),
            ),
          ],
        ),
      ),
    );
  }
}
"""
