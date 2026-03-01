import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Typography,
  Space,
  Button,
} from 'antd';
import {
  PlusOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getTasks, getStats } from '../api/client';
import type { AdaptationTask, StatsResponse } from '../types';
import { TaskStatus } from '../types';

const { Title, Text, Paragraph } = Typography;

const statusColorMap: Record<string, string> = {
  [TaskStatus.Created]: 'default',
  [TaskStatus.Parsing]: 'processing',
  [TaskStatus.Parsed]: 'blue',
  [TaskStatus.ParseFailed]: 'error',
  [TaskStatus.Downloading]: 'processing',
  [TaskStatus.Downloaded]: 'blue',
  [TaskStatus.DownloadFailed]: 'error',
  [TaskStatus.Building]: 'processing',
  [TaskStatus.Built]: 'blue',
  [TaskStatus.BuildFailed]: 'error',
  [TaskStatus.Deploying]: 'processing',
  [TaskStatus.Deployed]: 'success',
  [TaskStatus.DeployFailed]: 'error',
};

const statusLabelMap: Record<string, string> = {
  [TaskStatus.Created]: '已创建',
  [TaskStatus.Parsing]: '解析中',
  [TaskStatus.Parsed]: '已解析',
  [TaskStatus.ParseFailed]: '解析失败',
  [TaskStatus.Downloading]: '下载中',
  [TaskStatus.Downloaded]: '已下载',
  [TaskStatus.DownloadFailed]: '下载失败',
  [TaskStatus.Building]: '构建中',
  [TaskStatus.Built]: '已构建',
  [TaskStatus.BuildFailed]: '构建失败',
  [TaskStatus.Deploying]: '部署中',
  [TaskStatus.Deployed]: '已部署',
  [TaskStatus.DeployFailed]: '部署失败',
};

export default function Overview() {
  const navigate = useNavigate();
  const [recentTasks, setRecentTasks] = useState<AdaptationTask[]>([]);
  const [stats, setStats] = useState<StatsResponse>({
    total_tasks: 0,
    completed_tasks: 0,
    running_services: 0,
    registered_environments: 0,
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getTasks({ page: 1, page_size: 5 }).catch(() => ({
        items: [],
        total: 0,
        page: 1,
        page_size: 5,
      })),
      getStats().catch(() => ({
        total_tasks: 0,
        completed_tasks: 0,
        running_services: 0,
        registered_environments: 0,
      })),
    ]).then(([taskRes, statsRes]) => {
      setRecentTasks(taskRes.items);
      setStats(statsRes);
      setLoading(false);
    });
  }, []);

  const columns: ColumnsType<AdaptationTask> = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      render: (text: string, record: AdaptationTask) => (
        <Button type="link" onClick={() => navigate(`/tasks/${record.id}`)} style={{ padding: 0 }}>
          {text}
        </Button>
      ),
    },
    {
      title: '模型',
      dataIndex: 'model_identifier',
      key: 'model_identifier',
      ellipsis: true,
    },
    {
      title: '硬件',
      dataIndex: 'hardware_model',
      key: 'hardware_model',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: TaskStatus) => (
        <Tag color={statusColorMap[status] || 'default'}>
          {statusLabelMap[status] || status}
        </Tag>
      ),
    },
  ];

  const quickStartCards = [
    {
      title: '新建适配任务',
      description: '输入模型名称或链接 + 硬件型号，系统自动完成适配全流程',
      link: '/tasks/create',
      linkText: '开始创建',
      number: '01',
      icon: <PlusOutlined />,
    },
    {
      title: '注册部署环境',
      description: '添加 Docker 主机或 K8s 集群，管理目标部署环境',
      link: '/environments',
      linkText: '开始创建',
      number: '02',
      icon: <CloudServerOutlined />,
    },
    {
      title: '查看硬件知识库',
      description: '查看已支持的硬件型号和推理引擎兼容矩阵',
      link: '/hardware',
      linkText: '开始查看',
      number: '03',
      icon: <DatabaseOutlined />,
    },
  ];

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
        总览
      </Title>

      {/* Feature Intro Card */}
      <Card
        style={{
          marginBottom: 24,
          borderLeft: '4px solid #1677FF',
          background: 'linear-gradient(135deg, #f0f5ff 0%, #ffffff 100%)',
        }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        <Space direction="vertical" size={4}>
          <Space>
            <RocketOutlined style={{ fontSize: 20, color: '#1677FF' }} />
            <Text strong style={{ fontSize: 16, color: '#1677FF' }}>
              模型适配加速器
            </Text>
          </Space>
          <Paragraph style={{ marginBottom: 0, color: '#595959' }}>
            输入模型 + 硬件，自动完成适配全流程。支持 NVIDIA + 5 大国产卡（昇腾 / 海光 / 沐曦 / 昆仑芯 / 天数智芯）。自动推算启动参数，首次启动即为最优配置。
          </Paragraph>
        </Space>
      </Card>

      {/* Quick Start Cards */}
      <div style={{ marginBottom: 24 }}>
        <Text strong style={{ fontSize: 15, marginBottom: 12, display: 'block' }}>
          快速开始
        </Text>
        <Row gutter={16}>
          {quickStartCards.map((card) => (
            <Col span={8} key={card.number}>
              <Card
                hoverable
                onClick={() => navigate(card.link)}
                style={{ height: '100%' }}
                bodyStyle={{ padding: '20px 24px' }}
              >
                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                  <Space>
                    <span style={{ fontSize: 18, color: '#1677FF' }}>{card.icon}</span>
                    <Text strong style={{ fontSize: 15 }}>{card.title}</Text>
                  </Space>
                  <Text type="secondary" style={{ fontSize: 13 }}>
                    {card.description}
                  </Text>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Button type="link" style={{ padding: 0, fontSize: 13 }}>
                      {card.linkText} &rarr;
                    </Button>
                    <Text
                      style={{
                        fontSize: 32,
                        fontWeight: 700,
                        color: '#f0f0f0',
                        lineHeight: 1,
                      }}
                    >
                      {card.number}
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card bodyStyle={{ padding: '16px 24px' }}>
            <Statistic
              title="适配任务总数"
              value={stats.total_tasks}
              prefix={<AppstoreOutlined style={{ color: '#1677FF' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bodyStyle={{ padding: '16px 24px' }}>
            <Statistic
              title="已完成任务"
              value={stats.completed_tasks}
              prefix={<CheckCircleOutlined style={{ color: '#52C41A' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bodyStyle={{ padding: '16px 24px' }}>
            <Statistic
              title="运行中服务"
              value={stats.running_services}
              prefix={<PlayCircleOutlined style={{ color: '#1677FF' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bodyStyle={{ padding: '16px 24px' }}>
            <Statistic
              title="注册环境数"
              value={stats.registered_environments}
              prefix={<CloudServerOutlined style={{ color: '#1677FF' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* Recent Tasks */}
      <Card
        title="最近任务"
        bodyStyle={{ padding: 0 }}
        extra={
          <Button type="link" onClick={() => navigate('/tasks')}>
            查看全部
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={recentTasks}
          rowKey="id"
          pagination={false}
          loading={loading}
          locale={{ emptyText: '暂无任务，点击"新建适配任务"开始' }}
        />
      </Card>
    </div>
  );
}
