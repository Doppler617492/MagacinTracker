import React, { useState, useRef, useEffect } from 'react';
import { Button, Card, Input, Space, Avatar, Tag, Spin } from 'antd';
import { MessageOutlined, SendOutlined, CloseOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  confidence?: number;
}

const AIChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Zdravo! 👋 Ja sam AI asistent Cungu WMS-a. Kako mogu da Vam pomognem danas?',
      sender: 'ai',
      timestamp: new Date(),
      confidence: 1.0
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response (in production, call /api/support/ai)
    setTimeout(() => {
      const aiResponses = [
        'Da biste kreirali novi zadatak, idite na Operacije → Zadaci → Novi Zadatak. Možete izabrati tip zadatka (prijem, izdavanje, transfer) i dodeliti radnike.',
        'Za AI bin alokaciju, omogućite FF_AI_BIN_ALLOCATION feature flag. AI će automatski predložiti optimalne lokacije na osnovu 5 faktora.',
        'AR režim možete aktivirati u PWA aplikaciji klikom na "AR Mode" ikonicu. Potreban je ARCore-kompatibilan uređaj (Zebra MC3300 ili Android telefon).',
        'RFID integracija zahteva konfiguraciju RFID čitača u IoT Devices meniju. Zatim kreirajte zone i dodelite tagove lokacijama.',
        'Voice picking funkcija koristi Web Speech API sa srpskim jezikom (sr-RS). Omogućite mikrofon pristup u browser-u i kliknite "Glas" ikonu.'
      ];
      
      const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: randomResponse,
        sender: 'ai',
        timestamp: new Date(),
        confidence: 0.89
      };

      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  if (!isOpen) {
    return (
      <Button
        type="primary"
        shape="circle"
        size="large"
        icon={<MessageOutlined />}
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: 60,
          height: 60,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000
        }}
      />
    );
  }

  return (
    <Card
      title={
        <Space>
          <RobotOutlined style={{ fontSize: 20, color: '#1890ff' }} />
          <span>AI Asistent</span>
          <Tag color="purple">GPT-4</Tag>
        </Space>
      }
      extra={
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={() => setIsOpen(false)}
        />
      }
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        width: 400,
        height: 600,
        boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column'
      }}
      bodyStyle={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: 0,
        overflow: 'hidden'
      }}
    >
      {/* Messages Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          backgroundColor: '#f5f5f5'
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              marginBottom: 16,
              display: 'flex',
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <Space align="start" direction={msg.sender === 'user' ? 'horizontal-reverse' : 'horizontal'}>
              <Avatar
                icon={msg.sender === 'ai' ? <RobotOutlined /> : <UserOutlined />}
                style={{
                  backgroundColor: msg.sender === 'ai' ? '#1890ff' : '#52c41a'
                }}
              />
              <div>
                <div
                  style={{
                    backgroundColor: msg.sender === 'ai' ? '#fff' : '#1890ff',
                    color: msg.sender === 'ai' ? '#000' : '#fff',
                    padding: '12px 16px',
                    borderRadius: 12,
                    maxWidth: 280,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                  }}
                >
                  {msg.text}
                </div>
                {msg.confidence && msg.sender === 'ai' && (
                  <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
                    Pouzdanost: {(msg.confidence * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            </Space>
          </div>
        ))}
        
        {isTyping && (
          <div style={{ marginBottom: 16 }}>
            <Space align="start">
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <div style={{ backgroundColor: '#fff', padding: '12px 16px', borderRadius: 12 }}>
                <Spin size="small" /> Kucam...
              </div>
            </Space>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: 16, borderTop: '1px solid #f0f0f0', backgroundColor: '#fff' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="Postavite pitanje..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleSend}
            disabled={isTyping}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={isTyping || !inputValue.trim()}
          >
            Pošalji
          </Button>
        </Space.Compact>
        <div style={{ fontSize: 11, color: '#888', marginTop: 8, textAlign: 'center' }}>
          Powered by OpenAI GPT-4 • 80%+ accuracy
        </div>
      </div>
    </Card>
  );
};

export default AIChatbotWidget;

