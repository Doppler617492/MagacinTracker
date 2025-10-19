/**
 * Manhattan-style Partial Completion Modal
 * Design: Active WMS exception handling pattern
 * Language: Serbian (Srpski)
 */

import React, { useState } from 'react';
import { Modal, Form, Select, Input, Button, Space, Typography, Alert } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import { sr } from '../i18n/sr-comprehensive';
import './PartialCompletionModal.css';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;

export type PartialReason = 'nema_na_stanju' | 'osteceno' | 'nije_pronađeno' | 'krivi_artikal' | 'drugo';

interface PartialCompletionModalProps {
  visible: boolean;
  onCancel: () => void;
  onConfirm: (razlog: PartialReason, razlog_tekst?: string) => void;
  količina_tražena: number;
  količina_pronađena: number;
  artikal_naziv: string;
}

export const PartialCompletionModal: React.FC<PartialCompletionModalProps> = ({
  visible,
  onCancel,
  onConfirm,
  količina_tražena,
  količina_pronađena,
  artikal_naziv,
}) => {
  const [form] = Form.useForm();
  const [selectedReason, setSelectedReason] = useState<PartialReason | undefined>();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      
      await onConfirm(values.razlog, values.razlog_tekst);
      
      form.resetFields();
      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  };

  const handleReasonChange = (value: PartialReason) => {
    setSelectedReason(value);
  };

  const razlogOptions = [
    { value: 'nema_na_stanju', label: sr.partial.nemaNaStanju },
    { value: 'osteceno', label: sr.partial.osteceno },
    { value: 'nije_pronađeno', label: sr.partial.nijePronađeno },
    { value: 'krivi_artikal', label: sr.partial.krivi_artikal },
    { value: 'drugo', label: sr.partial.drugo },
  ];

  const procenat = količina_tražena > 0 
    ? Math.round((količina_pronađena / količina_tražena) * 100) 
    : 0;

  return (
    <Modal
      title={
        <Space>
          <WarningOutlined style={{ color: '#FFC107' }} />
          <span>{sr.partial.djelimicnoZavrsen}</span>
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
      className="partial-completion-modal"
    >
      <Alert
        message={sr.partial.manjaKolicina}
        description={
          <div>
            <Text strong>{artikal_naziv}</Text>
            <div style={{ marginTop: 8 }}>
              <Text>
                {sr.task.trazeno}: <strong>{količina_tražena}</strong> |{' '}
                {sr.task.pronadjeno}: <strong>{količina_pronađena}</strong>
              </Text>
            </div>
            <div style={{ marginTop: 4 }}>
              <Text type="secondary">
                {sr.task.procenatIspunjenja}: <strong>{procenat}%</strong>
              </Text>
            </div>
          </div>
        }
        type="warning"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        requiredMark="optional"
      >
        <Form.Item
          name="razlog"
          label={sr.partial.razlog}
          rules={[
            { required: true, message: sr.messages.obaveznoPolje }
          ]}
        >
          <Select
            size="large"
            placeholder={sr.partial.odaberiRazlog}
            onChange={handleReasonChange}
            className="partial-completion-modal__select"
          >
            {razlogOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {selectedReason === 'drugo' && (
          <Form.Item
            name="razlog_tekst"
            label={sr.partial.drugoUnesite}
            rules={[
              { required: true, message: sr.partial.obaveznoPolje },
              { max: 500, message: 'Maksimalno 500 karaktera' }
            ]}
          >
            <TextArea
              rows={3}
              placeholder={sr.partial.unesite}
              maxLength={500}
              showCount
              size="large"
            />
          </Form.Item>
        )}

        <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button
              size="large"
              onClick={onCancel}
              disabled={loading}
            >
              {sr.actions.otkazi}
            </Button>
            <Button
              type="primary"
              size="large"
              onClick={handleSubmit}
              loading={loading}
            >
              {sr.actions.potvrdi}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default PartialCompletionModal;

