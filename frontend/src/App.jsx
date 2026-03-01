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
  const [newCustomerName, setNewCustomerName] = useState('');
  const [newCustomerEmail, setNewCustomerEmail] = useState('');
  const [newCustomerAddress, setNewCustomerAddress] = useState('');

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

  async function saveProduct(productId, name, accessType, description, capabilities) {
    setError('');
    await apiFetch(`/products/${productId}`, token, {
      method: 'PUT',
      body: JSON.stringify({ name, access_type: accessType, description, capabilities }),
    });
    await loadData(token);
  }


  async function createCustomer() {
    setError('');
    await apiFetch('/customers', token, {
      method: 'POST',
      body: JSON.stringify({
        name: newCustomerName.trim(),
        email: newCustomerEmail.trim(),
        address: newCustomerAddress.trim(),
      }),
    });
    setNewCustomerName('');
    setNewCustomerEmail('');
    setNewCustomerAddress('');
    await loadData(token);
  }

  async function saveCustomer(customerId, name, email, address) {
    setError('');
    await apiFetch(`/customers/${customerId}`, token, {
      method: 'PUT',
      body: JSON.stringify({ name, email, address }),
    });
    await loadData(token);
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
            <h2>Customers</h2>
            <p>View all customers below. Support users can add new customers and edit customer details.</p>
            <div className="stack customer-create">
              <input
                placeholder="Customer name"
                value={newCustomerName}
                disabled={!canWrite}
                onChange={(e) => setNewCustomerName(e.target.value)}
              />
              <input
                placeholder="Customer email"
                value={newCustomerEmail}
                disabled={!canWrite}
                onChange={(e) => setNewCustomerEmail(e.target.value)}
              />
              <input
                placeholder="Customer address"
                value={newCustomerAddress}
                disabled={!canWrite}
                onChange={(e) => setNewCustomerAddress(e.target.value)}
              />
              <button
                disabled={!canWrite || !newCustomerName.trim() || !newCustomerEmail.trim()}
                onClick={createCustomer}
              >
                Add Customer
              </button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Email</th><th>Address</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <CustomerRow
                    key={customer.id}
                    customer={customer}
                    canWrite={canWrite}
                    onSave={saveCustomer}
                  />
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Products</h2>
            <p>View all products below. Support users can edit product name, access type, and description.</p>
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Capabilities</th><th>Description</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <ProductRow
                    key={product.id}
                    product={product}
                    canWrite={canWrite}
                    onSave={saveProduct}
                  />
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Grant Entitlement</h2>
            <select value={selectedCustomer} onChange={(e) => setSelectedCustomer(e.target.value)}>
              <option value="">Select Customer</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.email}</option>)}
            </select>
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
              <option value="">Select Product</option>
              {products.map((p) => <option key={p.id} value={p.id}>{`${p.name} — ${(p.capabilities || []).join(', ')}`}</option>)}
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
                    <td>{formatStatus(ent.status)}</td>
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


function formatStatus(status) {
  if (!status) return 'Unknown';
  return status.charAt(0).toUpperCase() + status.slice(1);
}


function CustomerRow({ customer, canWrite, onSave }) {
  const [name, setName] = useState(customer.name);
  const [email, setEmail] = useState(customer.email);
  const [address, setAddress] = useState(customer.address || '');

  useEffect(() => {
    setName(customer.name);
    setEmail(customer.email);
    setAddress(customer.address || '');
  }, [customer.id, customer.name, customer.email, customer.address]);

  return (
    <tr>
      <td>{customer.id}</td>
      <td><input value={name} disabled={!canWrite} onChange={(e) => setName(e.target.value)} /></td>
      <td><input value={email} disabled={!canWrite} onChange={(e) => setEmail(e.target.value)} /></td>
      <td><input value={address} disabled={!canWrite} onChange={(e) => setAddress(e.target.value)} /></td>
      <td>
        <button
          disabled={!canWrite || !name.trim() || !email.trim()}
          onClick={() => onSave(customer.id, name.trim(), email.trim(), address.trim())}
        >
          Save
        </button>
      </td>
    </tr>
  );
}

function ProductRow({ product, canWrite, onSave }) {
  const [name, setName] = useState(product.name);
  const [description, setDescription] = useState(product.description || '');
  const [capabilities, setCapabilities] = useState(product.capabilities || []);

  useEffect(() => {
    setName(product.name);
    setDescription(product.description || '');
    setCapabilities(product.capabilities || []);
  }, [product.id, product.name, product.description, product.capabilities]);

  return (
    <tr>
      <td>{product.id}</td>
      <td>
        <input
          value={name}
          disabled={!canWrite}
          onChange={(e) => setName(e.target.value)}
        />
      </td>
      <td>
        <CapabilityEditor
          selected={capabilities}
          disabled={!canWrite}
          onChange={setCapabilities}
        />
      </td>
      <td>
        <textarea
          value={description}
          disabled={!canWrite}
          className="product-description-input"
          placeholder="Describe this product"
          onChange={(e) => setDescription(e.target.value)}
        />
      </td>
      <td>
        <button
          disabled={!canWrite || !name.trim() || capabilities.length === 0 || !capabilities.includes('READ_DIGITAL')}
          onClick={() => onSave(product.id, name.trim(), inferAccessType(capabilities), description.trim(), capabilities)}
        >
          Save
        </button>
      </td>
    </tr>
  );
}


const CAPABILITY_OPTIONS = ['READ_DIGITAL', 'RECEIVE_PRINT', 'NO_ADS'];

function inferAccessType(capabilities) {
  if (capabilities.includes('NO_ADS')) return 'premium';
  if (capabilities.includes('RECEIVE_PRINT')) return 'print';
  return 'digital';
}

function CapabilityEditor({ selected, disabled, onChange }) {
  function toggleCapability(capability) {
    if (selected.includes(capability)) {
      onChange(selected.filter((item) => item !== capability));
      return;
    }
    onChange([...selected, capability]);
  }

  return (
    <div className="capabilities-wrap">
      {CAPABILITY_OPTIONS.map((capability) => (
        <label key={capability} className="capability-item">
          <input
            type="checkbox"
            checked={selected.includes(capability)}
            disabled={disabled}
            onChange={() => toggleCapability(capability)}
          />
          {capability}
        </label>
      ))}
    </div>
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
