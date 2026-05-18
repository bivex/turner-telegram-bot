import React, { useState, useEffect, useContext } from 'react';
import {
  Table, Button, Select, Tag, Modal, Image, Form, Input, message,
  Space, Card, Row, Col, Statistic, Avatar, Tooltip, Badge
} from 'antd';
import {
  EyeOutlined, EditOutlined, ShoppingCartOutlined,
  UserOutlined, SyncOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import dayjs from 'dayjs';
import AuthContext from '../contexts/AuthContext';

const { Option } = Select;
const { TextArea } = Input;

const Orders = () => {
  const { loading: authLoading } = useContext(AuthContext);
  const { t } = useTranslation();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [statusFilter, setStatusFilter] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [stats, setStats] = useState({
    total_orders: 0,
    new_orders: 0,
    active_orders: 0
  });

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [pagination.current, statusFilter]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/orders/', {
        params: {
          page: pagination.current,
          limit: pagination.pageSize,
          status_filter: statusFilter
        }
      });
      setOrders(response.data);
      setPagination(prev => ({ ...prev, total: response.data.length * 5 }));
    } catch (error) {
      message.error(t('orders.err_load'));
      console.error(error);
    }
    setLoading(false);
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/orders/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await axios.put(`/api/orders/${orderId}`, { status: newStatus });
      message.success(t('orders.msg_status_updated'));
      fetchOrders();
      fetchStats();
    } catch (error) {
      message.error(t('orders.err_status'));
    }
  };

  const showOrderDetails = async (order) => {
    setSelectedOrder(order);
    setModalVisible(true);

    try {
      const response = await axios.get(`/api/orders/${order.id}/photos`);
      setPhotos(response.data.photos);
    } catch (error) {
      console.error('Error loading photos:', error);
    }
  };

  const showEditModal = (order) => {
    setSelectedOrder(order);
    setEditModalVisible(true);
  };

  const handleEditSubmit = async (values) => {
    try {
      await axios.put(`/api/orders/${selectedOrder.id}`, values);
      message.success(t('orders.msg_order_updated'));
      setEditModalVisible(false);
      fetchOrders();
    } catch (error) {
      message.error(t('orders.err_update'));
    }
  };

  const columns = [
    {
      title: t('orders.col_id'),
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: t('orders.col_client'),
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>{text}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>@{record.username}</div>
          </div>
        </Space>
      ),
    },
    {
      title: t('orders.col_work_type'),
      dataIndex: 'work_type',
      key: 'work_type',
      render: (text) => text || '-',
    },
    {
      title: t('orders.col_urgency'),
      dataIndex: 'urgency',
      key: 'urgency',
      render: (text) => {
        const urgencyColors = {
          'red': 'red',
          'orange': 'orange',
          'green': 'green'
        };
        return <Tag color={urgencyColors[text] || 'default'}>{text || '-'}</Tag>;
      },
    },
    {
      title: t('orders.col_status'),
      dataIndex: 'status',
      key: 'status',
      render: (status, record) => (
        <Select
          value={status}
          style={{ width: 140 }}
          onChange={(value) => handleStatusChange(record.id, value)}
        >
          <Option value="new">{t('orders.status_new')}</Option>
          <Option value="discussion">{t('orders.status_discussion')}</Option>
          <Option value="approved">{t('orders.status_approved')}</Option>
          <Option value="work">{t('orders.status_work')}</Option>
          <Option value="done">{t('orders.status_done')}</Option>
          <Option value="rejected">{t('orders.status_rejected')}</Option>
        </Select>
      ),
    },
    {
      title: t('orders.col_date'),
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('DD.MM.YYYY HH:mm'),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
    },
    {
      title: t('orders.col_actions'),
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title={t('orders.btn_view')}>
            <Button
              icon={<EyeOutlined />}
              onClick={() => showOrderDetails(record)}
            />
          </Tooltip>
          <Tooltip title={t('orders.btn_edit')}>
            <Button
              icon={<EditOutlined />}
              onClick={() => showEditModal(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="orders-content">
      <h1>{t('orders.title')}</h1>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title={t('dashboard.total_orders')}
              value={stats.total_orders}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title={t('dashboard.new_orders')}
              value={stats.new_orders}
              prefix={<Badge dot status="success"><ShoppingCartOutlined /></Badge>}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title={t('dashboard.active_orders')}
              value={stats.active_orders}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>{t('orders.filter_label')}</span>
          <Select
            allowClear
            placeholder={t('orders.all_statuses')}
            style={{ width: 200 }}
            value={statusFilter}
            onChange={setStatusFilter}
          >
            <Option value="new">{t('orders.filter_new')}</Option>
            <Option value="discussion">{t('orders.filter_discussion')}</Option>
            <Option value="approved">{t('orders.filter_approved')}</Option>
            <Option value="work">{t('orders.filter_work')}</Option>
            <Option value="done">{t('orders.filter_done')}</Option>
            <Option value="rejected">{t('orders.filter_rejected')}</Option>
          </Select>
          <Button onClick={fetchOrders}>{t('orders.refresh')}</Button>
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={orders}
        rowKey="id"
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => t('orders.pagination', { from: range[0], to: range[1], total }),
        }}
        onChange={(pagination) => setPagination(pagination)}
      />

      <Modal
        title={selectedOrder ? t('orders.order_number', { id: selectedOrder.id }) : ''}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedOrder && (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <h3>{t('orders.client_info')}</h3>
                <p><strong>{t('orders.name_label')}</strong> {selectedOrder.full_name}</p>
                <p><strong>Username:</strong> @{selectedOrder.username}</p>
                <p><strong>Telegram ID:</strong> {selectedOrder.user_id}</p>
              </Col>
              <Col span={12}>
                <h3>{t('orders.order_details')}</h3>
                <p><strong>{t('orders.work_type')}</strong> {selectedOrder.work_type}</p>
                <p><strong>{t('orders.dimensions')}</strong> {selectedOrder.dimensions_info}</p>
                <p><strong>{t('orders.conditions')}</strong> {selectedOrder.conditions}</p>
                <p><strong>{t('orders.urgency')}</strong> {selectedOrder.urgency}</p>
              </Col>
            </Row>

            <div style={{ marginTop: 16 }}>
              <h3>{t('orders.comment')}</h3>
              <p>{selectedOrder.comment || t('orders.no_comment')}</p>
            </div>

            {photos.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h3>{t('orders.photos')}</h3>
                <div className="photo-gallery">
                  {photos.map((photoId, index) => (
                    <Image
                      key={index}
                      src={photoId}
                      alt={t('orders.photo_alt', { index: index + 1 })}
                      className="photo-item"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal
        title={selectedOrder ? t('orders.edit_title', { id: selectedOrder.id }) : ''}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        {selectedOrder && (
          <Form
            layout="vertical"
            onFinish={handleEditSubmit}
            initialValues={{
              status: selectedOrder.status,
              internal_note: selectedOrder.internal_note || ''
            }}
          >
            <Form.Item
              name="status"
              label={t('orders.status_label')}
              rules={[{ required: true }]}
            >
              <Select>
                <Option value="new">{t('orders.edit_status_new')}</Option>
                <Option value="discussion">{t('orders.edit_status_discussion')}</Option>
                <Option value="approved">{t('orders.edit_status_approved')}</Option>
                <Option value="work">{t('orders.edit_status_work')}</Option>
                <Option value="done">{t('orders.edit_status_done')}</Option>
                <Option value="rejected">{t('orders.edit_status_rejected')}</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="internal_note"
              label={t('orders.internal_note')}
            >
              <TextArea rows={4} placeholder={t('orders.note_placeholder')} />
            </Form.Item>

            <Form.Item style={{ textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setEditModalVisible(false)}>
                  {t('cancel')}
                </Button>
                <Button type="primary" htmlType="submit">
                  {t('save')}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
};

export default Orders;
