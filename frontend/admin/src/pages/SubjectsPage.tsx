import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  Select, 
  Space, 
  Tag, 
  message,
  Tooltip,
  Badge
} from 'antd';
import { 
  ReloadOutlined, 
  SyncOutlined, 
  SearchOutlined,
  ShopOutlined,
  UserOutlined,
  HomeOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;

interface Subject {
  id: string;
  code: string;
  name: string;
  type: 'supplier' | 'customer' | 'warehouse';
  pib?: string;
  address?: string;
  city?: string;
  phone?: string;
  email?: string;
  aktivan: boolean;
  last_synced_at?: string;
  source: string;
}

const SubjectsPage: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const queryClient = useQueryClient();

  // Fetch subjects
  const { data: subjectsData, isLoading, refetch } = useQuery({
    queryKey: ['subjects', typeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (typeFilter) params.append('type', typeFilter);
      
      const response = await fetch(`/api/pantheon/subjects?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch subjects');
      return response.json();
    },
    staleTime: 5 * 60 * 1000,
  });

  // Sync mutation
  const syncMutation = useMutation({
    mutationFn: async (fullSync: boolean) => {
      const response = await fetch(`/api/pantheon/sync/subjects?full_sync=${fullSync}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Sync failed');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      message.success(`✅ Subjects synced: ${data.created} created, ${data.updated} updated`);
      queryClient.invalidateQueries(['subjects']);
    },
    onError: (error: Error) => {
      message.error(`❌ Sync failed: ${error.message}`);
    }
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'supplier': return <ShopOutlined />;
      case 'customer': return <UserOutlined />;
      case 'warehouse': return <HomeOutlined />;
      default: return null;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'supplier': return 'blue';
      case 'customer': return 'green';
      case 'warehouse': return 'purple';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Šifra',
      dataIndex: 'code',
      key: 'code',
      width: 120,
      render: (code: string) => <strong>{code}</strong>
    },
    {
      title: 'Naziv',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Subject) => (
        <Space>
          {name}
          {record.source === 'PANTHEON' && (
            <Tooltip title="Synced from Pantheon ERP">
              <Badge count="ERP" style={{ backgroundColor: '#52c41a' }} />
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: 'Tip',
      dataIndex: 'type',
      key: 'type',
      width: 130,
      render: (type: string) => (
        <Tag icon={getTypeIcon(type)} color={getTypeColor(type)}>
          {type === 'supplier' ? 'Dobavljač' : type === 'customer' ? 'Kupac' : 'Magacin'}
        </Tag>
      )
    },
    {
      title: 'PIB',
      dataIndex: 'pib',
      key: 'pib',
      width: 120,
    },
    {
      title: 'Grad',
      dataIndex: 'city',
      key: 'city',
      width: 120,
    },
    {
      title: 'Kontakt',
      key: 'contact',
      width: 200,
      render: (_: any, record: Subject) => (
        <Space direction="vertical" size="small" style={{ fontSize: '12px' }}>
          {record.phone && <span>📞 {record.phone}</span>}
          {record.email && <span>📧 {record.email}</span>}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'aktivan',
      key: 'aktivan',
      width: 90,
      render: (aktivan: boolean) => (
        <Tag color={aktivan ? 'success' : 'default'}>
          {aktivan ? 'Aktivan' : 'Neaktivan'}
        </Tag>
      )
    },
    {
      title: 'Zadnja sinhronizacija',
      dataIndex: 'last_synced_at',
      key: 'last_synced_at',
      width: 160,
      render: (date: string) => date ? dayjs(date).format('DD.MM.YYYY HH:mm') : '-'
    }
  ];

  const filteredData = subjectsData?.items?.filter((subject: Subject) =>
    subject.name.toLowerCase().includes(searchText.toLowerCase()) ||
    subject.code.toLowerCase().includes(searchText.toLowerCase())
  ) || [];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>
          Subjekti / Partneri
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Partneri sinhronizirani iz Pantheon ERP-a (dobavljači, kupci, magacini)
        </p>
      </div>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: '16px' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Search
              placeholder="Pretraži po šifri ili nazivu..."
              allowClear
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
              onChange={(e) => setSearchText(e.target.value)}
            />
            
            <Select
              placeholder="Tip subjekta"
              style={{ width: 150 }}
              allowClear
              value={typeFilter || undefined}
              onChange={setTypeFilter}
            >
              <Option value="">Svi tipovi</Option>
              <Option value="supplier">
                <ShopOutlined /> Dobavljači
              </Option>
              <Option value="customer">
                <UserOutlined /> Kupci
              </Option>
              <Option value="warehouse">
                <HomeOutlined /> Magacini
              </Option>
            </Select>
          </Space>

          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetch()}
            >
              Osvježi
            </Button>
            
            <Button
              type="primary"
              icon={<SyncOutlined spin={syncMutation.isLoading} />}
              onClick={() => syncMutation.mutate(false)}
              loading={syncMutation.isLoading}
            >
              Sinhronizuj iz ERP-a
            </Button>
          </Space>
        </Space>
      </Card>

      {/* Statistics */}
      <Card style={{ marginBottom: '16px' }}>
        <Space size="large">
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
              {filteredData.length}
            </div>
            <div style={{ color: '#666' }}>Ukupno subjekata</div>
          </div>
          
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
              {filteredData.filter((s: Subject) => s.type === 'supplier').length}
            </div>
            <div style={{ color: '#666' }}>Dobavljači</div>
          </div>
          
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
              {filteredData.filter((s: Subject) => s.type === 'warehouse').length}
            </div>
            <div style={{ color: '#666' }}>Magacini</div>
          </div>
          
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
              {filteredData.filter((s: Subject) => s.type === 'customer').length}
            </div>
            <div style={{ color: '#666' }}>Kupci</div>
          </div>
        </Space>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showTotal: (total) => `Ukupno: ${total} subjekata`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default SubjectsPage;

