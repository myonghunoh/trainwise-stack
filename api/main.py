import os, uuid
from fastapi import FastAPI
from pydantic import BaseModel
import boto3
from redis import Redis
from rq import Queue
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TrainWise API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_KEY = os.getenv("S3_KEY")
S3_SECRET = os.getenv("S3_SECRET")
S3_BUCKET = os.getenv("S3_BUCKET")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
)

redis = Redis(host="redis", port=6379)
q = Queue("stt", connection=redis)

@app.get("/health")
def health():
    return {"status": "ok"}

class PresignReq(BaseModel):
    filename: str

@app.post("/upload/presign")
def presign(req: PresignReq):
    key = f"uploads/{uuid.uuid4()}-{req.filename}"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=3600,
        HttpMethod="PUT",
    )
    return {"put_url": url, "s3_key": key}

class STTRequest(BaseModel):
    s3_key: str
    lang: str | None = None
    model_size: str = "base"

@app.post("/stt/submit")
def submit(req: STTRequest):
    job = q.enqueue("worker.process", req.model_dump(), job_timeout=7200)
    return {"job_id": job.id, "status": "queued"}

@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    from rq.job import Job
    job = Job.fetch(job_id, connection=redis)
    return {"id": job.id, "status": job.get_status(), "result": job.result}
