import React, { useState, useEffect } from 'react';
import {
  Card, Form, Input, Button, Switch, message, Tabs, Space,
  Divider, InputNumber, Alert, Select, Row, Col, Table, Tag,
  List, Popconfirm
} from 'antd';
import { SaveOutlined, ReloadOutlined, PlusOutlined, MinusCircleOutlined, ArrowUpOutlined, ArrowDownOutlined, SendOutlined, UserAddOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const { TextArea } = Input;

const BotConfig = () => {
  const [loading, setLoading] = useState(false);
  const [settingsForm] = Form.useForm();
  const [flowForm] = Form.useForm();
  const { t } = useTranslation();
  const [admins, setAdmins] = useState([]);
  const [adminChatId, setAdminChatId] = useState('');
  const [broadcastText, setBroadcastText] = useState('');
  const [broadcastSending, setBroadcastSending] = useState(false);

  const requiredRule = [{ required: true, message: t('required_field') }];

  const loadConfig = React.useCallback(async () => {
    setLoading(true);
    try {
      const [settingsResponse, flowResponse, adminsResponse] = await Promise.all([
        axios.get('/api/bot-config/settings'),
        axios.get('/api/bot-config/flow'),
        axios.get('/api/bot-config/admins').catch(() => ({ data: [] }))
      ]);

      if (settingsResponse.data) {
        const normalizedSettings = { ...settingsResponse.data };
        ['is_photo_required', 'step_extra_enabled'].forEach(key => {
          if (normalizedSettings[key] !== undefined) {
            normalizedSettings[key] = normalizedSettings[key] === '1' || normalizedSettings[key] === 1 || normalizedSettings[key] === true || normalizedSettings[key] === "true";
          }
        });
        settingsForm.setFieldsValue(normalizedSettings);
      }

      if (flowResponse.data) {
          setTimeout(() => {
              flowForm.setFieldsValue({
                  steps: Array.isArray(flowResponse.data) ? flowResponse.data : []
              });
          }, 100);
      }

      if (adminsResponse.data) {
        setAdmins(Array.isArray(adminsResponse.data) ? adminsResponse.data : []);
      }
    } catch (error) {
      message.error(t('bot_config.err_load'));
    }
    setLoading(false);
  }, [settingsForm, flowForm, t]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const saveSettings = async (values) => {
    setLoading(true);
    try {
      await axios.put('/api/bot-config/settings', values);
      message.success(t('bot_config.msg_settings_saved'));
    } catch (error) {
      message.error(t('bot_config.err_save_settings'));
    } finally {
      setLoading(false);
    }
  };

  const saveFlow = async (values) => {
      setLoading(true);
      try {
          await axios.put('/api/bot-config/flow', values.steps);
          message.success(t('bot_config.msg_flow_saved'));
      } catch (error) {
          message.error(t('bot_config.err_save_flow'));
      } finally {
          setLoading(false);
      }
  };

  const handleAddAdmin = async () => {
    if (!adminChatId.trim()) {
      message.error(t('bot_config.err_admin_chat_id'));
      return;
    }
    try {
      await axios.post('/api/bot-config/admins', { chat_id: adminChatId });
      message.success(t('bot_config.msg_admin_added'));
      setAdminChatId('');
      loadConfig();
    } catch (error) {
      message.error(t('bot_config.err_add_admin'));
    }
  };

  const handleRemoveAdmin = async (chatId) => {
    try {
      await axios.delete(`/api/bot-config/admins/${chatId}`);
      message.success(t('bot_config.msg_admin_removed'));
      loadConfig();
    } catch (error) {
      message.error(t('bot_config.err_remove_admin'));
    }
  };

  const handleBroadcast = async () => {
    if (!broadcastText.trim()) {
      message.error(t('bot_config.err_broadcast_empty'));
      return;
    }
    setBroadcastSending(true);
    try {
      await axios.post('/api/bot-config/broadcast', { text: broadcastText });
      message.success(t('bot_config.msg_broadcast_sent'));
      setBroadcastText('');
    } catch (error) {
      message.error(t('bot_config.err_broadcast'));
    } finally {
      setBroadcastSending(false);
    }
  };

  const tabItems = [
    {
      key: 'flow',
      label: t('bot_config.tab_flow'),
      forceRender: true,
      children: (
        <Card title={t('bot_config.card_flow_editor')}>
           <Alert
              message={t('bot_config.flow_alert_title')}
              description={t('bot_config.flow_alert_desc')}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          <Form form={flowForm} layout="vertical" onFinish={saveFlow}>
            <Form.List name="steps">
              {(fields, { add, remove, move }) => (
                <>
                  {fields.map(({ key, name, ...restField }, index) => (
                    <Card size="small" key={key} style={{ marginBottom: 16, borderLeft: '4px solid #1890ff' }}
                      title={
                        <Space>
                          <strong>{t('bot_config.flow_step')} {index + 1}</strong>
                          <Button size="small" icon={<ArrowUpOutlined />} disabled={index === 0} onClick={() => move(index, index - 1)} />
                          <Button size="small" icon={<ArrowDownOutlined />} disabled={index === fields.length - 1} onClick={() => move(index, index + 1)} />
                        </Space>
                      }
                      extra={<MinusCircleOutlined style={{ color: 'red' }} onClick={() => remove(name)} />}
                    >
                      <Row gutter={16}>
                        <Col span={8}>
                          <Form.Item {...restField} name={[name, 'id']} label={t('bot_config.flow_field_id')} rules={[{ required: true, message: t('bot_config.flow_err_field_id') }]}>
                            <Input placeholder={t('bot_config.flow_field_id_ph')} />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item {...restField} name={[name, 'type']} label={t('bot_config.flow_field_type')} rules={[{ required: true, message: t('bot_config.flow_err_type') }]}>
                            <Select>
                              <Select.Option value="text">{t('bot_config.flow_type_text')}</Select.Option>
                              <Select.Option value="choice">{t('bot_config.flow_type_choice')}</Select.Option>
                              <Select.Option value="photo">{t('bot_config.flow_type_photo')}</Select.Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                           <Form.Item {...restField} name={[name, 'label_key']} label={t('bot_config.flow_field_label_key')}>
                            <Input placeholder={t('bot_config.flow_field_label_key_ph')} />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item {...restField} name={[name, 'label']} label={t('bot_config.flow_field_label')}>
                        <TextArea rows={2} placeholder={t('bot_config.flow_field_label_ph')} />
                      </Form.Item>

                      {/* Render options ONLY if type is 'choice' */}
                      <Form.Item
                        noStyle
                        shouldUpdate={(prevValues, currentValues) => prevValues.steps?.[name]?.type !== currentValues.steps?.[name]?.type}
                      >
                        {({ getFieldValue }) => {
                          const stepType = getFieldValue(['steps', name, 'type']);
                          if (stepType === 'choice') {
                            return (
                              <div style={{ backgroundColor: '#f5f5f5', padding: '16px', borderRadius: '4px', marginTop: '16px' }}>
                                <h4>{t('bot_config.flow_options_title')}</h4>
                                <Form.List name={[name, 'options']}>
                                  {(optFields, { add: addOpt, remove: optRemove }) => (
                                    <>
                                      {optFields.map(({ key: optKey, name: optName, ...optRestField }) => (
                                        <Row key={optKey} gutter={8} style={{ marginBottom: 8 }}>
                                          <Col span={8}>
                                            <Form.Item {...optRestField} name={[optName, 'val']} rules={[{ required: true, message: t('bot_config.flow_err_option_val') }]} style={{ marginBottom: 0 }}>
                                              <Input placeholder={t('bot_config.flow_option_val_ph')} />
                                            </Form.Item>
                                          </Col>
                                          <Col span={10}>
                                            <Form.Item {...optRestField} name={[optName, 'label']} rules={[{ required: true, message: t('bot_config.flow_err_option_label') }]} style={{ marginBottom: 0 }}>
                                              <Input placeholder={t('bot_config.flow_option_label_ph')} />
                                            </Form.Item>
                                          </Col>
                                          <Col span={4}>
                                             <Form.Item {...optRestField} name={[optName, 'label_key']} style={{ marginBottom: 0 }}>
                                              <Input placeholder={t('bot_config.flow_option_label_key_ph')} />
                                            </Form.Item>
                                          </Col>
                                          <Col span={2}>
                                            <Button type="text" danger icon={<MinusCircleOutlined />} onClick={() => optRemove(optName)} />
                                          </Col>
                                        </Row>
                                      ))}
                                      <Button type="dashed" onClick={() => addOpt()} block icon={<PlusOutlined />}>
                                        {t('bot_config.flow_add_option')}
                                      </Button>
                                    </>
                                  )}
                                </Form.List>
                              </div>
                            );
                          }
                          return null;
                        }}
                      </Form.Item>

                    </Card>
                  ))}
                  <Button type="dashed" onClick={() => add({ type: 'text' })} block icon={<PlusOutlined />}>
                    {t('bot_config.flow_add_step')}
                  </Button>
                </>
              )}
            </Form.List>

            <Form.Item style={{ textAlign: 'right', marginTop: 24 }}>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadConfig}>
                  {t('reset')}
                </Button>
                <Button type="primary" icon={<SaveOutlined />} htmlType="submit" loading={loading}>
                  {t('bot_config.flow_save')}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )
    },

    {
      key: 'settings',
      label: t('bot_config.tab_settings'),
      forceRender: true,
      children: (
        <Card title={t('bot_config.card_behavior_settings')}>
          <Form form={settingsForm} layout="vertical" onFinish={saveSettings}>
            <Form.Item
              label={t('bot_config.photo_required_label')}
              name="is_photo_required"
              valuePropName="checked"
              tooltip={t('bot_config.photo_required_tooltip')}
            >
              <Switch checkedChildren={t('yes')} unCheckedChildren={t('no')} />
            </Form.Item>

            <Form.Item
              label={t('bot_config.extra_question_label')}
              name="step_extra_enabled"
              valuePropName="checked"
              tooltip={t('bot_config.extra_question_tooltip')}
            >
              <Switch checkedChildren={t('yes')} unCheckedChildren={t('no')} />
            </Form.Item>

            <Divider />

            <Form.Item
              label={t('bot_config.admin_chat_id_label')}
              name="admin_chat_id"
              tooltip={t('bot_config.admin_chat_id_tooltip')}
            >
              <InputNumber style={{ width: '100%' }} placeholder="123456789" />
            </Form.Item>

            <Alert
              message={t('bot_config.info_title')}
              description={t('bot_config.info_description')}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Divider>{t('bot_config.admins_title')}</Divider>

            <Card size="small" title={t('bot_config.admins_current')} style={{ marginBottom: 16 }}>
              <Space style={{ width: '100%', marginBottom: 12 }} wrap>
                {admins.length === 0 && <Tag>{t('bot_config.admins_none')}</Tag>}
                {admins.map((admin) => (
                  <Tag
                    key={admin.chat_id || admin}
                    closable
                    onClose={() => handleRemoveAdmin(admin.chat_id || admin)}
                  >
                    {admin.username ? `@${admin.username}` : (admin.chat_id || admin)}
                  </Tag>
                ))}
              </Space>
              <Space>
                <Input
                  placeholder={t('bot_config.admin_chat_id_ph')}
                  value={adminChatId}
                  onChange={(e) => setAdminChatId(e.target.value)}
                  style={{ width: 200 }}
                  onPressEnter={handleAddAdmin}
                />
                <Button
                  type="primary"
                  icon={<UserAddOutlined />}
                  onClick={handleAddAdmin}
                >
                  {t('bot_config.admin_add')}
                </Button>
              </Space>
            </Card>

            <Divider>{t('bot_config.broadcast_title')}</Divider>

            <Card size="small" title={t('bot_config.broadcast_card')}>
              <TextArea
                rows={3}
                placeholder={t('bot_config.broadcast_ph')}
                value={broadcastText}
                onChange={(e) => setBroadcastText(e.target.value)}
                style={{ marginBottom: 12 }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleBroadcast}
                loading={broadcastSending}
                disabled={!broadcastText.trim()}
              >
                {t('bot_config.broadcast_send')}
              </Button>
            </Card>

            <Form.Item style={{ textAlign: 'right' }}>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadConfig}>
                  {t('reset')}
                </Button>
                <Button type="primary" icon={<SaveOutlined />} htmlType="submit" loading={loading}>
                  {t('bot_config.save_settings')}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )
    }
  ];

  return (
    <div className="bot-config-content">
      <h1>{t('bot_config.title')}</h1>

      <Alert
        message={t('bot_config.warning_title')}
        description={t('bot_config.warning_description')}
        type="warning"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Tabs defaultActiveKey="flow" items={tabItems} />
    </div>
  );
};

export default BotConfig;
