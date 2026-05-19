import React, { useState, useContext } from 'react';
import { Layout, Menu, Dropdown, Avatar, message, Spin } from 'antd';
import {
    DashboardOutlined,
    ShoppingCartOutlined,
    SettingOutlined,
    LogoutOutlined,
    UserOutlined,
    TeamOutlined,
    MessageOutlined,
    BarChartOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AuthContext from '../contexts/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';

const { Header, Content, Sider } = Layout;

const MainLayout = () => {
    const { logout, isAuthenticated, loading } = useContext(AuthContext);
    const navigate = useNavigate();
    const location = useLocation();
    const [collapsed, setCollapsed] = useState(false);
    const { t } = useTranslation();

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    const handleLogout = () => {
        logout();
        message.success(t('layout.logout_success'));
        navigate('/login');
    };

    const menuItems = [
        {
            key: '/dashboard',
            icon: <DashboardOutlined />,
            label: t('layout.dashboard'),
        },
        {
            key: '/orders',
            icon: <ShoppingCartOutlined />,
            label: t('layout.orders'),
        },
        {
            key: '/customers',
            icon: <TeamOutlined />,
            label: t('layout.customers'),
        },
        {
            key: '/templates',
            icon: <MessageOutlined />,
            label: t('layout.templates'),
        },
        {
            key: '/analytics',
            icon: <BarChartOutlined />,
            label: t('layout.analytics'),
        },
        {
            key: '/bot-config',
            icon: <SettingOutlined />,
            label: t('layout.bot_settings'),
        },
    ];

    const userMenuItems = [
        {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: t('layout.logout'),
            onClick: handleLogout,
        },
    ];

    const handleMenuClick = ({ key }) => {
        navigate(key);
    };

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
                <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '10px' }}>
                    {t('app_title')}
                </div>
                <Menu
                    theme="dark"
                    selectedKeys={[location.pathname]}
                    mode="inline"
                    items={menuItems}
                    onClick={handleMenuClick}
                />
            </Sider>
            <Layout>
                <Header style={{ padding: '0 24px', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ margin: 0 }}>{t('layout.panel_title')}</h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <LanguageSwitcher />
                        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                            <Avatar style={{ cursor: 'pointer' }} icon={<UserOutlined />} />
                        </Dropdown>
                    </div>
                </Header>
                <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: 8, minHeight: 280, overflow: 'initial' }}>
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
};

export default MainLayout;
