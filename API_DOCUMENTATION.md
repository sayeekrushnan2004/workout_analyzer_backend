# Workout Analyzer Backend - Real-Time Posture Analysis API

A FastAPI backend for real-time posture analysis using MediaPipe. This API can be integrated with Flutter or any frontend application to provide comprehensive posture monitoring and analysis.

## Features

- 🎯 **Real-time Posture Analysis**: Analyze posture from video frames
- 📊 **Session Tracking**: Track posture metrics across sessions
- 💾 **Data Persistence**: Store session history in CSV format
- 📈 **Statistics & Analytics**: Get comprehensive posture statistics
- 🔥 **Multiple Detection Types**: 
  - Good Posture
  - Slouching (Slight/Severe)
  - Leaning (Left/Right/Forward/Backward)
  - Bad Posture
- 🎨 **Visual Feedback**: Annotated images with pose landmarks
- 📱 **Mobile Ready**: CORS-enabled for Flutter/mobile apps

## Installation

### 1. Clone the repository
```bash
cd "c:\Users\sayee\Downloads\posture backend\workout_analyzer_backend"
```

### 2. Create virtual environment (optional but recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the server
```powershell
python app.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Start Posture Session
**POST** `/posture/start-session`

Start a new posture analysis session. Returns a session ID to use for frame analysis.

**Response:**
```json
{
  "status": "success",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Posture session started successfully",
  "start_time": "2025-11-09T10:30:00.000000"
}
```

---

### 3. Analyze Posture Frame
**POST** `/posture/analyze-frame`

Analyze a single video frame for posture.

**Parameters:**
- `session_id` (query): Active session identifier
- `file` (form-data): Image file (JPG/PNG)
- `draw_landmarks` (query, optional): Draw pose landmarks (default: true)

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/posture/analyze-frame?session_id=YOUR_SESSION_ID&draw_landmarks=true" \
  -F "file=@frame.jpg"
```

**Response:**
```json
{
  "status": "success",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "posture_status": "Good Posture",
  "posture_score": 95,
  "is_good_posture": true,
  "annotated_image": "base64_encoded_image_string...",
  "metrics": {
    "neck_angle": 176.5,
    "spine_tilt": 5.2,
    "shoulder_tilt": 3.1,
    "nose_shoulder_distance": 165.8
  },
  "landmarks": [...],
  "session_stats": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": "2025-11-09T10:30:00.000000",
    "duration_seconds": 45.67,
    "total_frames": 137,
    "good_frames": 98,
    "bad_frames": 39,
    "good_percent": 71.53,
    "bad_percent": 28.47,
    "average_score": 82.5,
    "longest_bad_duration": 5.2,
    "current_bad_duration": 0
  }
}
```

**Posture Status Values:**
- `"Good Posture"` - Ideal posture
- `"Bad Posture"` - Generic poor posture
- `"Slightly Slouched"` - Minor slouching
- `"Severely Slouched"` - Major slouching
- `"Leaning Left"` - Tilting left
- `"Leaning Right"` - Tilting right
- `"Severe Lean Left"` - Severe left tilt
- `"Severe Lean Right"` - Severe right tilt
- `"Leaning Forward"` - Forward lean
- `"Leaning Backward"` - Backward lean
- `"No person detected"` - No pose detected

---

### 4. End Posture Session
**POST** `/posture/end-session`

End an active session and save to database.

**Parameters:**
- `session_id` (query): Session identifier

**Response:**
```json
{
  "status": "success",
  "message": "Session ended and saved successfully",
  "session_statistics": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": "2025-11-09T10:30:00.000000",
    "end_time": "2025-11-09T10:35:00.000000",
    "duration_seconds": 300.0,
    "total_frames": 900,
    "good_frames": 650,
    "bad_frames": 250,
    "good_percent": 72.22,
    "bad_percent": 27.78,
    "average_score": 85.5,
    "longest_bad_duration": 8.5
  },
  "saved_to_database": true
}
```

---

### 5. Get Session Status
**GET** `/posture/session-status/{session_id}`

Get current statistics for an active session.

**Response:**
```json
{
  "status": "success",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": true,
  "statistics": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": "2025-11-09T10:30:00.000000",
    "duration_seconds": 45.67,
    "total_frames": 137,
    "good_frames": 98,
    "bad_frames": 39,
    "good_percent": 71.53,
    "bad_percent": 28.47,
    "average_score": 82.5,
    "longest_bad_duration": 5.2,
    "current_bad_duration": 0
  }
}
```

---

### 6. Get Posture History
**GET** `/posture/history`

Get recent posture session history.

**Parameters:**
- `limit` (query, optional): Number of sessions to return (default: 10)

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "sessions": [
    {
      "timestamp": "2025-11-08T14:47:37.786901",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_seconds": "31",
      "total_frames": "930",
      "good_frames": "534",
      "bad_frames": "396",
      "good_percent": "57.47",
      "bad_percent": "42.53",
      "average_score": "78.2",
      "longest_bad_secs": "8"
    }
  ]
}
```

---

### 7. Get Overall Statistics
**GET** `/posture/statistics`

Get aggregate statistics from all sessions.

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_sessions": 60,
    "total_duration_seconds": 1845.0,
    "average_good_percent": 45.62,
    "average_bad_percent": 54.38,
    "average_score": 72.5
  }
}
```

---

### 8. Get Active Sessions
**GET** `/posture/active-sessions`

Get all currently active posture sessions.

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "active_sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "statistics": {
        "duration_seconds": 45.67,
        "total_frames": 137,
        "good_percent": 71.53,
        "bad_percent": 28.47
      }
    }
  ]
}
```

---

### 9. Delete Session
**DELETE** `/posture/session/{session_id}`

Delete a session from history.

**Response:**
```json
{
  "status": "success",
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

---

### 10. Quick Posture Analysis
**POST** `/posture/quick-analyze`

Quick one-time posture analysis without session tracking. Perfect for single image analysis.

**Parameters:**
- `file` (form-data): Image file (JPG/PNG)
- `draw_landmarks` (query, optional): Draw pose landmarks (default: true)

**Response:**
```json
{
  "status": "success",
  "posture_status": "Good Posture",
  "posture_score": 92,
  "is_good_posture": true,
  "annotated_image": "base64_encoded_image_string...",
  "metrics": {
    "neck_angle": 177.2,
    "spine_tilt": 4.8,
    "shoulder_tilt": 2.9,
    "nose_shoulder_distance": 168.3
  }
}
```

---

### 11. Analyze Pose (Original Endpoint)
**POST** `/analyze-pose`

Original workout pose detection endpoint (maintained for backward compatibility).

---

## Flutter Integration Example

### 1. Add HTTP package
```yaml
dependencies:
  http: ^1.1.0
```

### 2. Sample Dart Code

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class PostureAnalyzerAPI {
  static const String baseUrl = 'http://YOUR_SERVER_IP:8000';
  
  // Start a posture session
  Future<String?> startSession() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/posture/start-session'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['session_id'];
      }
    } catch (e) {
      print('Error starting session: $e');
    }
    return null;
  }
  
  // Analyze a frame
  Future<Map<String, dynamic>?> analyzeFrame(
    String sessionId, 
    File imageFile
  ) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/posture/analyze-frame?session_id=$sessionId'),
      );
      
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path)
      );
      
      var response = await request.send();
      
      if (response.statusCode == 200) {
        final responseData = await response.stream.bytesToString();
        return jsonDecode(responseData);
      }
    } catch (e) {
      print('Error analyzing frame: $e');
    }
    return null;
  }
  
  // End session
  Future<Map<String, dynamic>?> endSession(String sessionId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/posture/end-session?session_id=$sessionId'),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error ending session: $e');
    }
    return null;
  }
  
  // Get history
  Future<List<dynamic>?> getHistory({int limit = 10}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/posture/history?limit=$limit'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['sessions'];
      }
    } catch (e) {
      print('Error getting history: $e');
    }
    return null;
  }
}
```

### 3. Example Usage

```dart
// In your widget
final api = PostureAnalyzerAPI();
String? sessionId;

// Start session
void startPostureSession() async {
  sessionId = await api.startSession();
  print('Session started: $sessionId');
}

// Analyze camera frame
void analyzeCurrentFrame(File imageFile) async {
  if (sessionId != null) {
    final result = await api.analyzeFrame(sessionId!, imageFile);
    
    if (result != null) {
      setState(() {
        postureStatus = result['posture_status'];
        postureScore = result['posture_score'];
        isGoodPosture = result['is_good_posture'];
        
        // Display annotated image
        String base64Image = result['annotated_image'];
        annotatedImage = base64Decode(base64Image);
      });
    }
  }
}

// End session
void endPostureSession() async {
  if (sessionId != null) {
    final stats = await api.endSession(sessionId!);
    print('Final statistics: $stats');
    sessionId = null;
  }
}
```

## Database Structure

Sessions are stored in `posture_sessions.csv` with the following fields:

| Field | Description |
|-------|-------------|
| timestamp | ISO 8601 timestamp when session ended |
| session_id | Unique session identifier (UUID) |
| session_seconds | Total session duration in seconds |
| total_frames | Total frames analyzed |
| good_frames | Frames with good posture |
| bad_frames | Frames with bad posture |
| good_percent | Percentage of good posture frames |
| bad_percent | Percentage of bad posture frames |
| average_score | Average posture score (0-100) |
| longest_bad_secs | Longest continuous bad posture duration |

## Posture Detection Logic

### Metrics Calculated:
1. **Neck Angle**: Angle between nose, neck, and hip
2. **Spine Tilt**: Horizontal deviation between neck and hip
3. **Shoulder Tilt**: Vertical difference between shoulders
4. **Nose-Shoulder Distance**: Vertical distance for forward/backward lean

### Thresholds:
- Neck angle: 175° (ideal)
- Spine tilt: < 10 pixels
- Shoulder tilt: < 10 pixels
- Lean threshold: 30 pixels
- Head drop: 60 pixels

### Posture Score (0-100):
- Starts at 100
- Deductions based on deviations from ideal metrics
- Higher score = Better posture

## Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid image, etc.)
- `404`: Resource not found (invalid session ID)
- `500`: Internal server error

## Development Tips

### Testing with Postman/Insomnia:
1. Start session → Get session_id
2. Upload frames using session_id
3. Check stats periodically
4. End session when done

### Performance Considerations:
- Send frames at 3-5 FPS for real-time analysis
- Reduce image size for faster upload (640x480 recommended)
- Use JPEG compression for smaller payloads

### Production Deployment:
- Update CORS origins in `app.py` to your domain
- Use HTTPS for secure transmission
- Consider rate limiting for API endpoints
- Set up proper logging and monitoring

## Troubleshooting

### "Session not found" error:
- Ensure you called `/posture/start-session` first
- Session IDs are case-sensitive
- Sessions are stored in memory and cleared on server restart

### "No person detected":
- Ensure person is fully visible in frame
- Check lighting conditions
- Verify image is not corrupted

### Low posture scores:
- Check camera angle (should capture full upper body)
- Ensure proper lighting
- Verify person is centered in frame

## License

MIT License

## Support

For issues or questions, please open an issue on the repository.
