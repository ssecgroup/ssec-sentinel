// ssec-sources.js - Multi-source data collector with fallbacks
const DataSources = {
    // Source configurations with priorities
    sources: {
        conflicts: [
            { name: 'ACLED', url: 'https://api.acleddata.com/acled/read?limit=50', requiresKey: true, priority: 1 },
            { name: 'GDELT', url: 'https://api.gdeltproject.org/api/v2/geo/geo?query=event&mode=PointData', requiresKey: false, priority: 2 },
            { name: 'RSS-News', url: '/api/rss-news', requiresKey: false, priority: 3 }
        ],
        flights: [
            { name: 'OpenSky', url: 'https://opensky-network.org/api/states/all', requiresKey: false, priority: 1 },
            { name: 'ADS-B Exchange', url: 'https://adsbexchange.com/api/aircraft/json/', requiresKey: true, priority: 2 }
        ],
        disasters: [
            { name: 'NASA EONET', url: 'https://eonet.gsfc.nasa.gov/api/v3/events', requiresKey: false, priority: 1 },
            { name: 'USGS', url: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson', requiresKey: false, priority: 2 },
            { name: 'ReliefWeb', url: 'https://api.reliefweb.int/v1/disasters?limit=10', requiresKey: false, priority: 3 }
        ],
        news: [
            { name: 'BBC', url: 'https://feeds.bbci.co.uk/news/world/rss.xml', requiresKey: false, priority: 1 },
            { name: 'Reuters', url: 'http://feeds.reuters.com/reuters/worldnews', requiresKey: false, priority: 2 },
            { name: 'Al Jazeera', url: 'https://www.aljazeera.com/xml/rss/all.xml', requiresKey: false, priority: 3 }
        ],
        signals: [
            { name: 'HDX', url: 'https://hapi.humdata.org/api/v1/signals', requiresKey: false, priority: 1 },
            { name: 'ReliefWeb', url: 'https://api.reliefweb.int/v1/reports?limit=5', requiresKey: false, priority: 2 }
        ]
    },

    // Cache for API responses
    cache: {
        conflicts: { data: null, timestamp: null, source: null },
        flights: { data: null, timestamp: null, source: null },
        disasters: { data: null, timestamp: null, source: null },
        news: { data: null, timestamp: null, source: null },
        signals: { data: null, timestamp: null, source: null }
    },

    // Cache TTL in milliseconds (5 minutes)
    CACHE_TTL: 300000,

    // Track last successful source
    lastSuccessfulSource: {},

    // ==================== CONFLICT SOURCES ====================
    async fetchConflicts() {
        // Check cache first
        if (this.cache.conflicts.data && 
            (Date.now() - this.cache.conflicts.timestamp) < this.CACHE_TTL) {
            return { 
                data: this.cache.conflicts.data, 
                source: this.cache.conflicts.source,
                cached: true 
            };
        }

        // Try sources in priority order
        for (const source of this.sources.conflicts) {
            try {
                let data = null;
                
                if (source.name === 'ACLED') {
                    data = await this.fetchACLED();
                } else if (source.name === 'GDELT') {
                    data = await this.fetchGDELT();
                } else if (source.name === 'RSS-News') {
                    data = await this.fetchRSSNews();
                }

                if (data && data.length > 0) {
                    // Update cache
                    this.cache.conflicts = {
                        data: data,
                        timestamp: Date.now(),
                        source: source.name
                    };
                    this.lastSuccessfulSource.conflicts = source.name;
                    
                    return { data, source: source.name };
                }
            } catch (error) {
                console.log(`${source.name} failed:`, error.message);
                continue;
            }
        }

        // All sources failed - use enhanced mock
        const mockData = this.generateMockConflicts();
        this.cache.conflicts = {
            data: mockData,
            timestamp: Date.now(),
            source: 'Mock Data'
        };
        return { data: mockData, source: 'Mock Data', mock: true };
    },

    async fetchACLED() {
        // Try your backend proxy first (with your API key)
        try {
            const response = await fetch('https://ssec-sentinel.onrender.com/conflicts?days=30');
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) return data;
            }
        } catch (e) {
            console.log('Backend ACLED failed, trying direct API');
        }

        // Fallback to direct API (if you have key)
        const ACLED_KEY = 'YOUR_KEY'; // Should come from env
        if (ACLED_KEY !== 'YOUR_KEY') {
            const response = await fetch(`https://api.acleddata.com/acled/read?key=${ACLED_KEY}&limit=50`);
            if (response.ok) return await response.json();
        }
        return null;
    },

    async fetchGDELT() {
        // GDELT GeoJSON feed - no API key needed
        const response = await fetch('https://api.gdeltproject.org/api/v2/geo/geo?query=event&mode=PointData');
        if (!response.ok) return null;
        
        const data = await response.json();
        return data.features.map(f => ({
            id: f.id,
            title: f.properties.title,
            lat: f.geometry.coordinates[1],
            lon: f.geometry.coordinates[0],
            type: f.properties.type,
            fatalities: f.properties.fatalities || 0,
            country: f.properties.country,
            source: 'GDELT'
        }));
    },

    async fetchRSSNews() {
        // Use your backend as proxy for RSS feeds
        const response = await fetch('/api/rss-news');
        if (!response.ok) return null;
        return await response.json();
    },

    // ==================== FLIGHT SOURCES ====================
    async fetchFlights(lat = 20, lon = 0, radius = 500) {
        // Check cache
        if (this.cache.flights.data && 
            (Date.now() - this.cache.flights.timestamp) < this.CACHE_TTL) {
            return { 
                data: this.cache.flights.data, 
                source: this.cache.flights.source,
                cached: true 
            };
        }

        // Try OpenSky first (free, no key)
        try {
            const response = await fetch('https://opensky-network.org/api/states/all');
            if (response.ok) {
                const data = await response.json();
                const flights = this.parseOpenSkyData(data, lat, lon, radius);
                if (flights.length > 0) {
                    this.cache.flights = {
                        data: flights,
                        timestamp: Date.now(),
                        source: 'OpenSky'
                    };
                    return { data: flights, source: 'OpenSky' };
                }
            }
        } catch (e) {
            console.log('OpenSky failed');
        }

        // Try your backend
        try {
            const response = await fetch(`https://ssec-sentinel.onrender.com/flights/near?lat=${lat}&lon=${lon}&radius=${radius}`);
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    this.cache.flights = {
                        data: data,
                        timestamp: Date.now(),
                        source: 'Backend'
                    };
                    return { data, source: 'Backend' };
                }
            }
        } catch (e) {}

        // All failed - use mock
        const mockData = this.generateMockFlights(lat, lon, radius);
        this.cache.flights = {
            data: mockData,
            timestamp: Date.now(),
            source: 'Mock Data'
        };
        return { data: mockData, source: 'Mock Data', mock: true };
    },

    parseOpenSkyData(data, centerLat, centerLon, radius) {
        const flights = [];
        const states = data.states || [];
        
        for (const state of states.slice(0, 50)) {
            const flight = {
                callsign: state[1]?.trim() || 'Unknown',
                lat: state[6],
                lon: state[5],
                altitude: state[7],
                speed: state[9],
                squawk: state[3],
                is_emergency: ['7500', '7600', '7700'].includes(state[3]),
                source: 'OpenSky'
            };
            
            // Filter by distance if coordinates valid
            if (flight.lat && flight.lon) {
                const dist = this.calculateDistance(
                    centerLat, centerLon, 
                    flight.lat, flight.lon
                );
                if (dist <= radius) {
                    flight.distance = dist;
                    flights.push(flight);
                }
            }
        }
        return flights;
    },

    // ==================== DISASTER SOURCES ====================
    async fetchDisasters() {
        // Check cache
        if (this.cache.disasters.data && 
            (Date.now() - this.cache.disasters.timestamp) < this.CACHE_TTL) {
            return { 
                data: this.cache.disasters.data, 
                source: this.cache.disasters.source,
                cached: true 
            };
        }

        // Try NASA EONET first
        try {
            const response = await fetch('https://eonet.gsfc.nasa.gov/api/v3/events');
            if (response.ok) {
                const data = await response.json();
                const disasters = this.parseEONET(data);
                if (disasters.length > 0) {
                    this.cache.disasters = {
                        data: disasters,
                        timestamp: Date.now(),
                        source: 'NASA EONET'
                    };
                    return { data: disasters, source: 'NASA EONET' };
                }
            }
        } catch (e) {}

        // Try USGS earthquakes
        try {
            const response = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson');
            if (response.ok) {
                const data = await response.json();
                const earthquakes = this.parseUSGS(data);
                if (earthquakes.length > 0) {
                    this.cache.disasters = {
                        data: earthquakes,
                        timestamp: Date.now(),
                        source: 'USGS'
                    };
                    return { data: earthquakes, source: 'USGS' };
                }
            }
        } catch (e) {}

        // Try ReliefWeb
        try {
            const response = await fetch('https://api.reliefweb.int/v1/disasters?limit=10');
            if (response.ok) {
                const data = await response.json();
                const disasters = this.parseReliefWeb(data);
                if (disasters.length > 0) {
                    this.cache.disasters = {
                        data: disasters,
                        timestamp: Date.now(),
                        source: 'ReliefWeb'
                    };
                    return { data: disasters, source: 'ReliefWeb' };
                }
            }
        } catch (e) {}

        // All failed - use mock
        const mockData = this.generateMockDisasters();
        this.cache.disasters = {
            data: mockData,
            timestamp: Date.now(),
            source: 'Mock Data'
        };
        return { data: mockData, source: 'Mock Data', mock: true };
    },

    parseEONET(data) {
        return (data.events || []).map(event => ({
            id: event.id,
            title: event.title,
            type: event.categories?.[0]?.title || 'Natural Disaster',
            lat: event.geometries?.[0]?.coordinates?.[1] || 0,
            lon: event.geometries?.[0]?.coordinates?.[0] || 0,
            date: event.geometries?.[0]?.date,
            source: 'NASA EONET'
        }));
    },

    parseUSGS(data) {
        return (data.features || []).map(f => ({
            id: f.id,
            title: `Earthquake M${f.properties.mag} - ${f.properties.place}`,
            type: 'Earthquake',
            lat: f.geometry.coordinates[1],
            lon: f.geometry.coordinates[0],
            mag: f.properties.mag,
            depth: f.geometry.coordinates[2],
            url: f.properties.url,
            source: 'USGS'
        }));
    },

    parseReliefWeb(data) {
        return (data.data || []).map(d => ({
            id: d.id,
            title: d.fields?.name || 'Disaster',
            type: d.fields?.type?.name || 'Unknown',
            country: d.fields?.country?.name,
            date: d.fields?.date?.created,
            source: 'ReliefWeb'
        }));
    },

    // ==================== NEWS SOURCES ====================
    async fetchNews() {
        // Check cache
        if (this.cache.news.data && 
            (Date.now() - this.cache.news.timestamp) < this.CACHE_TTL) {
            return { 
                data: this.cache.news.data, 
                source: this.cache.news.source,
                cached: true 
            };
        }

        // Use your backend RSS proxy
        try {
            const response = await fetch('/api/rss-news');
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    this.cache.news = {
                        data: data,
                        timestamp: Date.now(),
                        source: 'RSS Feeds'
                    };
                    return { data, source: 'RSS Feeds' };
                }
            }
        } catch (e) {}

        // Fallback to mock
        const mockData = this.generateMockNews();
        this.cache.news = {
            data: mockData,
            timestamp: Date.now(),
            source: 'Mock Data'
        };
        return { data: mockData, source: 'Mock Data', mock: true };
    },

    // ==================== SIGNALS SOURCES ====================
    async fetchSignals() {
        // Check cache
        if (this.cache.signals.data && 
            (Date.now() - this.cache.signals.timestamp) < this.CACHE_TTL) {
            return { 
                data: this.cache.signals.data, 
                source: this.cache.signals.source,
                cached: true 
            };
        }

        // Try HDX
        try {
            const response = await fetch('https://hapi.humdata.org/api/v1/signals');
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    this.cache.signals = {
                        data: data,
                        timestamp: Date.now(),
                        source: 'HDX'
                    };
                    return { data, source: 'HDX' };
                }
            }
        } catch (e) {}

        // Try ReliefWeb
        try {
            const response = await fetch('https://api.reliefweb.int/v1/reports?limit=5&profile=minimum');
            if (response.ok) {
                const data = await response.json();
                const signals = (data.data || []).map(d => ({
                    headline: d.fields?.title,
                    summary: d.fields?.body?.substring(0, 150),
                    source: 'ReliefWeb',
                    date: d.fields?.date?.created
                }));
                if (signals.length > 0) {
                    this.cache.signals = {
                        data: signals,
                        timestamp: Date.now(),
                        source: 'ReliefWeb'
                    };
                    return { data: signals, source: 'ReliefWeb' };
                }
            }
        } catch (e) {}

        // Fallback to mock
        const mockData = this.generateMockSignals();
        this.cache.signals = {
            data: mockData,
            timestamp: Date.now(),
            source: 'Mock Data'
        };
        return { data: mockData, source: 'Mock Data', mock: true };
    },

    // ==================== ENHANCED MOCK GENERATORS ====================
    generateMockConflicts() {
        const types = ['Battle', 'Explosion', 'Violence against civilians', 'Protest', 'Riots'];
        const countries = ['Syria', 'Ukraine', 'Myanmar', 'Sudan', 'Ethiopia', 'Yemen', 'Somalia', 'DRC'];
        const cities = ['Damascus', 'Donetsk', 'Mandalay', 'Khartoum', 'Addis Ababa', 'Sana\'a', 'Mogadishu', 'Goma'];
        
        return Array(8).fill().map((_, i) => ({
            id: `mock-${i}`,
            title: `⚔️ ${types[i % types.length]} - ${cities[i % cities.length]}`,
            type: types[i % types.length],
            lat: 15 + (i * 5) % 40,
            lon: 30 + (i * 10) % 60,
            alertLevel: ['RED', 'ORANGE', 'GREEN'][i % 3],
            severity: ['CRITICAL', 'HIGH', 'MODERATE'][i % 3],
            color: ['#ff4444', '#ff8844', '#4CAF50'][i % 3],
            timestamp: new Date(Date.now() - i * 86400000).toISOString(),
            description: `Intense fighting reported in ${cities[i % cities.length]}`,
            fatalities: Math.floor(Math.random() * 50) + 1,
            country: countries[i % countries.length],
            source: 'Enhanced Mock'
        }));
    },

    generateMockFlights(lat, lon, radius) {
        const callsigns = ['DAL123', 'UAL456', 'AAL789', 'JBU234', 'SWA567', 'BAW890', 'KLM123', 'AFR456'];
        return Array(12).fill().map((_, i) => {
            const isEmergency = Math.random() > 0.8;
            return {
                callsign: callsigns[i % callsigns.length],
                lat: lat + (Math.random() - 0.5) * (radius / 50),
                lon: lon + (Math.random() - 0.5) * (radius / 50),
                altitude: Math.floor(Math.random() * 35000) + 5000,
                speed: Math.floor(Math.random() * 300) + 200,
                is_emergency: isEmergency,
                squawk: isEmergency ? '7700' : '1200',
                source: 'Enhanced Mock'
            };
        });
    },

    generateMockDisasters() {
        const disasters = [
            { title: 'Earthquake M7.2 - Caribbean Sea', type: 'Earthquake', lat: 18.5, lon: -77.2 },
            { title: 'Hurricane Ian - Gulf of Mexico', type: 'Hurricane', lat: 25.3, lon: -86.5 },
            { title: 'Flooding - Southeast Asia', type: 'Flood', lat: 14.5, lon: 108.2 },
            { title: 'Wildfire - California', type: 'Wildfire', lat: 37.8, lon: -122.4 },
            { title: 'Volcanic Eruption - Indonesia', type: 'Volcano', lat: -6.1, lon: 105.4 }
        ];
        
        return disasters.map((d, i) => ({
            id: `disaster-${i}`,
            ...d,
            severity: ['RED', 'ORANGE', 'GREEN'][i % 3],
            timestamp: new Date(Date.now() - i * 7200000).toISOString(),
            source: 'Enhanced Mock'
        }));
    },

    generateMockNews() {
        const headlines = [
            '7.2 magnitude earthquake strikes Caribbean, tsunami warnings issued',
            'UN warns of famine risk in Gaza as humanitarian situation worsens',
            'Flooding in Southeast Asia displaces thousands, crops destroyed',
            'WHO declares mpox global health emergency as cases surge',
            'Climate disasters cost global economy $250B in 2025, report finds',
            'Major humanitarian airlift reaches flood victims in Pakistan',
            'Wildfires rage across Mediterranean, thousands evacuated',
            'Earthquake in Afghanistan kills hundreds, aid workers race to reach remote areas'
        ];
        
        return headlines.map((title, i) => ({
            id: `news-${i}`,
            title: title,
            source: ['Reuters', 'AP', 'BBC', 'Al Jazeera'][i % 4],
            timestamp: new Date(Date.now() - i * 3600000).toISOString(),
            url: '#',
            category: ['Disaster', 'Conflict', 'Health'][i % 3]
        }));
    },

    generateMockSignals() {
        return [
            {
                id: 'signal-1',
                headline: '🚨 CRITICAL: Escalation in Eastern Ukraine',
                summary: 'Fighting intensifies near Donetsk with heavy artillery',
                severity: 'high',
                timestamp: new Date().toISOString(),
                trend: '+25% vs last week'
            },
            {
                id: 'signal-2',
                headline: '⚠️ WARNING: Food security deteriorating in Haiti',
                summary: 'IPC Phase 4 (Emergency) likely in coming months',
                severity: 'medium',
                timestamp: new Date().toISOString(),
                trend: 'Worsening'
            },
            {
                id: 'signal-3',
                headline: '🌍 Sudan: Humanitarian access constraints',
                summary: 'Aid deliveries blocked in Darfur region',
                severity: 'high',
                timestamp: new Date(Date.now() - 86400000).toISOString(),
                trend: 'Critical'
            }
        ];
    },

    // ==================== UTILITY FUNCTIONS ====================
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
                Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },

    // Clear cache (useful for refresh)
    clearCache(type = null) {
        if (type) {
            this.cache[type] = { data: null, timestamp: null, source: null };
        } else {
            Object.keys(this.cache).forEach(key => {
                this.cache[key] = { data: null, timestamp: null, source: null };
            });
        }
    }
};