/**
 * Receiving Detail Page - Item-by-item receiving
 * Manhattan Active WMS - Inbound workflow
 * Language: Serbian (Srpski)
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  Card, 
  Button, 
  Space, 
  Typography, 
  Tag, 
  Progress, 
  Modal, 
  Select,
  Input,
  message,
  Badge,
  Image
} from 'antd';
import { 
  ArrowLeftOutlined,
  CameraOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  FilterOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { QuantityStepper } from '../components/QuantityStepper';
import { CameraCapture } from '../components/CameraCapture';
import { ManhattanHeader } from '../components/ManhattanHeader';
import api from '../api';
import './ReceivingDetailPage.css';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

type FilterType = 'sve' | 'ostalo' | 'djelimično';
type ReceivingReason = 'manjak' | 'višak' | 'oštećeno' | 'nije_isporučeno' | 'drugo';

interface ReceivingItem {
  id: string;
  sifra: string;
  naziv: string;
  jedinica_mjere: string;
  kolicina_trazena: number;
  kolicina_primljena: number;
  razlog?: ReceivingReason;
  napomena?: string;
  attachments: string[];
  status: string;
  completion_percentage: number;
  is_partial: boolean;
}

const reasonLabels: Record<ReceivingReason, string> = {
  'manjak': 'Manjak',
  'višak': 'Višak',
  'oštećeno': 'Oštećeno',
  'nije_isporučeno': 'Nije isporučeno',
  'drugo': 'Drugo'
};

export const ReceivingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [activeFilter, setActiveFilter] = useState<FilterType>('sve');
  const [selectedItem, setSelectedItem] = useState<ReceivingItem | null>(null);
  const [quantity, setQuantity] = useState(0);
  const [razlog, setRazlog] = useState<ReceivingReason | undefined>();
  const [napomena, setNapomena] = useState('');
  const [photos, setPhotos] = useState<string[]>([]);
  const [cameraVisible, setCameraVisible] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  // Fetch receiving detail
  const { data, refetch } = useQuery({
    queryKey: ['receiving', id],
    queryFn: async () => {
      const response = await api.get(`/receiving/${id}`);
      return response.data;
    }
  });

  // Receive item mutation
  const receiveItemMutation = useMutation({
    mutationFn: async (itemId: string) => {
      const response = await api.post(`/receiving/items/${itemId}/receive`, {
        quantity,
        razlog: quantity < selectedItem!.kolicina_trazena ? razlog : undefined,
        napomena: razlog === 'drugo' ? napomena : undefined,
        photo_ids: photos,
        operation_id: `receive-${itemId}-${Date.now()}`
      });
      return response.data;
    },
    onSuccess: () => {
      message.success('Stavka ažurirana');
      setSelectedItem(null);
      setQuantity(0);
      setRazlog(undefined);
      setNapomena('');
      setPhotos([]);
      refetch();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Greška pri ažuriranju');
    }
  });

  // Complete receiving mutation
  const completeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/receiving/${id}/complete`, {
        confirm_partial: true,
        operation_id: `complete-${id}-${Date.now()}`
      });
      return response.data;
    },
    onSuccess: (data) => {
      if (data.status === 'završeno_djelimično') {
        message.warning(`Prijem završen djelimično - ${data.completion_percentage}% primljeno`);
      } else {
        message.success('Prijem uspješno završen');
      }
      navigate('/receiving');
    }
  });

  // Filter items
  const filteredItems = data?.items?.filter((item: ReceivingItem) => {
    if (activeFilter === 'ostalo') return item.status !== 'gotovo';
    if (activeFilter === 'djelimično') return item.is_partial;
    return true;
  }) || [];

  const handleItemClick = (item: ReceivingItem) => {
    setSelectedItem(item);
    setQuantity(item.kolicina_primljena || 0);
    setRazlog(item.razlog);
    setNapomena(item.napomena || '');
    setPhotos(item.attachments || []);
  };

  const handlePhotoCapture = (base64: string, filename: string) => {
    setPhotos([...photos, base64]);
    setCameraVisible(false);
    message.success('Fotografija dodana');
  };

  const handlePhotoDelete = (index: number) => {
    setPhotos(photos.filter((_, i) => i !== index));
    message.info('Fotografija obrisana');
  };

  const handleSaveItem = () => {
    if (!selectedItem) return;
    
    // Validate
    if (quantity < selectedItem.kolicina_trazena && !razlog) {
      message.error('Odaberite razlog za djelimičnu količinu');
      return;
    }
    
    if (razlog === 'drugo' && !napomena.trim()) {
      message.error('Unesite napomenu za razlog "Drugo"');
      return;
    }
    
    receiveItemMutation.mutate(selectedItem.id);
  };

  if (!data) {
    return <Card loading />;
  }

  const { header } = data;
  const pendingCount = filteredItems.filter((i: ReceivingItem) => i.status !== 'gotovo').length;

  return (
    <div className="receiving-detail-page">
      <ManhattanHeader
        user={{ firstName: 'User', lastName: 'Name', role: 'magacioner' }}
        isOnline={!isOffline}
        onLogout={() => navigate('/login')}
      />

      <div className="receiving-detail-page__container">
        {/* Header */}
        <div className="receiving-detail-page__header">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/receiving')}
            size="large"
          >
            Nazad
          </Button>
          
          <div className="receiving-detail-page__title">
            <Title level={3}>{header.broj_prijema}</Title>
            <Space>
              <Text type="secondary">{header.dobavljac_naziv}</Text>
              <Text type="secondary">•</Text>
              <Text type="secondary">{new Date(header.datum).toLocaleDateString('sr-RS')}</Text>
            </Space>
          </div>

          <Tag color={header.status === 'završeno' ? 'success' : 'processing'}>
            {header.status_serbian}
          </Tag>
        </div>

        {/* Progress Summary */}
        <Card className="receiving-detail-page__progress">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text strong>Napredak:</Text>
              <Text>{header.items_received}/{header.total_items} stavki</Text>
            </div>
            <Progress percent={header.completion_percentage} status="active" />
          </Space>
        </Card>

        {/* Quick Filters */}
        <div className="receiving-detail-page__filters">
          <Space wrap>
            <Button
              type={activeFilter === 'sve' ? 'primary' : 'default'}
              onClick={() => setActiveFilter('sve')}
              size="large"
            >
              Sve ({data.items.length})
            </Button>
            <Button
              type={activeFilter === 'ostalo' ? 'primary' : 'default'}
              onClick={() => setActiveFilter('ostalo')}
              size="large"
            >
              Ostalo ({pendingCount})
            </Button>
            <Button
              type={activeFilter === 'djelimično' ? 'primary' : 'default'}
              onClick={() => setActiveFilter('djelimično')}
              size="large"
            >
              Djelimično ({data.items.filter((i: ReceivingItem) => i.is_partial).length})
            </Button>
          </Space>

          {/* Offline Badge */}
          {isOffline && (
            <Badge status="error" text="Offline - promjene će biti sinhronizovane" />
          )}
        </div>

        {/* Items List */}
        <div className="receiving-detail-page__items">
          {filteredItems.map((item: ReceivingItem) => (
            <Card
              key={item.id}
              hoverable
              onClick={() => handleItemClick(item)}
              className={`receiving-item-card ${item.status === 'gotovo' ? 'receiving-item-card--completed' : ''}`}
            >
              <div className="receiving-item-card__header">
                <div>
                  <Text strong>{item.sifra}</Text>
                  <Text className="receiving-item-card__naziv">{item.naziv}</Text>
                </div>
                {item.status === 'gotovo' && (
                  <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                )}
              </div>

              <div className="receiving-item-card__quantities">
                <div>
                  <Text type="secondary">Traženo:</Text>
                  <Text strong> {item.kolicina_trazena} {item.jedinica_mjere}</Text>
                </div>
                <div>
                  <Text type="secondary">Primljeno:</Text>
                  <Text strong style={{ color: item.is_partial ? '#faad14' : '#52c41a' }}>
                    {item.kolicina_primljena} {item.jedinica_mjere}
                  </Text>
                </div>
              </div>

              {item.razlog && (
                <Tag color="warning" icon={<WarningOutlined />}>
                  {reasonLabels[item.razlog]}
                </Tag>
              )}

              {item.attachments.length > 0 && (
                <Tag icon={<CameraOutlined />}>
                  {item.attachments.length} fotografija
                </Tag>
              )}

              <Progress
                percent={item.completion_percentage}
                size="small"
                strokeColor={item.completion_percentage === 100 ? '#52c41a' : '#faad14'}
                showInfo={false}
              />
            </Card>
          ))}
        </div>

        {/* Complete Button */}
        {header.status !== 'završeno' && header.status !== 'završeno_djelimično' && (
          <div className="receiving-detail-page__actions">
            <Button
              type="primary"
              size="large"
              block
              onClick={() => completeMutation.mutate()}
              loading={completeMutation.isPending}
              className="receiving-detail-page__complete-btn"
            >
              Završi prijem
            </Button>
          </div>
        )}
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <Modal
          title={selectedItem.naziv}
          open={!!selectedItem}
          onCancel={() => setSelectedItem(null)}
          footer={null}
          width={600}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Text type="secondary">Šifra: {selectedItem.sifra}</Text>
            </div>

            <QuantityStepper
              min={0}
              max={selectedItem.kolicina_trazena}
              value={quantity}
              onChange={setQuantity}
              label="Primljena količina"
              unit={selectedItem.jedinica_mjere}
            />

            {quantity < selectedItem.kolicina_trazena && (
              <>
                <div>
                  <Text strong>Razlog:</Text>
                  <Select
                    value={razlog}
                    onChange={setRazlog}
                    placeholder="Odaberite razlog"
                    style={{ width: '100%', marginTop: 8 }}
                    size="large"
                  >
                    <Option value="manjak">Manjak</Option>
                    <Option value="višak">Višak</Option>
                    <Option value="oštećeno">Oštećeno</Option>
                    <Option value="nije_isporučeno">Nije isporučeno</Option>
                    <Option value="drugo">Drugo</Option>
                  </Select>
                </div>

                {razlog === 'drugo' && (
                  <div>
                    <Text strong>Napomena:</Text>
                    <TextArea
                      value={napomena}
                      onChange={(e) => setNapomena(e.target.value)}
                      placeholder="Unesite napomenu..."
                      rows={3}
                      maxLength={500}
                      showCount
                      style={{ marginTop: 8 }}
                    />
                  </div>
                )}
              </>
            )}

            {/* Photo Attachments */}
            <div>
              <Text strong>Fotografije:</Text>
              <div style={{ marginTop: 12 }}>
                <Space wrap>
                  {photos.map((photo, index) => (
                    <div key={index} className="photo-preview">
                      <Image
                        src={photo}
                        width={80}
                        height={80}
                        style={{ objectFit: 'cover', borderRadius: 8 }}
                      />
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => handlePhotoDelete(index)}
                        className="photo-preview__delete"
                      >
                        Obriši
                      </Button>
                    </div>
                  ))}
                  
                  <Button
                    icon={<CameraOutlined />}
                    onClick={() => setCameraVisible(true)}
                    size="large"
                    style={{ width: 80, height: 80 }}
                  >
                    Dodaj
                  </Button>
                </Space>
              </div>
            </div>

            <Button
              type="primary"
              size="large"
              block
              onClick={handleSaveItem}
              loading={receiveItemMutation.isPending}
              disabled={quantity < selectedItem.kolicina_trazena && !razlog}
            >
              Sačuvaj stavku
            </Button>
          </Space>
        </Modal>
      )}

      {/* Camera Component */}
      <CameraCapture
        visible={cameraVisible}
        onCapture={handlePhotoCapture}
        onCancel={() => setCameraVisible(false)}
      />
    </div>
  );
};

export default ReceivingDetailPage;

