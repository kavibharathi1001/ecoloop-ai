import json
import os
import re
from datetime import datetime, timezone
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from groq import Groq
import base64
import binascii
import logging

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
# --------------------------------------------------
# GROQ AI CONFIGURATION
# --------------------------------------------------

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

GROQ_VISION_MODEL = os.environ.get(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.8-27b",
)

groq_client = (
    Groq(
        api_key=GROQ_API_KEY,
        timeout=15.0,
        max_retries=0,
    )
    if GROQ_API_KEY
    else None
)


def generate_ai_response(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 700,
) -> str:
    """Generate a response using Groq with safe response validation."""

    if groq_client is None:
        raise RuntimeError("Groq API is not configured.")

    completion = groq_client.chat.completions.create(
    model=GROQ_MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                system_prompt
                + "\n\nGive the final answer directly. "
                  "Keep internal reasoning brief. "
                  "Do not output internal reasoning. "
                  "Return a concise, useful response."
            ),
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ],
    temperature=0.4,
    max_completion_tokens=max(max_tokens, 1500),
)

    if not completion.choices:
        logging.error(
            "Groq returned no choices. Model=%s, usage=%s",
            GROQ_MODEL,
            getattr(completion, "usage", None),
        )
        raise RuntimeError("The AI model returned no choices.")

    choice = completion.choices[0]
    message = choice.message
    answer = message.content

    if isinstance(answer, str) and answer.strip():
        return answer.strip()

    # Capture diagnostic metadata without logging prompts or secrets.
    refusal = getattr(message, "refusal", None)
    finish_reason = getattr(choice, "finish_reason", None)

    logging.warning(
        "Groq returned no usable text. Model=%s, finish_reason=%s, "
        "refusal_present=%s, usage=%s",
        GROQ_MODEL,
        finish_reason,
        bool(refusal),
        getattr(completion, "usage", None),
    )

    if refusal:
        raise RuntimeError("The AI model declined the request.")

    raise RuntimeError(
        "The AI model returned no usable text "
        f"(finish_reason={finish_reason})."
    )

# --------------------------------------------------
# HTTP RESPONSE
# --------------------------------------------------

def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(
            body,
            ensure_ascii=False,
            default=lambda value: int(value)
            if isinstance(value, Decimal) and value % 1 == 0
            else float(value)
            if isinstance(value, Decimal)
            else str(value),
        ),
    }


def parse_body(event: dict) -> dict:
    body = event.get("body")

    if not body:
        return {}

    if isinstance(body, dict):
        return body

    if event.get("isBase64Encoded"):
        raise ValueError("Base64-encoded request bodies are not supported.")

    parsed = json.loads(body)

    if not isinstance(parsed, dict):
        raise ValueError("Request body must be a JSON object.")

    return parsed


# --------------------------------------------------
# WASTE RECOMMENDATION RULES
# --------------------------------------------------

WASTE_GUIDES = {
    "plastic": {
        "label": "Plastic",
        "reuse": [
            "Reuse a clean, intact container when it is safe for that purpose.",
            "Avoid reusing containers for food if they are not food-safe.",
        ],
        "recycle": [
            "Empty and rinse the item.",
            "Check the resin code and your local recycling rules.",
            "Keep plastic separate from wet and food-contaminated waste.",
        ],
        "upcycle": [
            "Create a planter from a suitable clean container.",
            "Use clean packaging for a small storage or craft project.",
        ],
        "safety": [
            "Never burn plastic; it can release harmful fumes.",
            "Do not cut containers into sharp-edged pieces without suitable tools.",
        ],
    },
    "paper": {
        "label": "Paper and cardboard",
        "reuse": [
            "Reuse clean paper for notes or drafts.",
            "Reuse intact cardboard boxes for storage or packing.",
        ],
        "recycle": [
            "Keep paper dry and free from food contamination.",
            "Remove non-paper materials when practical.",
            "Check local rules for coated or laminated paper.",
        ],
        "upcycle": [
            "Make paper crafts or gift tags.",
            "Turn suitable cardboard into desk organizers.",
        ],
        "safety": [
            "Keep paper away from flames and heat sources.",
        ],
    },
    "glass": {
        "label": "Glass",
        "reuse": [
            "Reuse an intact jar for storage after cleaning it properly.",
        ],
        "recycle": [
            "Separate glass according to your local collection rules.",
            "Keep broken glass separate and clearly contained.",
        ],
        "upcycle": [
            "Use an intact jar as a decorative container.",
        ],
        "safety": [
            "Never handle broken glass with bare hands.",
            "Do not place broken glass in ordinary recycling unless local rules allow it.",
        ],
    },
    "metal": {
        "label": "Metal",
        "reuse": [
            "Reuse a clean, undamaged metal container for a suitable purpose.",
        ],
        "recycle": [
            "Empty the container and check local metal collection rules.",
            "Separate sharp or contaminated metal safely.",
        ],
        "upcycle": [
            "Turn a safe, clean metal container into a desk organizer.",
        ],
        "safety": [
            "Watch for sharp edges and rust.",
            "Do not cut metal without appropriate equipment and supervision.",
        ],
    },
    "organic": {
        "label": "Organic waste",
        "reuse": [
            "Use suitable fruit and vegetable scraps for home composting.",
        ],
        "recycle": [
            "Separate food scraps from dry recyclable materials.",
            "Use a suitable composting or local organic-waste collection system.",
        ],
        "upcycle": [
            "Create compost from suitable fruit and vegetable scraps.",
        ],
        "safety": [
            "Do not compost meat, dairy, or other difficult materials unless your system supports them.",
            "Keep compost appropriately managed to discourage pests.",
        ],
    },
    "electronic": {
        "label": "Electronic waste",
        "reuse": [
            "Consider repair or donation if the device is functional and safe.",
        ],
        "recycle": [
            "Use an authorized e-waste collection or recycling channel.",
            "Follow the device manufacturer's instructions for data removal.",
        ],
        "upcycle": [
            "Reuse intact, safe components only when you have the required skills.",
        ],
        "safety": [
            "Do not dismantle batteries or damaged electronic devices.",
            "Never put batteries or electronic waste in ordinary household recycling.",
        ],
    },
    "textile": {
        "label": "Textiles and clothing",
        "reuse": [
            "Donate clean, usable clothing where accepted.",
            "Repair clothing before discarding it.",
        ],
        "recycle": [
            "Find a textile collection program that accepts the material.",
            "Keep reusable textiles dry and clean.",
        ],
        "upcycle": [
            "Turn old fabric into cleaning cloths or reusable bags.",
        ],
        "safety": [
            "Do not donate wet, moldy, or contaminated textiles.",
        ],
    },
}


KEYWORDS = {
    "plastic": [
        "plastic", "bottle", "polythene", "polyethylene", "wrapper",
        "plastic bag", "pet bottle",
    ],
    "paper": [
        "paper", "cardboard", "carton", "newspaper", "notebook",
        "paper box",
    ],
    "glass": [
        "glass", "glass bottle", "glass jar",
    ],
    "metal": [
        "metal", "aluminium", "aluminum", "steel can", "tin can",
        "metal can",
    ],
    "organic": [
        "organic", "food waste", "vegetable scraps", "fruit scraps",
        "banana peel", "leaves", "food scraps",
    ],
    "electronic": [
        "electronic", "e-waste", "ewaste", "battery", "mobile phone",
        "phone", "laptop", "charger", "circuit board",
    ],
    "textile": [
        "textile", "clothes", "clothing", "fabric", "old shirt",
        "old jeans",
    ],
}


def classify_material(item: str, supplied_material: str = "") -> str:
    material = supplied_material.strip().lower()

    if material in WASTE_GUIDES:
        return material

    text = item.lower()

    for category, keywords in KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "unknown"


def analyze_waste(payload: dict) -> dict:
    """Analyze waste with Groq when available; otherwise use local rules."""

    item = payload.get("item", "")
    supplied_material = payload.get("material", "")

    if not isinstance(item, str) or not isinstance(supplied_material, str):
        raise ValueError("'item' and 'material' must be strings.")

    item = item.strip()[:120]
    supplied_material = supplied_material.strip()[:40]

    if not item and not supplied_material:
        raise ValueError("Provide an 'item' or 'material'.")

    # Reliable offline classification and recommendations.
    material_key = classify_material(item, supplied_material)
    guide = WASTE_GUIDES.get(material_key, WASTE_GUIDES.get("unknown", {}))

    material_labels = {
        "plastic": "Plastic",
        "paper": "Paper",
        "glass": "Glass",
        "metal": "Metal",
        "organic": "Organic waste",
        "electronic": "Electronic waste",
        "textile": "Textile",
        "unknown": "Unknown",
    }

    fallback_result = {
        "success": True,
        "analysis_type": "rules_based",
        "identified_material": material_labels.get(material_key, "Unknown"),
        "item": item or supplied_material,
        "confidence": None,
        "message": (
            "Material identified using local rules. "
            "Check local recycling requirements before disposal."
        ),
        "recommendations": {
            "reuse": guide.get("reuse", []),
            "recycle": guide.get("recycle", []),
            "upcycle": guide.get("upcycle", []),
        },
        "safety": guide.get("safety", []),
        "requires_local_verification": True,
    }

    # Prefer AI when configured. Fall back to rules if it fails.
    if groq_client is None:
        return fallback_result

    system_prompt = """
You are EcoLoop AI, an expert in waste classification and circular economy.
Return ONLY valid JSON with these fields:
{
  "identified_material": "material name",
  "item": "normalized item description",
  "message": "brief explanation",
  "recommendations": {
    "reuse": ["practical suggestion"],
    "recycle": ["practical suggestion"],
    "upcycle": ["practical suggestion"]
  },
  "safety": ["important precautions"],
  "requires_local_verification": true
}
Never recommend burning waste or dismantling batteries.
Never invent recycling facilities, prices, or carbon savings.
If uncertain, say so. Local recycling rules must be verified.
Return JSON without Markdown fences.
"""

    try:
        raw_answer = generate_ai_response(
            system_prompt=system_prompt,
            user_prompt=(
                f"Item description: {item or 'Not provided'}\n"
                f"User-supplied material: {supplied_material or 'Not provided'}"
            ),
            max_tokens=600,
        )

        result = json.loads(raw_answer)
        required = {
            "identified_material",
            "item",
            "message",
            "recommendations",
            "safety",
            "requires_local_verification",
        }

        if not isinstance(result, dict) or not required.issubset(result):
            raise ValueError("Invalid AI response structure.")

        recommendations = result["recommendations"]
        if not isinstance(recommendations, dict):
            raise ValueError("Invalid recommendations.")

        for category in ("reuse", "recycle", "upcycle"):
            values = recommendations.get(category)
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                raise ValueError("Invalid recommendation list.")

        safety = result["safety"]
        if not isinstance(safety, list) or not all(
            isinstance(value, str) for value in safety
        ):
            raise ValueError("Invalid safety list.")

        return {
            "success": True,
            "analysis_type": "groq_llm",
            "identified_material": str(result["identified_material"])[:80],
            "item": str(result["item"])[:120],
            "confidence": None,
            "message": str(result["message"])[:500],
            "recommendations": {
                category: recommendations[category][:5]
                for category in ("reuse", "recycle", "upcycle")
            },
            "safety": safety[:8],
            "requires_local_verification": True,
        }

    except Exception as exc:
        logging.warning(
            "Groq waste analysis failed; using rules fallback: %s",
            type(exc).__name__,
        )
        return fallback_result

def analyze_waste_image(payload: dict) -> dict:
    """Analyze an uploaded waste photograph using Groq vision."""

    image_data = payload.get("image")
    mime_type = payload.get("mimeType", "image/jpeg")
    description = payload.get("description", "")

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if not isinstance(image_data, str) or not image_data:
        raise ValueError("An image is required.")

    if mime_type not in allowed_types:
        raise ValueError(
            "Supported image types are JPEG, PNG and WebP."
        )

    if not isinstance(description, str):
        raise ValueError("Description must be text.")

    # Accept a plain base64 string or a data URL.
    if image_data.startswith("data:"):
        header, separator, image_data = image_data.partition(",")

        if not separator or not header.endswith(";base64"):
            raise ValueError("Invalid image data URL.")

        declared_type = header[5:].split(";")[0]

        if declared_type != mime_type:
            raise ValueError("Image MIME type does not match.")

    # Reject oversized encoded requests before decoding.
    if len(image_data) > 4_200_000:
        raise ValueError(
            "Image is too large. Upload an image under 3 MB."
        )

    try:
        image_bytes = base64.b64decode(
            image_data,
            validate=True,
        )
    except (binascii.Error, ValueError):
        raise ValueError("The image is not valid base64 data.")

    if not image_bytes:
        raise ValueError("The uploaded image is empty.")

    if len(image_bytes) > 3 * 1024 * 1024:
        raise ValueError("Image must be smaller than 3 MB.")

    # Verify the file signature rather than trusting the MIME type.
    signatures = {
        "image/jpeg": lambda b: b.startswith(b"\xff\xd8\xff"),
        "image/png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda b: (
            len(b) >= 12
            and b.startswith(b"RIFF")
            and b[8:12] == b"WEBP"
        ),
    }

    if not signatures[mime_type](image_bytes):
        raise ValueError(
            "The image contents do not match the declared file type."
        )

    if groq_client is None:
        raise RuntimeError("Groq API is not configured.")

    prompt = f"""
You are EcoLoop AI, an environmental waste identification assistant.

Examine the actual uploaded photograph and identify the visible waste.

Return ONLY a valid JSON object with this structure:

{{
  "item": "short description of the visible item",
  "identified_material": "plastic, paper, glass, metal, organic, electronic, textile, or unknown",
  "confidence": "high, medium, or low",
  "observations": ["visible characteristics"],
  "recommendations": {{
    "reuse": ["practical reuse suggestions"],
    "recycle": ["safe recycling suggestions"],
    "upcycle": ["creative upcycling suggestions"]
  }},
  "safety": ["relevant precautions"],
  "requires_local_verification": true
}}

Rules:
- Base your answer on the photograph, not an assumed item.
- If the image is unclear, say so and use low confidence.
- Do not claim certainty about material composition when it cannot
  be determined visually.
- Do not invent recycling centres, prices, or carbon savings.
- Never recommend burning waste or unsafe handling of batteries.
- Explain that local recycling acceptance must be verified.
- Keep recommendations concise.
- User's optional description: {description[:300]}
"""

    completion = groq_client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,{image_data}"
                            ),
                        },
                    },
                ],
            }
        ],
        temperature=0.2,
        max_completion_tokens=1000,
        response_format={"type": "json_object"},
    )

    answer = completion.choices[0].message.content

    if not answer:
        raise RuntimeError("The vision model returned no result.")

    result = json.loads(answer)

    if not isinstance(result, dict):
        raise ValueError("Invalid vision response.")

    recommendations = result.get("recommendations")

    if not isinstance(recommendations, dict):
        raise ValueError("Missing recommendations.")

    for category in ("reuse", "recycle", "upcycle"):
        if not isinstance(recommendations.get(category), list):
            raise ValueError("Invalid recommendation structure.")

    if not isinstance(result.get("safety"), list):
        raise ValueError("Invalid safety information.")

    return {
        "success": True,
        "analysis_type": "groq_vision",
        "model": GROQ_VISION_MODEL,
        "item": str(result.get("item", "Unknown item"))[:200],
        "identified_material": str(
            result.get("identified_material", "unknown")
        )[:40],
        "confidence": result.get("confidence", "low"),
        "observations": [
            str(x)[:300] for x in result.get("observations", [])[:5]
        ],
        "recommendations": {
            category: [
                str(x)[:300] for x in recommendations[category][:5]
            ]
            for category in ("reuse", "recycle", "upcycle")
        },
        "safety": [
            str(x)[:300] for x in result["safety"][:8]
        ],
        "requires_local_verification": True,
    }
# --------------------------------------------------
# BASIC WASTE-MANAGEMENT CHAT
# --------------------------------------------------

def answer_chat(message: str) -> dict:
    """Answer environmental questions using a live Groq model."""

    system_prompt = """
You are EcoLoop Guide, an expert AI assistant for waste reduction,
recycling, reuse, upcycling, composting, circular economy, and
responsible waste-to-energy practices.

Your goals:
1. Give practical, clear and environmentally responsible guidance.
2. Explain how users can reduce waste before recycling it.
3. Suggest reuse, recycling and upcycling options where appropriate.
4. Explain safe ways to separate waste.
5. Never recommend burning plastic or household waste.
6. Never recommend dismantling damaged batteries or unsafe electronics.
7. Do not invent local recycling facilities, collection schedules,
   recycling prices, or environmental impact measurements.
8. Explain when advice depends on local rules.
9. Use simple language and numbered steps when useful.
10. If asked about earning money from waste, explain that prices and
    acceptance depend on local recyclers and must be verified.
11. Be honest about uncertainty and environmental claims.
12. Keep the response helpful and reasonably concise.

You are a sustainability guide, not a substitute for local
environmental regulations or professional hazardous-waste advice.
"""

    try:
        answer = generate_ai_response(
            system_prompt=system_prompt,
            user_prompt=message,
            max_tokens=700,
        )

        return {
            "success": True,
            "assistant": "EcoLoop AI",
            "answer": answer,
            "analysis_type": "groq_llm",
            "model": GROQ_MODEL,
        }

    except Exception as exc:
        logging.error(
            "EcoLoop chat failed: %s: %s",
            type(exc).__name__,
            str(exc)[:500],
        )
        return {
            "success": False,
            "assistant": "EcoLoop AI",
            "error": "AI temporarily unavailable",
            "message": (
                "The AI assistant could not respond right now. "
                "Please try again shortly."
            ),
        }
# --------------------------------------------------
# ACTION TRACKING AND IMPACT
# --------------------------------------------------

# ACTION TRACKING AND IMPACT
# Use in-memory storage for SAM Local development.
# Use DynamoDB when running in the deployed AWS Lambda environment.

# ACTION TRACKING AND IMPACT
ACTIONS_TABLE_NAME = os.environ.get("ACTIONS_TABLE")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "").strip()

LOCAL_ACTIONS = {}
dynamodb_table = None

if ACTIONS_TABLE_NAME and DYNAMODB_ENDPOINT:
    # Local development: explicitly connect to DynamoDB Local.
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=os.environ.get("AWS_REGION", "ap-south-1"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "local"),
        aws_secret_access_key=os.environ.get(
            "AWS_SECRET_ACCESS_KEY", "local"
        ),
        config=__import__("botocore.config", fromlist=["Config"]).Config(
            connect_timeout=2,
            read_timeout=3,
            retries={"max_attempts": 1},
        ),
    )
    dynamodb_table = dynamodb.Table(ACTIONS_TABLE_NAME)

elif ACTIONS_TABLE_NAME:
    # Deployed AWS Lambda: use the normal AWS DynamoDB endpoint.
    dynamodb = boto3.resource("dynamodb")
    dynamodb_table = dynamodb.Table(ACTIONS_TABLE_NAME)


ALLOWED_ACTION_TYPES = {
    "reused",
    "recycled",
    "composted",
    "donated",
    "repaired",
    "upcycled",
}


def save_action(payload: dict) -> dict:
    session_id = payload.get("sessionId")
    item = payload.get("item")
    material = payload.get("material")
    action_type = payload.get("actionType")
    quantity = payload.get("quantity", 1)

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("'sessionId' is required.")

    if len(session_id) > 100:
        raise ValueError("'sessionId' must be at most 100 characters.")

    if not isinstance(item, str) or not item.strip():
        raise ValueError("'item' is required.")

    if not isinstance(material, str) or not material.strip():
        raise ValueError("'material' is required.")

    if action_type not in ALLOWED_ACTION_TYPES:
        raise ValueError(
            "'actionType' must be one of: "
            + ", ".join(sorted(ALLOWED_ACTION_TYPES))
        )

    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValueError("'quantity' must be a positive integer.")

    if quantity < 1 or quantity > 10000:
        raise ValueError("'quantity' must be between 1 and 10000.")

    action = {
        "actionId": str(uuid.uuid4()),
        "sessionId": session_id.strip(),
        "item": item.strip()[:120],
        "material": material.strip().lower()[:40],
        "actionType": action_type,
        "quantity": quantity,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "verificationStatus": "self-reported",
    }

    if dynamodb_table is not None:
        dynamodb_table.put_item(Item=action)
    else:
        # Local-only fallback for development and automated tests.
        LOCAL_ACTIONS.setdefault(action["sessionId"], []).append(action)

    return {
        "success": True,
        "action": action,
        "storage": "dynamodb" if dynamodb_table is not None else "local-demo",
        "message": (
            "Action recorded as self-reported. "
            "This does not independently verify that recycling occurred."
        ),
    }


def get_session_actions(session_id: str) -> list:
    if not session_id or len(session_id) > 100:
        raise ValueError("A valid 'sessionId' is required.")

    if dynamodb_table is not None:
        result = dynamodb_table.query(
            KeyConditionExpression=Key("sessionId").eq(session_id),
            ScanIndexForward=False,
            Limit=100,
        )
        return result.get("Items", [])

    return list(LOCAL_ACTIONS.get(session_id, []))


def calculate_impact(session_id: str) -> dict:
    actions = get_session_actions(session_id)

    action_counts = {}
    material_counts = {}

    for action in actions:
        action_type = action["actionType"]
        material = action["material"]
        quantity = int(action["quantity"])

        action_counts[action_type] = (
            action_counts.get(action_type, 0) + quantity
        )
        material_counts[material] = (
            material_counts.get(material, 0) + quantity
        )

    return {
        "success": True,
        "sessionId": session_id,
        "totalReportedItems": sum(action_counts.values()),
        "totalRecordedActions": len(actions),
        "actionsByType": action_counts,
        "itemsByMaterial": material_counts,
        "verificationStatus": "self-reported",
        "carbonSavingsKg": None,
        "message": (
            "Counts represent user-reported records. "
            "Carbon savings have not been calculated or verified."
        ),
    }

# --------------------------------------------------
# API ROUTER
# --------------------------------------------------

def lambda_handler(event, context):
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "GET")
        .upper()
    )

    path = event.get("rawPath", "/").rstrip("/") or "/"

    if method == "OPTIONS":
        return response(200, {"message": "CORS preflight successful"})

    if method == "GET" and path == "/health":
        return response(
            200,
            {
                "status": "healthy",
                "service": "EcoLoop AI API",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    try:
        if method == "POST" and path == "/api/analyze":
            payload = parse_body(event)
            return response(200, analyze_waste(payload))

        if method == "POST" and path == "/api/analyze-image":
            payload = parse_body(event)

            try:
                result = analyze_waste_image(payload)
                return response(200, result)
            except ValueError as exc:
                return response(
                    400,
                    {
                        "success": False,
                        "error": str(exc),
                    },
                )
            except Exception:
                # Do not expose API keys or provider internals.
                return response(
                    502,
                    {
                        "success": False,
                        "error": "Image analysis is temporarily unavailable.",
                    },
                )


        if method == "POST" and path == "/api/chat":
            payload = parse_body(event)
            message = payload.get("message", "")

            if not isinstance(message, str):
                raise ValueError("'message' must be a string.")

            message = message.strip()

            if not message:
                raise ValueError("'message' cannot be empty.")

            if len(message) > 2000:
                raise ValueError("'message' must be at most 2000 characters.")

            return response(200, answer_chat(message))

        if method == "GET" and path == "/api/recycling":
            return response(
                200,
                {
                    "success": True,
                    "categories": [
                        {
                            "id": category,
                            "name": guide["label"],
                            "reuse": guide["reuse"],
                            "recycle": guide["recycle"],
                            "upcycle": guide["upcycle"],
                            "safety": guide["safety"],
                        }
                        for category, guide in WASTE_GUIDES.items()
                    ],
                    "message": (
                        "Verify collection availability and acceptance "
                        "with your local recycling service."
                    ),
                },
            )

        if method == "POST" and path == "/api/actions":
            payload = parse_body(event)
            return response(201, save_action(payload))

        if method == "GET" and path == "/api/actions":
            query = event.get("queryStringParameters") or {}
            session_id = query.get("sessionId", "")
            actions = get_session_actions(session_id)

            return response(
                200,
                {
                    "success": True,
                    "actions": actions,
                    "count": len(actions),
                    "storage": (
                        "dynamodb"
                        if dynamodb_table is not None
                        else "local-demo"
                    ),
                },
            )

        if method == "GET" and path == "/api/impact":
            query = event.get("queryStringParameters") or {}
            session_id = query.get("sessionId", "")

            return response(200, calculate_impact(session_id))

    except (ValueError, json.JSONDecodeError) as exc:
        return response(
            400,
            {
                "success": False,
                "error": "Invalid request",
                "message": str(exc),
            },
        )

    return response(
        404,
        {
            "success": False,
            "error": "Not found",
            "message": "This EcoLoop AI endpoint does not exist.",
        },
    )
