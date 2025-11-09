# 🚀 Render Deployment Guide

## Issues Fixed ✅

1. **MediaPipe version error** - Changed to 0.10.9 and opencv-python-headless
2. **Video streaming** - Added WebSocket support for real-time video analysis

---

## Deploy to Render

### Step 1: Push to GitHub

```powershell
cd "c:\Users\sayee\Downloads\posture backend\workout_analyzer_backend"

# Initialize git if not already done
git init
git add .
git commit -m "Added WebSocket support for real-time posture analysis"

# Push to your GitHub repo
git remote add origin https://github.com/NAVEENRAJ2004/workout_analyzer_backend.git
git branch -M main
git push -u origin main --force
```

### Step 2: Render Configuration

Your Render should automatically detect the changes. If not:

1. Go to https://render.com
2. Click on your service: `workout-analyzer-backend`
3. Click "Manual Deploy" → "Deploy latest commit"

### Build Command:
```bash
pip install -r requirements.txt
```

### Start Command:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

---

## Important URLs

After deployment, your API will be available at:

**REST API:**
```
https://workout-analyzer-backend.onrender.com
```

**WebSocket for Real-Time Video:**
```
wss://workout-analyzer-backend.onrender.com/ws/posture-stream/{session_id}
```

**API Documentation:**
```
https://workout-analyzer-backend.onrender.com/docs
```

**WebSocket Test Page:**
```
https://workout-analyzer-backend.onrender.com/posture/ws-test
```

---

## Test After Deployment

### Method 1: Browser Test
Visit:
```
https://workout-analyzer-backend.onrender.com/posture/ws-test
```

Click "Connect" button. If it says "✅ Connected", your WebSocket is working!

### Method 2: API Test
```powershell
# Health check
curl https://workout-analyzer-backend.onrender.com/health

# View API docs
Start-Process "https://workout-analyzer-backend.onrender.com/docs"
```

---

## Flutter Integration

### Update Your Flutter Code

In `lib/services/posture_websocket_service.dart`:

```dart
class PostureWebSocketService {
  // Change this line:
  static const String wsBaseUrl = 'wss://workout-analyzer-backend.onrender.com/ws/posture-stream';
  
  // Rest of code remains same...
}
```

That's it! Your Flutter app will now connect to your deployed backend.

---

## Testing WebSocket from Flutter

```dart
// In your Flutter app
final wsService = PostureWebSocketService();

// Connect
bool connected = await wsService.connect();

if (connected) {
  print('✅ Connected to Render backend!');
  
  // Send frames from camera
  wsService.postureResults.listen((result) {
    print('Posture: ${result.postureStatus}');
    print('Score: ${result.postureScore}');
  });
  
  // Send a frame
  await wsService.sendFrameBytes(cameraImageBytes);
}
```

---

## Troubleshooting

### Issue 1: WebSocket Connection Failed

**Check:**
```dart
// Make sure you're using WSS (not WS) for HTTPS sites
const wsUrl = 'wss://workout-analyzer-backend.onrender.com/ws/posture-stream';
```

**Test:**
1. Open https://workout-analyzer-backend.onrender.com/posture/ws-test
2. Click "Connect"
3. If it connects, your WebSocket is working

### Issue 2: Deployment Failed

**Check Render Logs:**
1. Go to Render dashboard
2. Click your service
3. Click "Logs" tab
4. Look for errors

**Common fixes:**
- Wait 5-10 minutes for cold start
- Check if all files are committed to GitHub
- Verify requirements.txt has correct versions

### Issue 3: "Service Unavailable" Error

**Reason:** Render free tier spins down after 15 minutes of inactivity.

**Solution:** 
1. First request will take 30-60 seconds to wake up
2. Just wait and retry
3. Or upgrade to paid tier for always-on service

---

## Performance Tips

### 1. Frame Rate
Send frames at **3-5 FPS** (not every frame):

```dart
// Send frame every 333ms = 3 FPS
while (monitoring) {
  await wsService.sendCompressedFrame(bytes);
  await Future.delayed(Duration(milliseconds: 333));
}
```

### 2. Image Compression
Always compress images before sending:

```dart
// Compress to 640x480, 80% quality
await wsService.sendCompressedFrame(bytes, quality: 80);
```

### 3. Handle Disconnections
```dart
wsService.connectionStatus.listen((connected) {
  if (!connected) {
    // Auto-reconnect
    Future.delayed(Duration(seconds: 2), () {
      wsService.connect();
    });
  }
});
```

---

## API Endpoints Available

### REST Endpoints (for history/stats):
- `GET /health` - Health check
- `GET /posture/history` - Get session history
- `GET /posture/statistics` - Overall stats
- `POST /posture/quick-analyze` - Single image analysis

### WebSocket Endpoint (for real-time):
- `WS /ws/posture-stream/{session_id}` - Real-time video analysis

**Use WebSocket for:**
- ✅ Real-time video monitoring
- ✅ Continuous posture tracking
- ✅ Live feedback

**Use REST API for:**
- ✅ Viewing history
- ✅ Getting statistics
- ✅ One-time image analysis

---

## Next Steps

1. ✅ **Test deployment:**
   ```
   https://workout-analyzer-backend.onrender.com/posture/ws-test
   ```

2. ✅ **Update Flutter code:**
   - Change WebSocket URL to your Render URL
   - Use `wss://` (not `ws://`)

3. ✅ **Test from Flutter:**
   - Run your Flutter app
   - Start monitoring
   - Check if posture results appear

4. ✅ **Monitor logs:**
   - Check Render dashboard for any errors
   - View real-time logs during testing

---

## Environment Variables (Optional)

In Render dashboard, you can add:

| Key | Value | Purpose |
|-----|-------|---------|
| `PORT` | 8000 | Server port (auto-set by Render) |
| `ENVIRONMENT` | production | Track environment |

---

## Cost Estimate

**Render Free Tier:**
- ✅ 750 hours/month free
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub
- ⚠️ Spins down after 15 min inactivity

**Paid Tier ($7/month):**
- ✅ Always on (no spin down)
- ✅ Better performance
- ✅ More resources

For production app with many users, consider paid tier.

---

## Security Considerations

### For Production:

1. **Add Authentication:**
```python
from fastapi import Header, HTTPException

async def verify_token(authorization: str = Header(None)):
    if authorization != "Bearer YOUR_SECRET_TOKEN":
        raise HTTPException(status_code=401)
```

2. **Rate Limiting:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.websocket("/ws/posture-stream/{session_id}")
@limiter.limit("100/minute")
async def posture_stream_websocket(websocket: WebSocket, session_id: str):
    # Your code...
```

3. **Update CORS:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-flutter-app.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Success! 🎉

Your backend is now deployed with:
- ✅ Real-time WebSocket video analysis
- ✅ REST API for history and stats
- ✅ HTTPS security
- ✅ Auto-deploy from GitHub
- ✅ Flutter-ready

**Test it now:**
https://workout-analyzer-backend.onrender.com/posture/ws-test

---

## Questions?

Check the logs in Render dashboard or test endpoints at:
https://workout-analyzer-backend.onrender.com/docs
