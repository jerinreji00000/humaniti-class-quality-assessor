# Approach and limitations (submission draft; edit to reflect your actual tests)

I built a local-first class quality assessment prototype using Streamlit, FFmpeg, faster-whisper, and Ollama. The user uploads an audio or video recording. FFmpeg extracts mono 16 kHz audio, faster-whisper creates a timestamped transcript, and the app calculates basic audio signal indicators. A locally running language model evaluates the transcript and indicators against a consistent five-dimension rubric: teaching clarity, lesson structure, evidence of student engagement, audio quality, and visual presentation evidence. The application calculates a weighted score and maps it to Poor, Average, Good, or Excellent. It presents dimension-level explanations, strengths, suggested improvements, evidence, limitations, and a downloadable JSON report.

The approach avoids sending recordings to an external AI API and does not require an API key. It is designed to run on a typical laptop, although transcription and inference speed depend on recording length and hardware.

The main limitation is that the current version does not semantically analyze video frames. A transcript cannot prove student attention or visual quality, and basic audio measurements cannot fully represent perceived sound quality. The model may also produce inconsistent judgements, so scores and evidence should be reviewed against the sample recordings. Next steps would be to validate the rubric against labelled examples, add privacy-approved visual analysis, and measure agreement between assessments.

**Before submitting:** replace or revise the claims above to match what you actually ran and observed. Do not claim tests or results you did not perform.
