/**
 * Receiving List Page (Prijemi)
 * Manhattan Active WMS - Inbound document list
 * Language: Serbian (Srpski)
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, Space, Typography, Tag, Progress, Button, Select, Input, Empty } from 'antd';
import { 
  SearchOutlined,
  FilterOutlined,
  InboxOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined 
} from '@ant-design/icons';
import { ManhattanHeader } from '../components/ManhattanHeader';
import api from '../api';
import './ReceivingListPage.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface ReceivingListItem {
  id: string;
  broj_prijema: string;
  dobavljac_naziv: string;
  magacin_naziv: string;
  datum: string;
  status: string;
  status_serbian: string;
  completion_percentage: number;
  total_items: number;
  items_received: number;
}

const statusColors: Record<string, string> = {
  'novo': 'default',
  'u_toku': 'processing',
  'završeno': 'success',
  'završeno_djelimično': 'warning'
};

const statusIcons: Record<string, React.ReactNode> = {
  'novo': <InboxOutlined />,
  'u_toku': <ClockCircleOutlined />,
  'završeno': <CheckCircleOutlined />,
  'završeno_djelimično': <WarningOutlined />
};

export const ReceivingListPage: React.FC = () => {
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch receivings
  const { data: receivings = [], isLoading, refetch } = useQuery({
    queryKey: ['receivings', filterStatus],
    queryFn: async () => {
      const params: any = {};
      if (filterStatus !== 'all') {
        params.status = filterStatus;
      }
      const response = await api.get('/receiving', { params });
      return response.data;
    }
  });

  // Filter by search
  const filteredReceivings = receivings.filter((r: ReceivingListItem) =>
    searchQuery === '' ||
    r.broj_prijema.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.dobavljac_naziv.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCardClick = (id: string) => {
    navigate(`/receiving/${id}`);
  };

  return (
    <div className="receiving-list-page">
      <ManhattanHeader
        user={{ firstName: 'User', lastName: 'Name', role: 'magacioner' }}
        isOnline={navigator.onLine}
        onLogout={() => navigate('/login')}
      />

      <div className="receiving-list-page__container">
        {/* Header */}
        <div className="receiving-list-page__header">
          <Title level={2}>Prijemi</Title>
          
          {/* Filters */}
          <div className="receiving-list-page__filters">
            <Space wrap>
              <Select
                value={filterStatus}
                onChange={setFilterStatus}
                style={{ width: 180 }}
                size="large"
                suffixIcon={<FilterOutlined />}
              >
                <Option value="all">Svi statusi</Option>
                <Option value="novo">Novo</Option>
                <Option value="u_toku">U toku</Option>
                <Option value="završeno">Završeno</Option>
                <Option value="završeno_djelimično">Djelimično</Option>
              </Select>

              <Input
                placeholder="Pretraži broj ili dobavljač..."
                prefix={<SearchOutlined />}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                size="large"
                style={{ width: 280 }}
                allowClear
              />
            </Space>
          </div>
        </div>

        {/* List */}
        <div className="receiving-list-page__list">
          {isLoading ? (
            <Card loading />
          ) : filteredReceivings.length === 0 ? (
            <Empty
              description="Nema prijema"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            filteredReceivings.map((receiving: ReceivingListItem) => (
              <Card
                key={receiving.id}
                hoverable
                onClick={() => handleCardClick(receiving.id)}
                className="receiving-card"
              >
                <div className="receiving-card__content">
                  {/* Header */}
                  <div className="receiving-card__header">
                    <div>
                      <Text strong className="receiving-card__broj">
                        {receiving.broj_prijema}
                      </Text>
                      <Tag
                        color={statusColors[receiving.status]}
                        icon={statusIcons[receiving.status]}
                        className="receiving-card__status"
                      >
                        {receiving.status_serbian}
                      </Tag>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="receiving-card__info">
                    <div className="receiving-card__row">
                      <Text type="secondary">Dobavljač:</Text>
                      <Text strong>{receiving.dobavljac_naziv || 'N/A'}</Text>
                    </div>
                    <div className="receiving-card__row">
                      <Text type="secondary">Magacin:</Text>
                      <Text>{receiving.magacin_naziv}</Text>
                    </div>
                    <div className="receiving-card__row">
                      <Text type="secondary">Datum:</Text>
                      <Text>{new Date(receiving.datum).toLocaleDateString('sr-RS')}</Text>
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="receiving-card__progress">
                    <div className="receiving-card__row">
                      <Text type="secondary">Napredak:</Text>
                      <Text strong>
                        {receiving.items_received}/{receiving.total_items} stavki
                      </Text>
                    </div>
                    <Progress
                      percent={receiving.completion_percentage}
                      strokeColor={receiving.completion_percentage === 100 ? '#52c41a' : '#1890ff'}
                      size="small"
                    />
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ReceivingListPage;

