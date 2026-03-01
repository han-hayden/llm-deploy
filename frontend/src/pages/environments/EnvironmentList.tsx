import { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Typography,
  Modal,
  Form,
  Radio,
  message,
  Popconfirm,
  Tag,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getEnvironments,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  testConnection,
} from '../../api/client';
import type { Environment } from '../../types';
import { EnvironmentType, ConnectionType } from '../../types';

const { Title, Text } = Typography;

export default function EnvironmentList() {
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEnv, setEditingEnv] = useState<Environment | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [testing, setTesting] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [form] = Form.useForm();

  const fetchEnvironments = async () => {
    setLoading(true);
    try {
      const data = await getEnvironments();
      setEnvironments(data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnvironments();
  }, []);

  const openCreate = () => {
    setEditingEnv(null);
    form.resetFields();
    form.setFieldsValue({
      env_type: EnvironmentType.DockerHost,
      connection_type: ConnectionType.SSH,
      connection_config: { port: 22, username: 'root' },
    });
    setTestResult(null);
    setModalOpen(true);
  };

  const openEdit = (env: Environment) => {
    setEditingEnv(env);
    form.setFieldsValue({
      name: env.name,
      env_type: env.env_type,
      connection_type: env.connection_type,
      connection_config: env.connection_config,
    });
    setTestResult(null);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editingEnv) {
        await updateEnvironment(editingEnv.id, values);
        message.success('环境已更新');
      } else {
        await createEnvironment(values);
        message.success('环境已注册');
      }
      setModalOpen(false);
      fetchEnvironments();
    } catch {
      // validation error
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteEnvironment(id);
      message.success('环境已删除');
      fetchEnvironments();
    } catch {
      message.error('删除失败');
    }
  };

  const handleTest = async (id: number) => {
    setTesting(id);
    setTestResult(null);
    try {
      const result = await testConnection(id);
      setTestResult(result);
      if (result.success) {
        message.success('连接成功');
      } else {
        message.warning(`连接失败: ${result.message}`);
      }
    } catch {
      setTestResult({ success: false, message: '测试连接请求失败' });
      message.error('连接测试失败');
    } finally {
      setTesting(null);
    }
  };

  const filteredEnvs = search
    ? environments.filter((e) =>
        e.name.toLowerCase().includes(search.toLowerCase())
      )
    : environments;

  const columns: ColumnsType<Environment> = [
    {
      title: '环境名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'env_type',
      key: 'env_type',
      width: 120,
      render: (val: EnvironmentType) =>
        val === EnvironmentType.DockerHost ? (
          <Tag color="blue">Docker 主机</Tag>
        ) : (
          <Tag color="purple">K8s 集群</Tag>
        ),
    },
    {
      title: '连接方式',
      dataIndex: 'connection_type',
      key: 'connection_type',
      width: 120,
      render: (val: ConnectionType) =>
        val === ConnectionType.SSH ? 'SSH' : 'kubeconfig',
    },
    {
      title: '硬件信息',
      dataIndex: 'hardware_info',
      key: 'hardware_info',
      render: (val: Environment['hardware_info']) =>
        val ? val.description : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (val: string) => (
        <Tag color={val === 'active' ? 'success' : 'default'}>
          {val === 'active' ? '在线' : '离线'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: unknown, record: Environment) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<ApiOutlined />}
            loading={testing === record.id}
            onClick={() => handleTest(record.id)}
          >
            测试
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除此环境？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const envType = Form.useWatch('env_type', form);

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
        环境管理
      </Title>

      <Card
        style={{ marginBottom: 16 }}
        bodyStyle={{ padding: '12px 20px' }}
      >
        <Text type="secondary">
          注册目标部署环境，用于模型服务部署。支持 Docker 主机和 K8s 集群。
        </Text>
      </Card>

      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={openCreate}
          >
            注册环境
          </Button>
          <Input
            placeholder="搜索环境名称"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
        </Space>
        <Button icon={<ReloadOutlined />} onClick={fetchEnvironments}>
          刷新
        </Button>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={filteredEnvs}
          rowKey="id"
          loading={loading}
          pagination={{
            showTotal: (t) => `共 ${t} 项`,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'],
          }}
          locale={{ emptyText: '暂无注册环境' }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingEnv ? '编辑环境' : '注册新环境'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        okText="确定"
        cancelText="取消"
        width={520}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            env_type: EnvironmentType.DockerHost,
            connection_type: ConnectionType.SSH,
            connection_config: { port: 22, username: 'root' },
          }}
        >
          <Form.Item
            name="name"
            label="环境名称"
            rules={[{ required: true, message: '请输入环境名称' }]}
          >
            <Input placeholder="例如 prod-ascend-01" />
          </Form.Item>

          <Form.Item name="env_type" label="环境类型">
            <Radio.Group>
              <Radio value={EnvironmentType.DockerHost}>Docker 主机</Radio>
              <Radio value={EnvironmentType.K8sCluster}>K8s 集群</Radio>
            </Radio.Group>
          </Form.Item>

          {envType === EnvironmentType.DockerHost && (
            <>
              <Form.Item
                name={['connection_config', 'host']}
                label="SSH 地址"
                rules={[{ required: true, message: '请输入 SSH 地址' }]}
              >
                <Input placeholder="10.0.1.100" />
              </Form.Item>
              <Form.Item
                name={['connection_config', 'port']}
                label="SSH 端口"
              >
                <Input type="number" placeholder="22" />
              </Form.Item>
              <Form.Item
                name={['connection_config', 'username']}
                label="SSH 用户"
                rules={[{ required: true, message: '请输入 SSH 用户名' }]}
              >
                <Input placeholder="root" />
              </Form.Item>
              <Form.Item
                name={['connection_config', 'password']}
                label="密码"
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
            </>
          )}

          {envType === EnvironmentType.K8sCluster && (
            <Form.Item
              name={['connection_config', 'kubeconfig']}
              label="Kubeconfig"
              rules={[{ required: true, message: '请输入 kubeconfig 内容' }]}
            >
              <Input.TextArea
                rows={8}
                placeholder="粘贴 kubeconfig 文件内容"
              />
            </Form.Item>
          )}

          {testResult && (
            <div style={{ marginTop: 8 }}>
              {testResult.success ? (
                <Tag color="success">连接成功</Tag>
              ) : (
                <Tag color="error">连接失败: {testResult.message}</Tag>
              )}
            </div>
          )}
        </Form>
      </Modal>
    </div>
  );
}
