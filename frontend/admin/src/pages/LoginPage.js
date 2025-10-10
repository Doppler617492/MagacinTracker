import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../api';
const { Title } = Typography;
const LoginPage = ({ onLoginSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const onFinish = async (values) => {
        try {
            setLoading(true);
            setError(null);
            await login(values.email, values.password);
            // Call success callback if provided
            if (onLoginSuccess) {
                onLoginSuccess();
            }
            else {
                window.location.reload();
            }
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Login failed');
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx("div", { style: {
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }, children: _jsxs(Card, { style: { width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }, children: [_jsxs("div", { style: { textAlign: 'center', marginBottom: 24 }, children: [_jsx(Title, { level: 2, style: { color: '#1890ff', marginBottom: 8 }, children: "Magacin Admin" }), _jsx(Typography.Text, { type: "secondary", children: "Prijavite se u admin panel" })] }), error && (_jsx(Alert, { message: error, type: "error", showIcon: true, style: { marginBottom: 16 } })), _jsxs(Form, { name: "login", onFinish: onFinish, autoComplete: "off", size: "large", children: [_jsx(Form.Item, { name: "email", rules: [
                                { required: true, message: 'Molimo unesite email' },
                                { type: 'email', message: 'Molimo unesite validan email' }
                            ], children: _jsx(Input, { prefix: _jsx(UserOutlined, {}), placeholder: "Email" }) }), _jsx(Form.Item, { name: "password", rules: [
                                { required: true, message: 'Molimo unesite lozinku' }
                            ], children: _jsx(Input.Password, { prefix: _jsx(LockOutlined, {}), placeholder: "Lozinka" }) }), _jsx(Form.Item, { children: _jsx(Button, { type: "primary", htmlType: "submit", loading: loading, block: true, size: "large", children: "Prijavi se" }) })] }), _jsx("div", { style: { textAlign: 'center', marginTop: 16 }, children: _jsxs(Space, { direction: "vertical", size: "small", children: [_jsx(Typography.Text, { type: "secondary", style: { fontSize: 12 }, children: "Testni korisnici:" }), _jsx(Typography.Text, { code: true, style: { fontSize: 11 }, children: "it@cungu.com / Dekodera1989" }), _jsx(Typography.Text, { code: true, style: { fontSize: 11 }, children: "admin@magacin.com / Admin123!" }), _jsx(Typography.Text, { code: true, style: { fontSize: 11 }, children: "marko.sef@magacin.com / Magacin123!" })] }) })] }) }));
};
export default LoginPage;
