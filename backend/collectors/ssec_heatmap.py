"""Heatmap Data Generator"""
import random
import math
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class HeatmapCollector:
    """Generates heatmap data from various sources"""
    
    def __init__(self):
        self.disaster_zones = [
            # Caribbean
            {"center": (18.5, -77.2), "radius": 3, "intensity": 0.9, "type": "earthquake"},
            {"center": (25.3, -86.5), "radius": 4, "intensity": 0.8, "type": "hurricane"},
            {"center": (14.5, 108.2), "radius": 5, "intensity": 0.7, "type": "flood"},
            # Middle East
            {"center": (33.5, 36.3), "radius": 2, "intensity": 0.95, "type": "conflict"},  # Syria
            {"center": (33.3, 44.4), "radius": 2, "intensity": 0.85, "type": "conflict"},  # Iraq
            {"center": (31.5, 34.5), "radius": 1.5, "intensity": 0.9, "type": "conflict"},  # Gaza
            # Africa
            {"center": (4.5, 18.5), "radius": 3, "intensity": 0.8, "type": "conflict"},  # CAR
            {"center": (9.5, 30.0), "radius": 3, "intensity": 0.75, "type": "flood"},  # South Sudan
            {"center": (-1.5, 29.5), "radius": 2, "intensity": 0.85, "type": "conflict"},  # DRC
            # Asia
            {"center": (27.5, 85.5), "radius": 2, "intensity": 0.7, "type": "earthquake"},  # Nepal
            {"center": (35.5, 75.5), "radius": 3, "intensity": 0.8, "type": "conflict"},  # Kashmir
            {"center": (16.5, 96.5), "radius": 2, "intensity": 0.75, "type": "cyclone"},  # Myanmar
            # Europe
            {"center": (48.5, 37.5), "radius": 3, "intensity": 0.9, "type": "conflict"},  # Ukraine
        ]
    
    def generate_heatmap_data(self, 
                             disaster_type: str = None, 
                             days: int = 30,
                             points: int = 100) -> List[Dict]:
        """Generate heatmap points based on disaster zones"""
        
        heatmap = []
        
        # Filter zones by type if specified
        zones = self.disaster_zones
        if disaster_type:
            zones = [z for z in self.disaster_zones if z["type"] == disaster_type]
        
        # Generate points around each zone
        for zone in zones:
            center_lat, center_lon = zone["center"]
            radius = zone["radius"]
            base_intensity = zone["intensity"]
            
            # Number of points proportional to intensity
            num_points = int(points * base_intensity / len(zones))
            
            for _ in range(num_points):
                # Random offset within radius
                lat_offset = random.uniform(-radius, radius)
                lon_offset = random.uniform(-radius, radius)
                
                # Distance from center affects intensity
                dist = math.sqrt(lat_offset**2 + lon_offset**2) / radius
                intensity = base_intensity * (1 - dist * 0.5)  # Fade with distance
                
                # Add some randomness
                intensity *= random.uniform(0.8, 1.0)
                
                heatmap.append({
                    "lat": center_lat + lat_offset,
                    "lon": center_lon + lon_offset,
                    "intensity": round(min(intensity, 1.0), 2),
                    "type": zone["type"],
                    "date": (datetime.now() - timedelta(days=random.randint(0, days))).isoformat()
                })
        
        return heatmap
    
    def get_conflict_hotspots(self, min_intensity: float = 0.7) -> List[Dict]:
        """Get conflict hotspots (conflict zones only)"""
        return self.generate_heatmap_data(disaster_type="conflict", points=50)
    
    def get_natural_disaster_hotspots(self) -> List[Dict]:
        """Get natural disaster hotspots"""
        natural_types = ["earthquake", "hurricane", "flood", "cyclone"]
        all_points = []
        
        for disaster_type in natural_types:
            points = self.generate_heatmap_data(disaster_type=disaster_type, points=25)
            all_points.extend(points)
        
        return all_points
    
    def get_density_grid(self, resolution: float = 0.5) -> List[Dict]:
        """Generate density grid for raster heatmap"""
        grid_points = []
        
        # Create a grid covering active areas
        for zone in self.disaster_zones:
            center_lat, center_lon = zone["center"]
            radius = zone["radius"]
            
            for i in range(-2, 3):
                for j in range(-2, 3):
                    lat = center_lat + i * resolution
                    lon = center_lon + j * resolution
                    
                    # Calculate distance from center
                    dist = math.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
                    if dist <= radius * 1.5:
                        intensity = zone["intensity"] * (1 - dist/(radius*1.5))
                        
                        grid_points.append({
                            "lat": round(lat, 2),
                            "lon": round(lon, 2),
                            "intensity": round(intensity, 2)
                        })
        
        return grid_points
    
    def get_time_series(self, hours: int = 24) -> List[Dict]:
        """Get time-series heatmap data"""
        import numpy as np
        
        data = []
        now = datetime.now()
        
        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            
            # Generate some random events per hour
            events = random.randint(0, 5)
            for _ in range(events):
                # Pick a random zone
                zone = random.choice(self.disaster_zones)
                
                # Random offset
                lat = zone["center"][0] + random.uniform(-zone["radius"], zone["radius"])
                lon = zone["center"][1] + random.uniform(-zone["radius"], zone["radius"])
                
                data.append({
                    "lat": lat,
                    "lon": lon,
                    "intensity": zone["intensity"] * random.uniform(0.5, 1.0),
                    "timestamp": timestamp.isoformat(),
                    "type": zone["type"]
                })
        
        return sorted(data, key=lambda x: x["timestamp"], reverse=True)
    
    def get_statistics(self) -> Dict:
        """Get heatmap statistics"""
        all_points = self.generate_heatmap_data(points=500)
        
        by_type = {}
        intensities = []
        
        for point in all_points:
            t = point.get("type", "unknown")
            if t not in by_type:
                by_type[t] = 0
            by_type[t] += 1
            intensities.append(point["intensity"])
        
        return {
            "total_points": len(all_points),
            "by_type": by_type,
            "avg_intensity": sum(intensities) / len(intensities) if intensities else 0,
            "max_intensity": max(intensities) if intensities else 0,
            "min_intensity": min(intensities) if intensities else 0,
            "active_zones": len(self.disaster_zones)
        }
