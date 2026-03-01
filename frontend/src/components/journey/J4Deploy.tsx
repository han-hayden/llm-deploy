import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Select,
  Space,
  Typography,
  Alert,
  Descriptions,
  Tag,
  message,
  Spin,
} from 'antd';
import {
  RocketOutlined,
  SafetyCertificateOutlined,
  CheckCircleOutlined,
  CopyOutlined,
  CloudServerOutlined,
} from '@ant-design/icons';
import type { AdaptationTask, Environment } from '../../types';
import { TaskStatus, DeployMode } from '../../types';
import {
  getEnvironments,
  precheck,
  deploy,
  getDeployment,
  getDeploymentByTask,
} from '../../api/client';
import TerminalLog from '../TerminalLog';
import PrecheckReport from '../PrecheckReport';
import type { PrecheckItem, Deployment } from '../../types';

const { Text, Title, Paragraph } = Typography;

interface J4DeployProps {
  task: AdaptationTask;
  onRefresh: () => void;
}

const deployModeOptions = [
  {
    value: DeployMode.DockerSingle,
    title: 'Docker 单实例',
    description: '1 个容器，N 张卡',
  },
  {
    value: DeployMode.DockerMulti,
    title: 'Docker 多实例',
    description: '多容器 + 负载均衡',
  },
  {
    value: DeployMode.K8s,
    title: 'K8s 部署',
    description: 'K8s YAML 部署',
  },
];

export default function J4Deploy({ task, onRefresh }: J4DeployProps) {
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [selectedEnvId, setSelectedEnvId] = useState<number | null>(
    task.deployment?.environment_id || null
  );
  const [deployMode, setDeployMode] = useState<DeployMode>(
    task.deployment?.deploy_mode || DeployMode.DockerSingle
  );
  const [precheckItems, setPrecheckItems] = useState<PrecheckItem[] | null>(
    task.deployment?.precheck_report || null
  );
  const [deployment, setDeployment] = useState<Deployment | null>(
    task.deployment || null
  );
  const [prechecking, setPrechecking] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isDeploying =
    task.status === TaskStatus.Deploying ||
    deployment?.status === 'deploying';
  const isDeployed =
    task.status === TaskStatus.Deployed ||
    deployment?.status === 'deployed';
  const isDeployFailed =
    task.status === TaskStatus.DeployFailed ||
    deployment?.status === 'deploy_failed';

  // Load environments
  useEffect(() => {
    setLoadingEnvs(true);
    getEnvironments()
      .then(setEnvironments)
      .catch(() => {
        /* empty */
      })
      .finally(() => setLoadingEnvs(false));
  }, []);

  // Try to load existing deployment
  useEffect(() => {
    if (!deployment && task.status === TaskStatus.Deploying) {
      getDeploymentByTask(task.id)
        .then((d) => {
          setDeployment(d);
          setPrecheckItems(d.precheck_report || null);
        })
        .catch(() => {
          /* no existing deployment */
        });
    }
  }, [task.id, task.status, deployment]);

  // Poll deployment status
  const pollDeployment = useCallback(async () => {
    if (deployment?.id) {
      try {
        const data = await getDeployment(deployment.id);
        setDeployment(data);
        if (data.status === 'deployed' || data.status === 'deploy_failed') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          if (data.status === 'deployed') {
            message.success('部署成功！');
            onRefresh();
          }
        }
      } catch {
        // silently fail
      }
    }
  }, [deployment?.id, onRefresh]);

  useEffect(() => {
    if (isDeploying && deployment?.id && !pollingRef.current) {
      pollingRef.current = setInterval(pollDeployment, 3000);
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isDeploying, deployment?.id, pollDeployment]);

  const handlePrecheck = async () => {
    if (!selectedEnvId) {
      message.warning('请先选择目标环境');
      return;
    }
    setPrechecking(true);
    try {
      const items = await precheck({
        task_id: task.id,
        environment_id: selectedEnvId,
      });
      setPrecheckItems(items);
    } catch {
      message.error('预检执行失败');
    } finally {
      setPrechecking(false);
    }
  };

  const handleDeploy = async () => {
    if (!selectedEnvId) {
      message.warning('请先选择目标环境');
      return;
    }
    setDeploying(true);
    try {
      const result = await deploy({
        task_id: task.id,
        environment_id: selectedEnvId,
        deploy_mode: deployMode,
      });
      setDeployment(result);
      message.success('部署已启动');
      onRefresh();
    } catch {
      message.error('部署启动失败');
    } finally {
      setDeploying(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).then(
      () => message.success('已复制到剪贴板'),
      () => message.error('复制失败')
    );
  };

  const precheckAllPassed =
    precheckItems != null &&
    precheckItems.length > 0 &&
    precheckItems.every((item) => item.status === 'passed');

  return (
    <div>
      {/* Deploy Config */}
      {!isDeployed && (
        <Card title="部署配置" style={{ marginBottom: 16 }}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                目标环境
              </Text>
              <Select
                placeholder="请选择目标部署环境"
                value={selectedEnvId}
                onChange={setSelectedEnvId}
                loading={loadingEnvs}
                style={{ width: 400 }}
                disabled={isDeploying}
                options={environments.map((env) => ({
                  value: env.id,
                  label: `${env.name} (${env.env_type === 'docker_host' ? 'Docker' : 'K8s'}${env.hardware_info ? ', ' + env.hardware_info.description : ''})`,
                }))}
              />
            </div>

            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                部署模式
              </Text>
              <Row gutter={12}>
                {deployModeOptions.map((opt) => (
                  <Col span={8} key={opt.value}>
                    <Card
                      size="small"
                      hoverable
                      onClick={() =>
                        !isDeploying && setDeployMode(opt.value)
                      }
                      style={{
                        border:
                          deployMode === opt.value
                            ? '2px solid #1677FF'
                            : '1px solid #d9d9d9',
                        cursor: isDeploying ? 'not-allowed' : 'pointer',
                      }}
                      bodyStyle={{ padding: '12px 16px' }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                        }}
                      >
                        <CloudServerOutlined
                          style={{
                            color:
                              deployMode === opt.value
                                ? '#1677FF'
                                : '#8C8C8C',
                          }}
                        />
                        <div>
                          <Text
                            strong
                            style={{
                              color:
                                deployMode === opt.value
                                  ? '#1677FF'
                                  : undefined,
                            }}
                          >
                            {opt.title}
                          </Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {opt.description}
                          </Text>
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>

            {!isDeploying && (
              <Button
                icon={<SafetyCertificateOutlined />}
                onClick={handlePrecheck}
                loading={prechecking}
                disabled={!selectedEnvId}
              >
                开始预检
              </Button>
            )}
          </Space>
        </Card>
      )}

      {/* Precheck Report */}
      {precheckItems && (
        <Card
          title="环境预检报告"
          style={{ marginBottom: 16 }}
          extra={
            precheckAllPassed ? (
              <Tag color="success">全部通过</Tag>
            ) : (
              <Tag color="error">存在问题</Tag>
            )
          }
        >
          <PrecheckReport items={precheckItems} />
          {precheckAllPassed && !isDeploying && !isDeployed && (
            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <Button
                type="primary"
                size="large"
                icon={<RocketOutlined />}
                onClick={handleDeploy}
                loading={deploying}
              >
                立即部署
              </Button>
            </div>
          )}
          {!precheckAllPassed && !isDeploying && !isDeployed && (
            <Space style={{ marginTop: 16 }}>
              <Button onClick={handlePrecheck} loading={prechecking}>
                重新预检
              </Button>
              <Button
                type="primary"
                danger
                onClick={handleDeploy}
                loading={deploying}
              >
                强制跳过（需确认风险）
              </Button>
            </Space>
          )}
        </Card>
      )}

      {/* Deploying Status */}
      {isDeploying && deployment && (
        <Card title="部署状态" style={{ marginBottom: 16 }}>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Spin spinning>
              <Tag color="processing">部署中...</Tag>
            </Spin>
            <Title level={5}>部署日志</Title>
            <TerminalLog content={deployment.deploy_log || '等待部署输出...'} />
          </Space>
        </Card>
      )}

      {/* Deploy Failed */}
      {isDeployFailed && deployment && (
        <div>
          <Alert
            type="error"
            message="部署失败"
            description="请检查部署日志并重试。"
            showIcon
            style={{ marginBottom: 16 }}
            action={
              <Button type="primary" onClick={handleDeploy}>
                重新部署
              </Button>
            }
          />
          {deployment.deploy_log && (
            <Card title="部署日志" style={{ marginBottom: 16 }}>
              <TerminalLog content={deployment.deploy_log} />
            </Card>
          )}
        </div>
      )}

      {/* Deploy Success */}
      {isDeployed && deployment && (
        <Card
          style={{
            borderColor: '#52C41A',
            background:
              'linear-gradient(135deg, #f6ffed 0%, #ffffff 100%)',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <CheckCircleOutlined
              style={{ fontSize: 48, color: '#52C41A', marginBottom: 12 }}
            />
            <Title level={4} style={{ color: '#52C41A', marginBottom: 0 }}>
              模型服务部署成功！
            </Title>
          </div>

          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="API 地址" span={2}>
              <Space>
                <code style={{ fontSize: 14, color: '#1677FF' }}>
                  {deployment.api_endpoint || '-'}
                </code>
                {deployment.api_endpoint && (
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() =>
                      handleCopy(deployment.api_endpoint || '')
                    }
                  />
                )}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="服务状态">
              <Tag color="success">Running</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="硬件">
              {task.hardware_model}
            </Descriptions.Item>
            <Descriptions.Item label="推理引擎">
              {task.engine || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="首次响应延迟">
              {deployment.verification_result?.response_time_ms
                ? `${(deployment.verification_result.response_time_ms / 1000).toFixed(1)}s`
                : '-'}
            </Descriptions.Item>
          </Descriptions>

          {deployment.api_endpoint && (
            <div style={{ marginTop: 20 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 8,
                }}
              >
                <Text strong>测试命令</Text>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => {
                    const cmd = `curl ${deployment.api_endpoint} \\\n  -H "Content-Type: application/json" \\\n  -d '{"model":"${task.model_identifier.split('/').pop()}", "messages":[{"role":"user","content":"hello"}]}'`;
                    handleCopy(cmd);
                  }}
                >
                  复制
                </Button>
              </div>
              <TerminalLog
                content={`curl ${deployment.api_endpoint} \\\n  -H "Content-Type: application/json" \\\n  -d '{"model":"${task.model_identifier.split('/').pop()}", "messages":[{"role":"user","content":"hello"}]}'`}
              />
            </div>
          )}

          {deployment.verification_result?.response_preview && (
            <div style={{ marginTop: 16 }}>
              <Paragraph type="secondary" style={{ fontSize: 12 }}>
                验证响应预览: {deployment.verification_result.response_preview}
              </Paragraph>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
