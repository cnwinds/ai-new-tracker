/**
 * 数据清理组件
 */
import { useState } from 'react';
import { Card, Form, InputNumber, Switch, Button, message, Alert } from 'antd';
import { useMutation } from '@tanstack/react-query';
import { apiService } from '@/services/api';

export default function DataCleanup() {
  const [form] = Form.useForm();

  const cleanupMutation = useMutation({
    mutationFn: (data: {
      delete_articles_older_than_days?: number;
      delete_logs_older_than_days?: number;
      delete_unanalyzed_articles?: boolean;
    }) => apiService.cleanupData(data),
    onSuccess: (data) => {
      message.success(data.message || '清理完成');
      form.resetFields();
    },
    onError: () => {
      message.error('清理失败');
    },
  });

  const handleCleanup = (values: any) => {
    cleanupMutation.mutate(values);
  };

  return (
    <div>
      <Card title="🗑️ 数据清理">
        <Alert
          message="警告"
          description="数据清理操作不可恢复，请谨慎操作！"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form form={form} onFinish={handleCleanup} layout="vertical">
          <Form.Item
            name="delete_articles_older_than_days"
            label="删除超过多少天的文章"
            help="设置为0表示不删除"
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="delete_logs_older_than_days"
            label="删除超过多少天的日志"
            help="设置为0表示不删除"
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="delete_unanalyzed_articles"
            label="删除未分析的文章"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              danger
              htmlType="submit"
              loading={cleanupMutation.isPending}
            >
              执行清理
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}


