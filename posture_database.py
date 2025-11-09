"""
Database handler for posture sessions
Stores session data in CSV format (matching posture_sessions.csv structure)
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class PostureDatabase:
    """Handle posture session data storage"""
    
    def __init__(self, csv_file: str = "posture_sessions.csv"):
        """Initialize database with CSV file"""
        self.csv_file = csv_file
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "session_id",
                    "session_seconds",
                    "total_frames",
                    "good_frames",
                    "bad_frames",
                    "good_percent",
                    "bad_percent",
                    "average_score",
                    "longest_bad_secs"
                ])
    
    def save_session(self, session_data: Dict) -> bool:
        """
        Save a posture session to CSV
        
        Args:
            session_data: Dictionary containing session information
            
        Returns:
            True if saved successfully
        """
        try:
            with open(self.csv_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    session_data.get('end_time', datetime.now().isoformat()),
                    session_data.get('session_id', ''),
                    round(session_data.get('duration_seconds', 0), 2),
                    session_data.get('total_frames', 0),
                    session_data.get('good_frames', 0),
                    session_data.get('bad_frames', 0),
                    round(session_data.get('good_percent', 0), 2),
                    round(session_data.get('bad_percent', 0), 2),
                    round(session_data.get('average_score', 0), 2),
                    round(session_data.get('longest_bad_duration', 0), 2)
                ])
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Retrieve all posture sessions from CSV
        
        Returns:
            List of session dictionaries
        """
        sessions = []
        
        if not os.path.exists(self.csv_file):
            return sessions
        
        try:
            with open(self.csv_file, mode='r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sessions.append(row)
            return sessions
        except Exception as e:
            print(f"Error reading sessions: {e}")
            return []
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """
        Get a specific session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dictionary or None
        """
        sessions = self.get_all_sessions()
        for session in sessions:
            if session.get('session_id') == session_id:
                return session
        return None
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of recent session dictionaries
        """
        sessions = self.get_all_sessions()
        return sessions[-limit:] if sessions else []
    
    def get_statistics(self) -> Dict:
        """
        Get overall statistics from all sessions
        
        Returns:
            Dictionary with aggregate statistics
        """
        sessions = self.get_all_sessions()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_duration": 0,
                "average_good_percent": 0,
                "average_bad_percent": 0,
                "average_score": 0
            }
        
        total_duration = 0
        total_good_percent = 0
        total_bad_percent = 0
        total_score = 0
        valid_sessions = 0
        
        for session in sessions:
            try:
                # Skip sessions with invalid data
                if session.get('session_seconds', '').replace('.', '').replace('-', '').isdigit():
                    total_duration += float(session.get('session_seconds', 0))
                
                good_pct = session.get('good_percent', '')
                if good_pct and good_pct.replace('.', '').replace('-', '').isdigit():
                    total_good_percent += float(good_pct)
                    valid_sessions += 1
                
                bad_pct = session.get('bad_percent', '')
                if bad_pct and bad_pct.replace('.', '').replace('-', '').isdigit():
                    total_bad_percent += float(bad_pct)
                
                score = session.get('average_score', '')
                if score and score.replace('.', '').replace('-', '').isdigit():
                    total_score += float(score)
            except (ValueError, TypeError):
                continue
        
        return {
            "total_sessions": len(sessions),
            "total_duration_seconds": round(total_duration, 2),
            "average_good_percent": round(total_good_percent / valid_sessions, 2) if valid_sessions > 0 else 0,
            "average_bad_percent": round(total_bad_percent / valid_sessions, 2) if valid_sessions > 0 else 0,
            "average_score": round(total_score / valid_sessions, 2) if valid_sessions > 0 else 0
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            sessions = self.get_all_sessions()
            sessions = [s for s in sessions if s.get('session_id') != session_id]
            
            # Rewrite CSV without the deleted session
            with open(self.csv_file, mode='w', newline='') as f:
                if sessions:
                    writer = csv.DictWriter(f, fieldnames=sessions[0].keys())
                    writer.writeheader()
                    writer.writerows(sessions)
                else:
                    # Recreate empty file with headers
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp",
                        "session_id",
                        "session_seconds",
                        "total_frames",
                        "good_frames",
                        "bad_frames",
                        "good_percent",
                        "bad_percent",
                        "average_score",
                        "longest_bad_secs"
                    ])
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def clear_all_sessions(self) -> bool:
        """
        Clear all sessions from the database
        
        Returns:
            True if cleared successfully
        """
        try:
            self._initialize_csv()
            return True
        except Exception as e:
            print(f"Error clearing sessions: {e}")
            return False
