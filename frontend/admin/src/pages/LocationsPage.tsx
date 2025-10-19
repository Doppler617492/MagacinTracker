/**
 * LocationsPage - Location hierarchy management
 * Manhattan Active WMS - Admin location management
 */
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Input, Select, InputNumber, Tree, Table, Tag, Space } from 'antd';
import type { DataNode } from 'antd/es/tree';
import './LocationsPage.css';

const { Option } = Select;

interface Location {
  id: string;
  naziv: string;
  code: string;
  tip: 'zone' | 'regal' | 'polica' | 'bin';
  parent_id?: string;
  magacin_id: string;
  zona?: string;
  x_coordinate?: number;
  y_coordinate?: number;
  capacity_max?: number;
  capacity_current: number;
  occupancy_percentage: number;
  status_color: string;
  is_active: boolean;
  children?: Location[];
}

interface Article {
  artikal_sifra: string;
  artikal_naziv: string;
  quantity: number;
  uom: string;
  is_primary_location: boolean;
}

export const LocationsPage: React.FC = () => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadLocationTree();
  }, []);

  const loadLocationTree = async () => {
    try {
      setLoading(true);
      const magacinId = localStorage.getItem('current_magacin_id') || '';
      const response = await fetch(`/api/locations/tree?magacin_id=${magacinId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setLocations(data);
      }
    } catch (error) {
      console.error('Failed to load locations:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadLocationArticles = async (locationId: string) => {
    try {
      const response = await fetch(`/api/locations/${locationId}/articles`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setArticles(data);
      }
    } catch (error) {
      console.error('Failed to load articles:', error);
    }
  };

  const buildTreeData = (locations: Location[]): DataNode[] => {
    return locations.map(loc => ({
      key: loc.id,
      title: (
        <span>
          <span style={{ marginRight: 8 }}>{loc.status_color}</span>
          <strong>{loc.code}</strong> - {loc.naziv}
          <Tag color={getTypeColor(loc.tip)} style={{ marginLeft: 8 }}>
            {getTypeLabel(loc.tip)}
          </Tag>
          {loc.tip === 'bin' && (
            <Tag color={getOccupancyColor(loc.occupancy_percentage)} style={{ marginLeft: 4 }}>
              {loc.occupancy_percentage.toFixed(0)}%
            </Tag>
          )}
        </span>
      ),
      children: loc.children ? buildTreeData(loc.children) : undefined
    }));
  };

  const getTypeLabel = (tip: string) => {
    const labels = {
      zone: 'ZONA',
      regal: 'REGAL',
      polica: 'POLICA',
      bin: 'BIN'
    };
    return labels[tip as keyof typeof labels] || tip;
  };

  const getTypeColor = (tip: string) => {
    const colors = {
      zone: 'blue',
      regal: 'green',
      polica: 'orange',
      bin: 'purple'
    };
    return colors[tip as keyof typeof colors] || 'default';
  };

  const getOccupancyColor = (percentage: number) => {
    if (percentage >= 90) return 'red';
    if (percentage >= 50) return 'orange';
    return 'green';
  };

  const handleTreeSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length > 0) {
      const locationId = selectedKeys[0] as string;
      findAndSelectLocation(locations, locationId);
      loadLocationArticles(locationId);
    }
  };

  const findAndSelectLocation = (locs: Location[], id: string): boolean => {
    for (const loc of locs) {
      if (loc.id === id) {
        setSelectedLocation(loc);
        return true;
      }
      if (loc.children && findAndSelectLocation(loc.children, id)) {
        return true;
      }
    }
    return false;
  };

  const handleCreateLocation = () => {
    form.resetFields();
    if (selectedLocation) {
      form.setFieldsValue({
        parent_id: selectedLocation.id,
        magacin_id: selectedLocation.magacin_id
      });
    }
    setModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const response = await fetch('/api/locations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(values)
      });
      
      if (response.ok) {
        setModalVisible(false);
        loadLocationTree();
      }
    } catch (error) {
      console.error('Failed to create location:', error);
    }
  };

  const articleColumns = [
    {
      title: 'Šifra',
      dataIndex: 'artikal_sifra',
      key: 'sifra',
      render: (text: string) => <code>{text}</code>
    },
    {
      title: 'Naziv',
      dataIndex: 'artikal_naziv',
      key: 'naziv'
    },
    {
      title: 'Količina',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (qty: number, record: Article) => `${qty} ${record.uom}`
    },
    {
      title: 'Status',
      dataIndex: 'is_primary_location',
      key: 'primary',
      render: (isPrimary: boolean) => (
        isPrimary ? <Tag color="blue">Primarna</Tag> : <Tag>Sekundarna</Tag>
      )
    }
  ];

  return (
    <div className="locations-page">
      <div className="page-header">
        <h1>Lokacije</h1>
        <Space>
          <Button onClick={loadLocationTree}>Osvježi</Button>
          <Button type="primary" onClick={handleCreateLocation}>
            + Nova lokacija
          </Button>
        </Space>
      </div>

      <div className="locations-content">
        <div className="tree-panel">
          <h3>Hijerarhija lokacija</h3>
          <Tree
            showLine
            defaultExpandAll
            treeData={buildTreeData(locations)}
            onSelect={handleTreeSelect}
            loading={loading}
          />
        </div>

        <div className="detail-panel">
          {selectedLocation ? (
            <>
              <div className="location-detail">
                <h3>
                  {selectedLocation.status_color} {selectedLocation.code}
                  <Tag color={getTypeColor(selectedLocation.tip)} style={{ marginLeft: 8 }}>
                    {getTypeLabel(selectedLocation.tip)}
                  </Tag>
                </h3>
                <div className="detail-grid">
                  <div className="detail-field">
                    <label>Naziv:</label>
                    <span>{selectedLocation.naziv}</span>
                  </div>
                  <div className="detail-field">
                    <label>Zona:</label>
                    <span>{selectedLocation.zona || '-'}</span>
                  </div>
                  {selectedLocation.capacity_max && (
                    <>
                      <div className="detail-field">
                        <label>Kapacitet:</label>
                        <span>
                          {selectedLocation.capacity_current} / {selectedLocation.capacity_max}
                        </span>
                      </div>
                      <div className="detail-field">
                        <label>Popunjenost:</label>
                        <Tag color={getOccupancyColor(selectedLocation.occupancy_percentage)}>
                          {selectedLocation.occupancy_percentage.toFixed(1)}%
                        </Tag>
                      </div>
                    </>
                  )}
                  {selectedLocation.x_coordinate && (
                    <div className="detail-field">
                      <label>Koordinate:</label>
                      <span>
                        X: {selectedLocation.x_coordinate}, Y: {selectedLocation.y_coordinate}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="articles-section">
                <h3>Artikli u lokaciji</h3>
                <Table
                  dataSource={articles}
                  columns={articleColumns}
                  rowKey={(record) => `${record.artikal_sifra}-${record.uom}`}
                  pagination={false}
                  size="small"
                />
              </div>
            </>
          ) : (
            <div className="no-selection">
              <p>Izaberite lokaciju iz stabla</p>
            </div>
          )}
        </div>
      </div>

      <Modal
        title="Nova lokacija"
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="naziv" label="Naziv" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="code" label="Kod" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="tip" label="Tip" rules={[{ required: true }]}>
            <Select>
              <Option value="zone">Zona</Option>
              <Option value="regal">Regal</Option>
              <Option value="polica">Polica</Option>
              <Option value="bin">Bin</Option>
            </Select>
          </Form.Item>
          <Form.Item name="capacity_max" label="Maksimalni kapacitet">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="x_coordinate" label="X koordinata">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="y_coordinate" label="Y koordinata">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="parent_id" label="Nadređena lokacija" hidden>
            <Input />
          </Form.Item>
          <Form.Item name="magacin_id" label="Magacin ID" hidden>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

