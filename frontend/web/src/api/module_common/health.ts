import { request } from "@utils";

const API_PATH = "/common/health";

export interface HealthDependency {
  status: number;
  latency_ms: number | null;
}

export interface HealthReadiness {
  status: number;
  timestamp: string;
  version: string;
  uptime_seconds: number;
  dependencies: {
    database: HealthDependency;
    redis: HealthDependency;
  };
  disk_usage: number;
}

const HealthAPI = {
  getReadiness() {
    return request<ApiResponse<HealthReadiness>>({
      url: `${API_PATH}/ready`,
      method: "get",
    });
  },
};

export default HealthAPI;
