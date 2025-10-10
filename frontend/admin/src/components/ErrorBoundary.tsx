import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('❌ React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          fontFamily: 'Arial, sans-serif',
          flexDirection: 'column',
          padding: '20px'
        }}>
          <h1 style={{ fontSize: '32px', marginBottom: '20px' }}>❌ Greška u Aplikaciji</h1>
          <div style={{
            background: 'rgba(0,0,0,0.3)',
            padding: '20px',
            borderRadius: '8px',
            maxWidth: '600px',
            wordBreak: 'break-word'
          }}>
            <h2>Error:</h2>
            <pre style={{ whiteSpace: 'pre-wrap' }}>
              {this.state.error?.toString()}
            </pre>
            <h3>Stack:</h3>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
              {this.state.error?.stack}
            </pre>
          </div>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '20px',
              padding: '12px 24px',
              background: 'white',
              color: '#667eea',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Osvežи Stranicu
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

