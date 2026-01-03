/**
 * 订阅源管理组件
 */
import { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Switch,
  InputNumber,
  message,
  Popconfirm,
  Checkbox,
  Divider,
  Tabs,
  Alert,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ImportOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import type { RSSSource, RSSSourceCreate, RSSSourceUpdate } from '@/types';

export default function SourceManagement() {
  const [modalVisible, setModalVisible] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [editingSource, setEditingSource] = useState<RSSSource | null>(null);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: sources, isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => apiService.getSources(),
  });

  const { data: defaultSources, isLoading: loadingDefault } = useQuery({
    queryKey: ['default-sources'],
    queryFn: () => apiService.getDefaultSources(),
    enabled: importModalVisible,
  });

  const createMutation = useMutation({
    mutationFn: (data: RSSSourceCreate) => apiService.createSource(data),
    onSuccess: () => {
      message.success('订阅源创建成功');
      setModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
    onError: () => {
      message.error('创建订阅源失败');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: RSSSourceUpdate }) =>
      apiService.updateSource(id, data),
    onSuccess: () => {
      message.success('订阅源更新成功');
      setModalVisible(false);
      setEditingSource(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
    onError: () => {
      message.error('更新订阅源失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiService.deleteSource(id),
    onSuccess: () => {
      message.success('订阅源已删除');
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
    onError: () => {
      message.error('删除订阅源失败');
    },
  });

  const importMutation = useMutation({
    mutationFn: (sourceNames: string[]) => apiService.importDefaultSources(sourceNames),
    onSuccess: (data) => {
      message.success(
        `导入完成：成功 ${data.imported} 个，跳过 ${data.skipped} 个${data.errors ? `，错误 ${data.errors.length} 个` : ''}`
      );
      setImportModalVisible(false);
      setSelectedSources([]);
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
    onError: () => {
      message.error('导入失败');
    },
  });

  const handleAdd = () => {
    setEditingSource(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (source: RSSSource) => {
    setEditingSource(source);
    form.setFieldsValue(source);
    setModalVisible(true);
  };

  const handleSubmit = (values: any) => {
    if (editingSource) {
      updateMutation.mutate({ id: editingSource.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleImport = () => {
    if (selectedSources.length === 0) {
      message.warning('请至少选择一个要导入的源');
      return;
    }
    importMutation.mutate(selectedSources);
  };

  // 按类型分组默认源
  const groupedSources = defaultSources?.reduce((acc: any, source: any) => {
    const type = source.source_type || 'rss';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(source);
    return acc;
  }, {}) || {};

  // 检查源是否已存在
  const isSourceExists = (sourceName: string, sourceUrl: string) => {
    return sources?.some(
      (s) => s.name === sourceName || s.url === sourceUrl
    ) || false;
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'red'}>{enabled ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '文章数',
      dataIndex: 'articles_count',
      key: 'articles_count',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: RSSSource) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个订阅源吗？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="⚙️ 订阅源管理"
        extra={
          <Space>
            <Button icon={<ImportOutlined />} onClick={() => setImportModalVisible(true)}>
              导入默认源
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加订阅源
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={sources}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingSource ? '编辑订阅源' : '添加订阅源'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingSource(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="url" label="URL" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="category" label="分类">
            <Input />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={1}>
            <InputNumber min={1} max={5} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入默认源对话框 */}
      <Modal
        title="导入默认数据源"
        open={importModalVisible}
        onCancel={() => {
          setImportModalVisible(false);
          setSelectedSources([]);
        }}
        onOk={handleImport}
        confirmLoading={importMutation.isPending}
        width={800}
        okText="导入选中"
        cancelText="取消"
      >
        {loadingDefault ? (
          <div>加载中...</div>
        ) : !defaultSources || defaultSources.length === 0 ? (
          <Alert message="没有可用的默认数据源" type="info" />
        ) : (
          <div>
            <Alert
              message="提示"
              description="选择要导入的数据源。已存在的源将被跳过。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Checkbox
              checked={selectedSources.length === defaultSources.length}
              indeterminate={
                selectedSources.length > 0 && selectedSources.length < defaultSources.length
              }
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedSources(defaultSources.map((s: any) => s.name));
                } else {
                  setSelectedSources([]);
                }
              }}
              style={{ marginBottom: 16 }}
            >
              全选 ({selectedSources.length}/{defaultSources.length})
            </Checkbox>
            <Divider />
            <Tabs
              items={[
                {
                  key: 'rss',
                  label: `RSS源 (${groupedSources.rss?.length || 0})`,
                  children: (
                    <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                      {groupedSources.rss?.map((source: any) => {
                        const exists = isSourceExists(source.name, source.url);
                        return (
                          <div key={source.name} style={{ marginBottom: 8 }}>
                            <Checkbox
                              checked={selectedSources.includes(source.name)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedSources([...selectedSources, source.name]);
                                } else {
                                  setSelectedSources(selectedSources.filter((n) => n !== source.name));
                                }
                              }}
                              disabled={exists}
                            >
                              <Space>
                                <strong>{source.name}</strong>
                                {exists && <Tag color="orange">已存在</Tag>}
                                <Tag>{source.category}</Tag>
                                {!source.enabled && <Tag color="red">禁用</Tag>}
                              </Space>
                            </Checkbox>
                            <div style={{ marginLeft: 24, fontSize: 12, color: '#666' }}>
                              {source.url}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ),
                },
                {
                  key: 'api',
                  label: `API源 (${groupedSources.api?.length || 0})`,
                  children: (
                    <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                      {groupedSources.api?.map((source: any) => {
                        const exists = isSourceExists(source.name, source.url);
                        return (
                          <div key={source.name} style={{ marginBottom: 8 }}>
                            <Checkbox
                              checked={selectedSources.includes(source.name)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedSources([...selectedSources, source.name]);
                                } else {
                                  setSelectedSources(selectedSources.filter((n) => n !== source.name));
                                }
                              }}
                              disabled={exists}
                            >
                              <Space>
                                <strong>{source.name}</strong>
                                {exists && <Tag color="orange">已存在</Tag>}
                                <Tag>{source.category}</Tag>
                                {!source.enabled && <Tag color="red">禁用</Tag>}
                              </Space>
                            </Checkbox>
                            <div style={{ marginLeft: 24, fontSize: 12, color: '#666' }}>
                              {source.url}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ),
                },
                {
                  key: 'web',
                  label: `Web源 (${groupedSources.web?.length || 0})`,
                  children: (
                    <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                      {groupedSources.web?.map((source: any) => {
                        const exists = isSourceExists(source.name, source.url);
                        return (
                          <div key={source.name} style={{ marginBottom: 8 }}>
                            <Checkbox
                              checked={selectedSources.includes(source.name)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedSources([...selectedSources, source.name]);
                                } else {
                                  setSelectedSources(selectedSources.filter((n) => n !== source.name));
                                }
                              }}
                              disabled={exists}
                            >
                              <Space>
                                <strong>{source.name}</strong>
                                {exists && <Tag color="orange">已存在</Tag>}
                                <Tag>{source.category}</Tag>
                                {!source.enabled && <Tag color="red">禁用</Tag>}
                              </Space>
                            </Checkbox>
                            <div style={{ marginLeft: 24, fontSize: 12, color: '#666' }}>
                              {source.url}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ),
                },
                {
                  key: 'social',
                  label: `社交媒体源 (${groupedSources.social?.length || 0})`,
                  children: (
                    <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                      {groupedSources.social?.map((source: any) => {
                        const exists = isSourceExists(source.name, source.url);
                        return (
                          <div key={source.name} style={{ marginBottom: 8 }}>
                            <Checkbox
                              checked={selectedSources.includes(source.name)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedSources([...selectedSources, source.name]);
                                } else {
                                  setSelectedSources(selectedSources.filter((n) => n !== source.name));
                                }
                              }}
                              disabled={exists}
                            >
                              <Space>
                                <strong>{source.name}</strong>
                                {exists && <Tag color="orange">已存在</Tag>}
                                <Tag>{source.category}</Tag>
                                {!source.enabled && <Tag color="red">禁用</Tag>}
                              </Space>
                            </Checkbox>
                            <div style={{ marginLeft: 24, fontSize: 12, color: '#666' }}>
                              {source.url}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ),
                },
              ]}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}

