import { Dropdown } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const languages = [
  { key: 'ru', label: '🇷🇺 Русский' },
  { key: 'en', label: '🇬🇧 English' },
  { key: 'uk', label: '🇺🇦 Українська' },
];

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  const current = languages.find(l => l.key === i18n.language) || languages[0];

  return (
    <Dropdown
      menu={{
        items: languages.map(l => ({
          key: l.key,
          label: l.label,
          onClick: () => i18n.changeLanguage(l.key),
        })),
        selectedKeys: [i18n.language],
      }}
    >
      <span style={{ cursor: 'pointer' }}>
        <GlobalOutlined style={{ fontSize: 18 }} /> {current.label}
      </span>
    </Dropdown>
  );
};

export default LanguageSwitcher;
