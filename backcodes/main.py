import os
import boto3
from botocore.config import Config
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List
import logging
from datetime import datetime
from pydantic import BaseModel
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Filebase S3 configuration
ACCESS_KEY = "2EF872A62061001F28F7"
SECRET_KEY = "qq1EjmvKg2WcTor8Zo3COVPksEPfsSFN0NNfqmwc"
BUCKET_NAME = "haams"
FILEBASE_ENDPOINT = "https://s3.filebase.com"

# Configure S3 client
s3_config = Config(
    signature_version='s3v4',
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    }
)

try:
    logger.info("Initializing S3 client.")
    s3_client = boto3.client(
        's3',
        endpoint_url=FILEBASE_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=s3_config
    )
    logger.info("S3 client initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing S3 client: {e}")
    raise

# Data Models
class FileInfo(BaseModel):
    name: str
    hash: str
    url: str
    timestamp: str
    block_number: int

class VerificationRequest(BaseModel):
    file_hash: str
    file_name: str

class BlockchainMatch(BaseModel):
    index: int
    file_name: str
    hash: str
    timestamp: str
    previous_hash: Optional[str] = None

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/history")
async def get_history() -> List[FileInfo]:
    try:
        logger.info("Fetching file history from Filebase.")
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        files = []
        for i, item in enumerate(response.get('Contents', []), 1):
            file_info = FileInfo(
                name=item['Key'],
                hash=item.get('ETag', '').strip('"'),
                url=f"{FILEBASE_ENDPOINT}/{BUCKET_NAME}/{item['Key']}",
                timestamp=item['LastModified'].isoformat(),
                block_number=i
            )
            files.append(file_info)
        files.sort(key=lambda x: x.timestamp, reverse=True)
        logger.info(f"File history fetched successfully: {len(files)} files found.")
        return files
    except Exception as e:
        logger.error(f"Error fetching file history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    try:
        logger.info(f"Attempting to download file: {file_name}")
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_name)
        return StreamingResponse(
            response['Body'],
            media_type=response.get('ContentType', 'application/octet-stream'),
            headers={'Content-Disposition': f'attachment; filename="{file_name}"'}
        )
    except Exception as e:
        logger.error(f"Error downloading file: {file_name}, Error: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"Starting upload for file: {file.filename}")
        file_content = await file.read()
        if not file_content:
            logger.error("Empty file content received.")
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        file_hash = hashlib.md5(file_content).hexdigest()
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file.filename,
            Body=file_content,
            ContentType=file.content_type or 'application/octet-stream',
            Metadata={'file_hash': file_hash}
        )
        file_url = f"{FILEBASE_ENDPOINT}/{BUCKET_NAME}/{file.filename}"
        logger.info(f"File uploaded successfully: {file_url}")
        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "file_url": file_url,
                "file_name": file.filename,
                "file_hash": file_hash
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify")
async def verify_file(request: VerificationRequest) -> List[BlockchainMatch]:
    try:
        logger.info("Verifying file in blockchain.")
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        matches = []
        previous_hash = None
        for index, item in enumerate(response.get('Contents', []), 1):
            obj = s3_client.head_object(Bucket=BUCKET_NAME, Key=item['Key'])
            stored_hash = obj.get('Metadata', {}).get('file_hash', obj.get('ETag', '').strip('"'))
            if stored_hash.lower() == request.file_hash.lower():
                match = BlockchainMatch(
                    index=index,
                    file_name=item['Key'],
                    hash=stored_hash,
                    timestamp=item['LastModified'].isoformat(),
                    previous_hash=previous_hash
                )
                matches.append(match)
            previous_hash = stored_hash
        logger.info(f"File verification completed. Matches found: {len(matches)}.")
        return matches
    except Exception as e:
        logger.error(f"Error verifying file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-hash")
async def calculate_file_hash(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_hash = hashlib.md5(content).hexdigest()
        logger.info(f"Calculated hash for file: {file.filename} -> {file_hash}")
        return JSONResponse(
            content={"file_name": file.filename, "hash": file_hash},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blockchain-info")
async def get_blockchain_info():
    try:
        logger.info("Fetching blockchain info.")
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        total_blocks = len(response.get('Contents', []))
        if total_blocks > 0:
            latest_block = response['Contents'][0]
            latest_block_info = {
                "timestamp": latest_block['LastModified'].isoformat(),
                "file_name": latest_block['Key'],
                "size": latest_block['Size']
            }
        else:
            latest_block_info = None
        logger.info(f"Blockchain info fetched: Total blocks: {total_blocks}")
        return {
            "total_blocks": total_blocks,
            "latest_block": latest_block_info,
            "blockchain_status": "active"
        }
    except Exception as e:
        logger.error(f"Error fetching blockchain info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
