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

      <div
        v-if="searchPerformed && !searchLoading && searchResultsExpanded"
        class="referral-search-results"
      >
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

    <ElCard
      v-if="summary"
      v-loading="summaryLoading"
      shadow="never"
      class="referral-card referral-summary-card"
    >
      <div class="referral-summary">
        <div class="referral-summary__identity">
          <div class="referral-card__eyebrow">当前用户</div>
          <h2 class="referral-card__title">{{ formatUserIdentity(summary) }}</h2>
          <div class="referral-summary__meta">
            <span>ID {{ summary.user_id }}</span>
            <span>{{ summary.mobile || "未填写手机号" }}</span>
            <span v-if="summary.referral_code">推荐码 {{ summary.referral_code }}</span>
          </div>
        </div>

        <div class="referral-summary__relationship">
          <div class="referral-summary__fact">
            <span>直属下级</span>
            <strong>{{ summary.direct_count }}</strong>
          </div>
          <div class="referral-summary__fact">
            <span>团队人数</span>
            <strong>{{ summary.total_descendant_count }}</strong>
          </div>
          <div class="referral-summary__referrer">
            <span>推荐人</span>
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
          </div>
        </div>

        <div class="referral-summary__statuses">
          <FaStatusTag v-bind="dictTagProps(USER_STATUS_DICT, summary.status)" />
          <FaStatusTag v-bind="dictTagProps(KYC_STATUS_DICT, summary.kyc_status)" />
        </div>

        <div class="referral-summary__actions">
          <ElButton plain size="small" class="referral-switch-user" @click="switchUser">
            切换用户
          </ElButton>
          <ElButton
            v-if="canViewUser"
            type="primary"
            plain
            size="small"
            class="referral-view-user"
            @click="openUserDetail(summary.user_id)"
          >
            查看用户
          </ElButton>
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
                    @click.stop="openUserDetail(data.user_id)"
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
            @node-detail="openUserDetail"
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

    <FaDialog
      v-if="nodeDetailVisible"
      v-model="nodeDetailVisible"
      title="用户端用户详情"
      width="720px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      form-mode="detail"
      @close="closeNodeDetail"
    >
      <div v-if="nodeDetailLoading" class="referral-detail-state" role="status">
        正在加载用户详情…
      </div>
      <AppUserDetailContent v-else :data="nodeDetail" />
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { Search } from "@element-plus/icons-vue";
import type { LoadFunction, TreeInstance } from "element-plus";
import { ElMessage } from "element-plus";
import { formatToDateTime } from "@utils";
import FaDialog from "@/components/modal/fa-dialog/index.vue";
import AppUserDetailContent from "./AppUserDetailContent.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import AppUserReferralCanvas from "@/components/charts/fa-referral-tree/index.vue";
import AppUserAPI, {
  type AppUserKycStatus,
  type AppUserReferralNode,
  type AppUserReferralSummary,
  type AppUserTable,
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
const canViewUser = computed(() => checkPerm("module_system:app_user:detail"));
const keyword = ref("");
const searchLoading = ref(false);
const searchPerformed = ref(false);
const searchTotal = ref(0);
const searchResults = ref<AppUserReferralNode[]>([]);
const searchResultsExpanded = ref(false);
const summaryLoading = ref(false);
const summary = ref<AppUserReferralSummary | null>(null);
const nodeDetailVisible = ref(false);
const nodeDetailLoading = ref(false);
const nodeDetail = ref<Partial<AppUserTable>>({});
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
let nodeDetailRequestSequence = 0;

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
  searchResultsExpanded.value = true;
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
    }
  } catch {
    // Keep the current relationship center while a replacement search fails.
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
    searchResultsExpanded.value = false;
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

function switchUser() {
  searchResultsExpanded.value = true;
}

async function openUserDetail(userId: number) {
  if (!canViewUser.value) return;

  const requestSequence = ++nodeDetailRequestSequence;
  nodeDetail.value = {};
  nodeDetailLoading.value = true;
  nodeDetailVisible.value = true;

  try {
    const response = await AppUserAPI.getAppUserDetail(userId);
    if (requestSequence !== nodeDetailRequestSequence) return;
    nodeDetail.value = response.data.data ?? {};
  } catch {
    if (requestSequence === nodeDetailRequestSequence) {
      nodeDetailVisible.value = false;
      ElMessage.error("用户详情加载失败，请重试。");
    }
  } finally {
    if (requestSequence === nodeDetailRequestSequence) nodeDetailLoading.value = false;
  }
}

function closeNodeDetail() {
  nodeDetailRequestSequence += 1;
  nodeDetailLoading.value = false;
  nodeDetailVisible.value = false;
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
  flex-shrink: 0;
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

.referral-summary {
  display: grid;
  grid-template-columns: minmax(190px, 1.1fr) minmax(280px, 1.5fr) auto auto;
  gap: 18px 24px;
  align-items: center;
}

.referral-summary__identity,
.referral-summary__relationship {
  min-width: 0;
}

.referral-summary__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  margin-top: 5px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.referral-summary__relationship {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 22px;
  align-items: center;
}

.referral-summary__fact,
.referral-summary__referrer {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 56px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.referral-summary__fact strong {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.25;
  color: var(--el-text-color-primary);
}

.referral-summary__referrer {
  min-width: 128px;
  max-width: 220px;
}

.referral-summary__referrer .referral-inline-link {
  justify-content: flex-start;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.referral-summary__statuses,
.referral-summary__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
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
.referral-canvas-error,
.referral-detail-state {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  min-height: 460px;
  padding: 24px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.referral-detail-state {
  min-height: 220px;
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
  .referral-summary {
    grid-template-columns: minmax(190px, 1fr) minmax(240px, 1.2fr) auto;
  }

  .referral-summary__actions {
    grid-column: 1 / -1;
    justify-content: flex-end;
  }

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
  .referral-search-form {
    flex-direction: column;
    align-items: stretch;
  }

  .referral-search-form .el-button {
    width: 100%;
  }

  .referral-summary {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .referral-summary__actions {
    grid-column: auto;
    justify-content: flex-start;
  }

  .referral-search-results__list {
    grid-template-columns: 1fr;
  }
}
</style>
