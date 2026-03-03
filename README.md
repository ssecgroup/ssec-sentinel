#  ssec-Sentinel - Emergency Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)

**ssec-Sentinel** is a comprehensive emergency intelligence platform that monitors:
- 🔴 **War Zones & Conflicts** (ACLED data)
- ✈️ **Emergency Flights** (OpenSky Network)
- 🌊 **Natural Disasters** (GDACS, NOAA)
- 🚨 **Crisis Alerts** (HDX Signals)
- 📻 **Emergency Radio** (Worldwide streams)
- 🆘 **Crisis Helplines** (50+ countries)

##  Mission

To provide **free, accessible emergency intelligence** to everyone, everywhere. When disaster strikes, information saves lives.

##  Features

- 🌍 **Interactive World Map** with conflict zones, military bases, and flight tracking
- 🔥 **Heatmap visualization** of disaster hotspots
- 📡 **Real-time conflict data** from ACLED
- ✈️ **Emergency flight detection** (squawk 7500/7600/7700)
- 📻 **Worldwide emergency radio** (BBC, NHK, KCRW, etc.)
- 🆘 **Country-specific crisis helplines** (50+ countries)
- 🚨 **Automated HDX Signals** for crisis detection
- 🔮 **VIEWS conflict forecasts** (3-36 months ahead)

##  Quick Start

```bash
# Clone the repository
git clone https://github.com/ssecgroup/ssec-sentinel.git
cd ssec-sentinel

# Set up backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Run backend
python backend/ssec_app.py

# In another terminal, serve frontend
cd frontend
python3 -m http.server 8001

# Open browser
open http://localhost:8001
```

##  API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ssec/health` | API health check |
| `/ssec/api/conflicts` | Active conflict zones |
| `/ssec/api/flights/near` | Flights near coordinates |
| `/ssec/api/heatmap` | Disaster heatmap data |
| `/ssec/api/signals` | HDX crisis alerts |
| `/ssec/api/forecasts` | Conflict risk forecasts |
| `/ssec/api/military-bases` | Global military installations |
| `/ssec/api/helplines` | Country crisis helplines |
| `/ssec/api/dashboard` | Complete dashboard data |

##  Map Controls

- **Conflicts** - Toggle conflict zone markers
- **Flights** - Toggle aircraft tracking
- **Heatmap** - Toggle disaster density
- **Military** - Toggle military bases
- **Reset** - Reset map view

##  Contributing

We welcome contributors! See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## 💖 Support the Project

Your donations fund decentralized disaster nodes in remote areas:

**ETH**: `0x8242f0f25c5445F7822e80d3C9615e57586c6639`

Funds go toward:
- 🌍 Raspberry Pi nodes with SDR receivers
- ☀️ Solar power setups for remote areas
- 📡 Satellite modems for internet-free zones
- 👨‍💻 Developer grants for blockchain integration

## 📜 License

MIT License - Free for humanitarian use forever

##  Links

- [GitHub Repository](https://github.com/ssecgroup/ssec-sentinel)
- [Blockchain Vision](docs/ssec-BLOCKCHAIN.md)
- [API Documentation](docs/ssec-API.md)
- [Legal & Compliance](docs/ssec-LEGAL.md)

##  Legal

ssec-Sentinel only uses **public data sources** and respects:
- robots.txt and rate limits
- API terms of service
- Privacy regulations (GDPR, etc.)

---

Built with ❤️ by [SSEC](https://github.com/ssecgroup) - Secure Systems & Emergency Communications
