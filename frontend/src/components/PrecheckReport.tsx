import { List, Typography, Tag, Space } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import type { PrecheckItem } from '../types';

const { Text } = Typography;

interface PrecheckReportProps {
  items: PrecheckItem[];
}

function StatusIcon({ status }: { status: PrecheckItem['status'] }) {
  switch (status) {
    case 'passed':
      return <CheckCircleOutlined style={{ color: '#52C41A', fontSize: 18 }} />;
    case 'failed':
      return <CloseCircleOutlined style={{ color: '#FF4D4F', fontSize: 18 }} />;
    case 'warning':
      return <WarningOutlined style={{ color: '#FAAD14', fontSize: 18 }} />;
    default:
      return null;
  }
}

export default function PrecheckReport({ items }: PrecheckReportProps) {
  return (
    <List
      dataSource={items}
      renderItem={(item) => (
        <List.Item style={{ padding: '8px 0' }}>
          <div style={{ width: '100%' }}>
            <Space align="start" size={12} style={{ width: '100%' }}>
              <StatusIcon status={item.status} />
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Text strong>{item.name}</Text>
                  <Space>
                    <Text type="secondary">{item.actual_value}</Text>
                    {item.expected_value && (
                      <Tag color={item.status === 'passed' ? 'default' : 'error'}>
                        {item.expected_value}
                      </Tag>
                    )}
                  </Space>
                </div>
                {item.status === 'failed' && item.suggestion && (
                  <div style={{ marginTop: 4 }}>
                    <Text type="warning" style={{ fontSize: 12 }}>
                      修复建议：{item.suggestion}
                    </Text>
                  </div>
                )}
              </div>
            </Space>
          </div>
        </List.Item>
      )}
    />
  );
}
