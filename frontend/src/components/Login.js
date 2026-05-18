import React, { useState, useContext } from 'react';
import { Form, Input, Button, Card, message, Spin } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AuthContext from '../contexts/AuthContext';
import '../App.css';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const onFinish = async (values) => {
    setLoading(true);
    const result = await login(values.password);
    setLoading(false);

    if (result.success) {
      message.success(t('login.success'));
      navigate('/dashboard');
    } else {
      message.error(result.error);
    }
  };

  return (
    <div className="login-container">
      <Card className="login-card" title={t('login.title')}>
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="password"
            rules={[{ required: true, message: t('login.password_required') }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={t('login.password_placeholder')}
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {t('login.button')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Login;
