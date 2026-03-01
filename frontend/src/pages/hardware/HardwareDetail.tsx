import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Table,
  Typography,
  Breadcrumb,
  Tag,
  Spin,
  Alert,
  Button,
  Space,
} from 'antd';
import {
  HomeOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { getHardwareCompatibility } from '../../api/client';
import type { HardwareVendorInfo, HardwareChip } from '../../types';

const { Title, Text } = Typography;

export default function HardwareDetail() {
  const { model } = useParams<{ model: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [chip, setChip] = useState<HardwareChip | null>(null);
  const [vendor, setVendor] = useState<HardwareVendorInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!model) return;

    const decoded = decodeURIComponent(model);
    const [vendorSlug, chipModel] = decoded.includes(':')
      ? decoded.split(':', 2)
      : ['', decoded];

    getHardwareCompatibility()
      .then((res) => {
        let foundVendor: HardwareVendorInfo | undefined;
        let foundChip: HardwareChip | undefined;

        if (vendorSlug) {
          foundVendor = res.vendors.find((v) => v.slug === vendorSlug);
          if (foundVendor) {
            foundChip = foundVendor.chips.find((c) => c.model === chipModel);
          }
        }

        if (!foundChip) {
          // Search across all vendors
          for (const v of res.vendors) {
            const c = v.chips.find(
              (ch) =>
                ch.model === chipModel || ch.model === decoded
            );
            if (c) {
              foundVendor = v;
              foundChip = c;
              break;
            }
          }
        }

        if (foundChip && foundVendor) {
          setChip(foundChip);
          setVendor(foundVendor);
        } else {
          setError(`未找到硬件型号: ${decoded}`);
        }
      })
      .catch(() => {
        setError('无法加载硬件知识库');
      })
      .finally(() => setLoading(false));
  }, [model]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !chip || !vendor) {
    return (
      <Alert
        type="error"
        message="加载失败"
        description={error}
        showIcon
        action={
          <Button onClick={() => navigate('/hardware')}>返回硬件列表</Button>
        }
      />
    );
  }

  // Find compatible engines for this chip
  const compatibleEngines = vendor.engines
    .flatMap((eng) =>
      eng.versions
        .filter((v) => v.compatible_chips.includes(chip.model))
        .map((v) => ({
          key: `${eng.name}-${v.version}`,
          engine_name: eng.name,
          version: v.version,
          min_driver: v.min_driver,
          min_sdk: v.min_sdk,
          base_image: v.base_image,
        }))
    );

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/hardware')}
        />
        <Breadcrumb
          items={[
            { href: '/', title: <HomeOutlined /> },
            { href: '/hardware', title: '硬件知识库' },
            { title: `${vendor.name} ${chip.model}` },
          ]}
        />
      </Space>

      <Title level={4} style={{ marginBottom: 24 }}>
        <span
          style={{
            display: 'inline-block',
            width: 4,
            height: 20,
            background: '#1677FF',
            borderRadius: 2,
            marginRight: 10,
            verticalAlign: 'middle',
          }}
        />
        {vendor.name} {chip.model}
      </Title>

      {/* Chip Specs */}
      <Card title="芯片规格" style={{ marginBottom: 16 }}>
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="厂商">{vendor.name}</Descriptions.Item>
          <Descriptions.Item label="芯片型号">{chip.model}</Descriptions.Item>
          <Descriptions.Item label="显存容量">
            {chip.memory_gb} GB
          </Descriptions.Item>
          <Descriptions.Item label="显存类型">
            {chip.memory_type}
          </Descriptions.Item>
          <Descriptions.Item label="算力 (FP16)">
            {chip.compute_tflops_fp16} TFLOPS
          </Descriptions.Item>
          <Descriptions.Item label="互联方式">
            {chip.interconnect}
          </Descriptions.Item>
          <Descriptions.Item label="BF16 支持">
            {chip.supports_bf16 ? (
              <Tag color="success">支持</Tag>
            ) : (
              <Tag color="default">不支持</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="FP8 支持">
            {chip.supports_fp8 ? (
              <Tag color="success">支持</Tag>
            ) : (
              <Tag color="default">不支持</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="设备检测命令" span={2}>
            <code>{chip.detection_command}</code>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Compatible Engines */}
      <Card title="兼容推理引擎" style={{ marginBottom: 16 }}>
        <Table
          dataSource={compatibleEngines}
          columns={[
            {
              title: '推理引擎',
              dataIndex: 'engine_name',
              key: 'engine_name',
              render: (val: string) => <Text strong>{val}</Text>,
            },
            {
              title: '版本',
              dataIndex: 'version',
              key: 'version',
            },
            {
              title: '最低驱动',
              dataIndex: 'min_driver',
              key: 'min_driver',
            },
            {
              title: '最低 SDK',
              dataIndex: 'min_sdk',
              key: 'min_sdk',
            },
            {
              title: '基础镜像',
              dataIndex: 'base_image',
              key: 'base_image',
              ellipsis: true,
              render: (val: string) => (
                <code style={{ fontSize: 12 }}>{val}</code>
              ),
            },
          ]}
          rowKey="key"
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无兼容引擎记录' }}
        />
      </Card>

      {/* Container Config */}
      <Card title="容器配置">
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="设备路径">
            <Space direction="vertical">
              {chip.device_paths.map((p) => (
                <code key={p}>{p}</code>
              ))}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="设备可见性环境变量">
            <code>{chip.env_var}</code>
          </Descriptions.Item>
          <Descriptions.Item label="K8s 资源声明">
            <code>{chip.k8s_resource}</code>
          </Descriptions.Item>
          {chip.extra_volumes.length > 0 && (
            <Descriptions.Item label="额外挂载卷">
              <Space direction="vertical">
                {chip.extra_volumes.map((v) => (
                  <code key={v}>{v}</code>
                ))}
              </Space>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>
    </div>
  );
}
