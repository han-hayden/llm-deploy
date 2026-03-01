import { Typography, Tooltip } from 'antd';
import type { MemoryAllocation } from '../types';

const { Text } = Typography;

interface MemoryChartProps {
  allocation: MemoryAllocation;
}

interface SegmentData {
  label: string;
  value: number;
  color: string;
}

export default function MemoryChart({ allocation }: MemoryChartProps) {
  const total = allocation.total_per_gpu_gb;
  if (total <= 0) return null;

  const segments: SegmentData[] = [
    { label: '权重', value: allocation.weight_gb, color: '#1677FF' },
    { label: 'KV Cache', value: allocation.kv_cache_gb, color: '#52C41A' },
    { label: '运行时', value: allocation.runtime_gb, color: '#FAAD14' },
    { label: '预留', value: allocation.reserved_gb, color: '#D9D9D9' },
  ];

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <Text type="secondary">
          每卡 {total} GB 显存分配：
        </Text>
      </div>

      {/* Stacked Bar */}
      <div
        style={{
          display: 'flex',
          height: 32,
          borderRadius: 4,
          overflow: 'hidden',
          background: '#f0f0f0',
          marginBottom: 12,
        }}
      >
        {segments.map((seg) => {
          const pct = (seg.value / total) * 100;
          if (pct <= 0) return null;
          return (
            <Tooltip
              key={seg.label}
              title={`${seg.label}: ${seg.value.toFixed(1)} GB (${pct.toFixed(0)}%)`}
            >
              <div
                style={{
                  width: `${pct}%`,
                  background: seg.color,
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: pct > 8 ? undefined : 0,
                  transition: 'width 0.3s',
                }}
              >
                {pct > 10 && (
                  <Text
                    style={{
                      color: seg.color === '#D9D9D9' ? '#595959' : '#fff',
                      fontSize: 11,
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {pct.toFixed(0)}%
                  </Text>
                )}
              </div>
            </Tooltip>
          );
        })}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        {segments.map((seg) => (
          <div
            key={seg.label}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: 2,
                background: seg.color,
              }}
            />
            <Text style={{ fontSize: 13 }}>
              {seg.label} {seg.value.toFixed(1)} GB (
              {((seg.value / total) * 100).toFixed(0)}%)
            </Text>
          </div>
        ))}
      </div>
    </div>
  );
}
