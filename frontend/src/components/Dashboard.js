import React, { useEffect, useState } from 'react';
import { Button, Statistic, Row, Col, Card } from 'antd';
import {
  ShoppingCartOutlined,
  SettingOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_orders: 0,
    new_orders: 0,
    active_orders: 0
  });
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/orders/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <div className="dashboard-content">
      <h1>{t('dashboard.title')}</h1>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title={t('dashboard.total_orders')}
              value={stats.total_orders}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title={t('dashboard.new_orders')}
              value={stats.new_orders}
              prefix={<ShoppingCartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title={t('dashboard.active_orders')}
              value={stats.active_orders}
              prefix={<ShoppingCartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title={t('dashboard.quick_actions')} style={{ marginTop: 24 }}>
        <Button
          type="primary"
          icon={<ShoppingCartOutlined />}
          onClick={() => navigate('/orders')}
          style={{ marginRight: 8 }}
        >
          {t('dashboard.view_orders')}
        </Button>
        <Button
          icon={<SettingOutlined />}
          onClick={() => navigate('/bot-config')}
        >
          {t('dashboard.bot_settings_btn')}
        </Button>
      </Card>
    </div>
  );
};

export default Dashboard;
