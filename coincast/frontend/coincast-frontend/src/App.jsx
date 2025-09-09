import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  Container, Row, Col, Form, Button, Navbar, Spinner, Alert, Card, Badge
} from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, Filler);

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
console.log('API base =', API);

export default function App() {
  const [coins, setCoins] = useState([]);
  const [coin, setCoin] = useState('bitcoin');
  const [horizon, setHorizon] = useState(7);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initError, setInitError] = useState('');
  const [predError, setPredError] = useState('');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [changePct, setChangePct] = useState(null);

  // Prevent double-fetch in StrictMode (dev)
  const didInit = useRef(false);

  // --- Load coin list once ---
  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;

    axios.get(`${API}/api/coins`)
      .then(r => {
        const list = r.data || [];
        setCoins(list);
        if (list.length > 0 && !list.find(c => c.id === 'bitcoin')) {
          setCoin(list[0].id);
        }
      })
      .catch(err => {
        console.error('Failed /api/coins', err);
        setInitError('Could not load coin list from API.');
      });
  }, []);

  // --- Fetch predictions when coin/horizon change ---
  const load = async () => {
    setLoading(true);
    setPredError('');
    try {
      const r = await axios.get(`${API}/api/predict`, {
        params: { coin_id: coin, horizon }
      });
      setData(r.data);

      // Derive latest price & 24h change from history
      const hist = r.data?.history || [];
      if (hist.length >= 2) {
        const last = hist[hist.length - 1].price;
        const prev = hist[hist.length - 2].price;
        setCurrentPrice(last);
        setChangePct(((last - prev) / prev) * 100);
      } else if (hist.length === 1) {
        setCurrentPrice(hist[0].price);
        setChangePct(null);
      } else {
        setCurrentPrice(null);
        setChangePct(null);
      }
    } catch (err) {
      console.error('Failed /api/predict', err);
      const msg = err?.response?.status === 429
        ? 'Rate limited by data provider. Please try again in a minute.'
        : 'Failed to load prediction data.';
      setPredError(msg);
      setData(null);
      setCurrentPrice(null);
      setChangePct(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (coin) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [coin, horizon]);

  // --- Chart data ---
  const chartData = data ? {
    datasets: [
      {
        label: 'History',
        data: (data.history || []).map(p => ({ x: p.t, y: p.price })),
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2
      },
      {
        label: 'Forecast',
        data: (data.forecast || []).map(p => ({ x: p.t, y: p.yhat })),
        borderDash: [6, 6],
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2
      }
    ]
  } : { datasets: [] };

  const options = {
    parsing: false,
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { type: 'time', time: { unit: 'day' }, grid: { color: '#e7e7e7' } },
      y: { beginAtZero: false, grid: { color: '#f2f2f2' } }
    },
    plugins: {
      legend: { position: 'top', labels: { boxWidth: 12 } },
      tooltip: { mode: 'index', intersect: false }
    },
    animation: false
  };

  const changeBadge =
    changePct == null ? null :
      <Badge bg={changePct >= 0 ? 'success' : 'danger'} className="ms-2">
        {changePct >= 0 ? '▲' : '▼'} {Math.abs(changePct).toFixed(2)}%
      </Badge>;

  return (
    <>
      {/* Header */}
      <Navbar bg="dark" variant="dark" expand="lg" className="mb-3">
        <Container>
          <Navbar.Brand>CoinCast</Navbar.Brand>
          <Navbar.Text className="ms-auto">
            {coin && currentPrice != null && (
              <>
                {coin.toUpperCase()}&nbsp;${currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                {changeBadge}
              </>
            )}
          </Navbar.Text>
        </Container>
      </Navbar>

      <Container>
        {initError && <Alert variant="danger" className="mb-3">{initError}</Alert>}

        {/* Controls */}
        <Card className="mb-3 shadow-sm">
          <Card.Body>
            <Row className="g-3 align-items-end">
              <Col xs={12} md={5}>
                <Form.Label className="fw-semibold">Cryptocurrency</Form.Label>
                <Form.Select value={coin} onChange={e => setCoin(e.target.value)} disabled={coins.length === 0}>
                  {coins.length === 0
                    ? <option value="">Loading coins…</option>
                    : coins.map(c => <option key={c.id} value={c.id}>{c.name}</option>)
                  }
                </Form.Select>
              </Col>

              <Col xs={12} md={4}>
                <Form.Label className="fw-semibold">Forecast Horizon</Form.Label>
                <Form.Select value={horizon} onChange={e => setHorizon(Number(e.target.value))}>
                  {[7, 14, 30].map(h => <option key={h} value={h}>{h}-day horizon</option>)}
                </Form.Select>
              </Col>

              <Col xs="auto">
                <Button onClick={load} disabled={loading || !coin}>
                  {loading ? (<><Spinner size="sm" className="me-2" />Loading…</>) : 'Refresh'}
                </Button>
              </Col>
            </Row>
          </Card.Body>
        </Card>

        {predError && <Alert variant="warning" className="mb-3">{predError}</Alert>}

        {/* Chart */}
        <Card className="shadow-sm position-relative">
          {loading && (
            <div
              className="d-flex justify-content-center align-items-center"
              style={{ position: 'absolute', inset: 0, background: 'rgba(255,255,255,0.55)', zIndex: 10 }}
            >
              <Spinner animation="border" />
            </div>
          )}
          <Card.Body>
            <div style={{ height: 460 }}>
              <Line data={chartData} options={options} />
            </div>
          </Card.Body>
        </Card>

        {/* Footer */}
        <div className="text-center text-muted mt-4 mb-2">
          <small>Predictions are for demonstration only — not financial advice.</small>
        </div>
      </Container>
    </>
  );
}
