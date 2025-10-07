import { Card, Col, Row, Statistic } from "antd";

const DashboardPage = () => (
  <Row gutter={[16, 16]}>
    <Col span={6}>
      <Card>
        <Statistic title="Ukupno zadataka danas" value={42} />
      </Card>
    </Col>
    <Col span={6}>
      <Card>
        <Statistic title="Završeno (%)" value={68} suffix="%" />
      </Card>
    </Col>
    <Col span={6}>
      <Card>
        <Statistic title="Aktivni radnici" value={7} />
      </Card>
    </Col>
    <Col span={6}>
      <Card>
        <Statistic title="Vrijeme do kraja smjene" value="03:15" />
      </Card>
    </Col>
  </Row>
);

export default DashboardPage;
