/**
 * 文章列表组件
 */
import { useState, useEffect } from 'react';
import { Card, Select, Radio, Space, Pagination, Spin, Empty, Alert } from 'antd';
import { useArticles } from '@/hooks/useArticles';
import ArticleCard from './ArticleCard';
import type { ArticleFilter } from '@/types';

const { Option } = Select;

export default function ArticleList() {
  const [filter, setFilter] = useState<ArticleFilter>({
    time_range: '全部',
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error, refetch } = useArticles(filter);

  const timeRanges = ['今天', '最近3天', '最近7天', '最近30天', '全部'];

  const handleTimeRangeChange = (value: string) => {
    setFilter({ ...filter, time_range: value, page: 1 });
  };

  const handlePageChange = (page: number, pageSize: number) => {
    setFilter({ ...filter, page, page_size: pageSize });
  };

  return (
    <div>
      <Card
        title="📰 最新AI资讯"
        extra={
          <Space>
            <Radio.Group
              value={filter.time_range}
              onChange={(e) => handleTimeRangeChange(e.target.value)}
              options={timeRanges.map((range) => ({ label: range, value: range }))}
              optionType="button"
              buttonStyle="solid"
            />
          </Space>
        }
      >
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" />
          </div>
        ) : error ? (
          <Alert message="加载失败" type="error" showIcon />
        ) : !data || data.items.length === 0 ? (
          <Empty description="暂无文章" />
        ) : (
          <>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <span>找到 {data.total} 篇文章</span>
              </Space>
            </div>
            {data.items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Pagination
                current={data.page}
                total={data.total}
                pageSize={data.page_size}
                showSizeChanger
                showTotal={(total) => `共 ${total} 条`}
                onChange={handlePageChange}
                onShowSizeChange={handlePageChange}
              />
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

