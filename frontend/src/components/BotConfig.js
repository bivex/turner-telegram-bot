import React, { useState, useEffect } from 'react';
import {
  Card, Form, Input, Button, Switch, message, Tabs, Space,
  Divider, InputNumber, Alert
} from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const { TextArea } = Input;

const BotConfig = () => {
  const [loading, setLoading] = useState(false);
  const [textsForm] = Form.useForm();
  const [settingsForm] = Form.useForm();
  const { t } = useTranslation();

  const requiredRule = [{ required: true, message: t('required_field') }];

  const loadConfig = React.useCallback(async () => {
    setLoading(true);
    try {
      const [textsResponse, settingsResponse] = await Promise.all([
        axios.get('/api/bot-config/texts'),
        axios.get('/api/bot-config/settings')
      ]);

      if (textsResponse.data) {
        textsForm.setFieldsValue(textsResponse.data);
      }

      if (settingsResponse.data) {
        const normalizedSettings = { ...settingsResponse.data };
        ['is_photo_required', 'step_extra_enabled'].forEach(key => {
          if (normalizedSettings[key] !== undefined) {
            normalizedSettings[key] = normalizedSettings[key] === '1' || normalizedSettings[key] === 1 || normalizedSettings[key] === true || normalizedSettings[key] === "true";
          }
        });
        settingsForm.setFieldsValue(normalizedSettings);
      }
    } catch (error) {
      message.error(t('bot_config.err_load'));
    }
    setLoading(false);
  }, [textsForm, settingsForm, t]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const saveTexts = async (values) => {
    setLoading(true);
    try {
      await axios.put('/api/bot-config/texts', values);
      message.success(t('bot_config.msg_texts_saved'));
    } catch (error) {
      message.error(t('bot_config.err_save_texts'));
    } finally {
      setLoading(false);
    }
  };

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

  const tabItems = [
    {
      key: 'texts',
      label: t('bot_config.tab_texts'),
      children: (
        <Card title={t('bot_config.card_text_constructor')}>
          <Form form={textsForm} layout="vertical" onFinish={saveTexts}>
            <Form.Item label={t('bot_config.welcome_msg_label')} name="welcome_msg" rules={requiredRule}>
              <TextArea rows={3} />
            </Form.Item>

            <Divider>{t('bot_config.divider_step1')}</Divider>

            <Form.Item label={t('bot_config.step_photo_text_label')} name="step_photo_text" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item label={t('bot_config.btn_skip_photo_label')} name="btn_skip_photo" rules={requiredRule}>
              <Input />
            </Form.Item>

            <Divider>{t('bot_config.divider_step2')}</Divider>

            <Form.Item label={t('bot_config.step_type_text_label')} name="step_type_text" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item label={t('bot_config.btn_type_repair_label')} name="btn_type_repair" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_type_copy_label')} name="btn_type_copy" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_type_drawing_label')} name="btn_type_drawing" rules={requiredRule}>
                <Input />
              </Form.Item>
            </Space>

            <Divider>{t('bot_config.divider_step3')}</Divider>

            <Form.Item label={t('bot_config.step_dim_text_label')} name="step_dim_text" rules={requiredRule}>
              <TextArea rows={3} />
            </Form.Item>

            <Divider>{t('bot_config.divider_step4')}</Divider>

            <Form.Item label={t('bot_config.step_cond_text_label')} name="step_cond_text" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item label={t('bot_config.btn_cond_rotation_label')} name="btn_cond_rotation" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_cond_static_label')} name="btn_cond_static" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_cond_impact_label')} name="btn_cond_impact" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_cond_unknown_label')} name="btn_cond_unknown" rules={requiredRule}>
                <Input />
              </Form.Item>
            </Space>

            <Divider>{t('bot_config.divider_step5')}</Divider>

            <Form.Item label={t('bot_config.step_urgency_text_label')} name="step_urgency_text" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item label={t('bot_config.btn_urgency_high_label')} name="btn_urgency_high" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_urgency_med_label')} name="btn_urgency_med" rules={requiredRule}>
                <Input />
              </Form.Item>
              <Form.Item label={t('bot_config.btn_urgency_low_label')} name="btn_urgency_low" rules={requiredRule}>
                <Input />
              </Form.Item>
            </Space>

            <Divider>{t('bot_config.divider_final')}</Divider>

            <Form.Item label={t('bot_config.step_final_text_label')} name="step_final_text" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item label={t('bot_config.msg_done_label')} name="msg_done" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item label={t('bot_config.err_photo_required_label')} name="err_photo_required" rules={requiredRule}>
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item label={t('bot_config.msg_order_canceled_label')} name="msg_order_canceled" rules={requiredRule}>
              <Input />
            </Form.Item>

            <Form.Item style={{ textAlign: 'right' }}>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadConfig}>
                  {t('reset')}
                </Button>
                <Button type="primary" icon={<SaveOutlined />} htmlType="submit" loading={loading}>
                  {t('bot_config.save_texts')}
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

      <Tabs defaultActiveKey="texts" items={tabItems} />
    </div>
  );
};

export default BotConfig;
