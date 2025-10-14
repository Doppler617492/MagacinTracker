import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Button,
  Card,
  Upload,
  message,
  Typography,
  Alert,
  Space,
  Progress,
  List,
  Tag,
  Divider
} from "antd";
import { InboxOutlined, UploadOutlined, FileExcelOutlined, FileTextOutlined } from "@ant-design/icons";
import type { UploadFile, UploadProps } from "antd";
import client from "../api";

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

interface ImportResponse {
  status: string;
  file: string;
}

const uploadFile = async (file: File): Promise<ImportResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await client.post('/import/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

const ImportPage = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploadHistory, setUploadHistory] = useState<Array<{
    id: string;
    filename: string;
    status: 'success' | 'error';
    message: string;
    timestamp: Date;
  }>>([]);

  const uploadMutation = useMutation({
    mutationFn: uploadFile,
    onSuccess: (data, variables) => {
      message.success(`Fajl ${variables.name} uspešno poslat za obradu`);
      setUploadHistory(prev => [{
        id: Date.now().toString(),
        filename: variables.name,
        status: 'success',
        message: 'Fajl je u redu za obradu',
        timestamp: new Date()
      }, ...prev]);
      setFileList([]);
    },
    onError: (error: any, variables) => {
      const errorMessage = error?.response?.data?.detail || 'Greška prilikom učitavanja fajla';
      message.error(`Greška: ${errorMessage}`);
      setUploadHistory(prev => [{
        id: Date.now().toString(),
        filename: variables.name,
        status: 'error',
        message: errorMessage,
        timestamp: new Date()
      }, ...prev]);
    }
  });

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    fileList,
    beforeUpload: (file) => {
      const isValidType = file.type === 'text/csv' || 
                         file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                         file.type === 'application/vnd.ms-excel.sheet.macroEnabled.12' ||
                         file.type === 'application/pdf';
      
      if (!isValidType) {
        message.error('Podržani su CSV, Excel i PDF fajlovi (.csv, .xlsx, .xlsm, .pdf)');
        return false;
      }

      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('Fajl mora biti manji od 10MB');
        return false;
      }

      return false; // Prevent auto upload
    },
    onChange: (info) => {
      setFileList(info.fileList);
    },
    onRemove: () => {
      setFileList([]);
    }
  };

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.warning('Molimo odaberite fajl za učitavanje');
      return;
    }

    const file = fileList[0].originFileObj;
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const getFileIcon = (filename: string) => {
    const extension = filename.toLowerCase().split('.').pop();
    switch (extension) {
      case 'csv':
        return <FileTextOutlined style={{ color: '#52c41a' }} />;
      case 'xlsx':
      case 'xlsm':
        return <FileExcelOutlined style={{ color: '#1890ff' }} />;
      default:
        return <FileTextOutlined />;
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Card>
        <Title level={2}>Uvoz trebovanja</Title>
        <Paragraph>
          Učitajte CSV ili Excel fajl sa trebovanjima. Fajl će biti poslat na obradu i trebovanja će biti kreirana automatski.
        </Paragraph>

        <Alert
          message="Format fajla"
          description={
            <div>
              <p>Fajl mora sadržavati sledeće kolone:</p>
              <ul>
                <li><strong>dokument_broj</strong> - Broj dokumenta (obavezno)</li>
                <li><strong>datum</strong> - Datum trebovanja (YYYY-MM-DD)</li>
                <li><strong>magacin</strong> - Naziv magacina</li>
                <li><strong>radnja</strong> - Naziv radnje</li>
                <li><strong>artikl_sifra</strong> - Šifra artikla</li>
                <li><strong>naziv</strong> - Naziv artikla</li>
                <li><strong>kolicina_trazena</strong> - Tražena količina</li>
                <li><strong>barkod</strong> - Barkod artikla (opciono)</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Kliknite ili prevucite fajl ovde</p>
          <p className="ant-upload-hint">
            Podržani su CSV, Excel i PDF fajlovi (.csv, .xlsx, .xlsm, .pdf). Maksimalna veličina: 10MB
          </p>
        </Dragger>

        {fileList.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <Text strong>Odabrani fajl:</Text>
            <div style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
              <Space>
                {getFileIcon(fileList[0].name)}
                <Text>{fileList[0].name}</Text>
                <Text type="secondary">
                  ({(fileList[0].size! / 1024 / 1024).toFixed(2)} MB)
                </Text>
              </Space>
            </div>
          </div>
        )}

        <Space>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleUpload}
            loading={uploadMutation.isPending}
            disabled={fileList.length === 0}
            size="large"
          >
            {uploadMutation.isPending ? 'Učitavam...' : 'Učitaj fajl'}
          </Button>
          <Button
            onClick={() => setFileList([])}
            disabled={fileList.length === 0}
          >
            Obriši
          </Button>
        </Space>

        {uploadMutation.isPending && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={50} status="active" showInfo={false} />
            <Text type="secondary">Obrađujem fajl...</Text>
          </div>
        )}
      </Card>

      {uploadHistory.length > 0 && (
        <Card title="Istorija učitavanja" style={{ marginTop: 24 }}>
          <List
            dataSource={uploadHistory}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  avatar={getFileIcon(item.filename)}
                  title={
                    <Space>
                      <Text strong>{item.filename}</Text>
                      <Tag color={item.status === 'success' ? 'green' : 'red'}>
                        {item.status === 'success' ? 'Uspešno' : 'Greška'}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text type="secondary">{item.message}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {item.timestamp.toLocaleString()}
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
};

export default ImportPage;
