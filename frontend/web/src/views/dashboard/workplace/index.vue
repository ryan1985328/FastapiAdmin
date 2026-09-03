<template>
  <div class="dashboard-overview">
    <section class="fa-card dashboard-overview__welcome" aria-labelledby="dashboard-overview-title">
      <div class="dashboard-overview__welcome-main">
        <div class="dashboard-overview__mark" aria-hidden="true">
          <FaSvgIcon icon="ri:layout-grid-line" class="text-2xl" />
        </div>

        <div class="min-w-0 flex-1">
          <p class="dashboard-overview__eyebrow">{{ resolvedAdminName }}</p>
          <h1 id="dashboard-overview-title" class="dashboard-overview__title">
            {{ t("dashboardOverview.welcome", { name: displayName }) }}
          </h1>
          <p class="dashboard-overview__description">
            {{ t("dashboardOverview.description") }}
          </p>

          <div class="dashboard-overview__context" aria-label="operator context">
            <span v-if="departmentName" class="dashboard-overview__context-item">
              <FaSvgIcon icon="ri:organization-chart" />
              {{ departmentName }}
            </span>
            <span class="dashboard-overview__context-item">
              <FaSvgIcon icon="ri:time-line" />
              {{ lastLoginText }}
            </span>
          </div>
        </div>

        <ElButton
          class="dashboard-overview__refresh"
          :loading="isLoading"
          plain
          type="primary"
          @click="loadAll"
        >
          <ElIcon><Refresh /></ElIcon>
          <span>{{ t("dashboardOverview.refresh") }}</span>
        </ElButton>
      </div>
    </section>

    <section class="dashboard-overview__metrics" aria-label="primary metrics">
      <article
        v-for="metric in metricCards"
        :key="metric.key"
        class="fa-card dashboard-overview__metric"
      >
        <div class="dashboard-overview__metric-icon" :class="metric.iconClass" aria-hidden="true">
          <FaSvgIcon :icon="metric.icon" class="text-xl" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="dashboard-overview__metric-label">{{ metric.label }}</p>
          <p class="dashboard-overview__metric-value">{{ metric.value }}</p>
          <p class="dashboard-overview__metric-hint">{{ metric.hint }}</p>
        </div>
      </article>
    </section>

    <div class="dashboard-overview__main">
      <section
        class="fa-card dashboard-overview__activity"
        aria-labelledby="dashboard-activity-title"
      >
        <div class="dashboard-overview__card-heading">
          <div>
            <h2 id="dashboard-activity-title">{{ t("dashboardOverview.activity.title") }}</h2>
            <p>{{ t("dashboardOverview.activity.subtitle") }}</p>
          </div>
          <span v-if="stats && trendHasData" class="dashboard-overview__card-summary">
            {{ t("dashboardOverview.activity.total", { count: formatNumber(trendTotal) }) }}
          </span>
        </div>

        <div v-if="statsLoading" class="dashboard-overview__loading" aria-live="polite">
          <ElSkeleton :rows="4" animated />
        </div>
        <div
          v-else-if="statsError"
          class="dashboard-overview__state dashboard-overview__state--error"
          role="status"
        >
          <FaSvgIcon icon="ri:cloud-off-line" class="text-xl" />
          <span>{{ statsErrorText }}</span>
        </div>
        <template v-else-if="stats">
          <div class="dashboard-overview__trend">
            <FaLineChart
              v-if="trendHasData"
              :data="trendValues"
              :x-axis-data="trendLabels"
              :show-area-color="true"
              :show-axis-line="false"
              :show-split-line="true"
              height="14rem"
            />
            <div v-else class="dashboard-overview__state" role="status">
              <FaSvgIcon icon="ri:line-chart-line" class="text-xl" />
              <span>{{ t("dashboardOverview.activity.noTrend") }}</span>
            </div>
          </div>

          <div class="dashboard-overview__recent-heading">
            <div>
              <h3>{{ t("dashboardOverview.activity.recentTitle") }}</h3>
              <p>{{ t("dashboardOverview.activity.recentSubtitle") }}</p>
            </div>
          </div>

          <div v-if="recentLogins.length" class="dashboard-overview__recent-list">
            <div
              v-for="item in recentLogins"
              :key="`${item.login_time}-${item.username}`"
              class="dashboard-overview__recent-item"
            >
              <div
                class="dashboard-overview__recent-icon"
                :class="item.status === 1 ? 'is-success' : 'is-failed'"
                aria-hidden="true"
              >
                <FaSvgIcon
                  :icon="item.status === 1 ? 'ri:login-circle-line' : 'ri:error-warning-line'"
                />
              </div>
              <div class="min-w-0 flex-1">
                <p class="dashboard-overview__recent-user">
                  {{ item.username || t("dashboardOverview.activity.unknown") }}
                </p>
                <p class="dashboard-overview__recent-meta">
                  {{ item.login_location || t("dashboardOverview.activity.locationUnknown") }}
                </p>
              </div>
              <div class="dashboard-overview__recent-side">
                <ElTag :type="item.status === 1 ? 'success' : 'danger'" size="small" effect="plain">
                  {{
                    item.status === 1
                      ? t("dashboardOverview.activity.success")
                      : t("dashboardOverview.activity.failed")
                  }}
                </ElTag>
                <span>{{ formatLoginTime(item.login_time) }}</span>
              </div>
            </div>
          </div>
          <div
            v-else
            class="dashboard-overview__state dashboard-overview__state--compact"
            role="status"
          >
            <FaSvgIcon icon="ri:inbox-line" class="text-xl" />
            <span>{{ t("dashboardOverview.activity.noRecent") }}</span>
          </div>
        </template>
      </section>

      <section class="fa-card dashboard-overview__health" aria-labelledby="dashboard-health-title">
        <div class="dashboard-overview__card-heading">
          <div>
            <h2 id="dashboard-health-title">{{ t("dashboardOverview.health.title") }}</h2>
            <p>{{ t("dashboardOverview.health.subtitle") }}</p>
          </div>
          <span
            class="dashboard-overview__health-dot"
            :class="healthStatusClass"
            aria-hidden="true"
          ></span>
        </div>

        <div v-if="healthLoading" class="dashboard-overview__loading" aria-live="polite">
          <ElSkeleton :rows="4" animated />
        </div>
        <div
          v-else-if="healthError"
          class="dashboard-overview__state dashboard-overview__state--error"
          role="status"
        >
          <FaSvgIcon icon="ri:heart-pulse-line" class="text-xl" />
          <span>{{ t("dashboardOverview.health.requestFailed") }}</span>
        </div>
        <div v-else-if="health" class="dashboard-overview__health-list">
          <div v-for="item in healthItems" :key="item.key" class="dashboard-overview__health-item">
            <div
              class="dashboard-overview__health-icon"
              :class="item.stateClass"
              aria-hidden="true"
            >
              <FaSvgIcon :icon="item.icon" />
            </div>
            <div class="min-w-0 flex-1">
              <p>{{ item.label }}</p>
              <span>{{ item.detail }}</span>
            </div>
            <span class="dashboard-overview__health-status" :class="item.stateClass">
              {{ item.statusLabel }}
            </span>
          </div>
        </div>
      </section>
    </div>

    <div class="dashboard-overview__footer" aria-live="polite">
      <span v-if="lastUpdated">{{
        t("dashboardOverview.lastUpdated", { time: lastUpdatedText })
      }}</span>
      <span v-else>{{ t("dashboardOverview.loading") }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { Refresh } from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";
import { formatToDateTime, formatToDate } from "@utils";
import DashboardAPI, { type DashboardStats } from "@/api/module_monitor/dashboard";
import HealthAPI, { type HealthReadiness } from "@/api/module_common/health";
import { useAdminBranding } from "@/hooks/core/useAdminBranding";
import { useUserStore } from "@stores";
import { checkPerm } from "@/utils/checkPerm";

defineOptions({ name: "DashboardWorkplace" });

type StatsError = "permission" | "request" | null;
type HealthState = "success" | "warning" | "error" | "unknown";

interface MetricCard {
  key: string;
  label: string;
  value: string;
  hint: string;
  icon: string;
  iconClass: string;
}

interface HealthItem {
  key: string;
  label: string;
  detail: string;
  statusLabel: string;
  stateClass: string;
  icon: string;
}

const REFRESH_INTERVAL_MS = 30_000;
const { t, locale } = useI18n();
const userStore = useUserStore();
const { resolvedAdminName } = useAdminBranding();

const stats = ref<DashboardStats | null>(null);
const health = ref<HealthReadiness | null>(null);
const statsLoading = ref(false);
const healthLoading = ref(false);
const statsError = ref<StatsError>(null);
const healthError = ref(false);
const lastUpdated = ref<Date | null>(null);
let refreshTimer: number | undefined;

const currentUser = computed(() => userStore.basicInfo);
const displayName = computed(
  () =>
    currentUser.value.name || currentUser.value.username || t("dashboardOverview.operatorFallback")
);
const departmentName = computed(
  () => currentUser.value.dept_name || currentUser.value.dept?.name || ""
);
const lastLoginText = computed(() => {
  const value = currentUser.value.last_login;
  return value
    ? t("dashboardOverview.lastLogin", { time: formatToDateTime(value) })
    : t("dashboardOverview.lastLoginNotAvailable");
});

const formatNumber = (value: number) =>
  value.toLocaleString(locale.value === "en" ? "en-US" : "zh-CN");

const metricValue = (value: number | undefined) =>
  typeof value === "number" ? formatNumber(value) : t("dashboardOverview.notAvailable");

const metricHint = (value: string) =>
  stats.value ? value : t("dashboardOverview.metricUnavailable");

const metricCards = computed<MetricCard[]>(() => [
  {
    key: "online-admins",
    label: t("dashboardOverview.metrics.onlineAdmins"),
    value: metricValue(stats.value?.online_users),
    hint: metricHint(t("dashboardOverview.metrics.onlineAdminsHint")),
    icon: "ri:group-line",
    iconClass: "is-blue",
  },
  {
    key: "business-users",
    label: t("dashboardOverview.metrics.businessUsers"),
    value: metricValue(stats.value?.total_users),
    hint: metricHint(
      stats.value
        ? t("dashboardOverview.metrics.businessUsersHint", {
            count: formatNumber(stats.value.week_user_created),
          })
        : ""
    ),
    icon: "ri:user-3-line",
    iconClass: "is-green",
  },
  {
    key: "today-logins",
    label: t("dashboardOverview.metrics.todayLogins"),
    value: metricValue(stats.value?.today_login_count),
    hint: metricHint(
      stats.value
        ? t("dashboardOverview.metrics.todayLoginsHint", {
            count: formatNumber(stats.value.today_unique_users),
          })
        : ""
    ),
    icon: "ri:login-circle-line",
    iconClass: "is-indigo",
  },
]);

const trendItems = computed(() => stats.value?.login_trend || []);
const trendHasData = computed(() => trendItems.value.some((item) => item.logins > 0));
const trendTotal = computed(() => trendItems.value.reduce((total, item) => total + item.logins, 0));
const trendValues = computed(() => trendItems.value.map((item) => item.logins));
const trendLabels = computed(() =>
  trendItems.value.map((item) =>
    formatToDate(item.day, locale.value === "en" ? "MM/DD" : "MM月DD日")
  )
);
const recentLogins = computed(() => (stats.value?.recent_logins || []).slice(0, 6));

const statsErrorText = computed(() =>
  statsError.value === "permission"
    ? t("dashboardOverview.permissionDenied")
    : t("dashboardOverview.statsRequestFailed")
);

const healthState = computed<HealthState>(() => {
  if (!health.value) return healthError.value ? "error" : "unknown";
  const dependencies = Object.values(health.value.dependencies || {});
  if (health.value.status === 1 && dependencies.every((item) => item.status === 1))
    return "success";
  return "warning";
});

const healthStatusClass = computed(() => `is-${healthState.value}`);

const healthItems = computed<HealthItem[]>(() => {
  const data = health.value;
  if (!data) return [];

  const dependencyItems = [
    {
      key: "database",
      label: t("dashboardOverview.health.database"),
      icon: "ri:database-2-line",
      dependency: data.dependencies.database,
    },
    {
      key: "redis",
      label: "Redis",
      icon: "ri:server-line",
      dependency: data.dependencies.redis,
    },
  ].map(({ key, label, icon, dependency }) => {
    const state: HealthState = dependency.status === 1 ? "success" : "error";
    return {
      key,
      label,
      icon,
      detail:
        dependency.latency_ms == null
          ? t("dashboardOverview.health.notAvailable")
          : t("dashboardOverview.health.latency", { value: dependency.latency_ms }),
      statusLabel:
        dependency.status === 1
          ? t("dashboardOverview.health.normal")
          : t("dashboardOverview.health.abnormal"),
      stateClass: `is-${state}`,
    };
  });

  const diskKnown = data.disk_usage >= 0;
  const diskState: HealthState = !diskKnown
    ? "unknown"
    : data.disk_usage >= 90
      ? "warning"
      : "success";
  return [
    ...dependencyItems,
    {
      key: "disk",
      label: t("dashboardOverview.health.disk"),
      icon: "ri:hard-drive-2-line",
      detail: diskKnown
        ? t("dashboardOverview.health.diskUsage", { value: data.disk_usage })
        : t("dashboardOverview.health.notAvailable"),
      statusLabel: diskKnown
        ? diskState === "warning"
          ? t("dashboardOverview.health.attention")
          : t("dashboardOverview.health.available")
        : t("dashboardOverview.health.unavailable"),
      stateClass: `is-${diskState}`,
    },
  ];
});

const lastUpdatedText = computed(() =>
  lastUpdated.value ? formatToDateTime(lastUpdated.value) : t("dashboardOverview.notAvailable")
);
const isLoading = computed(() => statsLoading.value || healthLoading.value);

async function loadStats(): Promise<boolean> {
  statsLoading.value = true;
  statsError.value = null;

  if (!checkPerm("module_monitor:dashboard:query")) {
    stats.value = null;
    statsError.value = "permission";
    statsLoading.value = false;
    return false;
  }

  try {
    const { data: response } = await DashboardAPI.getStats();
    const data = response?.data as DashboardStats | undefined;
    if (!data) throw new Error("Dashboard statistics are unavailable");
    stats.value = data;
    return true;
  } catch {
    stats.value = null;
    statsError.value = "request";
    return false;
  } finally {
    statsLoading.value = false;
  }
}

async function loadHealth(): Promise<boolean> {
  healthLoading.value = true;
  healthError.value = false;
  try {
    const { data: response } = await HealthAPI.getReadiness();
    const data = response?.data as HealthReadiness | undefined;
    if (!data?.dependencies?.database || !data.dependencies.redis)
      throw new Error("Health data is unavailable");
    health.value = data;
    return true;
  } catch {
    health.value = null;
    healthError.value = true;
    return false;
  } finally {
    healthLoading.value = false;
  }
}

async function loadAll() {
  const [statsOk, healthOk] = await Promise.all([loadStats(), loadHealth()]);
  if (statsOk || healthOk) lastUpdated.value = new Date();
}

function formatLoginTime(value: string) {
  return value ? formatToDateTime(value) : t("dashboardOverview.notAvailable");
}

onMounted(() => {
  void loadAll();
  refreshTimer = window.setInterval(() => void loadAll(), REFRESH_INTERVAL_MS);
});

onUnmounted(() => {
  if (refreshTimer !== undefined) window.clearInterval(refreshTimer);
});
</script>

<style scoped>
.dashboard-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.dashboard-overview__welcome,
.dashboard-overview__metric,
.dashboard-overview__activity,
.dashboard-overview__health {
  background: var(--default-box-color);
}

.dashboard-overview__welcome {
  padding: 24px;
}

.dashboard-overview__welcome-main {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.dashboard-overview__mark {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  border-radius: 14px;
}

.dashboard-overview__eyebrow {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--fa-gray-500);
  letter-spacing: 0.01em;
}

.dashboard-overview__title {
  margin: 4px 0 0;
  font-size: clamp(1.35rem, 2vw, 1.75rem);
  font-weight: 650;
  line-height: 1.25;
  color: var(--fa-gray-900);
}

.dashboard-overview__description {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--fa-gray-600);
}

.dashboard-overview__context {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 14px;
  font-size: 12px;
  color: var(--fa-gray-600);
}

.dashboard-overview__context-item {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}

.dashboard-overview__refresh {
  flex: 0 0 auto;
}

.dashboard-overview__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.dashboard-overview__metric {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  min-height: 142px;
  padding: 20px;
}

.dashboard-overview__metric-icon {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
}

.dashboard-overview__metric-icon.is-blue {
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
}

.dashboard-overview__metric-icon.is-green {
  color: var(--el-color-success);
  background: color-mix(in srgb, var(--el-color-success) 12%, transparent);
}

.dashboard-overview__metric-icon.is-indigo {
  color: #6d7cf4;
  background: color-mix(in srgb, #6d7cf4 12%, transparent);
}

.dashboard-overview__metric-label {
  margin: 0;
  font-size: 13px;
  color: var(--fa-gray-600);
}

.dashboard-overview__metric-value {
  margin: 8px 0 0;
  font-size: 28px;
  font-weight: 650;
  line-height: 1;
  color: var(--fa-gray-900);
}

.dashboard-overview__metric-hint {
  margin: 12px 0 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--fa-gray-500);
}

.dashboard-overview__main {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.75fr);
  gap: 16px;
  align-items: start;
}

.dashboard-overview__activity,
.dashboard-overview__health {
  min-width: 0;
  padding: 20px;
}

.dashboard-overview__card-heading,
.dashboard-overview__recent-heading {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.dashboard-overview__card-heading h2,
.dashboard-overview__recent-heading h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--fa-gray-900);
}

.dashboard-overview__card-heading p,
.dashboard-overview__recent-heading p {
  margin: 5px 0 0;
  font-size: 12px;
  color: var(--fa-gray-500);
}

.dashboard-overview__card-summary {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.dashboard-overview__trend {
  min-width: 0;
  min-height: 224px;
  margin-top: 14px;
}

.dashboard-overview__recent-heading {
  padding-top: 16px;
  margin-top: 12px;
  border-top: 1px solid var(--fa-card-border);
}

.dashboard-overview__recent-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 10px;
}

.dashboard-overview__recent-item {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 8px 0;
}

.dashboard-overview__recent-icon,
.dashboard-overview__health-icon {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.dashboard-overview__recent-icon {
  width: 32px;
  height: 32px;
  font-size: 16px;
}

.dashboard-overview__recent-icon.is-success,
.dashboard-overview__health-icon.is-success,
.dashboard-overview__health-status.is-success {
  color: var(--el-color-success);
  background: color-mix(in srgb, var(--el-color-success) 10%, transparent);
}

.dashboard-overview__recent-icon.is-failed,
.dashboard-overview__health-icon.is-error,
.dashboard-overview__health-status.is-error {
  color: var(--el-color-danger);
  background: color-mix(in srgb, var(--el-color-danger) 10%, transparent);
}

.dashboard-overview__recent-user,
.dashboard-overview__recent-meta {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-overview__recent-user {
  font-size: 13px;
  font-weight: 500;
  color: var(--fa-gray-800);
}

.dashboard-overview__recent-meta,
.dashboard-overview__recent-side span {
  font-size: 11px;
  color: var(--fa-gray-500);
}

.dashboard-overview__recent-side {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.dashboard-overview__health-dot {
  width: 8px;
  height: 8px;
  margin-top: 6px;
  background: var(--fa-gray-400);
  border-radius: 50%;
}

.dashboard-overview__health-dot.is-success {
  background: var(--el-color-success);
}

.dashboard-overview__health-dot.is-warning {
  background: var(--el-color-warning);
}

.dashboard-overview__health-dot.is-error {
  background: var(--el-color-danger);
}

.dashboard-overview__health-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 22px;
}

.dashboard-overview__health-item {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 12px 0;
  border-bottom: 1px solid var(--fa-card-border);
}

.dashboard-overview__health-item:last-child {
  border-bottom: 0;
}

.dashboard-overview__health-icon {
  width: 34px;
  height: 34px;
  font-size: 17px;
}

.dashboard-overview__health-icon.is-warning,
.dashboard-overview__health-status.is-warning {
  color: var(--el-color-warning);
  background: color-mix(in srgb, var(--el-color-warning) 12%, transparent);
}

.dashboard-overview__health-icon.is-unknown,
.dashboard-overview__health-status.is-unknown {
  color: var(--fa-gray-500);
  background: color-mix(in srgb, var(--fa-gray-500) 10%, transparent);
}

.dashboard-overview__health-item p,
.dashboard-overview__health-item span {
  margin: 0;
}

.dashboard-overview__health-item p {
  font-size: 13px;
  font-weight: 500;
  color: var(--fa-gray-800);
}

.dashboard-overview__health-item div > span {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: var(--fa-gray-500);
}

.dashboard-overview__health-status {
  flex: 0 0 auto;
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 6px;
}

.dashboard-overview__loading {
  min-height: 150px;
  padding-top: 18px;
}

.dashboard-overview__state {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  font-size: 13px;
  color: var(--fa-gray-500);
  text-align: center;
}

.dashboard-overview__state--compact {
  min-height: 68px;
}

.dashboard-overview__state--error {
  color: var(--el-color-danger);
}

.dashboard-overview__footer {
  min-height: 18px;
  font-size: 11px;
  color: var(--fa-gray-500);
  text-align: right;
}

@media (width <= 1100px) {
  .dashboard-overview__main {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (width <= 820px) {
  .dashboard-overview__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (width <= 640px) {
  .dashboard-overview__welcome {
    padding: 18px;
  }

  .dashboard-overview__welcome-main {
    flex-wrap: wrap;
  }

  .dashboard-overview__refresh {
    width: 100%;
    margin-left: 64px;
  }

  .dashboard-overview__metrics {
    grid-template-columns: minmax(0, 1fr);
  }

  .dashboard-overview__metric,
  .dashboard-overview__activity,
  .dashboard-overview__health {
    padding: 16px;
  }

  .dashboard-overview__recent-side span {
    display: none;
  }
}
</style>
