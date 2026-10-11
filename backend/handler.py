import json
import os
import re
from datetime import datetime, timezone
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")


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
    item = payload.get("item", "")
    supplied_material = payload.get("material", "")

    if not isinstance(item, str) or not isinstance(supplied_material, str):
        raise ValueError("'item' and 'material' must be strings.")

    item = item.strip()[:120]
    supplied_material = supplied_material.strip()[:40]

    if not item and not supplied_material:
        raise ValueError("Provide an 'item' or 'material'.")

    category = classify_material(item, supplied_material)

    if category == "unknown":
        return {
            "success": True,
            "analysis_type": "rules_based",
            "identified_material": "Unknown",
            "item": item,
            "confidence": None,
            "message": (
                "The material could not be determined from the supplied text. "
                "Please provide more details or consult a local waste service."
            ),
            "recommendations": [],
            "requires_local_verification": True,
        }

    guide = WASTE_GUIDES[category]

    return {
        "success": True,
        "analysis_type": "rules_based",
        "identified_material": guide["label"],
        "item": item or guide["label"],
        "confidence": None,
        "recommendations": {
            "reuse": guide["reuse"],
            "recycle": guide["recycle"],
            "upcycle": guide["upcycle"],
        },
        "safety": guide["safety"],
        "message": (
            "These recommendations are general guidance. "
            "Verify acceptance with your local waste collection service."
        ),
        "requires_local_verification": True,
    }


# --------------------------------------------------
# BASIC WASTE-MANAGEMENT CHAT
# --------------------------------------------------

def answer_chat(message: str) -> dict:
    text = message.lower()

    if any(word in text for word in ["plastic", "bottle", "wrapper"]):
        answer = (
            "For plastic, first check whether the item can be safely reused. "
            "If not, empty and rinse it, then check your local recycling rules. "
            "Never burn plastic."
        )
    elif any(word in text for word in ["compost", "food waste", "banana peel"]):
        answer = (
            "Suitable fruit and vegetable scraps can often be composted. "
            "Separate them from dry recyclables and manage the compost "
            "to discourage pests."
        )
    elif any(word in text for word in ["battery", "electronic", "e-waste", "ewaste"]):
        answer = (
            "Keep batteries and electronic waste out of ordinary household "
            "recycling. Use an authorized collection channel and do not "
            "dismantle damaged batteries."
        )
    elif any(word in text for word in ["earn", "money", "sell", "income"]):
        answer = (
            "Some recyclers pay for specific materials, depending on quality, "
            "quantity, and location. Contact local authorized scrap dealers "
            "or recycling centers to verify accepted materials and prices."
        )
    elif any(word in text for word in ["energy", "biogas", "waste-to-energy"]):
        answer = (
            "Some organic waste can support controlled anaerobic digestion "
            "to produce biogas. Suitable waste-to-energy processes depend "
            "on the material, equipment, emissions controls, and local rules. "
            "Do not burn household waste."
        )
    else:
        answer = (
            "Start by separating waste into reusable items, dry recyclables, "
            "organic waste, and hazardous or electronic waste. Follow local "
            "collection rules, and prioritize reduction and reuse."
        )

    return {
        "success": True,
        "assistant": "EcoLoop Guide",
        "answer": answer,
        "analysis_type": "rules_based",
        "message": "This response uses predefined guidance, not a live AI model.",
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
