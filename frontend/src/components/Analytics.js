import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, DatePicker, Spin, message, Progress
} from 'antd';
import {
  DollarOutlined, ShoppingCartOutlined, ClockCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const Analytics = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState({
    total_orders: 0,
    revenue: 0,
    avg_check: 0,
    avg_completion_hours: 0,
    by_status: {}
  });
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(30, 'day'),
    dayjs()
  ]);

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const params = {};
      if (dateRange && dateRange[0]) {
        params.date_from = dateRange[0].format('YYYY-MM-DD');
      }
      if (dateRange && dateRange[1]) {
        params.date_to = dateRange[1].format('YYYY-MM-DD');
      }
      const response = await axios.get('/api/orders/analytics', { params });
      setAnalytics(response.data);
    } catch (error) {
      message.error(t('analytics.err_load'));
      console.error(error);
    }
    setLoading(false);
  };

  const statusColors = {
    new: '#52c41a',
    discussion: '#faad14',
    approved: '#1890ff',
    work: '#722ed1',
    done: '#13c2c2',
    rejected: '#ff4d4f',
  };

  const statusLabels = {
    new: t('orders.filter_new'),
    discussion: t('orders.filter_discussion'),
    approved: t('orders.filter_approved'),
    work: t('orders.filter_work'),
    done: t('orders.filter_done'),
    rejected: t('orders.filter_rejected'),
  };

  const totalStatusOrders = Object.values(analytics.by_status || {}).reduce((sum, v) => sum + v, 0);

  return (
    <div className="analytics-content">
      <h1><BarChartOutlined /> {t('analytics.title')}</h1>

      <Card style={{ marginBottom: 24 }}>
        <span style={{ marginRight: 12 }}>{t('analytics.date_range')}:</span>
        <RangePicker
          value={dateRange}
          onChange={(dates) => setDateRange(dates)}
          format="DD.MM.YYYY"
          allowClear
        />
      </Card>

      <Spin spinning={loading}>
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('analytics.revenue')}
                value={analytics.revenue || 0}
                precision={2}
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('analytics.avg_order')}
                value={analytics.avg_check || 0}
                precision={2}
                prefix={<ShoppingCartOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('analytics.avg_time')}
                value={analytics.avg_completion_hours || 0}
                precision={1}
                prefix={<ClockCircleOutlined />}
                suffix={t('analytics.hours')}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('analytics.total_orders')}
                value={analytics.total_orders || 0}
                prefix={<ShoppingCartOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Card title={t('analytics.orders_by_status')}>
          {Object.entries(analytics.by_status || {}).map(([status, count]) => {
            const percent = totalStatusOrders > 0
              ? Math.round((count / totalStatusOrders) * 100)
              : 0;
            return (
              <div key={status} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>{statusLabels[status] || status}</span>
                  <span>{count} ({percent}%)</span>
                </div>
                <Progress
                  percent={percent}
                  showInfo={false}
                  strokeColor={statusColors[status] || '#1890ff'}
                />
              </div>
            );
          })}
        </Card>
      </Spin>
    </div>
  );
};

export default Analytics;
