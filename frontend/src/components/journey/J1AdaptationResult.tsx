import { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Descriptions,
  Radio,
  Button,
  Alert,
  Tag,
  Space,
  Spin,
  Typography,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  QuestionCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { AdaptationTask } from '../../types';
import { TaskStatus } from '../../types';
import { confirmAdaptation } from '../../api/client';

const { Text } = Typography;

interface J1AdaptationResultProps {
  task: AdaptationTask;
  onRefresh: () => void;
}

function AdaptationLabel({ label }: { label: string | null }) {
  if (!label) return <Tag>未知</Tag>;
  if (label.includes('官方已验证')) {
    return (
      <Tag color="success" icon={<CheckCircleOutlined />}>
        {label}
      </Tag>
    );
  }
  if (label.includes('社区适配')) {
    return (
      <Tag color="warning" icon={<WarningOutlined />}>
        {label}
      </Tag>
    );
  }
  return (
    <Tag color="default" icon={<QuestionCircleOutlined />}>
      {label || '未找到适配记录'}
    </Tag>
  );
}

export default function J1AdaptationResult({
  task,
  onRefresh,
}: J1AdaptationResultProps) {
  const [selectedEngine, setSelectedEngine] = useState(task.engine || '');
  const [selectedDtype, setSelectedDtype] = useState(task.dtype || 'bf16');
  const [confirming, setConfirming] = useState(false);

  const meta = task.model_metadata;
  const isParsing = task.status === TaskStatus.Parsing;
  const isParseFailed = task.status === TaskStatus.ParseFailed;
  const isConfirmable = task.status === TaskStatus.Parsed;

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await confirmAdaptation(task.id, {
        engine: selectedEngine || undefined,
        dtype: selectedDtype || undefined,
      });
      message.success('方案已确认，进入权重下载');
      onRefresh();
    } catch {
      message.error('确认失败，请重试');
    } finally {
      setConfirming(false);
    }
  };

  if (isParsing) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在解析模型信息与硬件适配方案...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (isParseFailed) {
    return (
      <Alert
        type="error"
        message="模型解析失败"
        description="模型信息获取失败，请检查模型标识是否正确或网络连接是否正常。"
        showIcon
        action={
          <Button type="primary" onClick={onRefresh}>
            重试
          </Button>
        }
      />
    );
  }

  const engineOptions = meta?.model_card_parsed?.recommended_frameworks || [
    'vLLM',
    'MindIE',
    'TGI',
  ];

  const dtypeOptions = ['bf16', 'fp16', 'int8', 'int4'];

  function formatParamCount(count: number | undefined): string {
    if (!count) return '-';
    if (count >= 1e12) return `${(count / 1e12).toFixed(1)}T`;
    if (count >= 1e9) return `${(count / 1e9).toFixed(0)}B`;
    if (count >= 1e6) return `${(count / 1e6).toFixed(0)}M`;
    return String(count);
  }

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {/* Model Info Card */}
        <Col span={12}>
          <Card title="模型信息" size="small" style={{ height: '100%' }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="模型名称">
                {meta?.model_name || task.model_identifier}
              </Descriptions.Item>
              <Descriptions.Item label="参数量">
                {formatParamCount(meta?.param_count)}
              </Descriptions.Item>
              <Descriptions.Item label="架构">
                {meta?.architectures || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="原生精度">
                {meta?.torch_dtype || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="最大上下文">
                {meta?.max_position_embeddings
                  ? meta.max_position_embeddings.toLocaleString()
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="权重大小">
                {meta?.total_weight_size_gb
                  ? `${meta.total_weight_size_gb.toFixed(1)} GB`
                  : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* Hardware Info Card */}
        <Col span={12}>
          <Card title="硬件信息" size="small" style={{ height: '100%' }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="硬件型号">
                {task.hardware_model}
              </Descriptions.Item>
              <Descriptions.Item label="单卡显存">
                -
              </Descriptions.Item>
              <Descriptions.Item label="算力">
                -
              </Descriptions.Item>
              <Descriptions.Item label="互联">
                -
              </Descriptions.Item>
              <Descriptions.Item label="BF16 支持">
                -
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      {/* Recommended Plan Card */}
      <Card title="推荐适配方案" style={{ marginBottom: 16 }}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong style={{ marginRight: 12 }}>
              适配状态
            </Text>
            <AdaptationLabel label={task.adaptation_label} />
          </div>

          <div>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>
              推理引擎
            </Text>
            <Radio.Group
              value={selectedEngine}
              onChange={(e) => setSelectedEngine(e.target.value)}
              disabled={!isConfirmable}
            >
              <Space direction="vertical">
                {engineOptions.map((engine, idx) => (
                  <Radio key={engine} value={engine}>
                    {engine} {idx === 0 ? '(推荐)' : ''}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </div>

          <div>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>
              计算精度
            </Text>
            <Radio.Group
              value={selectedDtype}
              onChange={(e) => setSelectedDtype(e.target.value)}
              disabled={!isConfirmable}
            >
              <Space>
                {dtypeOptions.map((dtype) => (
                  <Radio key={dtype} value={dtype}>
                    {dtype.toUpperCase()}
                    {dtype === meta?.torch_dtype ? ' (模型原生)' : ''}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </div>

          {task.anomaly_flags && task.anomaly_flags.length > 0 && (
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                异常检测
              </Text>
              <Space direction="vertical" size={4}>
                {task.anomaly_flags.map((flag, idx) => (
                  <Alert
                    key={idx}
                    type={flag.type === 'warning' ? 'warning' : 'info'}
                    message={flag.message}
                    showIcon
                    icon={
                      flag.type === 'warning' ? (
                        <WarningOutlined />
                      ) : (
                        <InfoCircleOutlined />
                      )
                    }
                    style={{ padding: '4px 12px' }}
                    banner
                  />
                ))}
              </Space>
            </div>
          )}
        </Space>
      </Card>

      {isConfirmable && (
        <div style={{ textAlign: 'right' }}>
          <Button
            type="primary"
            size="large"
            loading={confirming}
            onClick={handleConfirm}
          >
            确认方案，进入下一步 &rarr;
          </Button>
        </div>
      )}
    </div>
  );
}
