import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  Input,
  Button,
  List,
  Card,
  Typography,
  Space,
  Tag,
  Spin,
  message,
  Divider,
  Row,
  Col,
  Tooltip
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  HistoryOutlined,
  BulbOutlined,
  BarChartOutlined,
  LineOutlined,
  PieChartOutlined
} from '@ant-design/icons';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Line, Column } from '@ant-design/charts';
import { processAIQuery, getAISuggestions, getAIHistory, AIQueryRequest, AIQueryResponse } from '../api';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

interface AIAssistantModalProps {
  visible: boolean;
  onClose: () => void;
  filters?: {
    radnja?: string;
    period?: string;
    radnik?: string;
  };
}

interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  confidence?: number;
  chart_data?: any;
  data?: any;
}

const AIAssistantModal: React.FC<AIAssistantModalProps> = ({ visible, onClose, filters }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch suggestions and history
  const { data: suggestions } = useQuery({
    queryKey: ['ai-suggestions'],
    queryFn: getAISuggestions,
    enabled: visible,
  });

  const { data: history } = useQuery({
    queryKey: ['ai-history'],
    queryFn: () => getAIHistory(5),
    enabled: visible,
  });

  // AI Query mutation
  const aiQueryMutation = useMutation({
    mutationFn: (request: AIQueryRequest) => processAIQuery(request),
    onSuccess: (response: AIQueryResponse) => {
      const aiMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'ai',
        content: response.answer,
        timestamp: new Date(response.timestamp),
        confidence: response.confidence,
        chart_data: response.chart_data,
        data: response.data
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    },
    onError: (error: any) => {
      message.error('Greška pri obradi upita. Pokušajte ponovo.');
      setIsLoading(false);
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Prepare context from filters
    const context: AIQueryRequest['context'] = {
      days: filters?.period === '1d' ? 1 : 
            filters?.period === '7d' ? 7 : 
            filters?.period === '30d' ? 30 : 7,
      language: 'sr'
    };

    if (filters?.radnja) {
      context.radnja_id = filters.radnja;
    }

    if (filters?.radnik) {
      context.radnik_id = filters.radnik;
    }

    aiQueryMutation.mutate({
      query: inputValue,
      context
    });
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
  };

  const handleHistoryClick = (historyItem: any) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: historyItem.query,
      timestamp: new Date(historyItem.timestamp)
    };

    const aiMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'ai',
      content: historyItem.answer,
      timestamp: new Date(historyItem.timestamp),
      confidence: historyItem.confidence
    };

    setMessages([userMessage, aiMessage]);
  };

  const renderChart = (chartData: any) => {
    if (!chartData || !chartData.data || chartData.data.length === 0) {
      return <Text type="secondary">Nema podataka za prikaz grafikona</Text>;
    }

    const commonConfig = {
      data: chartData.data,
      animation: {
        appear: {
          animation: 'path-in',
          duration: 1000,
        },
      },
    };

    switch (chartData.type) {
      case 'line':
        return (
          <Line
            {...commonConfig}
            xField={chartData.x_field}
            yField={chartData.y_field}
            smooth
            color="#1890ff"
          />
        );
      case 'bar':
        return (
          <Column
            {...commonConfig}
            xField={chartData.x_field}
            yField={chartData.y_field}
            color="#52c41a"
          />
        );
      case 'pie':
        return (
          <Column
            {...commonConfig}
            angleField={chartData.angle_field}
            colorField={chartData.color_field}
            radius={0.8}
            label={{
              type: 'outer',
              content: '{name}: {percentage}',
            }}
          />
        );
      default:
        return <Text type="secondary">Nepoznat tip grafikona</Text>;
    }
  };

  const getChartIcon = (chartType: string) => {
    switch (chartType) {
      case 'line': return <LineOutlined />;
      case 'bar': return <BarChartOutlined />;
      case 'pie': return <PieChartOutlined />;
      default: return <BarChartOutlined />;
    }
  };

  return (
    <Modal
      title={
        <Space>
          <RobotOutlined style={{ color: '#1890ff' }} />
          <span>AI Analytics Asistent</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      style={{ top: 20 }}
      bodyStyle={{ height: '70vh', display: 'flex', flexDirection: 'column' }}
    >
      <Row gutter={16} style={{ height: '100%' }}>
        {/* Chat Area */}
        <Col span={16} style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Messages */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: '16px 0',
            border: '1px solid #f0f0f0',
            borderRadius: '6px',
            marginBottom: '16px'
          }}>
            {messages.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
                <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <Title level={4}>Dobrodošli u AI Analytics Asistent</Title>
                <Paragraph>
                  Postavite pitanje o vašim KPI podacima na prirodnom jeziku.
                  <br />
                  Primer: "Ko je bio najefikasniji radnik prošle sedmice?"
                </Paragraph>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    marginBottom: '16px',
                    padding: '0 16px',
                    display: 'flex',
                    justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div
                    style={{
                      maxWidth: '70%',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      backgroundColor: message.type === 'user' ? '#1890ff' : '#f5f5f5',
                      color: message.type === 'user' ? '#fff' : '#000'
                    }}
                  >
                    <div style={{ marginBottom: '8px' }}>
                      {message.content}
                    </div>
                    
                    {message.confidence && (
                      <div style={{ fontSize: '12px', opacity: 0.7 }}>
                        Pouzdanost: {Math.round(message.confidence * 100)}%
                      </div>
                    )}

                    {message.chart_data && (
                      <div style={{ marginTop: '16px' }}>
                        <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center' }}>
                          {getChartIcon(message.chart_data.type)}
                          <Text style={{ marginLeft: '8px', fontWeight: 500 }}>
                            Grafički prikaz
                          </Text>
                        </div>
                        <div style={{ height: '200px' }}>
                          {renderChart(message.chart_data)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div style={{ padding: '16px', textAlign: 'center' }}>
                <Spin />
                <Text style={{ marginLeft: '8px' }}>AI asistent razmišlja...</Text>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Postavite pitanje o vašim KPI podacima..."
              rows={2}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={isLoading}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={isLoading}
              disabled={!inputValue.trim()}
            >
              Pošalji
            </Button>
          </div>
        </Col>

        {/* Sidebar */}
        <Col span={8}>
          {/* Suggestions */}
          <Card 
            title={
              <Space>
                <BulbOutlined />
                <span>Predlozi</span>
              </Space>
            }
            size="small"
            style={{ marginBottom: '16px' }}
          >
            <List
              size="small"
              dataSource={suggestions?.suggestions || []}
              renderItem={(item: string) => (
                <List.Item style={{ padding: '4px 0' }}>
                  <Button
                    type="link"
                    size="small"
                    onClick={() => handleSuggestionClick(item)}
                    style={{ textAlign: 'left', padding: 0, height: 'auto' }}
                  >
                    {item}
                  </Button>
                </List.Item>
              )}
            />
          </Card>

          {/* History */}
          <Card 
            title={
              <Space>
                <HistoryOutlined />
                <span>Istorija</span>
              </Space>
            }
            size="small"
          >
            <List
              size="small"
              dataSource={history?.history || []}
              renderItem={(item: any) => (
                <List.Item style={{ padding: '4px 0' }}>
                  <div>
                    <Button
                      type="link"
                      size="small"
                      onClick={() => handleHistoryClick(item)}
                      style={{ textAlign: 'left', padding: 0, height: 'auto' }}
                    >
                      {item.query}
                    </Button>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                      {new Date(item.timestamp).toLocaleString('sr-RS')}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </Modal>
  );
};

export default AIAssistantModal;
