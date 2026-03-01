import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Breadcrumb, Typography, Spin, Alert, Space, Button } from 'antd';
import { HomeOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { getTask } from '../../api/client';
import type { AdaptationTask } from '../../types';
import { TaskStatus } from '../../types';
import JourneySteps from '../../components/JourneySteps';
import J1AdaptationResult from '../../components/journey/J1AdaptationResult';
import J2Download from '../../components/journey/J2Download';
import J3ParamAndBuild from '../../components/journey/J3ParamAndBuild';
import J4Deploy from '../../components/journey/J4Deploy';

const { Title } = Typography;

function getJourneyStep(status: TaskStatus): number {
  switch (status) {
    case TaskStatus.Created:
    case TaskStatus.Parsing:
    case TaskStatus.Parsed:
    case TaskStatus.ParseFailed:
      return 0;
    case TaskStatus.Downloading:
    case TaskStatus.Downloaded:
    case TaskStatus.DownloadFailed:
      return 1;
    case TaskStatus.Building:
    case TaskStatus.Built:
    case TaskStatus.BuildFailed:
      return 2;
    case TaskStatus.Deploying:
    case TaskStatus.Deployed:
    case TaskStatus.DeployFailed:
      return 3;
    default:
      return 0;
  }
}

function getStepStatus(
  status: TaskStatus
): 'wait' | 'process' | 'finish' | 'error' {
  if (
    status === TaskStatus.ParseFailed ||
    status === TaskStatus.DownloadFailed ||
    status === TaskStatus.BuildFailed ||
    status === TaskStatus.DeployFailed
  ) {
    return 'error';
  }
  if (status === TaskStatus.Deployed) {
    return 'finish';
  }
  return 'process';
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<AdaptationTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<number | null>(null);

  const fetchTask = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getTask(Number(id));
      setTask(data);
      setError(null);
      if (activeStep === null) {
        setActiveStep(getJourneyStep(data.status));
      }
    } catch {
      setError('无法加载任务详情');
    } finally {
      setLoading(false);
    }
  }, [id, activeStep]);

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  const refreshTask = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getTask(Number(id));
      setTask(data);
      setActiveStep(getJourneyStep(data.status));
    } catch {
      // silently fail on refresh
    }
  }, [id]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (error || !task) {
    return (
      <Alert
        type="error"
        message="加载失败"
        description={error || '任务不存在'}
        showIcon
        action={
          <Button onClick={() => navigate('/tasks')}>返回任务列表</Button>
        }
      />
    );
  }

  const currentStep = getJourneyStep(task.status);
  const displayStep = activeStep !== null ? activeStep : currentStep;
  const stepStatus = getStepStatus(task.status);

  const handleStepClick = (step: number) => {
    if (step <= currentStep) {
      setActiveStep(step);
    }
  };

  const renderJourney = () => {
    switch (displayStep) {
      case 0:
        return <J1AdaptationResult task={task} onRefresh={refreshTask} />;
      case 1:
        return <J2Download task={task} onRefresh={refreshTask} />;
      case 2:
        return <J3ParamAndBuild task={task} onRefresh={refreshTask} />;
      case 3:
        return <J4Deploy task={task} onRefresh={refreshTask} />;
      default:
        return <J1AdaptationResult task={task} onRefresh={refreshTask} />;
    }
  };

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/tasks')}
        />
        <Breadcrumb
          items={[
            { href: '/', title: <HomeOutlined /> },
            { href: '/tasks', title: '适配任务' },
            { title: task.task_name },
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
        {task.task_name}
      </Title>

      <JourneySteps
        currentStep={currentStep}
        activeStep={displayStep}
        status={stepStatus}
        onStepClick={handleStepClick}
      />

      <div style={{ marginTop: 24 }}>{renderJourney()}</div>
    </div>
  );
}
