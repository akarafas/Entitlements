import { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

async function apiFetch(path, token, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.error || JSON.stringify(body);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  return response.json();
}

export default function App() {
  const [token, setToken] = useState('');
  const [role, setRole] = useState('');
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [entitlements, setEntitlements] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [lengthDays, setLengthDays] = useState(30);
  const [selectedRightsCustomer, setSelectedRightsCustomer] = useState('');
  const [rights, setRights] = useState([]);
  const [error, setError] = useState('');

  const canWrite = useMemo(() => role === 'support', [role]);

  async function loadData(currentToken) {
    const [c, p, e] = await Promise.all([
      apiFetch('/customers', currentToken),
      apiFetch('/products', currentToken),
      apiFetch('/entitlements', currentToken),
    ]);
    setCustomers(c);
    setProducts(p);
    setEntitlements(e);
  }

  useEffect(() => {
    if (!token) return;
    loadData(token).catch((err) => setError(err.message));
  }, [token]);

  async function login(email, password) {
    setError('');
    const data = await apiFetch('/auth/login', '', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(data.token);
    setRole(data.role);
  }

  async function grantEntitlement() {
    setError('');
    await apiFetch('/entitlements', token, {
      method: 'POST',
      body: JSON.stringify({
        customer: Number(selectedCustomer),
        product: Number(selectedProduct),
        start_date: new Date().toISOString().slice(0, 10),
        length_days: Number(lengthDays),
      }),
    });
    await loadData(token);
  }

  async function revokeEntitlement(id) {
    setError('');
    await apiFetch(`/entitlements/${id}/revoke`, token, {
      method: 'POST',
      body: JSON.stringify({}),
    });
    await loadData(token);
  }

  async function fetchRights() {
    setError('');
    const data = await apiFetch(`/customers/${selectedRightsCustomer}/rights`, token);
    setRights(data.active_rights || []);
  }

  return (
    <main className="container">
      <h1>Entitlements Support Console (React + Flask)</h1>
      {error && <p className="error">{error}</p>}

      {!token ? (
        <section className="card">
          <h2>Login</h2>
          <LoginForm onSubmit={login} />
          <p><strong>Support:</strong> support@example.com / Support123!</p>
          <p><strong>Developer:</strong> developer@example.com / Developer123!</p>
        </section>
      ) : (
        <>
          <p>Logged in role: <strong>{role}</strong> ({canWrite ? 'read/write' : 'read-only'})</p>

          <section className="card">
            <h2>Grant Entitlement</h2>
            <select value={selectedCustomer} onChange={(e) => setSelectedCustomer(e.target.value)}>
              <option value="">Select Customer</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.email}</option>)}
            </select>
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
              <option value="">Select Product</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <input type="number" value={lengthDays} min={1} onChange={(e) => setLengthDays(e.target.value)} />
            <button disabled={!canWrite || !selectedCustomer || !selectedProduct} onClick={grantEntitlement}>Grant</button>
          </section>

          <section className="card">
            <h2>Entitlements</h2>
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Customer</th><th>Product</th><th>Start</th><th>End</th><th>Status</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {entitlements.map((ent) => (
                  <tr key={ent.id}>
                    <td>{ent.id}</td>
                    <td>{ent.customer_email}</td>
                    <td>{ent.product_name}</td>
                    <td>{ent.start_date}</td>
                    <td>{ent.end_date}</td>
                    <td>{ent.is_active ? 'Active' : ent.is_revoked ? 'Revoked' : 'Expired'}</td>
                    <td><button disabled={!canWrite || ent.is_revoked} onClick={() => revokeEntitlement(ent.id)}>Revoke</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Query Customer Rights</h2>
            <select value={selectedRightsCustomer} onChange={(e) => setSelectedRightsCustomer(e.target.value)}>
              <option value="">Select Customer</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.email}</option>)}
            </select>
            <button disabled={!selectedRightsCustomer} onClick={fetchRights}>Get Rights</button>
            <ul>
              {rights.map((r) => <li key={r.id}>{r.product_name} ({r.start_date} to {r.end_date})</li>)}
            </ul>
          </section>
        </>
      )}
    </main>
  );
}

function LoginForm({ onSubmit }) {
  const [email, setEmail] = useState('support@example.com');
  const [password, setPassword] = useState('Support123!');

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(email, password).catch((err) => alert(`Login failed: ${err.message}`));
      }}
    >
      <input type="email" placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Login</button>
    </form>
  );
}
