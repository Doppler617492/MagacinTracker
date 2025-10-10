import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Card, Col, Row, Statistic } from "antd";
const DashboardPage = () => (_jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Ukupno zadataka danas", value: 42 }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Zavr\u0161eno (%)", value: 68, suffix: "%" }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Aktivni radnici", value: 7 }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Vrijeme do kraja smjene", value: "03:15" }) }) })] }));
export default DashboardPage;
