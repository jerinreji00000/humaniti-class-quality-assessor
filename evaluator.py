# """Local Ollama-based class assessment with JSON validation."""

# import json
# import re
# import requests

# from rubric import DIMENSIONS, WEIGHTS, weighted_score


# class OllamaUnavailable(RuntimeError):
#     pass


# class ModelResponseError(RuntimeError):
#     pass


# OLLAMA_URL = "http://localhost:11434/api/chat"



# def _extract_json(text: str) -> dict:
#     """Extract a valid JSON object from an Ollama response."""
#     text = text.strip()

#     # Remove Markdown code fences.
#     text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
#     text = re.sub(r"\s*```$", "", text)

#     # Try parsing the entire response first.
#     try:
#         result = json.loads(text)
#         if isinstance(result, dict):
#             return result
#     except json.JSONDecodeError:
#         pass

#     # Find a JSON object, accounting for braces inside quoted strings.
#     start = text.find("{")
#     if start == -1:
#         raise ModelResponseError(
#             f"No JSON object found in model response. "
#             f"Raw response: {text[:1500]}"
#         )

#     depth = 0
#     in_string = False
#     escaped = False

#     for i in range(start, len(text)):
#         char = text[i]

#         if in_string:
#             if escaped:
#                 escaped = False
#             elif char == "\\":
#                 escaped = True
#             elif char == '"':
#                 in_string = False
#         else:
#             if char == '"':
#                 in_string = True
#             elif char == "{":
#                 depth += 1
#             elif char == "}":
#                 depth -= 1

#                 if depth == 0:
#                     candidate = text[start:i + 1]
#                     try:
#                         result = json.loads(candidate)
#                         if isinstance(result, dict):
#                             return result
#                     except json.JSONDecodeError:
#                         break

#     raise ModelResponseError(
#         f"The model returned malformed or incomplete JSON. "
#         f"Raw response: {text[:2000]}"
#     )


# def assess_class(transcript: str, audio_metrics: dict, model: str, duration_seconds: float) -> dict:
#     rubric_text = "\n".join(
#         f"- {name}: weight {weight:.0%}" for name, weight in WEIGHTS.items()
#     )
    
#     system_prompt = f"""
# You evaluate the quality of recorded online classes for children.

# Use only the supplied transcript and audio measurements.
# Never invent student responses, visual details, or timestamps.
# A transcript alone cannot establish actual student engagement or visual quality.
# When evidence is insufficient, say so clearly.

# Score each of these five dimensions from 1 to 5:
# {rubric_text}

# Return exactly one JSON object. Follow this structure:
# {{
#   "dimension_scores": {{
#     "teaching_clarity": {{
#       "score": 3,
#       "reason": "Brief evidence-based explanation.",
#       "evidence_status": "supported"
#     }},
#     "lesson_structure": {{
#       "score": 3,
#       "reason": "Brief evidence-based explanation.",
#       "evidence_status": "supported"
#     }},
#     "student_engagement_evidence": {{
#       "score": 3,
#       "reason": "Transcript does not establish actual student participation.",
#       "evidence_status": "limited"
#     }},
#     "audio_quality": {{
#       "score": 3,
#       "reason": "Audio measurements alone cannot establish perceived quality.",
#       "evidence_status": "limited"
#     }},
#     "visual_presentation_evidence": {{
#       "score": 1,
#       "reason": "No visual evidence was supplied for assessment.",
#       "evidence_status": "unavailable"
#     }}
#   }},
#   "strengths": ["One specific supported strength."],
#   "improvements": ["One actionable improvement."],
#   "evidence": [
#     {{
#       "timestamp": "00:00",
#       "observation": "Brief observation supported by the transcript.",
#       "source": "transcript"
#     }}
#   ],
#   "limitations": ["State what cannot be determined."]
# }}

# STRICT RULES:
# - dimension_scores MUST be a JSON object, not a list.
# - Use exactly the five dimension names shown above.
# - Each dimension must contain score, reason, and evidence_status.
# - Scores must be integers from 1 through 5.
# - evidence_status must be "supported", "limited", or "unavailable".
# - Keep reasons and observations short to avoid repetitive output.
# - Do not include extra keys, Markdown, or text outside the JSON.
# - Do not return a lesson plan, class summary, or general review.
# - Return one complete, syntactically valid JSON object.
# """


#     user_prompt = (
#         f"Recording duration: {duration_seconds:.1f} seconds\n\n"
#         f"Basic audio indicators:\n{json.dumps(audio_metrics, ensure_ascii=False)}\n\n"
#         f"Timestamped transcript:\n{transcript[:24000]}\n\n"
#         "Assess this class now. Cite transcript timestamps only when they are present in the transcript."
#         "\n\nSTRICT REQUIREMENT: Return ONLY a JSON object containing "
#         "'dimension_scores' with these exact five keys: "
#         "'teaching_clarity', 'lesson_structure', "
#         "'student_engagement_evidence', 'audio_quality', and "
#         "'visual_presentation_evidence'. Each key must contain "
#         "{'score': integer from 1 to 5, 'reason': string, "
#         "'evidence_status': string}. Also include 'strengths', "
#         "'improvements', 'evidence', and 'limitations'. "
#         "Do not return an overall review or alternative categories."
#     )

#     try:
#         response = requests.post(
#             OLLAMA_URL,
#             json={
#                 "model": model,
#                 "stream": False,
#                 "format": "json",
#                 "messages": [
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_prompt},
#                 ],
#                 "format": "json",
#                 "options": {
#                     "temperature": 0.2,
#                     "num_ctx": 4096,
#                     "num_predict": 1200,
#                     "repeat_penalty": 1.15,
#                 },

#             },
#             timeout=600,
#         )
#     except requests.RequestException as exc:
#         raise OllamaUnavailable(
#             "Could not connect to Ollama at http://localhost:11434. "
#             "Install/start Ollama and download the selected model."
#         ) from exc

#     if response.status_code != 200:
#         detail = response.text[:800]
#         raise OllamaUnavailable(
#             f"Ollama returned HTTP {response.status_code}. "
#             f"Make sure model '{model}' is downloaded. Details: {detail}"
#         )

#     try:
#         raw = response.json()["message"]["content"]
#         print("OLLAMA RAW RESPONSE:", repr(raw[:3000]), flush=True)
#         print(
#             "OLLAMA DONE REASON:",
#             response.json().get("done_reason"),
#             flush=True,
#         )
#     except (ValueError, KeyError, TypeError) as exc:
#         raise ModelResponseError("Unexpected response from Ollama.") from exc

    
#     result = _extract_json(raw)
    
#     scores = result.get("dimension_scores", {})

#     # Some models return a list instead of the required dictionary.
    
#     if isinstance(scores, list):
#         # The model omitted dimension names, so map scores by rubric order.
#         dimension_names = list(DIMENSIONS)

#         if len(scores) != len(dimension_names):
#             raise ModelResponseError(
#                 f"Expected {len(dimension_names)} dimension scores, "
#                 f"but the model returned {len(scores)}."
#             )

#         converted = {}

#         for name, item in zip(dimension_names, scores):
#             if not isinstance(item, dict):
#                 continue

#             status = str(item.get("evidence_status", "limited")).lower()
#             if status == "present":
#                 status = "supported"
#             if status not in ("supported", "limited", "unavailable"):
#                 status = "limited"

#             converted[name] = {
#                 "score": item.get("score"),
#                 "reason": item.get("reason", "No reason returned."),
#                 "evidence_status": status,
#             }

#         scores = converted

#     elif not isinstance(scores, dict):
#         raise ModelResponseError(
#             "Ollama returned an unsupported dimension_scores format. "
#             f"Received type: {type(scores).__name__}"
#         )

#     # Validate that at least one recognized dimension was returned.
#     if not any(
#         isinstance(scores.get(dim), dict)
#         and isinstance(scores[dim].get("score"), (int, float))
#         and 1 <= scores[dim]["score"] <= 5
#         for dim in DIMENSIONS
#     ):
#         raise ModelResponseError(
#                 "Ollama returned no valid dimension scores. "
#                 f"Received dimensions: {list(scores.keys())}"
#         )   

#         result["dimension_scores"] = scores

#     # Match dimension names even if the model uses spaces or different casing.
#     def normalize_key(value):
#         return re.sub(r"[^a-z0-9]", "", str(value).lower())

#     score_lookup = {
#         normalize_key(key): value
#         for key, value in scores.items()
#     }

#     normalized = {}
#     valid_score_count = 0

#     for dim in DIMENSIONS:
#         item = scores.get(dim)

#         if not isinstance(item, dict):
#             item = score_lookup.get(normalize_key(dim), {})

#         if not isinstance(item, dict):
#             item = {}

#         score = item.get("score")

#         # Accept integers, floats, and numeric strings such as "4" or "4.0".
#         if isinstance(score, str):
#             match = re.search(r"^\s*([1-5])(?:\.0+)?\s*$", score)
#             score = int(match.group(1)) if match else None

#         if (
#             isinstance(score, (int, float))
#             and not isinstance(score, bool)
#             and 1 <= score <= 5
#         ):
#             score = int(round(score))
#             valid_score_count += 1
#         else:
#             score = None

#         normalized[dim] = {
#             "score": score,
#             "reason": str(item.get("reason", "No reason returned.")),
#             "evidence_status": str(
#                 item.get("evidence_status", "limited")
#             ),
#         }

#     if valid_score_count == 0:
#         returned_keys = list(scores.keys())
#         raise ModelResponseError(
#             "Ollama returned no valid dimension scores. "
#             f"Expected dimensions: {list(DIMENSIONS)}. "
#             f"Received dimensions: {returned_keys}. "
#             f"Raw response: {raw[:1500]}"
#         )

#     result["dimension_scores"] = normalized
#     result["overall_score"] = weighted_score(normalized)
#     result["strengths"] = _as_string_list(result.get("strengths"))
#     result["improvements"] = _as_string_list(result.get("improvements"))
#     result["limitations"] = _as_string_list(result.get("limitations"))
#     result["evidence"] = _normalize_evidence(result.get("evidence"))
#     return result


# def _as_string_list(value):
#     if not isinstance(value, list):
#         return []
#     return [str(item) for item in value if isinstance(item, (str, int, float))]


# def _normalize_evidence(value):
#     if not isinstance(value, list):
#         return []
#     output = []
#     for item in value:
#         if isinstance(item, dict):
#             output.append({
#                 "timestamp": str(item.get("timestamp", "")),
#                 "observation": str(item.get("observation", "")),
#                 "source": str(item.get("source", "transcript")),
#             })
#     return output

"""Local Ollama-based class assessment with JSON validation."""

import json
import re
import requests

from rubric import DIMENSIONS, WEIGHTS, weighted_score


class OllamaUnavailable(RuntimeError):
    pass


class ModelResponseError(RuntimeError):
    pass


OLLAMA_URL = "http://localhost:11434/api/chat"



def _extract_json(text: str) -> dict:
    """Extract a valid JSON object from an Ollama response."""
    text = text.strip()

    # Remove Markdown code fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Try parsing the entire response first.
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Find a JSON object, accounting for braces inside quoted strings.
    start = text.find("{")
    if start == -1:
        raise ModelResponseError(
            f"No JSON object found in model response. "
            f"Raw response: {text[:1500]}"
        )

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        char = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1

                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        result = json.loads(candidate)
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        break

    raise ModelResponseError(
        f"The model returned malformed or incomplete JSON. "
        f"Raw response: {text[:2000]}"
    )


def assess_class(transcript: str, audio_metrics: dict, model: str, duration_seconds: float) -> dict:
    rubric_text = "\n".join(
        f"- {name}: weight {weight:.0%}" for name, weight in WEIGHTS.items()
    )
    
    system_prompt = f"""
You evaluate the quality of recorded online classes for children.

Use only the supplied transcript and audio measurements.
Never invent student responses, visual details, or timestamps.
A transcript alone cannot establish actual student engagement or visual quality.
When evidence is insufficient, say so clearly.

Score each of these five dimensions from 1 to 5:
{rubric_text}

Return exactly one JSON object. Follow this structure:
{{
  "dimension_scores": {{
    "teaching_clarity": {{
      "score": 3,
      "reason": "Brief evidence-based explanation.",
      "evidence_status": "supported"
    }},
    "lesson_structure": {{
      "score": 3,
      "reason": "Brief evidence-based explanation.",
      "evidence_status": "supported"
    }},
    "student_engagement_evidence": {{
      "score": 3,
      "reason": "Transcript does not establish actual student participation.",
      "evidence_status": "limited"
    }},
    "audio_quality": {{
      "score": 3,
      "reason": "Audio measurements alone cannot establish perceived quality.",
      "evidence_status": "limited"
    }},
    "visual_presentation_evidence": {{
      "score": 1,
      "reason": "No visual evidence was supplied for assessment.",
      "evidence_status": "unavailable"
    }}
  }},
  "strengths": ["One specific supported strength."],
  "improvements": ["One actionable improvement."],
  "evidence": [
    {{
      "timestamp": "00:00",
      "observation": "Brief observation supported by the transcript.",
      "source": "transcript"
    }}
  ],
  "limitations": ["State what cannot be determined."]
}}

STRICT RULES:
- dimension_scores MUST be a JSON object, not a list.
- Use exactly the five dimension names shown above.
- Each dimension must contain score, reason, and evidence_status.
- Scores must be integers from 1 through 5.
- evidence_status must be "supported", "limited", or "unavailable".
- Keep reasons and observations short to avoid repetitive output.
- Do not include extra keys, Markdown, or text outside the JSON.
- Do not return a lesson plan, class summary, or general review.
- Return one complete, syntactically valid JSON object.
"""


    user_prompt = (
        f"Recording duration: {duration_seconds:.1f} seconds\n\n"
        f"Basic audio indicators:\n{json.dumps(audio_metrics, ensure_ascii=False)}\n\n"
        f"Timestamped transcript:\n{transcript[:24000]}\n\n"
        "Assess this class now. Cite transcript timestamps only when they are present in the transcript."
        "\n\nSTRICT REQUIREMENT: Return ONLY a JSON object containing "
        "'dimension_scores' with these exact five keys: "
        "'teaching_clarity', 'lesson_structure', "
        "'student_engagement_evidence', 'audio_quality', and "
        "'visual_presentation_evidence'. Each key must contain "
        "{'score': integer from 1 to 5, 'reason': string, "
        "'evidence_status': string}. Also include 'strengths', "
        "'improvements', 'evidence', and 'limitations'. "
        "Do not return an overall review or alternative categories."
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 4096,
                    "num_predict": 1200,
                    "repeat_penalty": 1.15,
                },

            },
            timeout=600,
        )
    except requests.RequestException as exc:
        raise OllamaUnavailable(
            "Could not connect to Ollama at http://localhost:11434. "
            "Install/start Ollama and download the selected model."
        ) from exc

    if response.status_code != 200:
        detail = response.text[:800]
        raise OllamaUnavailable(
            f"Ollama returned HTTP {response.status_code}. "
            f"Make sure model '{model}' is downloaded. Details: {detail}"
        )

    try:
        raw = response.json()["message"]["content"]
        print("OLLAMA RAW RESPONSE:", repr(raw[:3000]), flush=True)
        print(
            "OLLAMA DONE REASON:",
            response.json().get("done_reason"),
            flush=True,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise ModelResponseError("Unexpected response from Ollama.") from exc

    
    result = _extract_json(raw)
    
    scores = result.get("dimension_scores", {})

    # Some models return a list instead of the required dictionary.
    
    if isinstance(scores, list):
        # The model omitted dimension names, so map scores by rubric order.
        dimension_names = list(DIMENSIONS)

        if len(scores) != len(dimension_names):
            raise ModelResponseError(
                f"Expected {len(dimension_names)} dimension scores, "
                f"but the model returned {len(scores)}."
            )

        converted = {}

        for name, item in zip(dimension_names, scores):
            if not isinstance(item, dict):
                continue

            status = str(item.get("evidence_status", "limited")).lower()
            if status == "present":
                status = "supported"
            if status not in ("supported", "limited", "unavailable"):
                status = "limited"

            converted[name] = {
                "score": item.get("score"),
                "reason": item.get("reason", "No reason returned."),
                "evidence_status": status,
            }

        scores = converted

    elif not isinstance(scores, dict):
        raise ModelResponseError(
            "Ollama returned an unsupported dimension_scores format. "
            f"Received type: {type(scores).__name__}"
        )

    # Validate that at least one recognized dimension was returned.
    if not any(
        isinstance(scores.get(dim), dict)
        and isinstance(scores[dim].get("score"), (int, float))
        and 1 <= scores[dim]["score"] <= 5
        for dim in DIMENSIONS
    ):
        raise ModelResponseError(
                "Ollama returned no valid dimension scores. "
                f"Received dimensions: {list(scores.keys())}"
        )   

        result["dimension_scores"] = scores

    # Match dimension names even if the model uses spaces or different casing.
    def normalize_key(value):
        return re.sub(r"[^a-z0-9]", "", str(value).lower())

    score_lookup = {
        normalize_key(key): value
        for key, value in scores.items()
    }

    normalized = {}
    valid_score_count = 0

    for dim in DIMENSIONS:
        item = scores.get(dim)

        if not isinstance(item, dict):
            item = score_lookup.get(normalize_key(dim), {})

        if not isinstance(item, dict):
            item = {}

        score = item.get("score")

        # Accept integers, floats, and numeric strings such as "4" or "4.0".
        if isinstance(score, str):
            match = re.search(r"^\s*([1-5])(?:\.0+)?\s*$", score)
            score = int(match.group(1)) if match else None

        if (
            isinstance(score, (int, float))
            and not isinstance(score, bool)
            and 1 <= score <= 5
        ):
            score = int(round(score))
            valid_score_count += 1
        else:
            score = None

        normalized[dim] = {
            "score": score,
            "reason": str(item.get("reason", "No reason returned.")),
            "evidence_status": str(
                item.get("evidence_status", "limited")
            ),
        }

    if valid_score_count == 0:
        returned_keys = list(scores.keys())
        raise ModelResponseError(
            "Ollama returned no valid dimension scores. "
            f"Expected dimensions: {list(DIMENSIONS)}. "
            f"Received dimensions: {returned_keys}. "
            f"Raw response: {raw[:1500]}"
        )

    result["dimension_scores"] = normalized
    result["overall_score"] = weighted_score(normalized)
    result["strengths"] = _as_string_list(result.get("strengths"))
    result["improvements"] = _as_string_list(result.get("improvements"))
    result["limitations"] = _as_string_list(result.get("limitations"))
    result["evidence"] = _normalize_evidence(result.get("evidence"))
    return result


def _as_string_list(value):
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, (str, int, float))]


def _normalize_evidence(value):
    if not isinstance(value, list):
        return []
    output = []
    for item in value:
        if isinstance(item, dict):
            output.append({
                "timestamp": str(item.get("timestamp", "")),
                "observation": str(item.get("observation", "")),
                "source": str(item.get("source", "transcript")),
            })
    return output


