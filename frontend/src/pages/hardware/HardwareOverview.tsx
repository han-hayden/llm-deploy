import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Table,
  Typography,
  Tag,
  Space,
  Spin,
  Button,
} from 'antd';
import {
  RightOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getHardwareCompatibility } from '../../api/client';
import type { HardwareVendorInfo, HardwareChip } from '../../types';

const { Title, Text } = Typography;

const vendorColors: Record<string, string> = {
  nvidia: '#76B900',
  huawei: '#CF0A2C',
  hygon: '#0055A5',
  metax: '#FF6600',
  kunlunxin: '#1A73E8',
  iluvatar: '#7B2FBE',
};

export default function HardwareOverview() {
  const navigate = useNavigate();
  const [vendors, setVendors] = useState<HardwareVendorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);

  useEffect(() => {
    getHardwareCompatibility()
      .then((res) => {
        setVendors(res.vendors);
        if (res.vendors.length > 0) {
          setSelectedVendor(res.vendors[0].slug);
        }
      })
      .catch(() => {
        // Provide fallback data for display
        const fallback: HardwareVendorInfo[] = [
          {
            name: 'NVIDIA',
            slug: 'nvidia' as HardwareVendorInfo['slug'],
            website: 'https://nvidia.com',
            modelzoo_url: '',
            chips: [
              {
                model: 'H100 80G',
                memory_gb: 80,
                memory_type: 'HBM3',
                compute_tflops_fp16: 1979,
                interconnect: 'NVLink',
                supports_bf16: true,
                supports_fp8: true,
                device_paths: ['/dev/nvidia{id}'],
                env_var: 'CUDA_VISIBLE_DEVICES',
                k8s_resource: 'nvidia.com/gpu',
                detection_command: 'nvidia-smi',
                extra_volumes: [],
              },
              {
                model: 'A100 80G',
                memory_gb: 80,
                memory_type: 'HBM2e',
                compute_tflops_fp16: 312,
                interconnect: 'NVLink',
                supports_bf16: true,
                supports_fp8: false,
                device_paths: ['/dev/nvidia{id}'],
                env_var: 'CUDA_VISIBLE_DEVICES',
                k8s_resource: 'nvidia.com/gpu',
                detection_command: 'nvidia-smi',
                extra_volumes: [],
              },
            ],
            engines: [
              {
                name: 'vLLM',
                versions: [
                  {
                    version: '0.6.0',
                    min_driver: '525.0',
                    min_sdk: 'CUDA 12.1',
                    base_image: 'vllm/vllm-openai:v0.6.0',
                    compatible_chips: ['H100 80G', 'A100 80G', 'A100 40G'],
                    param_mapping: {},
                    startup_template: '',
                  },
                ],
              },
            ],
          },
          {
            name: '华为昇腾',
            slug: 'huawei' as HardwareVendorInfo['slug'],
            website: 'https://www.hiascend.com/',
            modelzoo_url: 'https://gitee.com/ascend/ModelZoo-PyTorch',
            chips: [
              {
                model: '910B3 64G',
                memory_gb: 64,
                memory_type: 'HBM2e',
                compute_tflops_fp16: 280,
                interconnect: 'HCCS',
                supports_bf16: true,
                supports_fp8: false,
                device_paths: ['/dev/davinci{id}'],
                env_var: 'ASCEND_VISIBLE_DEVICES',
                k8s_resource: 'huawei.com/Ascend910',
                detection_command: 'npu-smi info',
                extra_volumes: ['/usr/local/Ascend/driver:/usr/local/Ascend/driver'],
              },
              {
                model: '910B4 64G',
                memory_gb: 64,
                memory_type: 'HBM2e',
                compute_tflops_fp16: 320,
                interconnect: 'HCCS',
                supports_bf16: true,
                supports_fp8: false,
                device_paths: ['/dev/davinci{id}'],
                env_var: 'ASCEND_VISIBLE_DEVICES',
                k8s_resource: 'huawei.com/Ascend910',
                detection_command: 'npu-smi info',
                extra_volumes: ['/usr/local/Ascend/driver:/usr/local/Ascend/driver'],
              },
              {
                model: '910C 128G',
                memory_gb: 128,
                memory_type: 'HBM2e',
                compute_tflops_fp16: 640,
                interconnect: 'HCCS',
                supports_bf16: true,
                supports_fp8: true,
                device_paths: ['/dev/davinci{id}'],
                env_var: 'ASCEND_VISIBLE_DEVICES',
                k8s_resource: 'huawei.com/Ascend910',
                detection_command: 'npu-smi info',
                extra_volumes: ['/usr/local/Ascend/driver:/usr/local/Ascend/driver'],
              },
            ],
            engines: [
              {
                name: 'MindIE',
                versions: [
                  {
                    version: '1.0',
                    min_driver: '24.1.RC2',
                    min_sdk: 'CANN 8.0.RC2',
                    base_image: 'ascendhub.huawei.com/public-ascendhub/mindie:1.0-cann8.0',
                    compatible_chips: ['910B3 64G', '910B4 64G'],
                    param_mapping: {},
                    startup_template: '',
                  },
                ],
              },
              {
                name: 'vLLM-Ascend',
                versions: [
                  {
                    version: '0.6.0',
                    min_driver: '24.1.RC2',
                    min_sdk: 'CANN 8.0.RC2',
                    base_image: 'ascendhub.huawei.com/public-ascendhub/vllm-ascend:0.6.0',
                    compatible_chips: ['910B3 64G', '910B4 64G', '910C 128G'],
                    param_mapping: {},
                    startup_template: '',
                  },
                ],
              },
            ],
          },
          {
            name: '海光 DCU',
            slug: 'hygon' as HardwareVendorInfo['slug'],
            website: 'https://www.hygon.cn/',
            modelzoo_url: '',
            chips: [
              {
                model: 'K100_AI 64G',
                memory_gb: 64,
                memory_type: 'HBM2e',
                compute_tflops_fp16: 200,
                interconnect: 'PCIe',
                supports_bf16: false,
                supports_fp8: false,
                device_paths: ['/dev/kfd', '/dev/dri'],
                env_var: 'HIP_VISIBLE_DEVICES',
                k8s_resource: 'hygon.com/dcu',
                detection_command: 'rocm-smi',
                extra_volumes: [],
              },
            ],
            engines: [
              {
                name: 'vLLM-DCU',
                versions: [
                  {
                    version: '0.5.0',
                    min_driver: 'DTK 24.04',
                    min_sdk: 'DTK 24.04',
                    base_image: 'image.sourcefind.cn:5000/dcu/admin/base/pytorch:2.1.0-ubuntu20.04-dtk24.04-py3.10',
                    compatible_chips: ['K100_AI 64G'],
                    param_mapping: {},
                    startup_template: '',
                  },
                ],
              },
            ],
          },
        ];
        setVendors(fallback);
        setSelectedVendor(fallback[0].slug);
      })
      .finally(() => setLoading(false));
  }, []);

  const currentVendor = vendors.find((v) => v.slug === selectedVendor);

  const chipColumns: ColumnsType<HardwareChip> = [
    {
      title: '芯片型号',
      dataIndex: 'model',
      key: 'model',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '显存',
      dataIndex: 'memory_gb',
      key: 'memory_gb',
      render: (val: number, record: HardwareChip) =>
        `${val} GB ${record.memory_type}`,
    },
    {
      title: '算力 (FP16)',
      dataIndex: 'compute_tflops_fp16',
      key: 'compute_tflops_fp16',
      render: (val: number) => `${val} TFLOPS`,
    },
    {
      title: '互联',
      dataIndex: 'interconnect',
      key: 'interconnect',
    },
    {
      title: 'BF16',
      dataIndex: 'supports_bf16',
      key: 'supports_bf16',
      width: 80,
      render: (val: boolean) =>
        val ? (
          <Tag color="success">支持</Tag>
        ) : (
          <Tag color="default">不支持</Tag>
        ),
    },
    {
      title: 'FP8',
      dataIndex: 'supports_fp8',
      key: 'supports_fp8',
      width: 80,
      render: (val: boolean) =>
        val ? (
          <Tag color="success">支持</Tag>
        ) : (
          <Tag color="default">不支持</Tag>
        ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: HardwareChip) => (
        <Button
          type="link"
          size="small"
          onClick={() =>
            navigate(
              `/hardware/${encodeURIComponent(selectedVendor + ':' + record.model)}`
            )
          }
        >
          详情 <RightOutlined />
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
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
        硬件知识库
      </Title>

      {/* Vendor Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {vendors.map((vendor) => (
          <Col
            span={Math.min(Math.floor(24 / vendors.length), 6)}
            key={vendor.slug}
          >
            <Card
              hoverable
              onClick={() => setSelectedVendor(vendor.slug)}
              style={{
                border:
                  selectedVendor === vendor.slug
                    ? `2px solid ${vendorColors[vendor.slug] || '#1677FF'}`
                    : '1px solid #d9d9d9',
                textAlign: 'center',
              }}
              bodyStyle={{ padding: '16px 12px' }}
            >
              <Text
                strong
                style={{
                  fontSize: 15,
                  color:
                    selectedVendor === vendor.slug
                      ? vendorColors[vendor.slug] || '#1677FF'
                      : undefined,
                }}
              >
                {vendor.name}
              </Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {vendor.chips.length} 款芯片 / {vendor.engines.length} 个引擎
              </Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Chip Table */}
      {currentVendor && (
        <Card
          title={
            <Space>
              <Text strong>{currentVendor.name}</Text>
              <Text type="secondary">芯片列表</Text>
            </Space>
          }
          bodyStyle={{ padding: 0 }}
          style={{ marginBottom: 24 }}
        >
          <Table
            columns={chipColumns}
            dataSource={currentVendor.chips}
            rowKey="model"
            pagination={false}
          />
        </Card>
      )}

      {/* Compatible Engines */}
      {currentVendor && currentVendor.engines.length > 0 && (
        <Card title="兼容推理引擎">
          <Table
            dataSource={currentVendor.engines.flatMap((eng) =>
              eng.versions.map((v) => ({
                key: `${eng.name}-${v.version}`,
                engine_name: eng.name,
                version: v.version,
                min_driver: v.min_driver,
                min_sdk: v.min_sdk,
                base_image: v.base_image,
                compatible_chips: v.compatible_chips,
              }))
            )}
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
                title: '兼容芯片',
                dataIndex: 'compatible_chips',
                key: 'compatible_chips',
                render: (chips: string[]) => (
                  <Space wrap>
                    {chips.map((c) => (
                      <Tag key={c}>{c}</Tag>
                    ))}
                  </Space>
                ),
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
          />
        </Card>
      )}
    </div>
  );
}
