import os
import re
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import datetime, timedelta
from memory import (
    load_memory, add_conversation, add_search,
    update_preferences, get_memory_summary
)

load_dotenv()

client = Anthropic()
serpapi_key = os.getenv("SERPAPI_KEY")

memory = load_memory()

system_prompt = """You are a personal travel agent assistant. You help the user find flights and hotels, track prices, and make travel recommendations.

When flight or hotel data is provided to you in the conversation, use that real data to answer the user. Always mention specific prices, airlines, and times from the data. Be conversational and friendly.

If the user mentions their home airport, preferred airlines, budget, or seat preference, acknowledge it and remember it.

Today's date is """ + datetime.now().strftime("%B %d, %Y") + """. Only search for future dates."""

def search_flights(origin, destination, outbound_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "api_key": serpapi_key
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    flights = []
    if "best_flights" in data:
        for flight in data["best_flights"][:3]:
            flights.append({
                "price": flight.get("price"),
                "airline": flight["flights"][0].get("airline"),
                "departure": flight["flights"][0].get("departure_airport", {}).get("time"),
                "arrival": flight["flights"][-1].get("arrival_airport", {}).get("time"),
                "duration": flight.get("total_duration")
            })
    return flights

def search_hotels(location, check_in, check_out):
    params = {
        "engine": "google_hotels",
        "q": f"hotels in {location}",
        "check_in_date": check_in,
        "check_out_date": check_out,
        "currency": "USD",
        "api_key": serpapi_key
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    hotels = []
    if "properties" in data:
        for hotel in data["properties"][:3]:
            hotels.append({
                "name": hotel.get("name"),
                "price": hotel.get("rate_per_night", {}).get("lowest"),
                "rating": hotel.get("overall_rating"),
                "location": hotel.get("neighborhood")
            })
    return hotels

def get_airport_code(city_name):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"What is the IATA airport code for the main airport serving {city_name}? Reply with only the 3-letter code, nothing else."
        }]
    )
    code = response.content[0].text.strip().upper()
    if len(code) == 3 and code.isalpha():
        return code
    return None

def get_city_from_code(airport_code):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"What city and country does the airport code {airport_code} serve? Reply with just the city and country, like 'Dublin, Ireland'. Nothing else."
        }]
    )
    return response.content[0].text.strip()

def extract_dates(message):
    month_map = {
        "january": "01", "jan": "01", "february": "02", "feb": "02",
        "march": "03", "mar": "03", "april": "04", "apr": "04",
        "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
        "august": "08", "aug": "08", "september": "09", "sep": "09",
        "october": "10", "oct": "10", "november": "11", "nov": "11",
        "december": "12", "dec": "12"
    }

    found_dates = []
    pattern = r'(' + '|'.join(month_map.keys()) + r')\s+(\d{1,2})'
    matches = re.findall(pattern, message.lower())
    current_year = datetime.now().year
    for month_str, day in matches:
        month = month_map[month_str]
        date_str = f"{current_year}-{month}-{day.zfill(2)}"
        if datetime.strptime(date_str, "%Y-%m-%d") < datetime.now():
            date_str = f"{current_year + 1}-{month}-{day.zfill(2)}"
        found_dates.append(date_str)

    explicit = re.findall(r'\d{4}-\d{2}-\d{2}', message)
    found_dates.extend(explicit)

    return found_dates

def extract_airports(message):
    airport_codes = {
        "san francisco": "SFO", "sf": "SFO", "sfo": "SFO",
        "dublin": "DUB", "dub": "DUB",
        "new york": "JFK", "nyc": "JFK", "jfk": "JFK",
        "london": "LHR", "lhr": "LHR",
        "seattle": "SEA", "sea": "SEA",
        "los angeles": "LAX", "la": "LAX", "lax": "LAX",
        "chicago": "ORD", "ord": "ORD",
        "paris": "CDG", "cdg": "CDG",
        "amsterdam": "AMS", "ams": "AMS",
        "tokyo": "NRT", "nrt": "NRT",
        "miami": "MIA", "mia": "MIA",
        "boston": "BOS", "bos": "BOS",
        "denver": "DEN", "den": "DEN",
        "atlanta": "ATL", "atl": "ATL",
        "rome": "FCO", "fco": "FCO",
        "barcelona": "BCN", "bcn": "BCN",
        "lisbon": "LIS", "lis": "LIS",
        "houston": "IAH", "iah": "IAH"
    }

    message_lower = message.lower()
    found = []

    for city, code in airport_codes.items():
        if city in message_lower and code not in found:
            found.append(code)

    if not found:
        skip_words = {
            "March", "April", "May", "June", "July", "August",
            "September", "October", "November", "December",
            "January", "February", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday",
            "Find", "Search", "Book", "Show", "Get", "Help"
        }
        potential_cities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', message)
        for city in potential_cities:
            if city not in skip_words:
                print(f"🌍 Looking up airport for {city}...")
                code = get_airport_code(city)
                if code and code not in found:
                    found.append(code)

    return found

def build_flight_info(user_message):
    info = {}

    airports = extract_airports(user_message)

    if len(airports) < 2:
        recent_messages = " ".join([
            m["content"] for m in memory["conversation_history"][-6:]
        ])
        past_airports = extract_airports(recent_messages)
        for code in past_airports:
            if code not in airports:
                airports.append(code)

    home = memory["preferences"]["home_airport"]
    if len(airports) >= 2:
        if home and home in airports:
            info["origin"] = home
            info["destination"] = [a for a in airports if a != home][0]
        else:
            info["origin"] = airports[0]
            info["destination"] = airports[1]
    elif len(airports) == 1:
        if home and airports[0] != home:
            info["origin"] = home
            info["destination"] = airports[0]
        else:
            info["origin"] = home
            info["destination"] = airports[0]
    elif home and memory.get("last_destination"):
        info["origin"] = home
        info["destination"] = memory["last_destination"]

    dates = extract_dates(user_message)

    if not dates:
        recent_messages = " ".join([
            m["content"] for m in memory["conversation_history"][-6:]
        ])
        dates = extract_dates(recent_messages)

    if dates:
        info["departure_date"] = dates[0]
    if len(dates) > 1:
        info["return_date"] = dates[1]
    elif "departure_date" in info:
        dep = datetime.strptime(info["departure_date"], "%Y-%m-%d")
        trip_length = memory["preferences"]["typical_trip_length"] or 14
        info["return_date"] = (dep + timedelta(days=trip_length)).strftime("%Y-%m-%d")

    return info

def is_flight_related(message):
    flight_words = [
        "flight", "fly", "flights", "ticket", "departing", "returning",
        "depart", "return", "outbound", "round trip", "one way"
    ]
    if any(word in message.lower() for word in flight_words):
        return True

    has_dates = bool(extract_dates(message))
    has_destination = bool(memory.get("last_destination"))
    if has_dates and has_destination:
        return True

    return False

def detect_preferences(message):
    message_lower = message.lower()

    airports = extract_airports(message)
    if airports and any(phrase in message_lower for phrase in
                        ["home airport", "i fly from", "i usually fly from", "i'm based in", "i am based in"]):
        update_preferences(memory, "home_airport", airports[0])

    airlines = ["aer lingus", "delta", "united", "american", "british airways",
                "lufthansa", "air france", "emirates", "southwest", "alaska"]
    for airline in airlines:
        if airline in message_lower and any(word in message_lower for word in ["prefer", "like", "usually fly", "favorite"]):
            prefs = memory["preferences"]["preferred_airlines"]
            if airline.title() not in prefs:
                prefs.append(airline.title())
                update_preferences(memory, "preferred_airlines", prefs)

    if "window" in message_lower and any(word in message_lower for word in ["prefer", "like", "always"]):
        update_preferences(memory, "seat_preference", "window")
    elif "aisle" in message_lower and any(word in message_lower for word in ["prefer", "like", "always"]):
        update_preferences(memory, "seat_preference", "aisle")

    # Detect price alert requests
    alert_phrases = ["alert me", "notify me", "watch", "track", "let me know when", "tell me when"]
    update_phrases = ["change my alert", "update my alert", "make it under", "lower my threshold",
                      "change the alert", "update the threshold", "change it to", "make the alert"]

    is_new_alert = any(phrase in message_lower for phrase in alert_phrases)
    is_update = any(phrase in message_lower for phrase in update_phrases)

    if is_new_alert or is_update:
        info = build_flight_info(message)
        price_match = re.search(r'\$?(\d{3,4})', message)
        if price_match:
            threshold = int(price_match.group(1))
            from memory import add_watched_route, save_memory

            existing = memory.get("watched_routes", [])
            updated = False
            for route in existing:
                same_origin = "origin" not in info or route["origin"] == info.get("origin")
                same_dest = "destination" not in info or route["destination"] == info.get("destination")
                if same_origin and same_dest:
                    route["threshold"] = threshold
                    updated = True
                    save_memory(memory)
                    print(f"🔔 Updated alert: {route['origin']} → {route['destination']} — new threshold ${threshold}")
                    break

            if not updated and "origin" in info and "destination" in info and "departure_date" in info:
                add_watched_route(
                    memory,
                    info["origin"],
                    info["destination"],
                    info["departure_date"],
                    info.get("return_date", ""),
                    threshold
                )
                save_memory(memory)
                print(f"🔔 Watching {info['origin']} → {info['destination']} — alert below ${threshold}")


def chat(user_message):
    add_conversation(memory, "user", user_message)
    detect_preferences(user_message)

    extra_context = ""
    message_lower = user_message.lower()

    # --- Flight search ---
    if is_flight_related(user_message):
        info = build_flight_info(user_message)
        if "origin" in info and "destination" in info and "departure_date" in info:
            print(f"🔍 Searching flights {info['origin']} → {info['destination']} on {info['departure_date']}...")
            flights = search_flights(
                info["origin"], info["destination"],
                info["departure_date"], info["return_date"]
            )
            if flights:
                extra_context += "\n\nLIVE FLIGHT DATA from SerpAPI:\n"
                for i, f in enumerate(flights, 1):
                    extra_context += f"{i}. {f['airline']} — ${f['price']} — departs {f['departure']} arrives {f['arrival']} — {f['duration']} mins total\n"
                add_search(memory, "flight", f"{info['origin']} → {info['destination']} on {info['departure_date']}")
                memory["last_destination"] = info["destination"]
                from memory import save_memory
                save_memory(memory)
            else:
                extra_context += "\n\nFlight search returned no results. Let the user know and suggest different dates."
        else:
            missing = []
            if "destination" not in info:
                missing.append("destination city")
            if "departure_date" not in info:
                missing.append("travel dates")
            extra_context += f"\n\nCould not search flights — missing: {', '.join(missing)}. Ask the user for these."

    # --- Hotel search ---
    if any(word in message_lower for word in ["hotel", "hotels", "stay", "accommodation", "where to stay"]):
        airport_to_city = {
            "DUB": "Dublin, Ireland",
            "SFO": "San Francisco, California",
            "JFK": "New York City, New York",
            "LHR": "London, England",
            "SEA": "Seattle, Washington",
            "LAX": "Los Angeles, California",
            "ORD": "Chicago, Illinois",
            "CDG": "Paris, France",
            "AMS": "Amsterdam, Netherlands",
            "NRT": "Tokyo, Japan",
            "MIA": "Miami, Florida",
            "BOS": "Boston, Massachusetts",
            "DEN": "Denver, Colorado",
            "ATL": "Atlanta, Georgia",
            "FCO": "Rome, Italy",
            "BCN": "Barcelona, Spain",
            "LIS": "Lisbon, Portugal",
            "IAH": "Houston, Texas"
        }
        airports = extract_airports(user_message)
        if not airports and memory.get("last_destination"):
            airports = [memory["last_destination"]]
        airport_code = airports[0] if airports else "DUB"
        if airport_code in airport_to_city:
            location = airport_to_city[airport_code]
        else:
            print(f"🌍 Looking up city for {airport_code}...")
            location = get_city_from_code(airport_code)
        dates = extract_dates(user_message)
        if not dates:
            recent_messages = " ".join([
                m["content"] for m in memory["conversation_history"][-6:]
            ])
            dates = extract_dates(recent_messages)
        check_in = dates[0] if dates else (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        check_out = dates[1] if len(dates) > 1 else (datetime.now() + timedelta(days=44)).strftime("%Y-%m-%d")
        print(f"🔍 Searching hotels in {location}...")
        hotels = search_hotels(location, check_in, check_out)
        if hotels:
            extra_context += "\n\nLIVE HOTEL DATA from SerpAPI:\n"
            for i, h in enumerate(hotels, 1):
                extra_context += f"{i}. {h['name']} — ${h['price']}/night — Rating: {h['rating']} — {h['location']}\n"
            add_search(memory, "hotel", f"{location} {check_in} to {check_out}")

    # --- Build messages for Claude ---
    recent_history = [
        {"role": m["role"], "content": m["content"]}
        for m in memory["conversation_history"][-20:]
        if m["role"] in ["user", "assistant"]
    ]

    memory_summary = get_memory_summary(memory)
    full_system = system_prompt
    if memory_summary:
        full_system += f"\n\nWhat you know about this user:\n{memory_summary}"

    if extra_context and recent_history:
        recent_history[-1]["content"] += extra_context

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=full_system,
        messages=recent_history if recent_history else [{"role": "user", "content": user_message}]
    )

    assistant_message = response.content[0].text
    add_conversation(memory, "assistant", assistant_message)

    return assistant_message


def main():
    print("✈️  Travel Agent ready! Type 'quit' to exit.\n")

    memory_summary = get_memory_summary(memory)
    if memory_summary:
        print("📋 I remember you! Here's what I know:\n")
        print(memory_summary)

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Safe travels!")
            break

        response = chat(user_input)
        print(f"\nAgent: {response}\n")

if __name__ == "__main__":
    main()
