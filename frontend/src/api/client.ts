import axios from 'axios';
import type {
  AdaptationTask,
  BuildImageRequest,
  CalculateParamsRequest,
  CreateTaskRequest,
  Deployment,
  DeployRequest,
  DownloadProgress,
  Environment,
  HardwareChip,
  HardwareCompatibilityResponse,
  ImageBuild,
  ParamCalculation,
  PrecheckItem,
  PrecheckRequest,
  RecalculateParamsRequest,
  StartDownloadRequest,
  StatsResponse,
  TaskListResponse,
} from '../types';

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || '请求失败';
    console.error('[API Error]', message);
    return Promise.reject(error);
  }
);

// ========== Tasks ==========

export async function getTasks(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  hardware_model?: string;
  search?: string;
}): Promise<TaskListResponse> {
  const { data } = await apiClient.get('/tasks', { params });
  return data;
}

export async function getTask(id: number): Promise<AdaptationTask> {
  const { data } = await apiClient.get(`/tasks/${id}`);
  return data;
}

export async function createTask(
  payload: CreateTaskRequest
): Promise<AdaptationTask> {
  const { data } = await apiClient.post('/tasks', payload);
  return data;
}

export async function deleteTask(id: number): Promise<void> {
  await apiClient.delete(`/tasks/${id}`);
}

export async function getStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get('/tasks/stats');
  return data;
}

// ========== Model Parsing ==========

export async function parseModel(taskId: number): Promise<AdaptationTask> {
  const { data } = await apiClient.post(`/tasks/${taskId}/parse`);
  return data;
}

export async function confirmAdaptation(
  taskId: number,
  payload: { engine?: string; dtype?: string }
): Promise<AdaptationTask> {
  const { data } = await apiClient.post(
    `/tasks/${taskId}/confirm`,
    payload
  );
  return data;
}

// ========== Downloads ==========

export async function startDownload(
  payload: StartDownloadRequest
): Promise<DownloadProgress> {
  const { data } = await apiClient.post('/models/download', payload);
  return data;
}

export async function getDownloadProgress(
  downloadId: number
): Promise<DownloadProgress> {
  const { data } = await apiClient.get(`/models/download/${downloadId}`);
  return data;
}

export async function getDownloadByTask(
  taskId: number
): Promise<DownloadProgress> {
  const { data } = await apiClient.get(`/models/download/by-task/${taskId}`);
  return data;
}

// ========== Parameter Calculation ==========

export async function calculateParams(
  payload: CalculateParamsRequest
): Promise<ParamCalculation> {
  const { data } = await apiClient.post('/params/calculate', payload);
  return data;
}

export async function recalculateParams(
  payload: RecalculateParamsRequest
): Promise<ParamCalculation> {
  const { data } = await apiClient.put('/params/calculate', payload);
  return data;
}

// ========== Image Build ==========

export async function buildImage(
  payload: BuildImageRequest
): Promise<ImageBuild> {
  const { data } = await apiClient.post('/images/build', payload);
  return data;
}

export async function getBuildStatus(buildId: number): Promise<ImageBuild> {
  const { data } = await apiClient.get(`/images/build/${buildId}`);
  return data;
}

export async function getBuildByTask(taskId: number): Promise<ImageBuild> {
  const { data } = await apiClient.get(`/images/build/by-task/${taskId}`);
  return data;
}

// ========== Environments ==========

export async function getEnvironments(): Promise<Environment[]> {
  const { data } = await apiClient.get('/environments');
  return data;
}

export async function createEnvironment(
  payload: Omit<Environment, 'id' | 'created_at' | 'status' | 'hardware_info'>
): Promise<Environment> {
  const { data } = await apiClient.post('/environments', payload);
  return data;
}

export async function updateEnvironment(
  id: number,
  payload: Partial<Environment>
): Promise<Environment> {
  const { data } = await apiClient.put(`/environments/${id}`, payload);
  return data;
}

export async function deleteEnvironment(id: number): Promise<void> {
  await apiClient.delete(`/environments/${id}`);
}

export async function testConnection(
  id: number
): Promise<{ success: boolean; message: string }> {
  const { data } = await apiClient.post(`/environments/${id}/test`);
  return data;
}

// ========== Deployment ==========

export async function precheck(
  payload: PrecheckRequest
): Promise<PrecheckItem[]> {
  const { data } = await apiClient.post('/deployments/precheck', payload);
  return data;
}

export async function deploy(payload: DeployRequest): Promise<Deployment> {
  const { data } = await apiClient.post('/deployments', payload);
  return data;
}

export async function verifyDeployment(
  deploymentId: number
): Promise<Deployment> {
  const { data } = await apiClient.post(
    `/deployments/${deploymentId}/verify`
  );
  return data;
}

export async function getDeployment(deploymentId: number): Promise<Deployment> {
  const { data } = await apiClient.get(`/deployments/${deploymentId}`);
  return data;
}

export async function getDeploymentByTask(
  taskId: number
): Promise<Deployment> {
  const { data } = await apiClient.get(`/deployments/by-task/${taskId}`);
  return data;
}

// ========== Hardware Knowledge Base ==========

export async function getHardwareCompatibility(): Promise<HardwareCompatibilityResponse> {
  const { data } = await apiClient.get('/hardware');
  return data;
}

export async function getChipDetail(
  vendor: string,
  model: string
): Promise<HardwareChip> {
  const { data } = await apiClient.get(
    `/hardware/${vendor}/chips/${model}`
  );
  return data;
}

export default apiClient;
