// frontend/js/ssec-signals.js
async function checkHDXSignals() {
    const response = await fetch('https://hapi.humdata.org/api/v1/signals');
    const signals = await response.json();
    
    signals.forEach(signal => {
        if (signal.severity === 'high') {
            showToast(`🚨 CRISIS ALERT: ${signal.headline}`);
            
            // Add alert marker to map
            L.marker([signal.lat, signal.lon], {
                icon: crisisIcon
            }).bindPopup(`
                <div style="border-left: 4px solid #ff4444; padding: 10px;">
                    <h3>🚨 HDX Signal</h3>
                    <p><strong>${signal.headline}</strong></p>
                    <p>${signal.summary}</p>
                    <small>${signal.trend_comparison}</small>
                </div>
            `).addTo(map);
        }
    });
}
