'use client';

import { useEffect, useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';

async function apiFetch(path, token, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export default function Home() {
  const [token, setToken] = useState('');
  const [role, setRole] = useState('');
  const [users, setUsers] = useState([]);
  const [products, setProducts] = useState([]);
  const [entitlements, setEntitlements] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [lengthDays, setLengthDays] = useState(30);
  const [selectedRightsUser, setSelectedRightsUser] = useState('');
  const [rights, setRights] = useState([]);

  const canWrite = useMemo(() => role === 'support', [role]);

  async function login(email, password) {
    const data = await apiFetch('/auth/login/', '', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(data.token);
    setRole(data.role);
  }

  async function loadData(currentToken) {
    const [u, p, e] = await Promise.all([
      apiFetch('/users/', currentToken),
      apiFetch('/products/', currentToken),
      apiFetch('/entitlements/', currentToken),
    ]);
    setUsers(u);
    setProducts(p);
    setEntitlements(e);
  }

  useEffect(() => {
    if (!token) return;
    loadData(token).catch(console.error);
  }, [token]);

  async function grantEntitlement() {
    await apiFetch('/entitlements/', token, {
      method: 'POST',
      body: JSON.stringify({
        user: Number(selectedUser),
        product: Number(selectedProduct),
        start_date: new Date().toISOString().slice(0, 10),
        length_days: Number(lengthDays),
      }),
    });
    await loadData(token);
  }

  async function revokeEntitlement(id) {
    await apiFetch(`/entitlements/${id}/revoke/`, token, { method: 'POST', body: '{}' });
    await loadData(token);
  }

  async function loadRights() {
    const data = await apiFetch(`/users/${selectedRightsUser}/rights/`, token);
    setRights(data.active_rights || []);
  }

  return (
    <main>
      <h1>Entitlements Support Console</h1>
      {!token ? (
        <div style={{ border: '1px solid #ddd', padding: 16, maxWidth: 420 }}>
          <h2>Login</h2>
          <LoginForm onSubmit={login} />
          <p><strong>Support:</strong> support@example.com / Support123!</p>
          <p><strong>Developer:</strong> developer@example.com / Developer123!</p>
        </div>
      ) : (
        <>
          <p>Logged in role: <strong>{role}</strong> ({canWrite ? 'read/write' : 'read-only'})</p>

          <section style={{ marginBottom: 24 }}>
            <h2>Grant Entitlement</h2>
            <select value={selectedUser} onChange={(e) => setSelectedUser(e.target.value)}>
              <option value="">Select User</option>
              {users.map((u) => <option key={u.id} value={u.id}>{u.email}</option>)}
            </select>{' '}
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
              <option value="">Select Product</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>{' '}
            <input type="number" value={lengthDays} onChange={(e) => setLengthDays(e.target.value)} min={1} /> days{' '}
            <button disabled={!canWrite || !selectedUser || !selectedProduct} onClick={grantEntitlement}>Grant</button>
          </section>

          <section style={{ marginBottom: 24 }}>
            <h2>Entitlements</h2>
            <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th>ID</th><th>User</th><th>Product</th><th>Start</th><th>End</th><th>Status</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {entitlements.map((e) => (
                  <tr key={e.id}>
                    <td>{e.id}</td>
                    <td>{e.user_email}</td>
                    <td>{e.product_name}</td>
                    <td>{e.start_date}</td>
                    <td>{e.end_date}</td>
                    <td>{e.is_active ? 'Active' : e.is_revoked ? 'Revoked' : 'Expired'}</td>
                    <td>
                      <button disabled={!canWrite || e.is_revoked} onClick={() => revokeEntitlement(e.id)}>Revoke</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h2>Query User Rights</h2>
            <select value={selectedRightsUser} onChange={(e) => setSelectedRightsUser(e.target.value)}>
              <option value="">Select User</option>
              {users.map((u) => <option key={u.id} value={u.id}>{u.email}</option>)}
            </select>{' '}
            <button disabled={!selectedRightsUser} onClick={loadRights}>Get Rights</button>
            <ul>
              {rights.map((r) => (
                <li key={r.id}>{r.product_name} ({r.start_date} to {r.end_date})</li>
              ))}
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
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(email, password).catch((err) => alert(`Login failed: ${err.message}`));
      }}
      style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
    >
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" />
      <button type="submit">Login</button>
    </form>
  );
}
