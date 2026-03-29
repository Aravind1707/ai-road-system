import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

function App() {
  const [vehicles, setVehicles] = useState([])
  const [complaints, setComplaints] = useState([])
  const [segments, setSegments] = useState([])
  const [routePoints, setRoutePoints] = useState([])
  const [segmentInput, setSegmentInput] = useState('')
  const [syncStatus, setSyncStatus] = useState('')

  useEffect(() => {
    fetchComplaints()
    fetchVehicleRoutes('V001')
  }, [])

  async function fetchComplaints() {
    const res = await fetch(`${API_BASE}/vehicle/complaints`)
    if (res.ok) {
      setComplaints(await res.json())
    }
  }

  async function fetchVehicleRoutes(vehicleId) {
    const res = await fetch(`${API_BASE}/vehicle/routes/${vehicleId}`)
    if (!res.ok) return
    const data = await res.json()
    setVehicles(data)
    if (data.length > 0) {
      const routeId = data[0].route_id
      const pointRes = await fetch(`${API_BASE}/route/${routeId}/points`)
      if (pointRes.ok) setRoutePoints(await pointRes.json())
    }
  }

  async function fetchPrediction(segmentId) {
    if (!segmentId) return
    const res = await fetch(`${API_BASE}/predict/segment/${segmentId}`)
    if (!res.ok) return
    const payload = await res.json()
    const entry = {
      segment_id: payload.segment_id,
      segment_damage_score: payload.segment_damage_score,
      ...payload.prediction
    }
    setSegments([entry])
  }

  async function closeComplaint(complaintId) {
    const res = await fetch(`${API_BASE}/vehicle/complaints/${complaintId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Resolved', remarks: 'Verified-complete' })
    })
    if (res.ok) {
      fetchComplaints()
    }
  }

  async function sendReport(complaintId) {
    const res = await fetch(`${API_BASE}/vehicle/complaints/${complaintId}/send`, {
      method: 'POST'
    })
    if (res.ok) {
      alert('Report sent to authority')
    }
  }

  async function downloadComplaintPdf(complaintId) {
    const res = await fetch(`${API_BASE}/vehicle/complaints/${complaintId}/pdf`, {
      headers: { 'Authorization': localStorage.getItem('authToken') || '' }
    })
    if (!res.ok) {
      alert('PDF generation failed')
      return
    }
    const data = await res.json()
    alert(`PDF generated: ${data.pdf_path}`)
  }

  async function syncOfflineData() {
    const samplePayload = [{
      vehicle_id: 'V001',
      latitude: 13.0827,
      longitude: 80.2707,
      timestamp: new Date().toISOString(),
      severity: 1,
      length: 2.5,
      vibration: 0.2,
      road_type: 'urban',
      traffic_density: 0.75
    }]

    const headers = {
      'Content-Type': 'application/json'
    }
    const token = localStorage.getItem('authToken')
    if (token) headers.Authorization = token

    const res = await fetch(`${API_BASE}/vehicle/offline/sync`, {
      method: 'POST',
      headers,
      body: JSON.stringify(samplePayload)
    })

    if (res.ok) {
      const result = await res.json()
      setSyncStatus(`Synced ${result.synced_records ?? 0} records`)
    } else {
      setSyncStatus('Offline sync failed')
    }
  }

  return (
    <div className="app">
      <header>
        <div className="hero-copy">
          <h1>Smart Road AI</h1>
          <p>Realtime road damage monitoring with contrast-first controls and a crisp dashboard experience.</p>
        </div>
      </header>

      <section className="grid">
        <div className="card">
          <h2>Vehicle Routes</h2>
          <ul>
            {vehicles.map((route) => (
              <li key={route.route_id}>
                Route {route.route_id} ({route.start_time} → {route.end_time || 'ongoing'})
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2>Segment Prediction</h2>
          <div className="input-row">
            <input
              type="text"
              value={segmentInput}
              onChange={(event) => setSegmentInput(event.target.value)}
              placeholder="Segment e.g. 13.0827_80.2707"
              aria-label="Segment ID"
            />
            <button className="primary" onClick={() => fetchPrediction(segmentInput)}>
              Predict 7-day Damage
            </button>
          </div>
          {segments[0] && (
            <div className="prediction-card">
              <p><strong>Segment:</strong> {segments[0].segment_id}</p>
              <p><strong>Current Score:</strong> {segments[0].segment_damage_score}</p>
              <p><strong>7-day forecast:</strong> {segments[0].predicted_damage.toFixed(2)}</p>
              <p><strong>Growth Rate:</strong> {segments[0].growth_rate.toFixed(2)}</p>
            </div>
          )}
        </div>

        <div className="card">
          <h2>Complaints</h2>
          <ul>
            {complaints.map((c) => (
              <li key={c.complaint_id}>
                {c.segment_id} • {c.priority} • {c.status}
                <div className="action-buttons">
                  <button className="secondary" onClick={() => sendReport(c.complaint_id)}>
                    Send Report
                  </button>
                  <button className="secondary" onClick={() => closeComplaint(c.complaint_id)}>
                    Mark Resolved
                  </button>
                  <button className="secondary" onClick={() => downloadComplaintPdf(c.complaint_id)}>
                    Download PDF
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2>Edge Offline Sync</h2>
          <p>Send cached edge data to the backend store and verify sync status.</p>
          <button className="primary" onClick={syncOfflineData}>Sync Now</button>
          {syncStatus && <p className="status-message">{syncStatus}</p>}
        </div>
      </section>

      <section className="map-container">
        <MapContainer center={[13.0827, 80.2707]} zoom={13} scrollWheelZoom className="leaflet-map">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {routePoints.length > 0 && (
            <Polyline positions={routePoints.map((p) => [p.latitude, p.longitude])} color="blue" />
          )}
          {routePoints.map((point, idx) => (
            <Marker key={idx} position={[point.latitude, point.longitude]}>
              <Popup>{point.timestamp}</Popup>
            </Marker>
          ))}
        </MapContainer>
      </section>
    </div>
  )
}

export default App
