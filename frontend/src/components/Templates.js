import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, message, Space, Card, Tag,
  Popconfirm
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, MessageOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import dayjs from 'dayjs';

const { TextArea } = Input;

const Templates = () => {
  const { t } = useTranslation();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/templates/');
      setTemplates(response.data.templates || []);
    } catch (error) {
      message.error(t('templates.err_load'));
      console.error(error);
    }
    setLoading(false);
  };

  const showAddModal = () => {
    setEditingTemplate(null);
    form.resetFields();
    setModalVisible(true);
  };

  const showEditModal = (template) => {
    setEditingTemplate(template);
    form.setFieldsValue({
      name: template.name,
      body: template.body,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values) => {
    try {
      if (editingTemplate) {
        await axios.put(`/api/templates/${editingTemplate.id}`, values);
      } else {
        await axios.post('/api/templates/', values);
      }
      message.success(t('templates.msg_saved'));
      setModalVisible(false);
      form.resetFields();
      fetchTemplates();
    } catch (error) {
      message.error(t('templates.err_load'));
    }
  };

  const handleDelete = async (templateId) => {
    try {
      await axios.delete(`/api/templates/${templateId}`);
      message.success(t('templates.msg_deleted'));
      fetchTemplates();
    } catch (error) {
      message.error(t('templates.err_load'));
    }
  };

  const columns = [
    {
      title: t('templates.col_name'),
      dataIndex: 'name',
      key: 'name',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: t('templates.col_body'),
      dataIndex: 'body',
      key: 'body',
      render: (text) => (
        <span style={{ maxWidth: 400, display: 'inline-block', whiteSpace: 'pre-wrap' }}>
          {text && text.length > 80 ? `${text.substring(0, 80)}...` : text}
        </span>
      ),
    },
    {
      title: t('orders.col_date'),
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? dayjs(date).format('DD.MM.YYYY HH:mm') : '-',
      sorter: (a, b) => dayjs(a.created_at || 0).unix() - dayjs(b.created_at || 0).unix(),
    },
    {
      title: t('orders.col_actions'),
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => showEditModal(record)}
          />
          <Popconfirm
            title={t('templates.msg_deleted')}
            onConfirm={() => handleDelete(record.id)}
            okText={t('yes')}
            cancelText={t('no')}
          >
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="templates-content">
      <h1><MessageOutlined /> {t('templates.title')}</h1>

      <Card
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={showAddModal}
          >
            {t('templates.btn_add')}
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={templates}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingTemplate ? t('templates.modal_edit_title') : t('templates.modal_add_title')}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label={t('templates.col_name')}
            rules={[{ required: true, message: t('required_field') }]}
          >
            <Input placeholder={t('templates.name_placeholder')} />
          </Form.Item>

          <Form.Item
            name="body"
            label={t('templates.col_body')}
            rules={[{ required: true, message: t('required_field') }]}
          >
            <TextArea
              rows={6}
              placeholder={t('templates.body_placeholder')}
            />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
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

export default Templates;
