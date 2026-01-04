/**
 * RAG AI对话组件
 */
import { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, List, Typography, Empty, Spin, Alert, Space, Tag, Avatar, Select } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, LinkOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { apiService } from '@/services/api';
import type { RAGQueryRequest, RAGQueryResponse, ArticleSearchResult } from '@/types';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  articles?: ArticleSearchResult[];
  sources?: string[];
}

export default function RAGChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [topK, setTopK] = useState(5);

  // 问答mutation
  const queryMutation = useMutation({
    mutationFn: (request: RAGQueryRequest) => apiService.queryArticles(request),
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim() || queryMutation.isPending) {
      return;
    }

    const question = inputValue.trim();
    setInputValue('');

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // 发送请求
    const request: RAGQueryRequest = {
      question,
      top_k: topK,
    };

    queryMutation.mutate(request, {
      onSuccess: (response: RAGQueryResponse) => {
        // 添加AI回复
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: response.answer,
          timestamp: new Date(),
          articles: response.articles,
          sources: response.sources,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      },
      onError: (error) => {
        // 添加错误消息
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `抱歉，处理您的问题时出现错误：${error instanceof Error ? error.message : '未知错误'}`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      },
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const importanceColors: Record<string, string> = {
    high: 'red',
    medium: 'orange',
    low: 'green',
  };

  return (
    <Card
      title="💬 AI智能问答"
      extra={
        <Space>
          <Text type="secondary">检索数量：</Text>
          <Select
            value={topK}
            onChange={setTopK}
            style={{ width: 80 }}
            options={[
              { label: '3', value: 3 },
              { label: '5', value: 5 },
              { label: '10', value: 10 },
            ]}
          />
        </Space>
      }
      style={{ minHeight: 600 }}
    >
        {/* 消息列表 */}
        <div
          style={{
            maxHeight: '500px',
            overflowY: 'auto',
            marginBottom: 16,
            padding: '0 8px',
          }}
        >
          {messages.length === 0 ? (
            <Empty
              description="开始与AI对话，询问关于文章内容的问题"
              style={{ marginTop: 100 }}
            />
          ) : (
            <List
              dataSource={messages}
              renderItem={(message) => (
                <List.Item style={{ border: 'none', padding: '12px 0' }}>
                  <div
                    style={{
                      width: '100%',
                      display: 'flex',
                      flexDirection: message.type === 'user' ? 'row-reverse' : 'row',
                      gap: 12,
                    }}
                  >
                    <Avatar
                      icon={message.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                      style={{
                        backgroundColor: message.type === 'user' ? '#1890ff' : '#52c41a',
                        flexShrink: 0,
                      }}
                    />
                    <div
                      style={{
                        flex: 1,
                        maxWidth: '75%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: message.type === 'user' ? 'flex-end' : 'flex-start',
                      }}
                    >
                      <div
                        style={{
                          backgroundColor: message.type === 'user' ? '#1890ff' : '#f0f0f0',
                          color: message.type === 'user' ? '#fff' : '#000',
                          padding: '12px 16px',
                          borderRadius: '12px',
                          wordBreak: 'break-word',
                        }}
                      >
                        {message.type === 'assistant' ? (
                          <div>
                            <ReactMarkdown
                              components={{
                                p: ({ children }) => <p style={{ marginBottom: '0.5em', marginTop: 0 }}>{children}</p>,
                                strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
                                em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
                                ul: ({ children }) => <ul style={{ marginBottom: '0.5em', paddingLeft: '1.5em' }}>{children}</ul>,
                                ol: ({ children }) => <ol style={{ marginBottom: '0.5em', paddingLeft: '1.5em' }}>{children}</ol>,
                                li: ({ children }) => <li style={{ marginBottom: '0.25em' }}>{children}</li>,
                                code: ({ children }) => (
                                  <code
                                    style={{
                                      backgroundColor: 'rgba(0, 0, 0, 0.1)',
                                      padding: '2px 4px',
                                      borderRadius: '3px',
                                      fontSize: '0.9em',
                                    }}
                                  >
                                    {children}
                                  </code>
                                ),
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <Text style={{ color: message.type === 'user' ? '#fff' : '#000' }}>
                            {message.content}
                          </Text>
                        )}
                      </div>

                      {/* 引用来源 */}
                      {message.type === 'assistant' && message.articles && message.articles.length > 0 && (
                        <div style={{ marginTop: 12, width: '100%' }}>
                          <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
                            参考来源：
                          </Text>
                          <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            {message.articles.map((article, idx) => (
                              <Card
                                key={idx}
                                size="small"
                                style={{
                                  backgroundColor: '#fafafa',
                                  border: '1px solid #e8e8e8',
                                }}
                              >
                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                                    {article.importance && (
                                      <Tag color={importanceColors[article.importance]}>
                                        {article.importance === 'high' ? '高' : article.importance === 'medium' ? '中' : '低'}
                                      </Tag>
                                    )}
                                    <Tag color="blue">{article.source}</Tag>
                                  </div>
                                  <Title level={5} style={{ marginBottom: 4, fontSize: 14 }}>
                                    {article.title_zh || article.title}
                                  </Title>
                                  {article.summary && (
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                      {article.summary.length > 100
                                        ? `${article.summary.substring(0, 100)}...`
                                        : article.summary}
                                    </Text>
                                  )}
                                  <Button
                                    type="link"
                                    icon={<LinkOutlined />}
                                    href={article.url}
                                    target="_blank"
                                    size="small"
                                    style={{ padding: 0 }}
                                  >
                                    查看原文
                                  </Button>
                                </Space>
                              </Card>
                            ))}
                          </Space>
                        </div>
                      )}

                      <Text
                        type="secondary"
                        style={{
                          fontSize: 11,
                          marginTop: 4,
                          textAlign: message.type === 'user' ? 'right' : 'left',
                        }}
                      >
                        {dayjs(message.timestamp).format('HH:mm:ss')}
                      </Text>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          )}
          {queryMutation.isPending && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0' }}>
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a', flexShrink: 0 }} />
              <div style={{ backgroundColor: '#f0f0f0', padding: '12px 16px', borderRadius: '12px' }}>
                <Spin size="small" /> <Text style={{ marginLeft: 8 }}>正在思考...</Text>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div>
          {queryMutation.error && (
            <Alert
              message="请求失败"
              description={queryMutation.error instanceof Error ? queryMutation.error.message : '未知错误'}
              type="error"
              showIcon
              style={{ marginBottom: 12 }}
            />
          )}
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onPressEnter={handleKeyPress}
              placeholder="输入您的问题，例如：最近有哪些关于大语言模型的重要突破？"
              autoSize={{ minRows: 2, maxRows: 4 }}
              disabled={queryMutation.isPending}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={queryMutation.isPending}
              disabled={!inputValue.trim()}
              style={{ height: 'auto' }}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
    </Card>
  );
}
