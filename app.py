import json
import tempfile
from pathlib import Path

import streamlit as st

from processor import process_recording
from evaluator import assess_class, OllamaUnavailable, ModelResponseError
from rubric import DIMENSIONS, category_from_score

st.set_page_config(page_title="Class Quality Assessor", page_icon="🎓", layout="wide")

st.title("🎓 Class Quality Assessor")
st.write(
    "Upload an online class recording to generate an evidence-based quality assessment. "
    "Processing is designed to run locally on your computer."
)
st.info(
    "Privacy: this app processes files locally. The optional Ollama model runs on your computer. "
    "Do not upload children’s recordings to public hosting or send them to an external service "
    "unless the organiser explicitly permits it."
)

with st.expander("How this prototype evaluates a class"):
    st.markdown(
        "- Transcribes speech locally with faster-whisper.\n"
        "- Calculates basic technical audio indicators.\n"
        "- Uses a local Ollama language model to score teaching clarity, structure, engagement evidence, "
        "audio quality, and visual presentation evidence.\n"
        "- A transcript cannot prove that students were attentive or that a visual aid was clear. "
        "The model is instructed to mark unsupported dimensions as uncertain."
    )

uploaded = st.file_uploader(
    "Choose a class recording",
    type=["mp4", "mov", "mkv", "webm", "avi", "mp3", "wav", "m4a", "aac", "flac", "ogg"],
    help="For an 8 GB RAM laptop, begin with a short sample recording if possible."
)

col1, col2 = st.columns(2)
with col1:
    whisper_model = st.selectbox(
        "Local transcription model",
        ["tiny", "base", "small"],
        index=0,
        help="Use tiny first on an 8 GB RAM laptop. Larger models are slower and use more memory."
    )
with col2:
    try:
        default_model = st.secrets.get("LLM_MODEL", "qwen2.5:3b")
    except Exception:
        default_model = "qwen2.5:3b"

    ollama_model = st.text_input(
        "Model name",
        value=default_model,
        help="Locally: run `ollama pull qwen2.5:3b`. On the cloud: use the hosted model name from your secrets."
    )

st.caption("Prerequisites: install FFmpeg and Ollama, then download the Ollama model. See README.md.")

if st.button("Analyze class", type="primary", disabled=uploaded is None):
    if not ollama_model.strip():
        st.error("Enter an Ollama model name.")
        st.stop()

    with tempfile.TemporaryDirectory(prefix="humaniti_assessor_") as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / Path(uploaded.name).name
        input_path.write_bytes(uploaded.getbuffer())

        try:
            with st.status("Processing the recording locally…", expanded=True) as status:
                st.write("Extracting audio and calculating technical indicators…")
                processed = process_recording(input_path, tmpdir, whisper_model)
                st.write("Transcription complete. Asking the local language model to assess the evidence…")
                result = assess_class(
                    transcript=processed["transcript"],
                    audio_metrics=processed["audio_metrics"],
                    model=ollama_model.strip(),
                    duration_seconds=processed["duration_seconds"],
                )
                status.update(label="Assessment complete", state="complete", expanded=False)

            score = float(result["overall_score"])
            category = category_from_score(score)
            st.subheader("Assessment result")
            a, b, c = st.columns(3)
            a.metric("Class quality", category)
            b.metric("Weighted score", f"{score:.2f} / 5")
            c.metric("Recording duration", f'{processed["duration_seconds"] / 60:.1f} min')

            st.progress(min(max(score / 5, 0.0), 1.0))
            st.caption("Category is calculated from the weighted score using the rubric in rubric.py.")

            st.subheader("Dimension scores")
            dimension_scores = result.get("dimension_scores", {})
            for dim in DIMENSIONS:
                item = dimension_scores.get(dim, {})
                value = item.get("score")
                evidence_status = item.get("evidence_status", "limited")
                left, right = st.columns([1, 4])
                with left:
                    st.metric(dim.replace("_", " ").title(), f"{value}/5" if value is not None else "N/A")
                with right:
                    st.write(item.get("reason", "No explanation supplied."))
                    st.caption(f"Evidence status: {evidence_status}")

            x, y = st.columns(2)
            with x:
                st.subheader("Strengths")
                strengths = result.get("strengths", [])
                if strengths:
                    for item in strengths:
                        st.markdown(f"- {item}")
                else:
                    st.write("No sufficiently supported strengths identified.")
            with y:
                st.subheader("Suggested improvements")
                improvements = result.get("improvements", [])
                if improvements:
                    for item in improvements:
                        st.markdown(f"- {item}")
                else:
                    st.write("No specific improvements returned.")

            st.subheader("Evidence")
            evidence = result.get("evidence", [])
            if evidence:
                for item in evidence:
                    timestamp = item.get("timestamp")
                    prefix = f"**[{timestamp}]** " if timestamp else ""
                    st.markdown(f"- {prefix}{item.get('observation', '')}")
                    if item.get("source"):
                        st.caption(f"Source: {item['source']}")
            else:
                st.write("No specific evidence returned. Treat the score as low-confidence.")

            if result.get("limitations"):
                st.subheader("Limitations / uncertainty")
                for item in result["limitations"]:
                    st.markdown(f"- {item}")

            with st.expander("View transcript"):
                st.text_area("Transcription", processed["transcript"], height=300)

            with st.expander("View technical audio indicators"):
                st.json(processed["audio_metrics"])

            report = {
                "filename": uploaded.name,
                "duration_seconds": processed["duration_seconds"],
                "category": category,
                **result,
                "audio_metrics": processed["audio_metrics"],
                "transcript": processed["transcript"],
            }
            st.download_button(
                "Download assessment report (JSON)",
                data=json.dumps(report, indent=2, ensure_ascii=False),
                file_name="class_assessment_report.json",
                mime="application/json",
            )
        except OllamaUnavailable as exc:
            st.error(str(exc))
            st.markdown(
                "Check that Ollama is installed and running, then download the model in Command Prompt:\n\n"
                "```bat\nollama pull qwen2.5:3b\n```"
            )
        except Exception as exc:
            st.error(f"Processing failed: {exc}")
            st.markdown(
                "Check that FFmpeg is installed and available on PATH, and try a shorter MP4/WAV sample. "
                "If transcription fails, try the `tiny` model."
            )

st.divider()
st.caption(
    "Prototype limitations: this version does not claim to fully understand classroom video, "
    "student emotions, or engagement from transcript alone. Review its evidence before using the rating."
)

with st.expander("Debug: models available to my key"):
    if st.button("List models"):
        import requests
        r = requests.get(
            st.secrets["LLM_BASE_URL"].rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {st.secrets['LLM_API_KEY']}"},
            timeout=30,
        )
        st.write(r.status_code)
        try:
            st.write([m["id"] for m in r.json().get("data", [])])
        except Exception:
            st.code(r.text[:1000])
