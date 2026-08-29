import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_watched_routes():
    result = supabase.table("memory").select("watched_routes").eq("id", "main").execute()
    if result.data:
        return result.data[0].get("watched_routes", [])
    return []

def check_price(origin, destination, outbound_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "api_key": SERPAPI_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    if "best_flights" in data and data["best_flights"]:
        best = data["best_flights"][0]
        return {
            "price": best.get("price"),
            "airline": best["flights"][0].get("airline"),
            "departure": best["flights"][0].get("departure_airport", {}).get("time"),
            "arrival": best["flights"][-1].get("arrival_airport", {}).get("time")
        }
    return None

def send_alert(route, flight, threshold):
    subject = f"✈️ Price Alert: {route['origin']} → {route['destination']} is ${flight['price']}!"

    body = f"""
Hi Ruchir!

Good news — a flight you're watching just dropped below your threshold!

Route: {route['origin']} → {route['destination']}
Date: {route['outbound_date']} → {route['return_date']}
Current price: ${flight['price']}
Your threshold: ${threshold}
Airline: {flight['airline']}
Departs: {flight['departure']}
Arrives: {flight['arrival']}

Book soon — prices can change quickly!

Your Travel Agent 🌍
"""

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Alert sent for {route['origin']} → {route['destination']} at ${flight['price']}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def run_checks():
    print(f"\n🕐 Running price checks at {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    watched = load_watched_routes()

    if not watched:
        print("No routes being watched.")
        return

    for route in watched:
        origin = route["origin"]
        destination = route["destination"]
        outbound_date = route["outbound_date"]
        return_date = route.get("return_date", "")
        threshold = route["threshold"]

        try:
            if datetime.strptime(outbound_date, "%Y-%m-%d") < datetime.now():
                print(f"⏭️  Skipping {origin} → {destination} — date has passed")
                continue
        except:
            continue

        print(f"🔍 Checking {origin} → {destination} on {outbound_date}...")
        flight = check_price(origin, destination, outbound_date, return_date)

        if flight:
            print(f"   Current price: ${flight['price']} (threshold: ${threshold})")
            if flight["price"] <= threshold:
                print(f"   🎉 Below threshold! Sending alert...")
                send_alert(route, flight, threshold)
            else:
                print(f"   Price above threshold, no alert needed")
        else:
            print(f"   No flights found for this route")

    print("✅ Price check complete\n")

if __name__ == "__main__":
    run_checks()
