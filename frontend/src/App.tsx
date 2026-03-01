import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './layouts/MainLayout';
import Overview from './pages/Overview';
import TaskList from './pages/tasks/TaskList';
import TaskCreate from './pages/tasks/TaskCreate';
import TaskDetail from './pages/tasks/TaskDetail';
import EnvironmentList from './pages/environments/EnvironmentList';
import HardwareOverview from './pages/hardware/HardwareOverview';
import HardwareDetail from './pages/hardware/HardwareDetail';

const theme = {
  token: {
    colorPrimary: '#1677FF',
    borderRadius: 6,
    colorBgLayout: '#F5F7FA',
  },
};

export default function App() {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route index element={<Overview />} />
            <Route path="tasks" element={<TaskList />} />
            <Route path="tasks/create" element={<TaskCreate />} />
            <Route path="tasks/:id" element={<TaskDetail />} />
            <Route path="environments" element={<EnvironmentList />} />
            <Route path="hardware" element={<HardwareOverview />} />
            <Route path="hardware/:model" element={<HardwareDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
