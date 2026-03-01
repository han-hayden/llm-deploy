import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Breadcrumb,
  Typography,
  Space,
  message,
  Spin,
} from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import { createTask, getHardwareCompatibility } from '../../api/client';
import type { CreateTaskRequest, HardwareChipGroupOption } from '../../types';

const { Title, Text } = Typography;

export default function TaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [chipOptions, setChipOptions] = useState<HardwareChipGroupOption[]>([]);
  const [chipLoading, setChipLoading] = useState(false);

  useEffect(() => {
    setChipLoading(true);
    getHardwareCompatibility()
      .then((res) => {
        const groups: HardwareChipGroupOption[] = res.vendors.map((v) => ({
          vendor: v.name,
          vendor_slug: v.slug,
          chips: v.chips.map((c) => ({
            label: `${v.name} ${c.model} ${c.memory_gb}G`,
            value: `${c.model} ${c.memory_gb}G`,
          })),
        }));
        setChipOptions(groups);
      })
      .catch(() => {
        // Provide fallback options if API fails
        setChipOptions([
          {
            vendor: 'NVIDIA',
            vendor_slug: 'nvidia' as HardwareChipGroupOption['vendor_slug'],
            chips: [
              { label: 'NVIDIA H100 80G', value: 'H100 80G' },
              { label: 'NVIDIA A100 80G', value: 'A100 80G' },
              { label: 'NVIDIA A100 40G', value: 'A100 40G' },
            ],
          },
          {
            vendor: '华为昇腾',
            vendor_slug: 'huawei' as HardwareChipGroupOption['vendor_slug'],
            chips: [
              { label: '华为昇腾 910B3 64G', value: '昇腾910B3 64G' },
              { label: '华为昇腾 910B4 64G', value: '昇腾910B4 64G' },
              { label: '华为昇腾 910C 128G', value: '昇腾910C 128G' },
            ],
          },
          {
            vendor: '海光 DCU',
            vendor_slug: 'hygon' as HardwareChipGroupOption['vendor_slug'],
            chips: [
              { label: '海光 K100_AI 64G', value: 'K100_AI 64G' },
            ],
          },
          {
            vendor: '沐曦 MetaX',
            vendor_slug: 'metax' as HardwareChipGroupOption['vendor_slug'],
            chips: [
              { label: '沐曦 N260', value: 'N260' },
              { label: '沐曦 C500', value: 'C500' },
              { label: '沐曦 C550', value: 'C550' },
            ],
          },
          {
            vendor: '百度昆仑芯',
            vendor_slug: 'kunlunxin' as HardwareChipGroupOption['vendor_slug'],
            chips: [
              { label: '昆仑芯 R200', value: 'R200' },
              { label: '昆仑芯 R300', value: 'R300' },
            ],
          },
          {
            vendor: '天数智芯',
            vendor_slug: 'iluvatar' as HardwareChipGroupOption['vendor_slug'],
            chips: [
              { label: '天数智芯 BI-150', value: 'BI-150' },
              { label: '天数智芯 MR-V100', value: 'MR-V100' },
            ],
          },
        ]);
      })
      .finally(() => setChipLoading(false));
  }, []);

  const handleSubmit = async (values: CreateTaskRequest) => {
    setLoading(true);
    try {
      const task = await createTask(values);
      message.success('适配任务创建成功，正在解析...');
      navigate(`/tasks/${task.id}`);
    } catch {
      message.error('创建失败，请检查输入');
    } finally {
      setLoading(false);
    }
  };

  const selectOptions = chipOptions.map((group) => ({
    label: group.vendor,
    options: group.chips,
  }));

  return (
    <div>
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          {
            href: '/',
            title: <HomeOutlined />,
          },
          {
            href: '/tasks',
            title: '适配任务',
          },
          {
            title: '新建适配任务',
          },
        ]}
      />

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
        新建适配任务
      </Title>

      <Card title="模型信息" style={{ maxWidth: 720 }}>
        <Spin spinning={chipLoading}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            requiredMark="optional"
          >
            <Form.Item
              name="model_identifier"
              label="模型标识"
              rules={[
                { required: true, message: '请输入模型标识' },
                { max: 256, message: '最多 256 个字符' },
              ]}
              extra={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  支持模型名称（如 Qwen/Qwen2.5-72B-Instruct）或 HuggingFace / ModelScope 链接
                </Text>
              }
            >
              <Input
                placeholder="Qwen/Qwen2.5-72B-Instruct 或 https://huggingface.co/..."
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="hardware_model"
              label="硬件型号"
              rules={[{ required: true, message: '请选择或输入硬件型号' }]}
            >
              <Select
                showSearch
                placeholder="请选择或输入硬件型号"
                size="large"
                options={selectOptions}
                filterOption={(input, option) =>
                  (option?.label as string)
                    ?.toLowerCase()
                    .includes(input.toLowerCase()) ?? false
                }
              />
            </Form.Item>

            <Form.Item
              name="task_name"
              label="任务名称"
              extra={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  选填，不填则自动生成（格式：模型_硬件_日期）
                </Text>
              }
              rules={[{ max: 64, message: '最多 64 个字符' }]}
            >
              <Input placeholder="自动生成" size="large" />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  size="large"
                >
                  开始解析
                </Button>
                <Button size="large" onClick={() => navigate('/tasks')}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  );
}
