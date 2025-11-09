from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
from pose_estimation import get_pose_keypoints_and_annotated_image
from posture_analysis import PostureAnalyzer, PostureSession
from posture_database import PostureDatabase
import logging
import traceback
from typing import Optional, Dict, List
import cv2
import numpy as np
from io import BytesIO
import uuid
from datetime import datetime
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize posture analyzer and database
posture_analyzer = PostureAnalyzer()
posture_db = PostureDatabase()

# Store active posture sessions (in-memory)
active_sessions: Dict[str, PostureSession] = {}

# Store active WebSocket connections
active_websockets: Dict[str, WebSocket] = {}

app = FastAPI(title="Pose Estimation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Validate and process the uploaded image"""
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
            
        # Check image dimensions
        height, width = image.shape[:2]
        if width < 100 or height < 100:
            raise ValueError("Image dimensions too small")
            
        # Check image format
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError("Invalid image format")
            
        return image
    except Exception as e:
        logger.error(f"Image validation error: {str(e)}")
        return None

@app.post("/analyze-pose")
async def analyze_pose(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Validate image
        image = validate_image(contents)
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format or corrupted image"
            )
            
        # Process the image
        try:
            keypoints, pose_name, annotated_image_bytes = get_pose_keypoints_and_annotated_image(contents)
        except Exception as e:
            logger.error(f"Pose estimation error: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in pose estimation: {str(e)}"
            )
        
        # Convert annotated image to base64
        try:
            annotated_image_base64 = base64.b64encode(annotated_image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Base64 encoding error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error encoding processed image"
            )
        
        return {
            "status": "success",
            "pose": pose_name,
            "keypoints": keypoints,
            "annotated_image": annotated_image_base64
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ==================== POSTURE ANALYSIS ENDPOINTS ====================

@app.post("/posture/start-session")
async def start_posture_session():
    """
    Start a new posture analysis session
    Returns a session_id to use for subsequent frame analysis
    """
    try:
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = PostureSession(session_id)
        
        logger.info(f"Started posture session: {session_id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Posture session started successfully",
            "start_time": active_sessions[session_id].start_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting posture session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/posture/analyze-frame")
async def analyze_posture_frame(
    session_id: str,
    file: UploadFile = File(...),
    draw_landmarks: bool = True
):
    """
    Analyze a single frame for posture
    
    Parameters:
    - session_id: Active session identifier
    - file: Image file to analyze
    - draw_landmarks: Whether to draw pose landmarks on returned image
    
    Returns:
    - Posture analysis result with annotated image
    """
    try:
        # Check if session exists
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found. Please start a session first."
            )
        
        # Read and validate image
        contents = await file.read()
        image = validate_image(contents)
        
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format or corrupted image"
            )
        
        # Analyze posture
        result = posture_analyzer.analyze_frame(image, draw_landmarks=draw_landmarks)
        
        # Update session
        session = active_sessions[session_id]
        session.update(result)
        
        # Draw posture info on image
        annotated_image = posture_analyzer.draw_posture_info(image.copy(), result)
        
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Prepare response
        response = {
            "status": "success",
            "session_id": session_id,
            "posture_status": result.posture_status,
            "posture_score": result.posture_score,
            "is_good_posture": result.is_good_posture,
            "annotated_image": annotated_image_base64,
            "session_stats": session.get_statistics()
        }
        
        # Add metrics if available
        if result.metrics:
            response["metrics"] = {
                "neck_angle": round(result.metrics.neck_angle, 2),
                "spine_tilt": round(result.metrics.spine_tilt, 2),
                "shoulder_tilt": round(result.metrics.shoulder_tilt, 2),
                "nose_shoulder_distance": round(result.metrics.nose_shoulder_dist, 2)
            }
        
        # Add landmarks if available
        if result.landmarks:
            response["landmarks"] = result.landmarks
        
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error analyzing posture frame: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/posture/end-session")
async def end_posture_session(session_id: str):
    """
    End a posture analysis session and save to database
    
    Parameters:
    - session_id: Session identifier
    
    Returns:
    - Final session statistics
    """
    try:
        # Check if session exists
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get session
        session = active_sessions[session_id]
        
        # Get final statistics
        stats = session.get_statistics()
        stats['end_time'] = datetime.now().isoformat()
        
        # Save to database
        save_success = posture_db.save_session(stats)
        
        # Remove from active sessions
        del active_sessions[session_id]
        
        logger.info(f"Ended posture session: {session_id}")
        
        return {
            "status": "success",
            "message": "Session ended and saved successfully" if save_success else "Session ended but save failed",
            "session_statistics": stats,
            "saved_to_database": save_success
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error ending posture session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posture/session-status/{session_id}")
async def get_session_status(session_id: str):
    """
    Get current statistics for an active session
    
    Parameters:
    - session_id: Session identifier
    
    Returns:
    - Current session statistics
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        session = active_sessions[session_id]
        stats = session.get_statistics()
        
        return {
            "status": "success",
            "session_id": session_id,
            "statistics": stats,
            "is_active": True
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posture/history")
async def get_posture_history(limit: int = 10):
    """
    Get posture session history
    
    Parameters:
    - limit: Maximum number of sessions to return (default: 10)
    
    Returns:
    - List of recent posture sessions
    """
    try:
        sessions = posture_db.get_recent_sessions(limit=limit)
        
        return {
            "status": "success",
            "count": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting posture history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posture/statistics")
async def get_overall_statistics():
    """
    Get overall posture statistics from all sessions
    
    Returns:
    - Aggregate statistics
    """
    try:
        stats = posture_db.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting posture statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posture/active-sessions")
async def get_active_sessions():
    """
    Get all currently active posture sessions
    
    Returns:
    - List of active session IDs and their current statistics
    """
    try:
        active = []
        for session_id, session in active_sessions.items():
            stats = session.get_statistics()
            active.append({
                "session_id": session_id,
                "statistics": stats
            })
        
        return {
            "status": "success",
            "count": len(active),
            "active_sessions": active
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/posture/session/{session_id}")
async def delete_posture_session(session_id: str):
    """
    Delete a posture session from history
    
    Parameters:
    - session_id: Session identifier
    
    Returns:
    - Deletion status
    """
    try:
        success = posture_db.delete_session(session_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Session {session_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/posture/quick-analyze")
async def quick_posture_analyze(file: UploadFile = File(...), draw_landmarks: bool = True):
    """
    Quick posture analysis without session tracking
    Useful for single image analysis
    
    Parameters:
    - file: Image file to analyze
    - draw_landmarks: Whether to draw pose landmarks
    
    Returns:
    - Posture analysis result
    """
    try:
        # Read and validate image
        contents = await file.read()
        image = validate_image(contents)
        
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format or corrupted image"
            )
        
        # Analyze posture
        result = posture_analyzer.analyze_frame(image, draw_landmarks=draw_landmarks)
        
        # Draw posture info on image
        annotated_image = posture_analyzer.draw_posture_info(image.copy(), result)
        
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Prepare response
        response = {
            "status": "success",
            "posture_status": result.posture_status,
            "posture_score": result.posture_score,
            "is_good_posture": result.is_good_posture,
            "annotated_image": annotated_image_base64
        }
        
        # Add metrics if available
        if result.metrics:
            response["metrics"] = {
                "neck_angle": round(result.metrics.neck_angle, 2),
                "spine_tilt": round(result.metrics.spine_tilt, 2),
                "shoulder_tilt": round(result.metrics.shoulder_tilt, 2),
                "nose_shoulder_distance": round(result.metrics.nose_shoulder_dist, 2)
            }
        
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in quick posture analysis: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEBSOCKET FOR REAL-TIME VIDEO STREAMING ====================

@app.websocket("/ws/posture-stream/{session_id}")
async def posture_stream_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time posture analysis
    
    Client sends: Base64 encoded video frames
    Server responds: Posture analysis results in real-time
    
    Protocol:
    1. Client connects with session_id
    2. Client sends JSON: {"frame": "base64_image_data"}
    3. Server responds: {"status": "success", "posture_status": "...", "posture_score": 95, ...}
    4. Repeat for each frame
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for session: {session_id}")
    
    # Check if session exists, create if not
    if session_id not in active_sessions:
        active_sessions[session_id] = PostureSession(session_id)
        logger.info(f"Created new session: {session_id}")
    
    active_websockets[session_id] = websocket
    session = active_sessions[session_id]
    
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "frame":
                    # Get base64 frame
                    frame_base64 = message.get("frame", "")
                    
                    if not frame_base64:
                        await websocket.send_json({
                            "status": "error",
                            "message": "No frame data provided"
                        })
                        continue
                    
                    # Decode base64 to image
                    try:
                        image_bytes = base64.b64decode(frame_base64)
                        nparr = np.frombuffer(image_bytes, np.uint8)
                        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if image is None:
                            await websocket.send_json({
                                "status": "error",
                                "message": "Failed to decode image"
                            })
                            continue
                        
                    except Exception as e:
                        await websocket.send_json({
                            "status": "error",
                            "message": f"Invalid base64 image: {str(e)}"
                        })
                        continue
                    
                    # Analyze posture
                    result = posture_analyzer.analyze_frame(image, draw_landmarks=False)
                    
                    # Update session
                    session.update(result)
                    
                    # Prepare response
                    response = {
                        "status": "success",
                        "posture_status": result.posture_status,
                        "posture_score": result.posture_score,
                        "is_good_posture": result.is_good_posture,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Add metrics
                    if result.metrics:
                        response["metrics"] = {
                            "neck_angle": round(result.metrics.neck_angle, 2),
                            "spine_tilt": round(result.metrics.spine_tilt, 2),
                            "shoulder_tilt": round(result.metrics.shoulder_tilt, 2)
                        }
                    
                    # Add session stats (every 10 frames to reduce data)
                    if session.total_frames % 10 == 0:
                        response["session_stats"] = {
                            "total_frames": session.total_frames,
                            "good_percent": round((session.good_frames / session.total_frames * 100), 2) if session.total_frames > 0 else 0,
                            "bad_percent": round((session.bad_frames / session.total_frames * 100), 2) if session.total_frames > 0 else 0,
                            "average_score": round(sum(session.score_history) / len(session.score_history), 2) if session.score_history else 0,
                            "current_bad_duration": round(session.current_bad_duration, 2)
                        }
                    
                    # Send response back to client
                    await websocket.send_json(response)
                
                elif message.get("type") == "ping":
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})
                
                elif message.get("type") == "end_session":
                    # End session and save
                    stats = session.get_statistics()
                    stats['end_time'] = datetime.now().isoformat()
                    posture_db.save_session(stats)
                    
                    await websocket.send_json({
                        "status": "success",
                        "message": "Session ended and saved",
                        "final_stats": stats
                    })
                    
                    # Clean up
                    del active_sessions[session_id]
                    break
                
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Unknown message type"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid JSON format"
                })
            
            except Exception as e:
                logger.error(f"Error processing frame: {str(e)}\n{traceback.format_exc()}")
                await websocket.send_json({
                    "status": "error",
                    "message": f"Error processing frame: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        # Save session on disconnect
        if session_id in active_sessions:
            stats = active_sessions[session_id].get_statistics()
            stats['end_time'] = datetime.now().isoformat()
            posture_db.save_session(stats)
            del active_sessions[session_id]
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}\n{traceback.format_exc()}")
    
    finally:
        # Clean up
        if session_id in active_websockets:
            del active_websockets[session_id]


@app.get("/posture/ws-test")
async def websocket_test_page():
    """
    Simple HTML page to test WebSocket connection
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Posture Analysis WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .good { background-color: #06D6A0; color: white; }
            .bad { background-color: #EF476F; color: white; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Posture Analysis - WebSocket Test</h1>
            <div id="status" class="status">Not connected</div>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
            <div id="stats"></div>
        </div>
        <script>
            let ws = null;
            const sessionId = 'test-session-' + Date.now();
            
            function connect() {
                const wsUrl = 'ws://' + window.location.host + '/ws/posture-stream/' + sessionId;
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    document.getElementById('status').textContent = '✅ Connected - Session: ' + sessionId;
                    document.getElementById('status').className = 'status good';
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    console.log('Received:', data);
                    
                    if (data.status === 'success') {
                        document.getElementById('stats').innerHTML = 
                            '<h3>Latest Result:</h3>' +
                            '<p>Posture: ' + data.posture_status + '</p>' +
                            '<p>Score: ' + data.posture_score + '</p>' +
                            '<p>Good Posture: ' + data.is_good_posture + '</p>';
                    }
                };
                
                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    document.getElementById('status').textContent = '❌ Connection error';
                    document.getElementById('status').className = 'status bad';
                };
                
                ws.onclose = () => {
                    document.getElementById('status').textContent = '❌ Disconnected';
                    document.getElementById('status').className = 'status bad';
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.send(JSON.stringify({type: 'end_session'}));
                    ws.close();
                }
            }
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import os
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
