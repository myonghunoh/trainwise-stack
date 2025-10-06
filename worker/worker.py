import os, tempfile, subprocess, json
import boto3
from faster_whisper import WhisperModel

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

def _load_model(size: str):
    device = os.getenv("FW_DEVICE", "cpu")   # "cpu" oder "cuda"
    compute_type = "int8_float16" if device == "cuda" else "int8"
    return WhisperModel(size, device=device, compute_type=compute_type)

def process(args: dict):
    url = args.get("url"); key = args.get("s3_key"); lang = args.get("lang"); model_size = args.get("model_size","base")
with tempfile.TemporaryDirectory() as d:
    if url:
        import subprocess
        src = f"{d}/audio.wav"
        subprocess.check_call(["yt-dlp", "-f", "bestaudio", "-x", "--audio-format", "wav", "-o", src, url])
        wav = src
    else:
        src = f"{d}/in.bin"
        s3.download_file(S3_BUCKET, key, src)
        wav = f"{d}/audio.wav"
        subprocess.check_call(["ffmpeg","-y","-i",src,"-ar","16000","-ac","1",wav])

        model = _load_model(model_size)
        segments, info = model.transcribe(wav, language=lang, vad_filter=True, vad_parameters={"min_silence_duration_ms": 500})

        data = {
            "language": info.language,
            "duration": info.duration,
            "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in segments],
        }
        out_json = f"{d}/result.json"
        with open(out_json,"w",encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

        result_key = key.replace("uploads/", "results/") + ".json"
        s3.upload_file(out_json, S3_BUCKET, result_key)
        return {"result_key": result_key}
