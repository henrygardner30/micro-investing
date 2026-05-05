"""Ledger for Lambda - logs to CloudWatch and optionally S3"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict

def save_to_ledger(entry: Dict):
    """
    Save investment record to CloudWatch and optionally S3.
    
    @PARAMS:
        - entry -> dictionary with investment details
    """
    # always log to CloudWatch
    print(f"[LEDGER] {json.dumps(entry)}")
    
    # optionally save to S3
    s3_bucket = os.getenv('S3_LEDGER_BUCKET')
    if not s3_bucket:
        return
    
    try:
        s3 = boto3.client('s3')
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        key = f"ledger/{timestamp}.json"
        
        s3.put_object(
            Bucket=s3_bucket,
            Key=key,
            Body=json.dumps(entry, indent=2),
            ContentType='application/json'
        )
        
        print(f"[LEDGER] Saved to S3: s3://{s3_bucket}/{key}")
    except Exception as e:
        print(f"[LEDGER] Failed to save to S3: {e}")

