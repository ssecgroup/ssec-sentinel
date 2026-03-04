#  ssec·Sentinel - Emergency Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Vercel](https://img.shields.io/badge/deployed%20on-Vercel-black.svg)](https://vercel.com)
[![Render](https://img.shields.io/badge/deployed%20on-Render-46E3B7.svg)](https://render.com)
[![GitHub](https://img.shields.io/badge/Open%20Source-❤️-red.svg)](https://github.com/ssecgroup/ssec-sentinel)

<div align="center">
  <img src="https://raw.githubusercontent.com/ssecgroup/ssec-sentinel/main/frontend/assets/icons/ssec-logo.png" alt="ssec·Sentinel Logo" width="200"/>
  <p><strong>Real-time emergency intelligence for everyone, everywhere.</strong></p>
</div>

---

##  **Mission**

**ssec·Sentinel** provides **free, accessible emergency intelligence** to everyone. When disaster strikes, information saves lives. Our platform aggregates real-time data from multiple sources to give you a comprehensive view of conflicts, disasters, and emergencies worldwide.

---

##  **Features**

###  **Interactive World Map**
- Real-time conflict zone visualization
- Military base locations
- Live flight tracking with emergency squawk detection (7500/7600/7700)
- Disaster heatmap overlay
- Layer toggles for different data types

###  **Flight Tracking**
- Live aircraft positions from OpenSky Network
- Emergency squawk detection
- Filter by location and emergency status
- Detailed flight information (callsign, altitude, speed)

###  **Emergency Radio**
- Global emergency broadcast streams
- BBC World Service, France Inter, NHK World, KCRW, CBC Radio
- One-click play/stop

###  **Crisis Helplines**
- Emergency numbers for 50+ countries
- Search by country name
- 24/7 availability indicators
- Police, medical, humanitarian, disaster response

###  **World Disaster News**
- Live RSS feeds from major news sources
- BBC, Reuters, Al Jazeera, NPR, NDTV, NHK
- Real-time updates
- Category tagging (Disaster/Conflict/Health)

###  **Crisis Signals**
- HDX humanitarian alerts
- Severity indicators (HIGH/MEDIUM/LOW)
- Trend analysis
- Geographic targeting

###  **Military Installations**
- Global military bases
- US, NATO, Russian facilities
- Country-specific filtering

---

##  **Architecture**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   API Proxy     │────▶│   Backend API   │
│   (Vercel)      │     │   (Vercel)      │     │   (Render)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                           ┌─────────────────────────┐
                                           │    Data Sources         │
                                           │  ┌─────────────────────┐ │
                                           │  │ ACLED (Conflicts)   │ │
                                           │  ├─────────────────────┤ │
                                           │  │ OpenSky (Flights)   │ │
                                           │  ├─────────────────────┤ │
                                           │  │ HDX (Signals)       │ │
                                           │  ├─────────────────────┤ │
                                           │  │ RSS News (BBC, etc) │ │
                                           │  └─────────────────────┘ │
                                           └─────────────────────────┘
```

---

##  **Live Demo**

| Service | URL |
|---------|-----|
| **Frontend** | [https://ssec-sentinel.vercel.app](https://ssec-sentinel.vercel.app) |
| **Backend API** | [https://ssec-sentinel.onrender.com](https://ssec-sentinel.onrender.com) |
| **API Documentation** | [https://ssec-sentinel.onrender.com/docs](https://ssec-sentinel.onrender.com/docs) |

---

##  **API Endpoints**

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/` | API information | - |
| `/health` | Health check | - |
| `/conflicts` | Conflict events | `country`, `days`, `min_fatalities`, `event_type` |
| `/flights/near` | Flights near location | `lat`, `lon`, `radius`, `emergency_only` |
| `/flights/emergency` | Emergency flights only | - |
| `/heatmap` | Disaster heatmap | `disaster_type`, `days`, `points` |
| `/signals` | Crisis signals | `severity` |
| `/military-bases` | Military installations | `country` |
| `/helplines` | Crisis helplines | `country`, `helpline_type` |
| `/news` | World disaster news | `limit` |
| `/dashboard` | Complete dashboard data | `country` |

---

##  **Tech Stack**

### **Backend**
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [Uvicorn](https://www.uvicorn.org/) - ASGI server
- [HTTPX](https://www.python-httpx.org/) - Async HTTP client
- [Feedparser](https://feedparser.readthedocs.io/) - RSS parsing
- [Cachetools](https://github.com/tkem/cachetools) - Caching

### **Frontend**
- [Leaflet](https://leafletjs.com/) - Interactive maps
- [Font Awesome](https://fontawesome.com/) - Icons
- [Google Fonts](https://fonts.google.com/) - Typography
- Vanilla JavaScript - No framework dependencies

### **DevOps**
- [Vercel](https://vercel.com/) - Frontend hosting
- [Render](https://render.com/) - Backend hosting
- [GitHub](https://github.com/) - Version control

---

## 🏁 **Quick Start**

### **Local Development**

```bash
# Clone the repository
git clone https://github.com/ssecgroup/ssec-sentinel.git
cd ssec-sentinel

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file (for local development)
cp .env.example .env
# Edit .env with your credentials

# Run backend
python backend/ssec_app.py

# Frontend setup (in another terminal)
cd frontend
python -m http.server 8001

# Open browser
open http://localhost:8001
```

### **Environment Variables**

Create a `.env` file with:

```bash
# ACLED API Credentials (get from https://developer.acleddata.com)
ACLED_USERNAME=your_email@example.com
ACLED_PASSWORD=your_password_here

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379
```

---

##  **Deployment**

### **Deploy to Render (Backend)**

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect your repository
4. Set environment variables:
   ```
   ACLED_USERNAME=your_email@example.com
   ACLED_PASSWORD=your_password
   PYTHON_VERSION=3.11.0
   ```
5. Deploy!

### **Deploy to Vercel (Frontend)**

```bash
npm install -g vercel
vercel
```

Or connect your GitHub repository directly on [Vercel](https://vercel.com).

---

##  **Project Structure**

```
ssec-sentinel/
├── backend/
│   ├── collectors/
│   │   ├── ssec_acled.py      # ACLED conflict data
│   │   ├── ssec_flights.py     # OpenSky flight tracking
│   │   ├── ssec_hdx.py         # HDX humanitarian data
│   │   ├── ssec_heatmap.py     # Heatmap generator
│   │   ├── ssec_helplines_enhanced.py # Crisis helplines
│   │   ├── ssec_military.py    # Military bases
│   │   ├── ssec_news.py        # RSS news aggregator
│   │   ├── ssec_signals.py     # HDX crisis signals
│   │   ├── ssec_transport.py   # Transportation data
│   │   └── ssec_views.py       # VIEWS conflict forecasts
│   ├── models/                  # Data models
│   ├── utils/                   # Utilities
│   ├── ssec_app.py              # Main FastAPI app
│   ├── ssec_config.py           # Configuration
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── index.html               # Main dashboard
│   ├── css/                     # Stylesheets
│   ├── js/                      # JavaScript modules
│   └── assets/                   # Icons and images
├── api/
│   └── index.py                  # Vercel serverless function
├── docs/                          # Documentation
├── tests/                         # Test files
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore file
├── vercel.json                      # Vercel configuration
├── render.yaml                      # Render configuration
├── LICENSE                          # MIT License
└── README.md                        # This file
```

---

##  **Contributing**

We welcome contributions! Here's how you can help:

### **Ways to Contribute**
- 🐛 Report bugs via GitHub Issues
- 💡 Suggest new features
- 🌐 Add translations
- 📝 Improve documentation
- 🔧 Submit pull requests

### **Development Process**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Code Style**
- Python: Follow PEP 8
- JavaScript: Use consistent formatting
- HTML/CSS: Keep it clean and responsive

---

##  **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  **Acknowledgments**

- [ACLED](https://acleddata.com/) for conflict data
- [OpenSky Network](https://opensky-network.org/) for flight data
- [HDX](https://data.humdata.org/) for humanitarian data
- [VIEWS](https://views.pcr.uu.se/) for conflict forecasts
- [ReliefWeb](https://reliefweb.int/) for disaster reports
- All the news organizations providing RSS feeds

---

##  **Contact & Support**

### **Project Links**
- GitHub: [https://github.com/ssecgroup/ssec-sentinel](https://github.com/ssecgroup/ssec-sentinel)
- Live Demo: [https://ssec-sentinel.vercel.app](https://ssec-sentinel.vercel.app)
- API Docs: [https://ssec-sentinel.onrender.com/docs](https://ssec-sentinel.onrender.com/docs)

### **Donations**
Your support helps fund decentralized disaster nodes in remote areas:

**ETH**: `0x8242f0f25c5445F7822e80d3C9615e57586c6639`

Funds go toward:
- 🌍 Raspberry Pi nodes with SDR receivers
- ☀️ Solar power setups for remote areas
- 📡 Satellite modems for internet-free zones
- 👨‍💻 Developer grants for blockchain integration

---

<div align="center">
  <p>Built with ❤️ by <a href="https://github.com/ssecgroup">SSEC - Secure Systems & Emergency Communications</a></p>
  <p>🌍 <strong>Free. Open Source. For Everyone.</strong></p>
</div>
