import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_memory():
    result = supabase.table("memory").select("*").eq("id", "main").execute()
    if result.data:
        row = result.data[0]
        return {
            "preferences": row.get("preferences", {
                "home_airport": None,
                "preferred_airlines": [],
                "typical_trip_length": None,
                "seat_preference": None,
                "budget_range": None
            }),
            "past_searches": row.get("past_searches", []),
            "watched_routes": row.get("watched_routes", []),
            "conversation_history": row.get("conversation_history", []),
            "last_destination": row.get("last_destination")
        }
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
        "conversation_history": [],
        "last_destination": None
    }

def save_memory(memory):
    supabase.table("memory").upsert({
        "id": "main",
        "preferences": memory.get("preferences", {}),
        "past_searches": memory.get("past_searches", []),
        "watched_routes": memory.get("watched_routes", []),
        "conversation_history": memory.get("conversation_history", []),
        "last_destination": memory.get("last_destination"),
        "updated_at": datetime.now().isoformat()
    }).execute()

def add_conversation(memory, role, content):
    memory["conversation_history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    if len(memory["conversation_history"]) > 50:
        memory["conversation_history"] = memory["conversation_history"][-50:]
    save_memory(memory)

def add_search(memory, search_type, details):
    memory["past_searches"].append({
        "type": search_type,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
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