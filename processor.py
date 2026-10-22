"""Local audio extraction, transcription, and simple audio measurements."""

import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


def _run_ffmpeg(args):
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "FFmpeg was not found. Install FFmpeg and add its bin folder to Windows PATH."
        ) from exc
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg could not process this recording: {result.stderr[-1200:]}")


def _audio_metrics(wav_path: Path) -> dict:
    with wave.open(str(wav_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width != 2:
        return {
            "sample_rate_hz": sample_rate,
            "channels": channels,
            "note": "Audio was extracted, but this sample format was not measured.",
        }

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if audio.size == 0:
        return {"error": "No audio samples found."}

    rms = float(np.sqrt(np.mean(np.square(audio))))
    peak = float(np.max(np.abs(audio)))
    clipped_fraction = float(np.mean(np.abs(audio) >= 0.999))
    return {
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "rms_loudness_linear": round(rms, 5),
        "peak_amplitude_linear": round(peak, 5),
        "clipped_sample_fraction": round(clipped_fraction, 6),
        "interpretation_note": (
            "These are basic signal indicators, not a full subjective audio-quality score. "
            "RMS varies with recording volume and must not be treated as quality by itself."
        ),
    }


def process_recording(input_path: Path, work_dir: Path, whisper_model: str = "tiny") -> dict:
    wav_path = work_dir / "extracted_audio.wav"

    print(f"[1/4] Extracting audio from: {input_path}", flush=True)

    # Mono 16 kHz PCM is a broadly compatible format for speech transcription.
    _run_ffmpeg([
        "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(wav_path),
    ])

    print(f"[2/4] Audio extracted: {wav_path}", flush=True)

    # Probe duration using ffprobe, included with a standard FFmpeg installation.
    try:
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(input_path)
            ],
            capture_output=True, text=True, check=True,
        )
        duration = float(probe.stdout.strip())
    except Exception:
        with wave.open(str(wav_path), "rb") as wav:
            duration = wav.getnframes() / float(wav.getframerate())

    print("[3/4] Loading Whisper model...", flush=True)

    # CPU + int8 keeps memory use lower on typical laptops.
    model = WhisperModel(whisper_model, device="cpu", compute_type="int8")

    print("[4/4] Transcribing audio...", flush=True)

    segments, info = model.transcribe(
        str(wav_path),
        beam_size=1,
        vad_filter=True,
        word_timestamps=False,
    )

    transcript_parts = []
    for segment in segments:
        start = max(0, int(segment.start))
        minutes, seconds = divmod(start, 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        text = segment.text.strip()
        if text:
            transcript_parts.append(f"[{timestamp}] {text}")

    transcript = "\n".join(transcript_parts).strip()
    if not transcript:
        transcript = "[No speech could be transcribed from this recording.]"
    
    print("[Done] Transcription completed.", flush=True)

    return {
        "transcript": transcript,
        "duration_seconds": max(0.0, duration),
        "audio_metrics": _audio_metrics(wav_path),
        "detected_language": getattr(info, "language", None),
    }
