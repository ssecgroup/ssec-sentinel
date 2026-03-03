# backend/collectors/ssec_acled.py
import requests
from datetime import datetime, timedelta

class ACLEDCollector:
    def __init__(self, api_key, email):
        self.api_key = api_key
        self.email = email
        self.base_url = "https://api.acleddata.com/acled/read"
    
    async def fetch_conflicts(self, country=None, days_back=7):
        """Fetch recent conflict events"""
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "key": self.api_key,
            "email": self.email,
            "event_date": f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            "event_type": "Battles,Explosions/Remote violence,Violence against civilians",
            "fields": "event_date,country,admin1,admin2,location,latitude,longitude,event_type,actor1,fatalities,notes"
        }
        
        if country:
            params["country"] = country
            
        response = requests.get(self.base_url, params=params)
        return response.json().get("data", [])
    
    def format_for_map(self, event):
        """Convert ACLED event to your map format"""
        # Color code by event type and fatalities
        if event["fatalities"] > 10:
            color = "#ff4444"  # Red - major
        elif event["fatalities"] > 0:
            color = "#ff8844"  # Orange - minor casualties
        else:
            color = "#4CAF50"  # Green - no casualties
            
        return {
            "id": f"acled-{event['event_id_cnty']}",
            "name": f"{event['event_type']} - {event['location']}",
            "type": event["event_type"],
            "lat": float(event["latitude"]),
            "lon": float(event["longitude"]),
            "alertLevel": "RED" if event["fatalities"] > 5 else "ORANGE" if event["fatalities"] > 0 else "GREEN",
            "startTime": event["event_date"],
            "description": f"{event['actor1']} - {event['notes'][:200]}",
            "fatalities": event["fatalities"],
            "source": "ACLED"
        }
