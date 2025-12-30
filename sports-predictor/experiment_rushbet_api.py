import requests
import json
import time

def test_rushbet_api():
    # Correct URL found via browser interception
    # Host: us1.offering-api.kambicdn.com
    # Offering: rsico (Rush Street Interactive Colombia)
    # Protocol: v2018
    
    url = "https://us1.offering-api.kambicdn.com/offering/v2018/rsico/listView/football.json"
    
    params = {
        "lang": "es_ES",
        "market": "CO",
        "client_id": "2", # Found in logs as 200, but 2 often works. Let's try 2 first, or 200 if failed. 
        # Logs said client_id=200. I will use 200 to be safe.
        "client_id": "200",
        "channel_id": "1",
        "nc_id": int(time.time() * 1000),
        "useCombined": "true"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://www.rushbet.co",
        "Referer": "https://www.rushbet.co/"
    }

    print(f"Testing Correct URL: {url}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Save raw output
        with open("rushbet_football_raw.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print("\n>>> SUCCESS! Data fetched from Rushbet/Kambi API.")
        
        if "events" in data:
            events = data["events"]
            print(f"Found {len(events)} events.")
            print("\nSample Events:")
            for event in events[:5]: 
                event_name = event.get("event", {}).get("name")
                league = event.get("event", {}).get("path", [{}])[0].get("name", "Unknown League")
                start = event.get("event", {}).get("start")
                print(f"- [{league}] {event_name} ({start})")
                
                # Check for odds 
                offers = event.get("betOffers", [])
                if offers:
                    print(f"  Available Markets: {len(offers)}")
                    for offer in offers[:1]: 
                        print(f"  Market: {offer.get('criterion', {}).get('label')}")
                        for outcome in offer.get("outcomes", []):
                            print(f"    {outcome.get('label')}: {outcome.get('odds')/1000 if 'odds' in outcome else 'N/A'}")
        else:
            print("Response valid but 'events' key not found.")
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response content: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rushbet_api()
