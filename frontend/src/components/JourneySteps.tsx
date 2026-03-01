import { Steps, Card } from 'antd';
import {
  FileSearchOutlined,
  CloudDownloadOutlined,
  BuildOutlined,
  RocketOutlined,
} from '@ant-design/icons';

interface JourneyStepsProps {
  currentStep: number;
  activeStep: number;
  status: 'wait' | 'process' | 'finish' | 'error';
  onStepClick: (step: number) => void;
}

const journeyItems = [
  {
    title: '适配登记',
    icon: <FileSearchOutlined />,
    description: '解析模型+硬件',
  },
  {
    title: '权重下载',
    icon: <CloudDownloadOutlined />,
    description: '下载模型权重',
  },
  {
    title: '镜像生成',
    icon: <BuildOutlined />,
    description: '推算参数+构建镜像',
  },
  {
    title: '部署启动',
    icon: <RocketOutlined />,
    description: '预检+部署+验证',
  },
];

export default function JourneySteps({
  currentStep,
  activeStep,
  status,
  onStepClick,
}: JourneyStepsProps) {
  const items = journeyItems.map((item, index) => {
    let stepStatus: 'wait' | 'process' | 'finish' | 'error' = 'wait';
    if (index < currentStep) {
      stepStatus = 'finish';
    } else if (index === currentStep) {
      stepStatus = status;
    }

    return {
      ...item,
      status: stepStatus as 'wait' | 'process' | 'finish' | 'error',
      disabled: index > currentStep,
      style: {
        cursor: index <= currentStep ? 'pointer' : 'not-allowed',
      },
    };
  });

  return (
    <Card bodyStyle={{ padding: '20px 24px' }}>
      <Steps
        current={activeStep}
        items={items}
        onChange={(step) => {
          if (step <= currentStep) {
            onStepClick(step);
          }
        }}
      />
    </Card>
  );
}
