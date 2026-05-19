import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import enUS from 'antd/locale/en_US';
import ukUA from 'antd/locale/uk_UA';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import 'dayjs/locale/en';
import 'dayjs/locale/uk';
import './App.css';

import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Orders from './components/Orders';
import BotConfig from './components/BotConfig';
import MainLayout from './components/MainLayout';
import Customers from './components/Customers';
import Templates from './components/Templates';
import Analytics from './components/Analytics';

import { AuthProvider } from './contexts/AuthContext';

const antLocales = { ru: ruRU, en: enUS, uk: ukUA };
const dayjsLocales = { ru: 'ru', en: 'en', uk: 'uk' };

function App() {
  const { i18n } = useTranslation();
  const antLocale = antLocales[i18n.language] || ruRU;
  dayjs.locale(dayjsLocales[i18n.language] || 'ru');

  return (
    <ConfigProvider locale={antLocale}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route element={<MainLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/orders" element={<Orders />} />
                <Route path="/customers" element={<Customers />} />
                <Route path="/templates" element={<Templates />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/bot-config" element={<BotConfig />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;
