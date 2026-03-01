import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Table,
  Button,
  InputNumber,
  Space,
  Typography,
  Alert,
  Tag,
  Descriptions,
  message,
  Spin,
} from 'antd';
import {
  EditOutlined,
  CheckOutlined,
  BuildOutlined,
} from '@ant-design/icons';
import type { AdaptationTask, ParamCalculation, ImageBuild, ParamItem } from '../../types';
import { TaskStatus } from '../../types';
import {
  calculateParams,
  recalculateParams,
  buildImage,
  getBuildStatus,
  getBuildByTask,
} from '../../api/client';
import MemoryChart from '../MemoryChart';
import TerminalLog from '../TerminalLog';

const { Text, Title } = Typography;

interface J3ParamAndBuildProps {
  task: AdaptationTask;
  onRefresh: () => void;
}

export default function J3ParamAndBuild({
  task,
  onRefresh,
}: J3ParamAndBuildProps) {
  const [params, setParams] = useState<ParamCalculation | null>(
    task.image_build?.param_calculation || null
  );
  const [build, setBuild] = useState<ImageBuild | null>(
    task.image_build || null
  );
  const [gpuCount, setGpuCount] = useState<number>(
    task.image_build?.param_calculation?.gpu_count || 4
  );
  const [editingGpu, setEditingGpu] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [building, setBuilding] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isBuilding =
    task.status === TaskStatus.Building || build?.status === 'building';
  const isBuildComplete =
    task.status === TaskStatus.Built || build?.status === 'completed';
  const isBuildFailed =
    task.status === TaskStatus.BuildFailed || build?.status === 'failed';

  // Calculate params on first load if not already done
  useEffect(() => {
    if (
      !params &&
      (task.status === TaskStatus.Downloaded ||
        task.status === TaskStatus.Building ||
        task.status === TaskStatus.Built ||
        task.status === TaskStatus.BuildFailed)
    ) {
      setCalculating(true);
      calculateParams({ task_id: task.id })
        .then((data) => {
          setParams(data);
          setGpuCount(data.gpu_count);
        })
        .catch(() => {
          // params not yet calculated
        })
        .finally(() => setCalculating(false));
    }
  }, [task.id, task.status, params]);

  // Try to load existing build
  useEffect(() => {
    if (!build && task.status === TaskStatus.Building) {
      getBuildByTask(task.id)
        .then((b) => setBuild(b))
        .catch(() => {
          /* no build yet */
        });
    }
  }, [task.id, task.status, build]);

  // Poll build status
  const pollBuild = useCallback(async () => {
    if (build?.id) {
      try {
        const data = await getBuildStatus(build.id);
        setBuild(data);
        if (data.status === 'completed' || data.status === 'failed') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          if (data.status === 'completed') {
            message.success('镜像构建完成');
            onRefresh();
          }
        }
      } catch {
        // silently fail
      }
    }
  }, [build?.id, onRefresh]);

  useEffect(() => {
    if (isBuilding && build?.id && !pollingRef.current) {
      pollingRef.current = setInterval(pollBuild, 3000);
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isBuilding, build?.id, pollBuild]);

  const handleRecalculate = async () => {
    setCalculating(true);
    try {
      const data = await recalculateParams({
        task_id: task.id,
        gpu_count: gpuCount,
      });
      setParams(data);
      setEditingGpu(false);
      message.success('参数已重新推算');
    } catch {
      message.error('参数推算失败');
    } finally {
      setCalculating(false);
    }
  };

  const handleBuild = async () => {
    setBuilding(true);
    try {
      const result = await buildImage({ task_id: task.id });
      setBuild(result);
      message.success('镜像构建已启动');
      onRefresh();
    } catch {
      message.error('构建启动失败');
    } finally {
      setBuilding(false);
    }
  };

  if (calculating && !params) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在推算启动参数...</Text>
          </div>
        </div>
      </Card>
    );
  }

  const paramColumns = [
    {
      title: '参数',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (val: string) => <Text strong>{val}</Text>,
    },
    {
      title: '推荐值',
      dataIndex: 'value',
      key: 'value',
      width: 150,
      render: (val: string | number | boolean) => {
        if (typeof val === 'boolean') return val ? 'true' : 'false';
        return String(val);
      },
    },
    {
      title: '推算依据',
      dataIndex: 'rationale',
      key: 'rationale',
      ellipsis: true,
    },
    {
      title: '可调整',
      dataIndex: 'editable',
      key: 'editable',
      width: 80,
      render: (val: boolean | string) => {
        if (val === true) return <Tag color="blue">是</Tag>;
        if (val === 'linked') return <Tag color="orange">联动</Tag>;
        return <Tag>自动</Tag>;
      },
    },
  ];

  return (
    <div>
      {/* Query Summary */}
      {build?.query_summary && (
        <Card title="查询结果摘要" size="small" style={{ marginBottom: 16 }}>
          <Descriptions column={1} size="small">
            <Descriptions.Item label="模型官方说明">
              {build.query_summary.model_official_note}
            </Descriptions.Item>
            <Descriptions.Item label="厂商适配状态">
              {build.query_summary.vendor_adaptation_status}
            </Descriptions.Item>
            <Descriptions.Item label="推荐基础镜像">
              <code>{build.query_summary.recommended_base_image}</code>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* Hardware Spec + GPU Count */}
      {params && (
        <Card
          title="推荐硬件部署规格"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Row gutter={24}>
            <Col span={8}>
              <Text type="secondary">硬件</Text>
              <div>
                <Text strong>{task.hardware_model}</Text>
              </div>
            </Col>
            <Col span={8}>
              <Text type="secondary">推荐卡数</Text>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {editingGpu ? (
                  <Space>
                    <InputNumber
                      min={1}
                      max={64}
                      value={gpuCount}
                      onChange={(val) => val && setGpuCount(val)}
                      style={{ width: 80 }}
                    />
                    <Text>张</Text>
                    <Button
                      type="primary"
                      size="small"
                      icon={<CheckOutlined />}
                      onClick={handleRecalculate}
                      loading={calculating}
                    >
                      确认
                    </Button>
                  </Space>
                ) : (
                  <Space>
                    <Text strong style={{ fontSize: 20 }}>
                      {params.gpu_count}
                    </Text>
                    <Text>张</Text>
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => setEditingGpu(true)}
                      disabled={isBuilding || isBuildComplete}
                    >
                      修改
                    </Button>
                  </Space>
                )}
              </div>
            </Col>
            <Col span={8}>
              <Text type="secondary">部署模式</Text>
              <div>
                <Text strong>
                  {params.pipeline_parallel_size > 1
                    ? '多机 Pipeline Parallel'
                    : '单机 Tensor Parallel'}
                </Text>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Params Table */}
      {params?.all_params && (
        <Card
          title="启动参数详情"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Table
            columns={paramColumns}
            dataSource={params.all_params.map((p: ParamItem, i: number) => ({
              ...p,
              key: i,
            }))}
            size="small"
            pagination={false}
          />
        </Card>
      )}

      {/* Memory Allocation */}
      {params?.memory_allocation && (
        <Card
          title="显存分配可视化"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <MemoryChart allocation={params.memory_allocation} />
        </Card>
      )}

      {/* Build Button */}
      {params && !isBuilding && !isBuildComplete && !isBuildFailed && (
        <div style={{ textAlign: 'right', marginBottom: 16 }}>
          <Button
            type="primary"
            size="large"
            icon={<BuildOutlined />}
            onClick={handleBuild}
            loading={building}
          >
            确认参数，开始构建 &rarr;
          </Button>
        </div>
      )}

      {/* Build Progress */}
      {isBuilding && build && (
        <Card title="构建进度" style={{ marginBottom: 16 }}>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <div>
              <Text type="secondary">镜像 Tag: </Text>
              <code>{build.image_tag || '-'}</code>
            </div>
            <Tag icon={<BuildOutlined />} color="processing">
              构建中...
            </Tag>
            <Title level={5}>构建日志</Title>
            <TerminalLog content={build.build_log || ''} />
          </Space>
        </Card>
      )}

      {/* Build Failed */}
      {isBuildFailed && build && (
        <div>
          <Alert
            type="error"
            message="镜像构建失败"
            description="请检查构建日志并重试。"
            showIcon
            style={{ marginBottom: 16 }}
            action={
              <Button type="primary" onClick={handleBuild}>
                重新构建
              </Button>
            }
          />
          {build.build_log && (
            <Card title="构建日志" style={{ marginBottom: 16 }}>
              <TerminalLog content={build.build_log} />
            </Card>
          )}
        </div>
      )}

      {/* Build Complete */}
      {isBuildComplete && build && (
        <div>
          <Card
            title={
              <span style={{ color: '#52C41A' }}>
                <CheckOutlined style={{ marginRight: 8 }} />
                构建完成
              </span>
            }
            style={{ marginBottom: 16, borderColor: '#52C41A' }}
          >
            <Descriptions column={2} size="small">
              <Descriptions.Item label="镜像名称">
                <code>{build.image_tag}</code>
              </Descriptions.Item>
              <Descriptions.Item label="镜像大小">
                {build.image_size_gb
                  ? `${build.image_size_gb.toFixed(1)} GB`
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="基础镜像">
                <code>{build.base_image}</code>
              </Descriptions.Item>
              <Descriptions.Item label="推理引擎">
                {build.engine_name} {build.engine_version}
              </Descriptions.Item>
              <Descriptions.Item label="API 封装">
                {build.api_wrapper_injected
                  ? '已注入 OpenAI 兼容 API'
                  : '无需（引擎原生支持）'}
              </Descriptions.Item>
            </Descriptions>

            {build.startup_command && (
              <div style={{ marginTop: 16 }}>
                <Text strong>启动命令</Text>
                <TerminalLog content={build.startup_command} />
              </div>
            )}
          </Card>

          <div style={{ textAlign: 'right' }}>
            <Button type="primary" size="large" onClick={onRefresh}>
              进入部署 &rarr;
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
