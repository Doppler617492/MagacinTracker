import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Component } from 'react';
class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, errorInfo) {
        console.error('❌ React Error Boundary caught an error:', error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (_jsxs("div", { style: {
                    minHeight: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    fontFamily: 'Arial, sans-serif',
                    flexDirection: 'column',
                    padding: '20px'
                }, children: [_jsx("h1", { style: { fontSize: '32px', marginBottom: '20px' }, children: "\u274C Gre\u0161ka u Aplikaciji" }), _jsxs("div", { style: {
                            background: 'rgba(0,0,0,0.3)',
                            padding: '20px',
                            borderRadius: '8px',
                            maxWidth: '600px',
                            wordBreak: 'break-word'
                        }, children: [_jsx("h2", { children: "Error:" }), _jsx("pre", { style: { whiteSpace: 'pre-wrap' }, children: this.state.error?.toString() }), _jsx("h3", { children: "Stack:" }), _jsx("pre", { style: { whiteSpace: 'pre-wrap', fontSize: '12px' }, children: this.state.error?.stack })] }), _jsx("button", { onClick: () => window.location.reload(), style: {
                            marginTop: '20px',
                            padding: '12px 24px',
                            background: 'white',
                            color: '#667eea',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '16px',
                            fontWeight: 'bold',
                            cursor: 'pointer'
                        }, children: "Osve\u017E\u0438 Stranicu" })] }));
        }
        return this.props.children;
    }
}
export default ErrorBoundary;
