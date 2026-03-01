import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || 'Unknown UI error' };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main style={{ padding: 16 }}>
          <h1>Frontend failed to render</h1>
          <p>{this.state.message}</p>
          <p>Open browser devtools console for full stack trace.</p>
        </main>
      );
    }
    return this.props.children;
  }
}

const rootEl = document.getElementById('root');
if (!rootEl) {
  throw new Error('Missing #root mount element');
}

createRoot(rootEl).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </React.StrictMode>,
);
