import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, message, Space, Card, Tag,
  Avatar, Tooltip, Row, Col
} from 'antd';
import {
  TeamOutlined, UserOutlined, EditOutlined, EyeOutlined,
  PhoneOutlined, MailOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import dayjs from 'dayjs';

const Customers = () => {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [customerOrders, setCustomerOrders] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [editForm] = Form.useForm();

  useEffect(() => {
    fetchCustomers();
  }, [pagination.current]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/customers/', {
        params: {
          page: pagination.current,
          limit: pagination.pageSize
        }
      });
      setCustomers(response.data.customers);
      setPagination(prev => ({
        ...prev,
        total: response.data.total
      }));
    } catch (error) {
      message.error(t('customers.err_load'));
      console.error(error);
    }
    setLoading(false);
  };

  const showCustomerDetail = async (customer) => {
    setSelectedCustomer(customer);
    setDetailModalVisible(true);
    setDetailLoading(true);
    try {
      const response = await axios.get(`/api/customers/${customer.user_id}`);
      setCustomerOrders(response.data.orders || []);
    } catch (error) {
      console.error('Error loading customer detail:', error);
      setCustomerOrders([]);
    }
    setDetailLoading(false);
  };

  const showEditModal = (customer) => {
    setSelectedCustomer(customer);
    editForm.setFieldsValue({
      phone: customer.phone || '',
      email: customer.email || '',
      notes: customer.notes || ''
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async (values) => {
    try {
      await axios.put(`/api/customers/${selectedCustomer.user_id}`, values);
      message.success(t('customers.msg_updated'));
      setEditModalVisible(false);
      fetchCustomers();
    } catch (error) {
      message.error(t('customers.err_update'));
    }
  };

  const columns = [
    {
      title: t('customers.col_name'),
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>{text || '-'}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              @{record.username || '-'}
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: t('customers.col_phone'),
      dataIndex: 'phone',
      key: 'phone',
      render: (text) => text || <Tag>-</Tag>,
    },
    {
      title: t('customers.col_email'),
      dataIndex: 'email',
      key: 'email',
      render: (text) => text || <Tag>-</Tag>,
    },
    {
      title: t('customers.col_orders'),
      dataIndex: 'total_orders',
      key: 'total_orders',
      sorter: (a, b) => (a.total_orders || 0) - (b.total_orders || 0),
    },
    {
      title: t('customers.col_spent'),
      dataIndex: 'total_spent',
      key: 'total_spent',
      render: (value) => value ? `${Number(value).toFixed(2)}` : '0.00',
      sorter: (a, b) => (a.total_spent || 0) - (b.total_spent || 0),
    },
    {
      title: t('customers.col_last_order'),
      dataIndex: 'last_order_date',
      key: 'last_order_date',
      render: (date) => date ? dayjs(date).format('DD.MM.YYYY HH:mm') : '-',
      sorter: (a, b) => dayjs(a.last_order_date || 0).unix() - dayjs(b.last_order_date || 0).unix(),
    },
    {
      title: t('orders.col_actions'),
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title={t('orders.btn_view')}>
            <Button
              icon={<EyeOutlined />}
              onClick={() => showCustomerDetail(record)}
            />
          </Tooltip>
          <Tooltip title={t('customers.btn_edit')}>
            <Button
              icon={<EditOutlined />}
              onClick={() => showEditModal(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const orderColumns = [
    {
      title: t('customers.col_id'),
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: t('orders.col_status'),
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag>{status}</Tag>,
    },
    {
      title: t('orders.col_date'),
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? dayjs(date).format('DD.MM.YYYY HH:mm') : '-',
    },
  ];

  return (
    <div className="customers-content">
      <h1><TeamOutlined /> {t('customers.title')}</h1>

      <Card>
        <Table
          columns={columns}
          dataSource={customers}
          rowKey="user_id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              t('customers.pagination', { from: range[0], to: range[1], total }),
          }}
          onChange={(pag) => setPagination(pag)}
        />
      </Card>

      <Modal
        title={selectedCustomer ? selectedCustomer.full_name || `@${selectedCustomer.username}` : ''}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={700}
      >
        {selectedCustomer && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Card size="small">
                  <Space>
                    <PhoneOutlined />
                    <span>{selectedCustomer.phone || '-'}</span>
                  </Space>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Space>
                    <MailOutlined />
                    <span>{selectedCustomer.email || '-'}</span>
                  </Space>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Space>
                    <UserOutlined />
                    <span>@{selectedCustomer.username || '-'}</span>
                  </Space>
                </Card>
              </Col>
            </Row>

            <h3>{t('customers.orders_history')}</h3>
            <Table
              columns={orderColumns}
              dataSource={customerOrders}
              rowKey="id"
              loading={detailLoading}
              size="small"
              pagination={{ pageSize: 5 }}
            />
          </div>
        )}
      </Modal>

      <Modal
        title={t('customers.btn_edit')}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item name="phone" label={t('customers.col_phone')}>
            <Input placeholder="+380..." />
          </Form.Item>

          <Form.Item name="email" label={t('customers.col_email')}>
            <Input placeholder="email@example.com" />
          </Form.Item>

          <Form.Item name="notes" label={t('customers.col_notes')}>
            <Input.TextArea rows={3} />
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
      </Modal>
    </div>
  );
};

export default Customers;
