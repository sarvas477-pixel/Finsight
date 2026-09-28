"""Live and deterministic tools for FinSight Copilot."""

from __future__ import annotations

import ast
import operator
import re
import urllib.parse
import urllib.request
import json
from typing import Any


def _json_get(url: str, timeout: int = 8) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "FinSight-Copilot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather(city: str) -> str:
    """Fetch current weather using Open-Meteo, without requiring an API key."""
    city = city.strip() or "Delhi"
    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
    )
    geo = _json_get(geo_url)
    places = geo.get("results") or []
    if not places:
        return f"I couldn't find a location named {city!r}."

    place = places[0]
    lat, lon = place["latitude"], place["longitude"]
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                       "precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        })
    )
    data = _json_get(weather_url)
    current = data.get("current", {})

    codes = {
        0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "fog", 48: "depositing rime fog", 51: "light drizzle",
        53: "moderate drizzle", 55: "dense drizzle", 61: "slight rain",
        63: "moderate rain", 65: "heavy rain", 71: "slight snow",
        73: "moderate snow", 75: "heavy snow", 80: "rain showers",
        81: "moderate rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
    }
    condition = codes.get(current.get("weather_code"), "unknown conditions")
    name = place.get("name", city)
    country = place.get("country", "")
    return (
        f"Current weather in {name}{', ' + country if country else ''}: "
        f"{current.get('temperature_2m', '—')}°C, feels like "
        f"{current.get('apparent_temperature', '—')}°C, {condition}. "
        f"Humidity {current.get('relative_humidity_2m', '—')}%, "
        f"wind {current.get('wind_speed_10m', '—')} km/h."
    )


_ALLOWED_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculate(expression: str) -> str:
    """Safely evaluate arithmetic without eval()."""
    expression = expression.strip().replace("^", "**")
    if len(expression) > 300:
        return "That calculation is too long for the calculator tool."

    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large.")
            return _ALLOWED_BINOPS[type(node.op)](left, right)
        raise ValueError("Only arithmetic expressions are supported.")

    try:
        value = visit(tree)
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return f"{value:.12g}"
    except ZeroDivisionError:
        return "I can't divide by zero."
    except (SyntaxError, ValueError, TypeError):
        return "I couldn't parse that as a safe arithmetic expression."


def _extract_expression(question: str) -> str | None:
    q = question.lower().strip()
    if not re.search(r"\b(calculate|compute|what is|solve)\b", q):
        return None
    expr = re.sub(r"\b(calculate|compute|what is|solve)\b", "", q).strip()
    expr = expr.rstrip("?").strip()
    if re.fullmatch(r"[0-9\s+\-*/().%^]+", expr):
        return expr
    return None


def tool_route(question: str) -> dict[str, Any] | None:
    """Return a tool response when a local/live tool should answer the request."""
    q = " ".join(question.lower().split())

    weather_match = re.search(
        r"(?:weather|temperature|forecast)(?:\s+(?:in|at|for))?\s+([a-z][a-z .'-]{1,60})$",
        q,
    )
    if weather_match:
        city = weather_match.group(1).strip(" .?")
        try:
            return {"tool": "weather", "answer": get_weather(city)}
        except Exception:
            return {"tool": "weather", "answer": "I couldn't retrieve live weather right now. Please try again shortly."}

    if q in {"weather", "whats the weather", "what's the weather", "weather today",
              "whats the weather today", "what's the weather today"}:
        try:
            return {"tool": "weather", "answer": get_weather("Delhi")}
        except Exception:
            return {"tool": "weather", "answer": "I couldn't retrieve live weather right now. Please try again shortly."}

    expr = _extract_expression(question)
    if expr:
        return {"tool": "calculator", "answer": f"Calculation result: {calculate(expr)}"}

    return None
