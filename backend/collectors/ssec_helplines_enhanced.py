"""Enhanced Helplines with Worldwide Coverage"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class EnhancedHelplinesCollector:
    """Provides comprehensive crisis helplines by country"""
    
    def __init__(self):
        self.helplines_db = {
            # Africa
            "ZA": [  # South Africa
                {"name": "🚨 National Emergency", "number": "10111", "available": "24/7", "type": "police"},
                {"name": "🚑 Ambulance", "number": "10177", "available": "24/7", "type": "medical"},
                {"name": "🧠 Suicide Crisis Line", "number": "0800 567 567", "available": "24/7", "type": "mental health"},
                {"name": "❤️ Red Cross South Africa", "number": "021 418 6640", "available": "08:00-17:00", "type": "humanitarian"}
            ],
            "KE": [  # Kenya
                {"name": "🚨 Police", "number": "999", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "1199", "available": "24/7", "type": "medical"},
                {"name": "🧠 Befrienders Kenya", "number": "0722 200 531", "available": "24/7", "type": "mental health"},
                {"name": "🇺🇳 UN Kenya", "number": "+254 20 762 2000", "available": "08:00-17:00", "type": "humanitarian"}
            ],
            "NG": [  # Nigeria
                {"name": "🚨 Police", "number": "199", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "112", "available": "24/7", "type": "medical"},
                {"name": "❤️ Red Cross Nigeria", "number": "+234 809 636 0300", "available": "24/7", "type": "humanitarian"},
                {"name": "🧠 Suicide Prevention", "number": "0806 210 6493", "available": "24/7", "type": "mental health"}
            ],
            
            # Middle East
            "SY": [  # Syria
                {"name": "🚨 Civil Defence (White Helmets)", "number": "+963 933 333 333", "available": "24/7", "type": "emergency"},
                {"name": "❤️ Syrian Red Crescent", "number": "+963 11 331 0666", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Syria", "number": "+963 11 339 7000", "available": "09:00-17:00", "type": "humanitarian"},
                {"name": "🆘 ICRC Syria", "number": "+963 11 331 0667", "available": "24/7", "type": "humanitarian"}
            ],
            "IQ": [  # Iraq
                {"name": "🚨 Police", "number": "104", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "122", "available": "24/7", "type": "medical"},
                {"name": "❤️ Iraqi Red Crescent", "number": "+964 1 884 0060", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Iraq", "number": "+964 1 778 0010", "available": "09:00-17:00", "type": "humanitarian"}
            ],
            "JO": [  # Jordan
                {"name": "🚨 Police", "number": "911", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "911", "available": "24/7", "type": "medical"},
                {"name": "❤️ Jordan Red Crescent", "number": "+962 6 477 6262", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UNHCR Jordan", "number": "+962 6 500 1500", "available": "09:00-17:00", "type": "refugee"}
            ],
            "LB": [  # Lebanon
                {"name": "🚨 Police", "number": "112", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "140", "available": "24/7", "type": "medical"},
                {"name": "❤️ Lebanese Red Cross", "number": "140", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Lebanon", "number": "+961 1 978 000", "available": "09:00-17:00", "type": "humanitarian"}
            ],
            
            # Asia
            "AF": [  # Afghanistan
                {"name": "🚨 Police", "number": "119", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "112", "available": "24/7", "type": "medical"},
                {"name": "❤️ Afghan Red Crescent", "number": "+93 20 220 2155", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Afghanistan", "number": "+93 20 230 1400", "available": "09:00-16:00", "type": "humanitarian"}
            ],
            "PK": [  # Pakistan
                {"name": "🚨 Police", "number": "15", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Rescue 1122", "number": "1122", "available": "24/7", "type": "medical"},
                {"name": "❤️ Pakistan Red Crescent", "number": "+92 51 925 0404", "available": "24/7", "type": "humanitarian"},
                {"name": "🧠 Edhi Foundation", "number": "115", "available": "24/7", "type": "emergency"}
            ],
            "IN": [  # India
                {"name": "🚨 Police", "number": "100", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "102", "available": "24/7", "type": "medical"},
                {"name": "🚒 Fire", "number": "101", "available": "24/7", "type": "fire"},
                {"name": "🧠 iCall", "number": "022 2556 3291", "available": "10:00-20:00", "type": "mental health"},
                {"name": "❤️ Indian Red Cross", "number": "+91 11 2371 6441", "available": "10:00-17:00", "type": "humanitarian"}
            ],
            
            # Europe
            "UA": [  # Ukraine
                {"name": "🚨 Emergency", "number": "112", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "103", "available": "24/7", "type": "medical"},
                {"name": "❤️ Ukrainian Red Cross", "number": "0 800 332 656", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Ukraine", "number": "+380 44 254 0035", "available": "09:00-18:00", "type": "humanitarian"},
                {"name": "🆘 Civil Defense", "number": "101", "available": "24/7", "type": "emergency"}
            ],
            "TR": [  # Turkey
                {"name": "🚨 Emergency", "number": "112", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "112", "available": "24/7", "type": "medical"},
                {"name": "❤️ Turkish Red Crescent", "number": "168", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Turkey", "number": "+90 312 454 1000", "available": "09:00-18:00", "type": "humanitarian"},
                {"name": "🌍 AFAD (Disaster)", "number": "122", "available": "24/7", "type": "disaster response"}
            ],
            
            # Americas
            "US": [  # United States
                {"name": "🚨 911 Emergency", "number": "911", "available": "24/7", "type": "emergency"},
                {"name": "🧠 988 Suicide & Crisis", "number": "988", "available": "24/7", "type": "mental health"},
                {"name": "🌪️ Disaster Distress", "number": "1-800-985-5990", "available": "24/7", "type": "disaster"},
                {"name": "❤️ Red Cross", "number": "1-800-733-2767", "available": "24/7", "type": "humanitarian"},
                {"name": "🏠 Domestic Violence", "number": "1-800-799-7233", "available": "24/7", "type": "abuse"},
                {"name": "👶 Child Abuse", "number": "1-800-422-4453", "available": "24/7", "type": "child protection"},
                {"name": "⚓ Coast Guard", "number": "1-800-323-7233", "available": "24/7", "type": "maritime"},
                {"name": "🐾 Animal Poison", "number": "1-888-426-4435", "available": "24/7", "type": "pets"},
                {"name": "🧪 Poison Control", "number": "1-800-222-1222", "available": "24/7", "type": "poison"}
            ],
            "CA": [  # Canada
                {"name": "🚨 Emergency", "number": "911", "available": "24/7", "type": "emergency"},
                {"name": "🧠 Talk Suicide", "number": "988", "available": "24/7", "type": "mental health"},
                {"name": "❤️ Canadian Red Cross", "number": "1-800-418-1111", "available": "24/7", "type": "humanitarian"},
                {"name": "🌊 Coast Guard", "number": "1-800-267-7270", "available": "24/7", "type": "maritime"}
            ],
            "MX": [  # Mexico
                {"name": "🚨 Emergency", "number": "911", "available": "24/7", "type": "emergency"},
                {"name": "❤️ Mexican Red Cross", "number": "065", "available": "24/7", "type": "humanitarian"},
                {"name": "🧠 SAPTEL", "number": "0155 5259 8121", "available": "24/7", "type": "mental health"}
            ],
            "HT": [  # Haiti
                {"name": "🚨 Police", "number": "114", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "116", "available": "24/7", "type": "medical"},
                {"name": "❤️ Haitian Red Cross", "number": "+509 2813 5678", "available": "24/7", "type": "humanitarian"},
                {"name": "🇺🇳 UN Haiti", "number": "+509 2813 5000", "available": "09:00-17:00", "type": "humanitarian"}
            ],
            
            # Caribbean
            "JM": [  # Jamaica
                {"name": "🚨 Police", "number": "119", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "110", "available": "24/7", "type": "medical"},
                {"name": "❤️ Jamaica Red Cross", "number": "+1 876 984 7860", "available": "24/7", "type": "humanitarian"},
                {"name": "🌪️ ODIPERC", "number": "1-888-225-5637", "available": "24/7", "type": "disaster"}
            ],
            "CU": [  # Cuba
                {"name": "🚨 Police", "number": "106", "available": "24/7", "type": "emergency"},
                {"name": "🚑 Ambulance", "number": "104", "available": "24/7", "type": "medical"},
                {"name": "❤️ Cuban Red Cross", "number": "+53 7 864 2511", "available": "24/7", "type": "humanitarian"},
                {"name": "🌪️ Civil Defense", "number": "103", "available": "24/7", "type": "disaster"}
            ],
            
            # Pacific
            "AU": [  # Australia
                {"name": "🚨 Emergency", "number": "000", "available": "24/7", "type": "emergency"},
                {"name": "🧠 Lifeline", "number": "13 11 14", "available": "24/7", "type": "mental health"},
                {"name": "❤️ Australian Red Cross", "number": "1800 733 276", "available": "24/7", "type": "humanitarian"},
                {"name": "🌊 Coast Guard", "number": "1800 641 792", "available": "24/7", "type": "maritime"}
            ],
            "NZ": [  # New Zealand
                {"name": "🚨 Emergency", "number": "111", "available": "24/7", "type": "emergency"},
                {"name": "🧠 Lifeline", "number": "0800 543 354", "available": "24/7", "type": "mental health"},
                {"name": "❤️ NZ Red Cross", "number": "0800 733 276", "available": "24/7", "type": "humanitarian"},
                {"name": "🌪️ Civil Defense", "number": "0800 225 5637", "available": "24/7", "type": "disaster"}
            ],
            
            # Global/Multi-country
            "GLOBAL": [
                {"name": "🇺🇳 UN Humanitarian", "number": "+41 22 917 1234", "available": "24/7", "type": "humanitarian"},
                {"name": "❤️ ICRC (Red Cross)", "number": "+41 22 730 2111", "available": "24/7", "type": "humanitarian"},
                {"name": "🌍 MSF (Doctors Without Borders)", "number": "+41 22 849 8400", "available": "24/7", "type": "medical"},
                {"name": "🆘 International SOS", "number": "+65 6338 7800", "available": "24/7", "type": "emergency"}
            ]
        }
    
    def get_helplines(self, country_code: str) -> List[Dict]:
        """Get helplines for a specific country"""
        # Try exact match
        if country_code in self.helplines_db:
            return self.helplines_db[country_code]
        
        # Try uppercase
        if country_code.upper() in self.helplines_db:
            return self.helplines_db[country_code.upper()]
        
        # Return global if country not found
        return self.helplines_db.get("GLOBAL", [])
    
    def search_helplines(self, query: str) -> List[Dict]:
        """Search helplines by name or number"""
        results = []
        for country, helplines in self.helplines_db.items():
            for h in helplines:
                if (query.lower() in h["name"].lower() or 
                    query in h["number"]):
                    results.append({**h, "country": country})
        return results
    
    def get_emergency_by_type(self, country_code: str, helpline_type: str) -> List[Dict]:
        """Get helplines of specific type (police, medical, humanitarian, etc.)"""
        all_helplines = self.get_helplines(country_code)
        return [h for h in all_helplines if h["type"] == helpline_type]
    
    def get_all_countries(self) -> List[str]:
        """Get list of all available countries"""
        return list(self.helplines_db.keys())
