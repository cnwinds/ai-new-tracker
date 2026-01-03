/**
 * 采集历史组件
 */
import { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Tag,
  Space,
  Alert,
  Modal,
  Form,
  InputNumber,
  message,
} from 'antd';
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import dayjs from 'dayjs';
import type { CollectionTask } from '@/types';

export default function CollectionHistory() {
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['collection-tasks'],
    queryFn: () => apiService.getCollectionTasks(50),
  });

  const { data: status } = useQuery({
    queryKey: ['collection-status'],
    queryFn: () => apiService.getCollectionStatus(),
    refetchInterval: 2000, // 每2秒刷新一次
  });

  const startCollectionMutation = useMutation({
    mutationFn: (enableAi: boolean) => apiService.startCollection(enableAi),
    onSuccess: () => {
      message.success('采集任务已启动');
      queryClient.invalidateQueries({ queryKey: ['collection-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['collection-status'] });
    },
    onError: () => {
      message.error('启动采集任务失败');
    },
  });

  useEffect(() => {
    const unsubscribe = subscribe('collection_status', () => {
      queryClient.invalidateQueries({ queryKey: ['collection-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['collection-status'] });
    });
    return unsubscribe;
  }, [subscribe, queryClient]);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colors: Record<string, string> = {
          running: 'processing',
          completed: 'success',
          error: 'error',
        };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: '新增文章',
      dataIndex: 'new_articles_count',
      key: 'new_articles_count',
      width: 100,
    },
    {
      title: '成功源',
      dataIndex: 'success_sources',
      key: 'success_sources',
      width: 100,
    },
    {
      title: '失败源',
      dataIndex: 'failed_sources',
      key: 'failed_sources',
      width: 100,
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (duration: number) => (duration ? `${duration.toFixed(1)}秒` : '-'),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ];

  const handleStartCollection = (enableAi: boolean) => {
    startCollectionMutation.mutate(enableAi);
  };

  return (
    <div>
      <Card
        title="🚀 采集历史"
        extra={
          <Space>
            <Button
              icon={<PlayCircleOutlined />}
              type="primary"
              onClick={() => handleStartCollection(true)}
              loading={startCollectionMutation.isPending}
              disabled={status?.status === 'running'}
            >
              开始采集（AI分析）
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => queryClient.invalidateQueries({ queryKey: ['collection-tasks'] })}
            >
              刷新
            </Button>
          </Space>
        }
      >
        {status && status.status === 'running' && (
          <Alert
            message={status.message}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}

