/**
 * Shortage Reports Page - Admin view for shortage analytics and export
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Table,
  DatePicker,
  Select,
  Button,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  message,
} from 'antd';
import {
  DownloadOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';
import client from '../api';

const { RangePicker } = DatePicker;

interface ShortageReportItem {
  trebovanje_dokument_broj: string;
  trebovanje_datum: string;
  radnja_naziv: string;
  magacin_naziv: string;
  artikal_sifra: string;
  artikal_naziv: string;
  required_qty: number;
  picked_qty: number;
  missing_qty: number;
  discrepancy_status: string;
  discrepancy_reason?: string;
  magacioner_name: string;
  completed_at?: string;
}

const ShortageReportsPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  // Fetch shortage data
  const { data: shortages, isLoading, refetch } = useQuery({
    queryKey: ['shortages', dateRange, statusFilter],
    queryFn: async () => {
      const params: any = { format: 'json' };
      
      if (dateRange) {
        params.from_date = dateRange[0].format('YYYY-MM-DD');
        params.to_date = dateRange[1].format('YYYY-MM-DD');
      }
      
      if (statusFilter) {
        params.discrepancy_status = statusFilter;
      }

      const { data } = await client.get('/reports/shortages', { params });
      return data as ShortageReportItem[];
    },
  });

  // Calculate statistics
  const stats = React.useMemo(() => {
    if (!shortages) return { total: 0, totalMissing: 0, totalRequired: 0, shortPickRate: 0 };

    const total = shortages.length;
    const totalMissing = shortages.reduce((sum, item) => sum + item.missing_qty, 0);
    const totalRequired = shortages.reduce((sum, item) => sum + item.required_qty, 0);
    const shortPickRate = totalRequired > 0 ? ((totalMissing / totalRequired) * 100).toFixed(1) : '0';

    return { total, totalMissing, totalRequired, shortPickRate };
  }, [shortages]);

  // Export to CSV
  const handleExport = async () => {
    try {
      const params: any = { format: 'csv' };
      
      if (dateRange) {
        params.from_date = dateRange[0].format('YYYY-MM-DD');
        params.to_date = dateRange[1].format('YYYY-MM-DD');
      }
      
      if (statusFilter) {
        params.discrepancy_status = statusFilter;
      }

      const response = await client.get('/reports/shortages', {
        params,
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `shortage_report_${dayjs().format('YYYYMMDD_HHmmss')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      message.success('Izvještaj preuzet!');
    } catch (error) {
      message.error('Greška pri preuzimanju izvještaja');
      console.error(error);
    }
  };

  // Table columns
  const columns: ColumnsType<ShortageReportItem> = [
    {
      title: 'Dokument',
      dataIndex: 'trebovanje_dokument_broj',
      key: 'dokument',
      width: 150,
      fixed: 'left',
    },
    {
      title: 'Datum',
      dataIndex: 'trebovanje_datum',
      key: 'datum',
      width: 150,
      render: (text) => dayjs(text).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Radnja',
      dataIndex: 'radnja_naziv',
      key: 'radnja',
      width: 150,
    },
    {
      title: 'Skladište',
      dataIndex: 'magacin_naziv',
      key: 'magacin',
      width: 150,
    },
    {
      title: 'Šifra',
      dataIndex: 'artikal_sifra',
      key: 'sifra',
      width: 120,
    },
    {
      title: 'Artikal',
      dataIndex: 'artikal_naziv',
      key: 'artikal',
      width: 250,
    },
    {
      title: 'Traženo',
      dataIndex: 'required_qty',
      key: 'required',
      width: 100,
      align: 'right',
    },
    {
      title: 'Prikupljeno',
      dataIndex: 'picked_qty',
      key: 'picked',
      width: 110,
      align: 'right',
    },
    {
      title: 'Nedostaje',
      dataIndex: 'missing_qty',
      key: 'missing',
      width: 110,
      align: 'right',
      render: (value) => (
        <span style={{ color: value > 0 ? '#ff4d4f' : '#52c41a', fontWeight: 600 }}>
          {value}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'discrepancy_status',
      key: 'status',
      width: 150,
      render: (status) => {
        const statusConfig: Record<string, { text: string; color: string; icon: React.ReactNode }> = {
          short_pick: { text: 'Djelimično', color: 'orange', icon: <WarningOutlined /> },
          not_found: { text: 'Nije pronađeno', color: 'red', icon: <CloseCircleOutlined /> },
          damaged: { text: 'Oštećeno', color: 'volcano', icon: <ExclamationCircleOutlined /> },
        };

        const config = statusConfig[status] || { text: status, color: 'default', icon: null };

        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: 'Razlog',
      dataIndex: 'discrepancy_reason',
      key: 'reason',
      width: 200,
      render: (text) => text || '-',
    },
    {
      title: 'Radnik',
      dataIndex: 'magacioner_name',
      key: 'worker',
      width: 150,
    },
    {
      title: 'Završeno',
      dataIndex: 'completed_at',
      key: 'completed',
      width: 150,
      render: (text) => text ? dayjs(text).format('DD.MM.YYYY HH:mm') : '-',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1>Izvještaji o manjkovima</h1>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ukupno stavki sa manjkom"
              value={stats.total}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ukupno nedostaje"
              value={stats.totalMissing}
              suffix="kom"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ukupno traženo"
              value={stats.totalRequired}
              suffix="kom"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Stopa manjka"
              value={stats.shortPickRate}
              suffix="%"
              precision={1}
              valueStyle={{ color: Number(stats.shortPickRate) > 5 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle" wrap>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs] | null)}
            format="DD.MM.YYYY"
            placeholder={['Datum od', 'Datum do']}
          />

          <Select
            placeholder="Status manjka"
            style={{ width: 200 }}
            value={statusFilter}
            onChange={setStatusFilter}
            allowClear
            options={[
              { value: 'short_pick', label: 'Djelimično prikupljeno' },
              { value: 'not_found', label: 'Nije pronađeno' },
              { value: 'damaged', label: 'Oštećeno' },
            ]}
          />

          <Button onClick={() => refetch()}>
            Pretraži
          </Button>

          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={!shortages || shortages.length === 0}
          >
            Preuzmi CSV
          </Button>
        </Space>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={shortages}
          loading={isLoading}
          rowKey={(record) => `${record.trebovanje_dokument_broj}-${record.artikal_sifra}`}
          scroll={{ x: 2000 }}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showTotal: (total) => `Ukupno ${total} stavki`,
          }}
        />
      </Card>
    </div>
  );
};

export default ShortageReportsPage;
