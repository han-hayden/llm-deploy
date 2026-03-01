import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Radio,
  Input,
  Button,
  Progress,
  Space,
  Typography,
  Alert,
  message,
  Table,
  Tag,
} from 'antd';
import {
  CloudDownloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import type { AdaptationTask, DownloadFileProgress } from '../../types';
import { TaskStatus, DownloadSource, DownloadTargetType } from '../../types';
import {
  startDownload,
  getDownloadProgress,
  getDownloadByTask,
} from '../../api/client';

const { Text } = Typography;

interface J2DownloadProps {
  task: AdaptationTask;
  onRefresh: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function formatDuration(seconds: number): string {
  if (seconds <= 0) return '-';
  if (seconds < 60) return `${Math.round(seconds)} 秒`;
  if (seconds < 3600) {
    const min = Math.floor(seconds / 60);
    const sec = Math.round(seconds % 60);
    return `${min} 分 ${sec} 秒`;
  }
  const hr = Math.floor(seconds / 3600);
  const min = Math.round((seconds % 3600) / 60);
  return `${hr} 小时 ${min} 分`;
}

const fileColumns = [
  {
    title: '文件名',
    dataIndex: 'filename',
    key: 'filename',
    ellipsis: true,
  },
  {
    title: '大小',
    dataIndex: 'file_size_bytes',
    key: 'file_size_bytes',
    width: 100,
    render: (val: number) => formatBytes(val),
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 140,
    render: (status: string, record: DownloadFileProgress) => {
      if (status === 'completed') {
        return (
          <Tag icon={<CheckCircleOutlined />} color="success">
            已完成
          </Tag>
        );
      }
      if (status === 'downloading') {
        const pct =
          record.file_size_bytes > 0
            ? Math.round(
                (record.downloaded_bytes / record.file_size_bytes) * 100
              )
            : 0;
        return (
          <Tag icon={<SyncOutlined spin />} color="processing">
            下载中 ({pct}%)
          </Tag>
        );
      }
      if (status === 'failed') {
        return <Tag color="error">失败</Tag>;
      }
      return (
        <Tag icon={<ClockCircleOutlined />} color="default">
          等待中
        </Tag>
      );
    },
  },
];

export default function J2Download({ task, onRefresh }: J2DownloadProps) {
  const [source, setSource] = useState<DownloadSource>(
    DownloadSource.ModelScope
  );
  const [targetType, setTargetType] = useState<DownloadTargetType>(
    DownloadTargetType.Local
  );
  const [targetPath, setTargetPath] = useState(
    `/data/models/${task.model_identifier.replace('/', '_')}`
  );
  const [downloading, setDownloading] = useState(false);
  const [downloadId, setDownloadId] = useState<number | null>(
    task.download?.id || null
  );
  const [progress, setProgress] = useState(task.download || null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isDownloading =
    task.status === TaskStatus.Downloading ||
    progress?.status === 'downloading';
  const isCompleted =
    task.status === TaskStatus.Downloaded ||
    progress?.status === 'completed';

  const pollProgress = useCallback(async () => {
    if (downloadId) {
      try {
        const data = await getDownloadProgress(downloadId);
        setProgress(data);
        if (
          data.status === 'completed' ||
          data.status === 'failed' ||
          data.status === 'interrupted'
        ) {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          if (data.status === 'completed') {
            message.success('模型权重下载完成，SHA256 校验通过');
            onRefresh();
          }
        }
      } catch {
        // silently fail
      }
    }
  }, [downloadId, onRefresh]);

  useEffect(() => {
    // Try to load existing download
    if (!downloadId && task.status === TaskStatus.Downloading) {
      getDownloadByTask(task.id)
        .then((d) => {
          setDownloadId(d.id);
          setProgress(d);
        })
        .catch(() => {
          /* no existing download */
        });
    }
  }, [task.id, task.status, downloadId]);

  useEffect(() => {
    if (isDownloading && downloadId && !pollingRef.current) {
      pollingRef.current = setInterval(pollProgress, 2000);
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isDownloading, downloadId, pollProgress]);

  const handleStartDownload = async () => {
    setDownloading(true);
    try {
      const result = await startDownload({
        task_id: task.id,
        source,
        target_type: targetType,
        target_path: targetPath,
      });
      setDownloadId(result.id);
      setProgress(result);
      message.success('下载已启动');
      onRefresh();
    } catch {
      message.error('启动下载失败');
    } finally {
      setDownloading(false);
    }
  };

  const showConfig =
    task.status === TaskStatus.Parsed ||
    task.status === TaskStatus.Downloaded ||
    task.status === TaskStatus.Downloading ||
    task.status === TaskStatus.DownloadFailed;

  return (
    <div>
      {/* Download Config */}
      {showConfig && (
        <Card title="下载配置" style={{ marginBottom: 16 }}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                下载源
              </Text>
              <Radio.Group
                value={source}
                onChange={(e) => setSource(e.target.value)}
                disabled={isDownloading || isCompleted}
              >
                <Radio value={DownloadSource.ModelScope}>
                  ModelScope (推荐，国内网络更稳定)
                </Radio>
                <Radio value={DownloadSource.HuggingFace}>HuggingFace</Radio>
              </Radio.Group>
            </div>

            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                下载目标
              </Text>
              <Radio.Group
                value={targetType}
                onChange={(e) => setTargetType(e.target.value)}
                disabled={isDownloading || isCompleted}
              >
                <Radio value={DownloadTargetType.Local}>下载到本地</Radio>
                <Radio value={DownloadTargetType.Remote}>
                  下载到指定环境
                </Radio>
              </Radio.Group>
            </div>

            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                存储路径
              </Text>
              <Input
                value={targetPath}
                onChange={(e) => setTargetPath(e.target.value)}
                disabled={isDownloading || isCompleted}
                style={{ maxWidth: 500 }}
              />
            </div>

            {!isDownloading && !isCompleted && (
              <Button
                type="primary"
                icon={<CloudDownloadOutlined />}
                size="large"
                onClick={handleStartDownload}
                loading={downloading}
              >
                开始下载
              </Button>
            )}
          </Space>
        </Card>
      )}

      {/* Progress */}
      {(isDownloading || isCompleted || progress) && progress && (
        <Card title="下载进度" style={{ marginBottom: 16 }}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: 4,
                }}
              >
                <Text>
                  总进度{' '}
                  {progress.total_bytes > 0
                    ? `${formatBytes(progress.downloaded_bytes)} / ${formatBytes(progress.total_bytes)}`
                    : ''}
                </Text>
                <Text>
                  {Math.round(progress.progress_percent)}%
                </Text>
              </div>
              <Progress
                percent={Math.round(progress.progress_percent)}
                status={
                  progress.status === 'completed'
                    ? 'success'
                    : progress.status === 'failed' ||
                        progress.status === 'interrupted'
                      ? 'exception'
                      : 'active'
                }
                showInfo={false}
              />
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginTop: 4,
                }}
              >
                <Text type="secondary">
                  速度 {formatBytes(progress.speed_bytes_per_sec)}/s
                </Text>
                <Text type="secondary">
                  预计剩余 {formatDuration(progress.eta_seconds)}
                </Text>
              </div>
            </div>

            {progress.files && progress.files.length > 0 && (
              <Table
                columns={fileColumns}
                dataSource={progress.files}
                rowKey="id"
                size="small"
                pagination={false}
                scroll={{ y: 300 }}
              />
            )}

            {progress.status === 'completed' && (
              <Alert
                type="success"
                message="下载完成，SHA256 校验通过"
                showIcon
              />
            )}

            {(progress.status === 'failed' ||
              progress.status === 'interrupted') && (
              <Alert
                type="error"
                message="下载中断"
                description="下载过程中出现错误，支持断点续传。"
                showIcon
                action={
                  <Button type="primary" onClick={handleStartDownload}>
                    重试下载
                  </Button>
                }
              />
            )}
          </Space>
        </Card>
      )}

      {isCompleted && (
        <div style={{ textAlign: 'right' }}>
          <Button type="primary" size="large" onClick={onRefresh}>
            进入镜像生成 &rarr;
          </Button>
        </div>
      )}
    </div>
  );
}
