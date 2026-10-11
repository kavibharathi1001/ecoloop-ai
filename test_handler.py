import json
import sys
import unittest

sys.path.insert(0, "backend")
from handler import lambda_handler


def make_event(method, path, body=None):
    event = {
        "requestContext": {
            "http": {"method": method}
        },
        "rawPath": path,
    }

    if body is not None:
        event["body"] = json.dumps(body)

    return event


def call_api(method, path, body=None):
    return lambda_handler(make_event(method, path, body), None)


class EcoLoopAPITests(unittest.TestCase):

    def test_health(self):
        result = call_api("GET", "/health")
        self.assertEqual(result["statusCode"], 200)

    def test_plastic_analysis(self):
        result = call_api(
            "POST",
            "/api/analyze",
            {"item": "plastic bottle"}
        )
        data = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(data["identified_material"], "Plastic")
        self.assertEqual(data["analysis_type"], "rules_based")

    def test_electronic_waste_safety(self):
        result = call_api(
            "POST",
            "/api/analyze",
            {"item": "old laptop"}
        )
        data = json.loads(result["body"])
        self.assertEqual(data["identified_material"], "Electronic waste")
        self.assertTrue(data["safety"])

    def test_chat(self):
        result = call_api(
            "POST",
            "/api/chat",
            {"message": "How should I dispose of a battery?"}
        )
        self.assertEqual(result["statusCode"], 200)

    def test_recycling_categories(self):
        result = call_api("GET", "/api/recycling")
        data = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 200)
        self.assertGreaterEqual(len(data["categories"]), 5)

    def test_missing_analysis_input(self):
        result = call_api("POST", "/api/analyze", {})
        self.assertEqual(result["statusCode"], 400)

    def test_unknown_endpoint(self):
        result = call_api("GET", "/unknown")
        self.assertEqual(result["statusCode"], 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
