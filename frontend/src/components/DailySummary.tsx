/**
 * 每日摘要组件
 */
import { useState } from 'react';
import {
  Card,
  Button,
  List,
  Typography,
  Space,
  Tag,
  Modal,
  Form,
  InputNumber,
  Radio,
  message,
} from 'antd';
import { FileTextOutlined, PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import dayjs from 'dayjs';

const { Title, Paragraph } = Typography;

export default function DailySummary() {
  const [generateModalVisible, setGenerateModalVisible] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: summaries, isLoading } = useQuery({
    queryKey: ['summaries'],
    queryFn: () => apiService.getSummaries(50),
  });

  const generateMutation = useMutation({
    mutationFn: (data: { summary_type: string; limit: number; hours: number }) =>
      apiService.generateSummary(data),
    onSuccess: () => {
      message.success('摘要生成成功');
      setGenerateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['summaries'] });
    },
    onError: () => {
      message.error('生成摘要失败');
    },
  });

  const handleGenerate = (values: any) => {
    generateMutation.mutate(values);
  };

  return (
    <div>
      <Card
        title="📊 每日/每周总结"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setGenerateModalVisible(true)}
          >
            生成新摘要
          </Button>
        }
      >
        {isLoading ? (
          <div>加载中...</div>
        ) : !summaries || summaries.length === 0 ? (
          <div>暂无摘要</div>
        ) : (
          <List
            dataSource={summaries}
            renderItem={(summary) => (
              <List.Item>
                <Card style={{ width: '100%' }}>
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div>
                      <Title level={5}>
                        {summary.summary_type === 'daily' ? '每日' : '每周'}摘要 -{' '}
                        {dayjs(summary.summary_date).format('YYYY-MM-DD')}
                      </Title>
                      <Space>
                        <Tag>文章数: {summary.total_articles}</Tag>
                        <Tag color="red">高重要性: {summary.high_importance_count}</Tag>
                        <Tag color="orange">中重要性: {summary.medium_importance_count}</Tag>
                      </Space>
                    </div>
                    <Paragraph>{summary.summary_content}</Paragraph>
                    {summary.key_topics && summary.key_topics.length > 0 && (
                      <div>
                        <strong>关键主题：</strong>
                        {summary.key_topics.map((topic, index) => (
                          <Tag key={index} style={{ marginBottom: 4 }}>
                            {topic}
                          </Tag>
                        ))}
                      </div>
                    )}
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        )}
      </Card>

      <Modal
        title="生成新摘要"
        open={generateModalVisible}
        onCancel={() => setGenerateModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={generateMutation.isPending}
      >
        <Form form={form} onFinish={handleGenerate} layout="vertical">
          <Form.Item
            name="summary_type"
            label="摘要类型"
            initialValue="daily"
            rules={[{ required: true }]}
          >
            <Radio.Group>
              <Radio value="daily">每日</Radio>
              <Radio value="weekly">每周</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item
            name="limit"
            label="文章数量"
            initialValue={20}
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={50} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="hours"
            label="时间范围（小时）"
            initialValue={24}
            rules={[{ required: true }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

