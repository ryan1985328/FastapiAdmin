<template>
  <div class="relative flex flex-col last:mb-0">
    <ElRow :gutter="20">
      <ElCol :xs="24" :md="18">
        <Banner class="mb-5" />
        <CardList />
      </ElCol>

      <ElCol :xs="24" :md="6" class="flex flex-col gap-5">
        <QuickLinks class="mb-5" />
        <FaDataListCard
          v-if="healthList.length"
          :max-count="4"
          :list="healthList"
          title="系统健康"
          subtitle="来自健康检查接口"
        />
      </ElCol>
    </ElRow>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import HealthAPI, { type HealthDependency, type HealthReadiness } from "@/api/module_common/health";
import Banner from "./modules/banner.vue";
import CardList from "./modules/card-list.vue";
import QuickLinks from "./modules/quick-links.vue";

defineOptions({ name: "Home", inheritAttrs: false });

interface HealthListItem {
  icon: string;
  class: string;
  title: string;
  status: string;
  time: string;
}

const healthList = ref<HealthListItem[]>([]);

const statusClass = (status: string) =>
  status === "正常" ? "bg-success/12 text-success" : "bg-warning/12 text-warning";

const dependencyItem = (
  title: string,
  icon: string,
  dependency: HealthDependency,
  checkedAt: string
): HealthListItem => {
  const status = dependency.status === 1 ? "正常" : "异常";
  return {
    title,
    icon,
    class: statusClass(status),
    status,
    time: dependency.latency_ms == null ? checkedAt : `${dependency.latency_ms} ms`,
  };
};

const formatTimestamp = (timestamp: string) => timestamp.replace("T", " ").slice(0, 19);

function buildHealthList(data: HealthReadiness): HealthListItem[] {
  const checkedAt = formatTimestamp(data.timestamp);
  const database = data.dependencies.database;
  const redis = data.dependencies.redis;
  const diskAvailable = data.disk_usage >= 0;

  return [
    dependencyItem("数据库", "ri:database-2-line", database, checkedAt),
    dependencyItem("Redis", "ri:server-line", redis, checkedAt),
    {
      title: "磁盘",
      icon: "ri:hard-drive-2-line",
      class: diskAvailable ? "bg-success/12 text-success" : "bg-warning/12 text-warning",
      status: diskAvailable ? "可用" : "不可用",
      time: diskAvailable ? `${data.disk_usage}% 已使用` : checkedAt,
    },
  ];
}

async function loadHealth() {
  try {
    const { data: response } = await HealthAPI.getReadiness();
    const data = response?.data as HealthReadiness | undefined;
    if (data?.dependencies?.database && data.dependencies.redis) {
      healthList.value = buildHealthList(data);
    }
  } catch {
    // 健康接口不可用时不显示未经确认的状态。
    healthList.value = [];
  }
}

onMounted(loadHealth);
</script>
