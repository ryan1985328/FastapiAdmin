<template>
  <div class="fa-full-height referral-page">
    <ElCard shadow="never" class="referral-card referral-search-card">
      <div class="referral-card__heading">
        <div>
          <h2 class="referral-card__title">推荐关系</h2>
          <p class="referral-card__description">
            搜索用户，查看其在推荐网络中的位置并继续向下追踪。
          </p>
        </div>
      </div>

      <div class="referral-search-form">
        <ElInput
          v-model="keyword"
          clearable
          size="large"
          class="referral-search-input"
          placeholder="ID / 用户名 / 昵称 / 手机号 / 推荐码"
          @keyup.enter="searchUsers"
        >
          <template #prefix>
            <ElIcon><Search /></ElIcon>
          </template>
        </ElInput>
        <ElButton type="primary" size="large" :loading="searchLoading" @click="searchUsers">
          搜索
        </ElButton>
      </div>

      <div v-if="searchPerformed && !searchLoading" class="referral-search-results">
        <div class="referral-search-results__header">
          <span>匹配用户</span>
          <span class="text-g-500">共 {{ searchTotal }} 条</span>
        </div>

        <div v-if="searchResults.length" class="referral-search-results__list">
          <button
            v-for="user in searchResults"
            :key="user.user_id"
            type="button"
            class="referral-search-result"
            :class="{ 'is-selected': summary?.user_id === user.user_id }"
            @click="selectUser(user.user_id)"
          >
            <span class="referral-search-result__main">
              <strong>{{ formatUserIdentity(user) }}</strong>
              <span>{{ user.mobile || "未填写手机号" }}</span>
            </span>
            <span class="referral-search-result__meta">
              <span>ID {{ user.user_id }}</span>
              <span>推荐码 {{ user.referral_code }}</span>
            </span>
          </button>
        </div>
        <ElEmpty v-else :image-size="72" description="未找到匹配用户" />

        <p v-if="searchTotal > searchResults.length" class="referral-search-results__hint">
          匹配结果较多，请继续缩小关键词范围。
        </p>
      </div>
    </ElCard>

    <ElCard v-if="summary" v-loading="summaryLoading" shadow="never" class="referral-card">
      <div class="referral-card__heading referral-summary-heading">
        <div>
          <div class="referral-card__eyebrow">当前用户</div>
          <h2 class="referral-card__title">{{ formatUserIdentity(summary) }}</h2>
          <p class="referral-card__description">用户 ID {{ summary.user_id }}</p>
        </div>
        <div class="referral-card__actions">
          <ElButton
            v-if="canViewUser"
            type="primary"
            plain
            size="small"
            @click="viewUser(summary.user_id)"
          >
            查看用户
          </ElButton>
        </div>
      </div>

      <FaDescriptions
        :column="2"
        :border="true"
        :data="summary"
        :items="summaryItems"
        :scrollbar="false"
      >
        <template #mobile="{ value }">
          <span>{{ value || "—" }}</span>
        </template>
        <template #status="{ value }">
          <FaStatusTag v-bind="dictTagProps(USER_STATUS_DICT, value)" />
        </template>
        <template #kyc_status="{ value }">
          <FaStatusTag v-bind="dictTagProps(KYC_STATUS_DICT, value)" />
        </template>
        <template #referrer>
          <ElButton
            v-if="summary.referrer"
            link
            type="primary"
            class="referral-inline-link"
            @click="selectUser(summary.referrer.user_id)"
          >
            {{ formatUserIdentity(summary.referrer) }}
          </ElButton>
          <span v-else-if="summary.referrer_id">关联用户不可用</span>
          <span v-else>无 / 顶级用户</span>
        </template>
        <template #referrer_bound_at>
          <span>{{ formatDateTime(summary.referrer_bound_at) }}</span>
        </template>
      </FaDescriptions>

      <div class="referral-metrics">
        <div class="referral-metric">
          <span class="referral-metric__label">直属下级</span>
          <strong class="referral-metric__value">{{ summary.direct_count }}</strong>
          <span class="referral-metric__hint">直接推荐用户</span>
        </div>
        <div class="referral-metric">
          <span class="referral-metric__label">团队总人数</span>
          <strong class="referral-metric__value">{{ summary.total_descendant_count }}</strong>
          <span class="referral-metric__hint">所有层级后代</span>
        </div>
      </div>
    </ElCard>

    <ElCard v-if="summary" shadow="never" class="referral-card referral-tree-card">
      <div class="referral-card__heading">
        <div>
          <div class="referral-card__eyebrow">关系浏览</div>
          <h2 class="referral-card__title">推荐关系</h2>
          <p class="referral-card__description">
            保留层级树的逐层浏览，并增加关系画布用于理解推荐层级；所有视图均为只读。
          </p>
        </div>
      </div>

      <ElTabs
        v-model="activeReferralView"
        class="referral-view-tabs"
        @tab-change="handleReferralViewChange"
      >
        <ElTabPane label="层级树" name="hierarchy">
          <ElEmpty
            v-if="summary.direct_count === 0"
            :image-size="96"
            description="该用户暂无直属下级"
            class="referral-tree-empty"
          />
          <ElTree
            v-else
            :key="treeRenderKey"
            ref="treeRef"
            node-key="user_id"
            lazy
            :data="treeData"
            :props="treeProps"
            :load="loadTreeNode"
            :expand-on-click-node="false"
            :default-expanded-keys="[summary.user_id]"
            class="referral-tree"
          >
            <template #default="{ data }">
              <div class="referral-tree-node">
                <div class="referral-tree-node__identity">
                  <strong>{{ formatUserIdentity(data) }}</strong>
                  <span class="referral-tree-node__meta">
                    ID {{ data.user_id }} · {{ data.mobile || "未填写手机号" }} · 推荐码
                    {{ data.referral_code }}
                  </span>
                </div>
                <div class="referral-tree-node__details">
                  <FaStatusTag v-bind="dictTagProps(USER_STATUS_DICT, data.status)" size="small" />
                  <FaStatusTag
                    v-bind="dictTagProps(KYC_STATUS_DICT, data.kyc_status)"
                    size="small"
                  />
                  <span class="referral-tree-node__count">直属 {{ data.direct_count }}</span>
                  <span v-if="data.referrer_bound_at" class="referral-tree-node__bound-time">
                    绑定 {{ formatDateTime(data.referrer_bound_at) }}
                  </span>
                  <ElButton link type="primary" size="small" @click.stop="focusUser(data.user_id)">
                    以此为中心
                  </ElButton>
                  <ElButton
                    v-if="canViewUser"
                    link
                    type="primary"
                    size="small"
                    @click.stop="viewUser(data.user_id)"
                  >
                    查看用户
                  </ElButton>
                </div>
              </div>
            </template>
          </ElTree>
        </ElTabPane>

        <ElTabPane label="关系画布" name="canvas" lazy>
          <ElEmpty
            v-if="summary.direct_count === 0"
            :image-size="96"
            description="该用户暂无直属下级"
            class="referral-tree-empty"
          />
          <div v-else-if="canvasLoading" class="referral-canvas-state" role="status">
            正在加载关系画布…
          </div>
          <div v-else-if="canvasError" class="referral-canvas-error" role="alert">
            <span>{{ canvasError }}</span>
            <ElButton type="primary" plain size="small" @click="loadCanvasTree">重试</ElButton>
          </div>
          <AppUserReferralCanvas
            v-else-if="canvasTree"
            :tree="canvasTree"
            :loaded-count="canvasLoadedCount"
            :max-depth="REFERRAL_CANVAS_MAX_DEPTH"
            :node-budget="REFERRAL_CANVAS_NODE_BUDGET"
            :truncated="canvasTruncated"
            :skipped-count="canvasSkippedCount"
            :can-view-user="canViewUser"
            :maximized="canvasMaximized"
            @node-detail="viewUser"
            @toggle-maximize="toggleCanvasMaximize"
          />
          <ElEmpty
            v-else
            :image-size="96"
            description="切换到关系画布后加载当前用户关系"
            class="referral-tree-empty"
          />
        </ElTabPane>
      </ElTabs>
    </ElCard>

    <ElEmpty
      v-else-if="!summaryLoading"
      :image-size="120"
      description="搜索并选择一个用户开始查看"
    />
  </div>
</template>

<script setup lang="ts">
import { Search } from "@element-plus/icons-vue";
import type { LoadFunction, TreeInstance } from "element-plus";
import { ElMessage } from "element-plus";
import { formatToDateTime } from "@utils";
import FaDescriptions, {
  type DescriptionsItem,
} from "@/components/display/fa-descriptions/index.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import AppUserReferralCanvas from "@/components/charts/fa-referral-tree/index.vue";
import AppUserAPI, {
  type AppUserKycStatus,
  type AppUserReferralNode,
  type AppUserReferralSummary,
} from "@/api/module_system/app_user";
import {
  loadReferralCanvasTree,
  REFERRAL_CANVAS_MAX_DEPTH,
  REFERRAL_CANVAS_NODE_BUDGET,
  REFERRAL_CANVAS_PAGE_SIZE,
  type ReferralCanvasNode,
} from "@/utils/app-user-referral-tree";
import { checkPerm } from "@/utils/checkPerm";
import { useDictStore } from "@stores";
import { computed, nextTick, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

defineOptions({
  name: "AppUserReferralTree",
  inheritAttrs: false,
});

const USER_STATUS_DICT = "app_user_status";
const KYC_STATUS_DICT = "app_user_kyc_status";
const TREE_PAGE_SIZE = 50;
const SEARCH_PAGE_SIZE = 20;
const DICT_TAG_TYPES = ["primary", "success", "warning", "danger", "info"] as const;
type DictTagType = (typeof DICT_TAG_TYPES)[number];

type ReferralTreeNode = AppUserReferralNode & {
  label: string;
  is_leaf: boolean;
  ancestor_user_ids: number[];
};

const treeProps = {
  children: "children",
  label: "label",
  isLeaf: "is_leaf",
};

const dictStore = useDictStore();
const router = useRouter();
const canViewUser = computed(() => checkPerm("module_system:app_user:detail"));
const keyword = ref("");
const searchLoading = ref(false);
const searchPerformed = ref(false);
const searchTotal = ref(0);
const searchResults = ref<AppUserReferralNode[]>([]);
const summaryLoading = ref(false);
const summary = ref<AppUserReferralSummary | null>(null);
const treeData = ref<ReferralTreeNode[]>([]);
const treeRenderKey = ref(0);
const treeRef = ref<TreeInstance>();
const activeReferralView = ref<"hierarchy" | "canvas">("hierarchy");
const canvasTree = ref<ReferralCanvasNode | null>(null);
const canvasLoading = ref(false);
const canvasError = ref("");
const canvasLoadedCount = ref(0);
const canvasTruncated = ref(false);
const canvasSkippedCount = ref(0);
const canvasMaximized = ref(false);
let canvasRequestSequence = 0;

const summaryItems: DescriptionsItem[] = [
  { label: "用户 ID", prop: "user_id" },
  { label: "手机号", prop: "mobile" },
  { label: "推荐码", prop: "referral_code" },
  { label: "账号状态", prop: "status" },
  { label: "实名状态", prop: "kyc_status" },
  { label: "推荐人", prop: "referrer" },
  { label: "推荐绑定时间", prop: "referrer_bound_at" },
];

const USER_STATUS_FALLBACK: Record<string, string> = {
  "0": "正常",
  "1": "禁用",
  "2": "冻结",
};
const KYC_STATUS_FALLBACK: Record<AppUserKycStatus, string> = {
  unverified: "未实名",
  pending: "待审核",
  verified: "已实名",
  rejected: "已驳回",
};

function getDictTagType(value?: string): DictTagType {
  return DICT_TAG_TYPES.includes(value as DictTagType) ? (value as DictTagType) : "info";
}

function dictTagProps(dictType: string, value: unknown) {
  const lookupValue = String(value ?? "");
  const entry = dictStore.dictData[dictType]?.find((item) => item.dict_value === lookupValue);
  const fallback =
    dictType === USER_STATUS_DICT
      ? USER_STATUS_FALLBACK[lookupValue]
      : KYC_STATUS_FALLBACK[lookupValue as AppUserKycStatus];
  return {
    type: getDictTagType(entry?.list_class),
    label: entry?.dict_label ?? fallback ?? "未知",
  };
}

function formatUserIdentity(
  user?: Pick<AppUserReferralNode, "username" | "nickname"> | null
): string {
  if (!user) return "—";
  const username = user.username?.trim();
  const nickname = user.nickname?.trim();
  if (nickname && username && nickname !== username) return `${nickname}（${username}）`;
  return nickname || username || "—";
}

function formatDateTime(value?: string | null): string {
  return value ? formatToDateTime(value) : "—";
}

function toTreeNode(user: AppUserReferralNode, ancestorUserIds: number[] = []): ReferralTreeNode {
  return {
    ...user,
    label: formatUserIdentity(user),
    is_leaf: !user.has_children,
    ancestor_user_ids: ancestorUserIds,
  };
}

function clearCanvasState() {
  canvasRequestSequence += 1;
  canvasLoading.value = false;
  canvasError.value = "";
  canvasTree.value = null;
  canvasLoadedCount.value = 0;
  canvasTruncated.value = false;
  canvasSkippedCount.value = 0;
  canvasMaximized.value = false;
}

async function loadCanvasTree() {
  const root = summary.value;
  if (!root || root.direct_count === 0) {
    clearCanvasState();
    return;
  }

  const requestSequence = ++canvasRequestSequence;
  canvasLoading.value = true;
  canvasError.value = "";
  canvasTree.value = null;
  canvasLoadedCount.value = 0;
  canvasTruncated.value = false;
  canvasSkippedCount.value = 0;

  try {
    const result = await loadReferralCanvasTree(
      root,
      async (userId, pageNo, pageSize) => {
        const response = await AppUserAPI.getReferralChildren(userId, {
          page_no: pageNo,
          page_size: pageSize,
        });
        return response.data.data;
      },
      {
        maxDepth: REFERRAL_CANVAS_MAX_DEPTH,
        nodeBudget: REFERRAL_CANVAS_NODE_BUDGET,
        pageSize: REFERRAL_CANVAS_PAGE_SIZE,
        shouldCancel: () => requestSequence !== canvasRequestSequence,
      }
    );

    if (requestSequence !== canvasRequestSequence || result.cancelled) return;
    canvasTree.value = result.tree;
    canvasLoadedCount.value = result.loadedCount;
    canvasTruncated.value = result.truncated;
    canvasSkippedCount.value = result.skippedCount;
  } catch {
    if (requestSequence === canvasRequestSequence) {
      canvasTree.value = null;
      canvasError.value = "关系画布加载失败，请重试。";
    }
  } finally {
    if (requestSequence === canvasRequestSequence) canvasLoading.value = false;
  }
}

function handleReferralViewChange(view: string | number) {
  if (String(view) !== "canvas" || !summary.value) return;
  if (canvasTree.value?.user_id === summary.value.user_id && !canvasError.value) return;
  void loadCanvasTree();
}

function toggleCanvasMaximize() {
  canvasMaximized.value = !canvasMaximized.value;
}

async function searchUsers() {
  const value = keyword.value.trim();
  if (!value) {
    ElMessage.warning("请输入用户 ID、用户名、昵称、手机号或推荐码");
    return;
  }

  searchLoading.value = true;
  searchPerformed.value = true;
  searchResults.value = [];
  searchTotal.value = 0;
  try {
    const response = await AppUserAPI.searchReferralUsers({
      keyword: value,
      page_no: 1,
      page_size: SEARCH_PAGE_SIZE,
    });
    const page = response.data.data;
    searchResults.value = page.items;
    searchTotal.value = page.total;
    if (page.total === 1 && page.items[0]) {
      await selectUser(page.items[0].user_id);
    } else if (!page.total) {
      summary.value = null;
      treeData.value = [];
      clearCanvasState();
    }
  } catch {
    summary.value = null;
    treeData.value = [];
    clearCanvasState();
  } finally {
    searchLoading.value = false;
  }
}

async function selectUser(userId: number) {
  clearCanvasState();
  summaryLoading.value = true;
  try {
    const response = await AppUserAPI.getReferralSummary(userId);
    summary.value = response.data.data;
    treeData.value = [toTreeNode(summary.value)];
    treeRenderKey.value += 1;
    await nextTick();
    treeRef.value?.getNode(userId)?.expand();
    if (activeReferralView.value === "canvas") void loadCanvasTree();
  } catch {
    summary.value = null;
    treeData.value = [];
    clearCanvasState();
  } finally {
    summaryLoading.value = false;
  }
}

const loadTreeNode: LoadFunction = async (node, resolve) => {
  // Element Plus invokes the lazy loader once for its synthetic level-0 root.
  // The actual center user is supplied as the first item in treeData, so the
  // synthetic root must expose that item before user-level loading begins.
  if (node.level === 0) {
    resolve(treeData.value);
    return;
  }

  const parent = node.data as ReferralTreeNode;
  const ancestorUserIds = [...parent.ancestor_user_ids, parent.user_id];
  const seenUserIds = new Set(ancestorUserIds);
  const children: ReferralTreeNode[] = [];
  let skippedCount = 0;
  let pageNo = 1;
  try {
    while (true) {
      const response = await AppUserAPI.getReferralChildren(parent.user_id, {
        page_no: pageNo,
        page_size: TREE_PAGE_SIZE,
      });
      const page = response.data.data;
      for (const user of page.items) {
        if (seenUserIds.has(user.user_id)) {
          skippedCount += 1;
          continue;
        }
        seenUserIds.add(user.user_id);
        children.push(toTreeNode(user, ancestorUserIds));
      }

      if (!page.has_next || page.items.length === 0) break;
      pageNo += 1;
    }

    if (skippedCount > 0) ElMessage.warning("发现异常或重复推荐关系，已忽略异常节点");
    if (!children.length) parent.is_leaf = true;
    resolve(children);
  } catch {
    // Preserve any successfully loaded pages if a later page fails.
    resolve(children);
  }
};

function focusUser(userId: number) {
  void selectUser(userId);
}

function viewUser(userId: number) {
  if (!canViewUser.value) return;
  void router.push({
    name: "AppUserUsers",
    query: { user_id: String(userId) },
  });
}

onMounted(() => {
  void dictStore.getDict([USER_STATUS_DICT, KYC_STATUS_DICT]);
});
</script>

<style scoped lang="scss">
.referral-page {
  padding: 0 0 16px;
  overflow: auto;
}

.referral-card {
  margin-bottom: 12px;
}

.referral-search-card {
  position: relative;
  z-index: 1;
}

.referral-card__heading {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
}

.referral-summary-heading {
  align-items: center;
}

.referral-card__eyebrow {
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  letter-spacing: 0.08em;
}

.referral-card__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--el-text-color-primary);
}

.referral-card__description {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.referral-card__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.referral-search-form {
  display: flex;
  gap: 12px;
  align-items: center;
  max-width: 760px;
}

.referral-search-input {
  flex: 1;
}

.referral-search-results {
  padding-top: 14px;
  margin-top: 18px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.referral-search-results__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.referral-search-results__list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 8px;
}

.referral-search-result {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 12px;
  color: var(--el-text-color-primary);
  text-align: left;
  cursor: pointer;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  transition:
    border-color 0.2s,
    background-color 0.2s;
}

.referral-search-result:hover,
.referral-search-result.is-selected {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.referral-search-result__main,
.referral-search-result__meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.referral-search-result__main {
  overflow: hidden;
}

.referral-search-result__main strong,
.referral-search-result__main span,
.referral-search-result__meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.referral-search-result__main span,
.referral-search-result__meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.referral-search-results__hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.referral-inline-link {
  padding: 0;
}

.referral-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.referral-metric {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 14px 16px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.referral-metric__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.referral-metric__value {
  font-size: 26px;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.referral-metric__hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.referral-tree-card {
  min-height: 260px;
}

.referral-tree-empty {
  padding: 20px 0 30px;
}

.referral-tree {
  --el-tree-node-hover-bg-color: var(--el-color-primary-light-9);

  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.referral-canvas-state,
.referral-canvas-error {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  min-height: 460px;
  padding: 24px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.referral-canvas-error {
  flex-direction: column;
  color: var(--el-color-danger);
}

.referral-tree-node {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-width: 0;
  padding: 5px 8px 5px 0;
}

.referral-tree-node__identity,
.referral-tree-node__details {
  display: flex;
  align-items: center;
  min-width: 0;
}

.referral-tree-node__identity {
  flex: 1;
  gap: 10px;
}

.referral-tree-node__identity strong {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.referral-tree-node__meta,
.referral-tree-node__count,
.referral-tree-node__bound-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.referral-tree-node__meta {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.referral-tree-node__details {
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}

@media (width <= 900px) {
  .referral-tree-node {
    flex-direction: column;
    gap: 6px;
    align-items: flex-start;
  }

  .referral-tree-node__details {
    justify-content: flex-start;
  }
}

@media (width <= 560px) {
  .referral-search-form,
  .referral-summary-heading {
    flex-direction: column;
    align-items: stretch;
  }

  .referral-search-form .el-button {
    width: 100%;
  }

  .referral-metrics {
    grid-template-columns: 1fr;
  }

  .referral-search-results__list {
    grid-template-columns: 1fr;
  }
}
</style>
