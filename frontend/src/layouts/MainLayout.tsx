import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import {
  HomeOutlined,
  UnorderedListOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';

const { Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  {
    key: '/',
    icon: <HomeOutlined />,
    label: '总览',
  },
  {
    key: '/tasks',
    icon: <UnorderedListOutlined />,
    label: '适配任务',
  },
  {
    key: '/environments',
    icon: <CloudServerOutlined />,
    label: '环境管理',
  },
  {
    key: '/hardware',
    icon: <DatabaseOutlined />,
    label: '硬件知识库',
  },
];

function getSelectedKey(pathname: string): string {
  if (pathname === '/') return '/';
  if (pathname.startsWith('/tasks')) return '/tasks';
  if (pathname.startsWith('/environments')) return '/environments';
  if (pathname.startsWith('/hardware')) return '/hardware';
  return '/';
}

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = getSelectedKey(location.pathname);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={200}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        style={{
          borderRight: '1px solid #f0f0f0',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          overflow: 'auto',
        }}
      >
        <div
          style={{
            padding: collapsed ? '16px 8px' : '16px 20px',
            borderBottom: '1px solid #f0f0f0',
            textAlign: collapsed ? 'center' : 'left',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              justifyContent: collapsed ? 'center' : 'flex-start',
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                background: '#1677FF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 700,
                fontSize: 14,
                flexShrink: 0,
              }}
            >
              LD
            </div>
            {!collapsed && (
              <div>
                <Text strong style={{ fontSize: 15, display: 'block', lineHeight: 1.3 }}>
                  LLM Deploy
                </Text>
                <Text
                  type="secondary"
                  style={{ fontSize: 11, display: 'block', lineHeight: 1.3 }}
                >
                  大模型自助部署平台
                </Text>
              </div>
            )}
          </div>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 'none', marginTop: 4 }}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        <Content
          style={{
            background: '#F5F7FA',
            padding: 24,
            minHeight: '100vh',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
