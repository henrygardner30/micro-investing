"""
State Storage for Lambda Deployment

Provides S3-based persistent storage for strategy state.
Falls back to /tmp for local testing without S3.
"""

import json
import os
from pathlib import Path
from typing import Dict

class StateStorage:
    """Abstract base for state storage"""
    
    def load(self) -> Dict:
        """Load state dictionary"""
        raise NotImplementedError
    
    def save(self, state: Dict):
        """Save state dictionary"""
        raise NotImplementedError


class S3StateStorage(StateStorage):
    """
    S3-based state storage for Lambda.
    Stores state in S3 bucket for persistence across Lambda invocations.
    """
    
    def __init__(self, bucket_name: str, key: str = "scheduled_state.json"):
        """
        Initialize S3 state storage.
        
        @PARAMS:
            - bucket_name -> S3 bucket name for state storage
            - key -> Object key (filename) in S3 bucket
        """
        self.bucket_name = bucket_name
        self.key = key
        
        try:
            import boto3
            self.s3 = boto3.client('s3')
            self.available = True
        except Exception as e:
            print(f"Warning: S3 not available: {e}")
            self.available = False
    
    def load(self) -> Dict:
        """
        Function to load state from S3 bucket.
        Returns dictionary of state data or empty dict if not found.
        """
        if not self.available:
            return {}
        
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=self.key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except self.s3.exceptions.NoSuchKey:
            # First run, no state exists yet
            return {}
        except Exception as e:
            print(f"Error loading state from S3: {e}")
            return {}
    
    def save(self, state: Dict):
        """
        Function to save state to S3 bucket.
        
        @PARAMS:
            - state -> Dictionary of state data to persist
        """
        if not self.available:
            return
        
        try:
            content = json.dumps(state, indent=2)
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=self.key,
                Body=content.encode('utf-8'),
                ContentType='application/json'
            )
        except Exception as e:
            print(f"Error saving state to S3: {e}")


class LocalFileStorage(StateStorage):
    """
    File-based state storage for local deployment or Lambda fallback.
    """
    
    def __init__(self, file_path: str = "/tmp/scheduled_state.json"):
        """
        Initialize local file storage.
        
        @PARAMS:
            - file_path -> Path to state file (default: /tmp for Lambda)
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict:
        """
        Function to load state from local file.
        Returns dictionary of state data or empty dict if not found.
        """
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return {}
    
    def save(self, state: Dict):
        """
        Function to save state to local file.
        
        @PARAMS:
            - state -> Dictionary of state data to persist
        """
        try:
            with open(self.file_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state to file: {e}")


def get_state_storage() -> StateStorage:
    """
    Function to get appropriate state storage based on environment.
    Uses S3 if bucket is configured, otherwise falls back to local file.
    Returns StateStorage instance.
    """
    s3_bucket = os.getenv('STATE_S3_BUCKET')
    
    if s3_bucket:
        print(f"Using S3 state storage: {s3_bucket}")
        return S3StateStorage(s3_bucket)
    else:
        print("Warning: STATE_S3_BUCKET not set, using /tmp (not persistent!)")
        return LocalFileStorage("/tmp/scheduled_state.json")

