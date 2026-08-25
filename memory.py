import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "preferences": {
            "home_airport": None,
            "preferred_airlines": [],
            "typical_trip_length": None,
            "seat_preference": None,
            "budget_range": None
        },
        "past_searches": [],
        "watched_routes": [],
        "conversation_history": []
    }

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def add_conversation(memory, role, content):
    memory["conversation_history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # Keep last 50 messages so the file doesn't grow forever
    if len(memory["conversation_history"]) > 50:
        memory["conversation_history"] = memory["conversation_history"][-50:]
    save_memory(memory)

def add_search(memory, search_type, details):
    memory["past_searches"].append({
        "type": search_type,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
    # Keep last 20 searches
    if len(memory["past_searches"]) > 20:
        memory["past_searches"] = memory["past_searches"][-20:]
    save_memory(memory)

def update_preferences(memory, key, value):
    memory["preferences"][key] = value
    save_memory(memory)

def add_watched_route(memory, origin, destination, outbound_date, return_date, threshold):
    memory["watched_routes"].append({
        "origin": origin,
        "destination": destination,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "threshold": threshold,
        "added": datetime.now().isoformat()
    })
    save_memory(memory)

def get_memory_summary(memory):
    summary = ""
    
    prefs = memory["preferences"]
    if any(prefs.values()):
        summary += "User preferences:\n"
        if prefs["home_airport"]:
            summary += f"- Home airport: {prefs['home_airport']}\n"
        if prefs["preferred_airlines"]:
            summary += f"- Preferred airlines: {', '.join(prefs['preferred_airlines'])}\n"
        if prefs["typical_trip_length"]:
            summary += f"- Typical trip length: {prefs['typical_trip_length']} days\n"
        if prefs["seat_preference"]:
            summary += f"- Seat preference: {prefs['seat_preference']}\n"
        if prefs["budget_range"]:
            summary += f"- Budget range: {prefs['budget_range']}\n"

    if memory["past_searches"]:
        summary += "\nRecent searches:\n"
        for s in memory["past_searches"][-5:]:
            summary += f"- {s['type']}: {s['details']} ({s['timestamp'][:10]})\n"

    if memory["watched_routes"]:
        summary += "\nCurrently watching:\n"
        for r in memory["watched_routes"]:
            summary += f"- {r['origin']} → {r['destination']} on {r['outbound_date']}, alert below ${r['threshold']}\n"

    return summary