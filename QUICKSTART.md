# Quick Start Guide - Posture Analysis API

This guide will help you quickly set up and start using the Posture Analysis API.

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies
```powershell
cd "c:\Users\sayee\Downloads\posture backend\workout_analyzer_backend"
pip install -r requirements.txt
```

### Step 2: Start the Server
```powershell
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test the API
Open a new PowerShell window:
```powershell
python test_api.py
```

### Step 4: View API Documentation
Open your browser and visit:
```
http://localhost:8000/docs
```

## 📱 Flutter Integration (Quick Example)

### 1. Basic Setup
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class PostureAPI {
  final String baseUrl = 'http://YOUR_IP:8000';
  String? sessionId;
  
  Future<void> startSession() async {
    final response = await http.post(
      Uri.parse('$baseUrl/posture/start-session')
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      sessionId = data['session_id'];
    }
  }
  
  Future<Map<String, dynamic>?> analyzeFrame(File image) async {
    if (sessionId == null) return null;
    
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/posture/analyze-frame?session_id=$sessionId')
    );
    
    request.files.add(await http.MultipartFile.fromPath('file', image.path));
    
    var response = await request.send();
    if (response.statusCode == 200) {
      final data = await response.stream.bytesToString();
      return jsonDecode(data);
    }
    return null;
  }
}
```

### 2. Usage in Widget
```dart
final api = PostureAPI();

// In your build method
ElevatedButton(
  onPressed: () async {
    await api.startSession();
    // Start camera and send frames
  },
  child: Text('Start Posture Analysis')
)
```

## 🔥 Most Common Use Cases

### Use Case 1: Single Image Analysis
**Endpoint:** `POST /posture/quick-analyze`

```python
import requests

with open('person.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/posture/quick-analyze',
        files={'file': f}
    )
    
result = response.json()
print(f"Posture: {result['posture_status']}")
print(f"Score: {result['posture_score']}")
```

### Use Case 2: Real-Time Video Analysis
**Flow:** Start Session → Analyze Frames → End Session

```python
import requests
import cv2

# 1. Start session
response = requests.post('http://localhost:8000/posture/start-session')
session_id = response.json()['session_id']

# 2. Analyze video frames
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Save frame temporarily
    cv2.imwrite('temp.jpg', frame)
    
    # Send to API
    with open('temp.jpg', 'rb') as f:
        response = requests.post(
            f'http://localhost:8000/posture/analyze-frame?session_id={session_id}',
            files={'file': f}
        )
        result = response.json()
        
        # Display result
        print(f"Posture: {result['posture_status']} - Score: {result['posture_score']}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 3. End session
response = requests.post(
    f'http://localhost:8000/posture/end-session?session_id={session_id}'
)
stats = response.json()
print(f"Session complete: {stats['session_statistics']}")
```

### Use Case 3: View History
```python
import requests

response = requests.get('http://localhost:8000/posture/history?limit=10')
history = response.json()

for session in history['sessions']:
    print(f"Date: {session['timestamp']}")
    print(f"Duration: {session['session_seconds']}s")
    print(f"Good posture: {session['good_percent']}%")
    print("---")
```

## 🎯 API Endpoints Cheat Sheet

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check if server is running |
| `/posture/start-session` | POST | Start a new session |
| `/posture/analyze-frame` | POST | Analyze a video frame |
| `/posture/end-session` | POST | End session and save data |
| `/posture/quick-analyze` | POST | One-time image analysis |
| `/posture/history` | GET | Get past sessions |
| `/posture/statistics` | GET | Get overall stats |
| `/posture/active-sessions` | GET | List active sessions |

## 🎨 Response Example

```json
{
  "status": "success",
  "posture_status": "Good Posture",
  "posture_score": 92,
  "is_good_posture": true,
  "metrics": {
    "neck_angle": 177.2,
    "spine_tilt": 4.8,
    "shoulder_tilt": 2.9,
    "nose_shoulder_distance": 168.3
  },
  "session_stats": {
    "good_percent": 75.5,
    "bad_percent": 24.5,
    "average_score": 85.3
  }
}
```

## 🔧 Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process if needed
taskkill /PID <PID> /F
```

### "No person detected"
- Ensure person is fully visible in frame
- Check lighting
- Make sure camera/image quality is good

### Connection refused from Flutter
- Replace `localhost` with your computer's IP address
- Make sure firewall allows port 8000
- Use `ipconfig` to find your IP

```dart
// Instead of:
final baseUrl = 'http://localhost:8000';

// Use:
final baseUrl = 'http://192.168.1.X:8000';  // Your actual IP
```

## 📊 Understanding Posture Status

| Status | Meaning | Score Range |
|--------|---------|-------------|
| Good Posture | Perfect alignment | 85-100 |
| Bad Posture | Poor alignment | 40-84 |
| Slightly Slouched | Minor forward bend | 50-75 |
| Severely Slouched | Major forward bend | 0-50 |
| Leaning Left/Right | Sideways tilt | 60-80 |
| Leaning Forward/Backward | Front/back lean | 50-75 |

## 🎓 Next Steps

1. **Read Full Documentation**: See `API_DOCUMENTATION.md`
2. **Customize Thresholds**: Edit `posture_analysis.py` constants
3. **Add Alerts**: Implement notification system in your app
4. **Data Visualization**: Create charts from session history
5. **Production Deployment**: Set up HTTPS and proper CORS

## 💡 Tips for Best Results

1. **Frame Rate**: Send 3-5 frames per second (not every frame)
2. **Image Size**: 640x480 is optimal
3. **Lighting**: Ensure good, even lighting
4. **Camera Position**: Place camera at chest height, 2-3 feet away
5. **Background**: Plain background works best

## 📞 Need Help?

- Check logs: The server prints detailed logs to console
- API docs: `http://localhost:8000/docs`
- Test script: Run `python test_api.py` to diagnose issues

---

**Ready to integrate?** Start with `/posture/quick-analyze` for testing, then move to session-based tracking for production!
