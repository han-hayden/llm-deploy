// ========== Enum-like constants (erasableSyntaxOnly compatible) ==========

export const TaskStatus = {
  Created: 'created',
  Parsing: 'parsing',
  Parsed: 'parsed',
  ParseFailed: 'parse_failed',
  Downloading: 'downloading',
  Downloaded: 'downloaded',
  DownloadFailed: 'download_failed',
  Building: 'building',
  Built: 'built',
  BuildFailed: 'build_failed',
  Deploying: 'deploying',
  Deployed: 'deployed',
  DeployFailed: 'deploy_failed',
} as const;
export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

export const HardwareVendor = {
  NVIDIA: 'nvidia',
  HuaweiAscend: 'huawei',
  HygonDCU: 'hygon',
  MetaX: 'metax',
  KunlunXin: 'kunlunxin',
  Iluvatar: 'iluvatar',
} as const;
export type HardwareVendor = (typeof HardwareVendor)[keyof typeof HardwareVendor];

export const DeployMode = {
  DockerSingle: 'docker_single',
  DockerMulti: 'docker_multi',
  K8s: 'k8s',
} as const;
export type DeployMode = (typeof DeployMode)[keyof typeof DeployMode];

export const EnvironmentType = {
  DockerHost: 'docker_host',
  K8sCluster: 'k8s_cluster',
} as const;
export type EnvironmentType = (typeof EnvironmentType)[keyof typeof EnvironmentType];

export const ConnectionType = {
  SSH: 'ssh',
  Kubeconfig: 'kubeconfig',
} as const;
export type ConnectionType = (typeof ConnectionType)[keyof typeof ConnectionType];

export const DownloadSource = {
  HuggingFace: 'huggingface',
  ModelScope: 'modelscope',
} as const;
export type DownloadSource = (typeof DownloadSource)[keyof typeof DownloadSource];

export const DownloadTargetType = {
  Local: 'local',
  Remote: 'remote',
} as const;
export type DownloadTargetType = (typeof DownloadTargetType)[keyof typeof DownloadTargetType];

// ========== Core Domain Types ==========

export interface AdaptationTask {
  id: number;
  task_name: string;
  model_identifier: string;
  model_source: DownloadSource | null;
  hardware_model: string;
  engine: string | null;
  dtype: string | null;
  status: TaskStatus;
  model_type: string | null;
  adaptation_label: string | null;
  anomaly_flags: AnomalyFlag[] | null;
  created_at: string;
  updated_at: string;
  model_metadata: ModelMetadata | null;
  download: DownloadProgress | null;
  image_build: ImageBuild | null;
  deployment: Deployment | null;
}

export interface AnomalyFlag {
  type: 'warning' | 'info';
  message: string;
}

export interface ModelMetadata {
  id: number;
  task_id: number;
  model_name: string;
  architectures: string;
  param_count: number;
  hidden_size: number;
  num_hidden_layers: number;
  num_attention_heads: number;
  num_key_value_heads: number;
  vocab_size: number;
  max_position_embeddings: number;
  torch_dtype: string;
  quantization_config: Record<string, unknown> | null;
  model_card_parsed: ModelCardParsed | null;
  dependencies: string[] | null;
  total_weight_size_gb: number;
  weight_files: WeightFile[] | null;
  created_at: string;
}

export interface ModelCardParsed {
  recommended_frameworks: string[];
  recommended_commands: string[];
  special_params: string[];
  pip_dependencies: string[];
  min_memory_gb: number | null;
}

export interface WeightFile {
  filename: string;
  size_bytes: number;
}

export interface DownloadProgress {
  id: number;
  task_id: number;
  source: DownloadSource;
  target_type: DownloadTargetType;
  target_path: string;
  environment_id: number | null;
  status: string;
  progress_percent: number;
  downloaded_bytes: number;
  total_bytes: number;
  speed_bytes_per_sec: number;
  eta_seconds: number;
  retry_count: number;
  files: DownloadFileProgress[] | null;
  created_at: string;
  updated_at: string;
}

export interface DownloadFileProgress {
  id: number;
  filename: string;
  file_size_bytes: number;
  downloaded_bytes: number;
  sha256_expected: string | null;
  sha256_actual: string | null;
  status: string;
}

export interface ParamCalculation {
  id: number;
  build_task_id: number;
  gpu_count: number;
  dtype: string;
  tensor_parallel_size: number;
  pipeline_parallel_size: number;
  max_model_len: number;
  max_num_seqs: number;
  gpu_memory_utilization: number;
  enforce_eager: boolean;
  all_params: ParamItem[];
  rationale: Record<string, string>;
  memory_allocation: MemoryAllocation;
}

export interface ParamItem {
  name: string;
  value: string | number | boolean;
  rationale: string;
  editable: boolean | 'linked';
}

export interface MemoryAllocation {
  total_per_gpu_gb: number;
  weight_gb: number;
  kv_cache_gb: number;
  runtime_gb: number;
  reserved_gb: number;
}

export interface ImageBuild {
  id: number;
  task_id: number;
  engine_name: string;
  engine_version: string;
  base_image: string;
  dockerfile_content: string;
  startup_command: string;
  image_tag: string;
  api_wrapper_injected: boolean;
  status: string;
  build_log: string;
  image_size_gb: number | null;
  param_calculation: ParamCalculation | null;
  query_summary: QuerySummary | null;
  created_at: string;
  updated_at: string;
}

export interface QuerySummary {
  model_official_note: string;
  vendor_adaptation_status: string;
  recommended_base_image: string;
}

export interface Deployment {
  id: number;
  task_id: number;
  environment_id: number;
  deploy_mode: DeployMode;
  status: string;
  precheck_report: PrecheckItem[] | null;
  api_endpoint: string | null;
  deploy_config: string | null;
  deploy_log: string | null;
  verification_result: VerificationResult | null;
  created_at: string;
  updated_at: string;
}

export interface PrecheckItem {
  name: string;
  status: 'passed' | 'failed' | 'warning';
  actual_value: string;
  expected_value: string;
  suggestion: string | null;
}

export interface VerificationResult {
  success: boolean;
  response_time_ms: number;
  response_preview: string;
}

export interface Environment {
  id: number;
  name: string;
  env_type: EnvironmentType;
  connection_type: ConnectionType;
  connection_config: ConnectionConfig;
  status: 'active' | 'inactive';
  hardware_info: EnvironmentHardwareInfo | null;
  created_at: string;
}

export interface ConnectionConfig {
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  private_key?: string;
  kubeconfig?: string;
}

export interface EnvironmentHardwareInfo {
  gpu_count: number;
  gpu_model: string;
  description: string;
}

// ========== Hardware Knowledge Base Types ==========

export interface HardwareChip {
  model: string;
  memory_gb: number;
  memory_type: string;
  compute_tflops_fp16: number;
  interconnect: string;
  supports_bf16: boolean;
  supports_fp8: boolean;
  device_paths: string[];
  env_var: string;
  k8s_resource: string;
  detection_command: string;
  extra_volumes: string[];
}

export interface HardwareVendorInfo {
  name: string;
  slug: HardwareVendor;
  website: string;
  modelzoo_url: string;
  chips: HardwareChip[];
  engines: HardwareEngineInfo[];
}

export interface HardwareEngineInfo {
  name: string;
  versions: EngineVersion[];
}

export interface EngineVersion {
  version: string;
  min_driver: string;
  min_sdk: string;
  base_image: string;
  compatible_chips: string[];
  param_mapping: Record<string, string>;
  startup_template: string;
}

// ========== API Request/Response Types ==========

export interface CreateTaskRequest {
  model_identifier: string;
  hardware_model: string;
  task_name?: string;
}

export interface StartDownloadRequest {
  task_id: number;
  source: DownloadSource;
  target_type: DownloadTargetType;
  target_path: string;
  environment_id?: number;
}

export interface CalculateParamsRequest {
  task_id: number;
}

export interface RecalculateParamsRequest {
  task_id: number;
  gpu_count: number;
}

export interface BuildImageRequest {
  task_id: number;
}

export interface DeployRequest {
  task_id: number;
  environment_id: number;
  deploy_mode: DeployMode;
}

export interface PrecheckRequest {
  task_id: number;
  environment_id: number;
}

export interface TaskListResponse {
  items: AdaptationTask[];
  total: number;
  page: number;
  page_size: number;
}

export interface StatsResponse {
  total_tasks: number;
  completed_tasks: number;
  running_services: number;
  registered_environments: number;
}

export interface HardwareCompatibilityResponse {
  vendors: HardwareVendorInfo[];
}

export interface HardwareChipGroupOption {
  vendor: string;
  vendor_slug: HardwareVendor;
  chips: Array<{
    label: string;
    value: string;
  }>;
}
