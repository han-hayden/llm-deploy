import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Tag,
  Button,
  Input,
  Select,
  Space,
  Typography,
  Dropdown,
  message,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  DownOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getTasks, deleteTask } from '../../api/client';
import type { AdaptationTask } from '../../types';
import { TaskStatus } from '../../types';

const { Title, Text } = Typography;

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: TaskStatus.Created, label: '已创建' },
  { value: TaskStatus.Parsing, label: '解析中' },
  { value: TaskStatus.Parsed, label: '已解析' },
  { value: TaskStatus.ParseFailed, label: '解析失败' },
  { value: TaskStatus.Downloading, label: '下载中' },
  { value: TaskStatus.Downloaded, label: '已下载' },
  { value: TaskStatus.DownloadFailed, label: '下载失败' },
  { value: TaskStatus.Building, label: '构建中' },
  { value: TaskStatus.Built, label: '已构建' },
  { value: TaskStatus.BuildFailed, label: '构建失败' },
  { value: TaskStatus.Deploying, label: '部署中' },
  { value: TaskStatus.Deployed, label: '已部署' },
  { value: TaskStatus.DeployFailed, label: '部署失败' },
];

const hardwareFilterOptions = [
  { value: '', label: '全部硬件' },
  { value: 'H100', label: 'NVIDIA H100' },
  { value: 'A100', label: 'NVIDIA A100' },
  { value: '910B3', label: '昇腾 910B3' },
  { value: '910B4', label: '昇腾 910B4' },
  { value: '910C', label: '昇腾 910C' },
  { value: 'K100_AI', label: '海光 K100_AI' },
];

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

export default function TaskList() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<AdaptationTask[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [hardwareFilter, setHardwareFilter] = useState('');
  const [search, setSearch] = useState('');

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTasks({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        hardware_model: hardwareFilter || undefined,
        search: search || undefined,
      });
      setTasks(res.items);
      setTotal(res.total);
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, hardwareFilter, search]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleDelete = async (id: number) => {
    try {
      await deleteTask(id);
      message.success('任务已删除');
      fetchTasks();
    } catch {
      message.error('删除失败');
    }
  };

  const columns: ColumnsType<AdaptationTask> = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      width: 240,
      render: (text: string, record: AdaptationTask) => (
        <Button
          type="link"
          onClick={() => navigate(`/tasks/${record.id}`)}
          style={{ padding: 0, textAlign: 'left' }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '模型标识',
      dataIndex: 'model_identifier',
      key: 'model_identifier',
      ellipsis: true,
      width: 220,
    },
    {
      title: '硬件型号',
      dataIndex: 'hardware_model',
      key: 'hardware_model',
      width: 150,
    },
    {
      title: '推理引擎',
      dataIndex: 'engine',
      key: 'engine',
      width: 120,
      render: (val: string | null) => val || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: TaskStatus) => (
        <Tag color={statusColorMap[status] || 'default'}>
          {statusLabelMap[status] || status}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (val: string) =>
        val ? new Date(val).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_: unknown, record: AdaptationTask) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'view',
                label: '查看详情',
                icon: <EyeOutlined />,
                onClick: () => navigate(`/tasks/${record.id}`),
              },
              {
                key: 'continue',
                label: '继续执行',
                icon: <PlayCircleOutlined />,
                onClick: () => navigate(`/tasks/${record.id}`),
              },
              { type: 'divider' },
              {
                key: 'delete',
                label: (
                  <Popconfirm
                    title="确认删除此任务？"
                    onConfirm={() => handleDelete(record.id)}
                    okText="删除"
                    cancelText="取消"
                    okButtonProps={{ danger: true }}
                  >
                    <span style={{ color: '#ff4d4f' }}>删除</span>
                  </Popconfirm>
                ),
                icon: <DeleteOutlined style={{ color: '#ff4d4f' }} />,
              },
            ],
          }}
          trigger={['click']}
        >
          <Button type="link" size="small">
            操作 <DownOutlined />
          </Button>
        </Dropdown>
      ),
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
        适配任务
      </Title>

      {/* Guide Card */}
      <Card
        style={{ marginBottom: 16 }}
        bodyStyle={{ padding: '12px 20px' }}
      >
        <Text type="secondary">
          输入一个模型名称/链接 + 一个硬件型号，系统自动完成从模型解析、权重下载、镜像生成到部署验证的全流程
        </Text>
      </Card>

      {/* Action Bar */}
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <Space wrap>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/tasks/create')}
          >
            新建任务
          </Button>
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={statusOptions}
            style={{ width: 140 }}
          />
          <Select
            value={hardwareFilter}
            onChange={setHardwareFilter}
            options={hardwareFilterOptions}
            style={{ width: 160 }}
          />
          <Input
            placeholder="搜索任务名称"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onPressEnter={fetchTasks}
            style={{ width: 200 }}
            allowClear
          />
        </Space>
        <Button icon={<ReloadOutlined />} onClick={fetchTasks}>
          刷新
        </Button>
      </div>

      {/* Table */}
      <Card bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1100 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showTotal: (t) => `共 ${t} 项`,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'],
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
          locale={{ emptyText: '暂无适配任务' }}
        />
      </Card>
    </div>
  );
}
