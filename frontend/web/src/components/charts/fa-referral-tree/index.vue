<template>
  <section
    class="referral-canvas"
    :class="{ 'is-maximized': props.maximized }"
    :aria-busy="!chartReady"
  >
    <div class="referral-canvas__toolbar">
      <div class="referral-canvas__help">
        <span class="referral-canvas__direction"
          >上级推荐人 <span aria-hidden="true">↓</span> 被推荐会员</span
        >
        <span>点击节点查看用户；点击 +/− 展开/收起；拖动浏览，Ctrl/Cmd+滚轮缩放。</span>
        <span>已展示 {{ visibleNodeCount }} 个节点</span>
      </div>
      <div class="referral-canvas__actions">
        <ElButton
          class="referral-canvas__zoom-button"
          :disabled="!chartReady || zoomScale <= ZOOM_MIN"
          aria-label="缩小关系画布"
          title="缩小 15%"
          @click="zoomOut"
        >
          −
        </ElButton>
        <ElButton
          class="referral-canvas__zoom-reset"
          :disabled="!chartReady"
          :aria-label="`恢复关系画布缩放至 ${zoomLabel}`"
          title="恢复 100% 缩放"
          @click="resetZoom"
        >
          {{ zoomLabel }}
        </ElButton>
        <ElButton
          class="referral-canvas__zoom-button"
          :disabled="!chartReady || zoomScale >= ZOOM_MAX"
          aria-label="放大关系画布"
          title="放大 15%"
          @click="zoomIn"
        >
          ＋
        </ElButton>
        <ElButton plain :disabled="!chartReady" title="适配当前已展开的可见节点" @click="fitView">
          适应画布
        </ElButton>
        <ElButton
          plain
          :disabled="!chartReady"
          title="保持当前缩放并将 Root 置中"
          @click="resetView"
        >
          回到中心
        </ElButton>
        <ElButton :disabled="!chartReady" @click="emit('toggle-maximize')">
          {{ props.maximized ? "退出最大化" : "最大化" }}
        </ElButton>
      </div>
    </div>

    <div class="referral-canvas__frame" :style="{ height: `${chartHeight}px` }">
      <div
        ref="chartRef"
        class="referral-canvas__chart"
        role="img"
        aria-label="推荐关系画布：上级推荐人到被推荐会员"
      />
      <div v-if="!chartReady" class="referral-canvas__state" role="status">正在准备关系画布…</div>
    </div>

    <div v-if="props.truncated || props.skippedCount" class="referral-canvas__notice" role="status">
      <span>
        当前画布为受限只读视图：自动加载最多第 {{ props.maxDepth }} 层、{{
          props.nodeBudget
        }}
        个节点。 已展示 {{ visibleNodeCount }} 个节点，不代表完整关系网络。
        <template v-if="props.skippedCount"
          >已忽略 {{ props.skippedCount }} 条异常或重复关系。</template
        >
      </span>
    </div>

    <div v-if="selectedNode" class="referral-canvas__selection">
      <span
        >已选中 ID {{ selectedNode.user_id }} ·
        {{ selectedNode.level === 0 ? "当前 Root" : `第 ${selectedNode.level} 层` }}</span
      >
      <ElButton
        v-if="props.canViewUser"
        link
        type="primary"
        size="small"
        title="打开用户详情"
        @click="emit('node-detail', selectedNode.user_id)"
      >
        查看用户
      </ElButton>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ECElementEvent } from "echarts/core";
import type {
  EChartsOption,
  TooltipComponentFormatterCallbackParams,
  TreeSeriesOption,
} from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useChart } from "@/hooks/core/useChart";
import { getCssVar } from "@utils";
import {
  countVisibleReferralCanvasNodes,
  resolveReferralCanvasClickAction,
  type ReferralCanvasNode,
} from "@/utils/app-user-referral-tree";

defineOptions({ name: "FaReferralTreeCanvas" });

const ZOOM_MIN = 0.45;
const ZOOM_MAX = 2.25;
const ZOOM_STEP = 0.15;

const props = withDefaults(
  defineProps<{
    tree: ReferralCanvasNode;
    loadedCount: number;
    maxDepth: number;
    nodeBudget: number;
    truncated: boolean;
    skippedCount: number;
    canViewUser: boolean;
    maximized?: boolean;
  }>(),
  { maximized: false }
);

const emit = defineEmits<{
  "node-detail": [userId: number];
  "toggle-maximize": [];
}>();

type StatusTone = "normal" | "disabled" | "frozen" | "unknown";
type ChartProfile = {
  initialTreeDepth: number;
  nodeWidth: number;
  fontSize: number;
  compact: boolean;
};
type ChartView = { zoom: number; center: [number, number] | null };
type CanvasChartNode = {
  id: string;
  name: string;
  user_id: number;
  displayName: string;
  mobile: string | null | undefined;
  status: number;
  directCount: number;
  hasChildren: boolean;
  hasLoadedChildren: boolean;
  isRoot: boolean;
  level: number;
  isTruncated: boolean;
  children: CanvasChartNode[];
  [key: string]: unknown;
};

const { chartRef, initChart, getChartInstance, handleResize, isDark } = useChart({
  autoTheme: false,
});
const chartReady = ref(false);
const selectedNode = ref<CanvasChartNode | null>(null);
const zoomScale = ref(1);
const wheelAttached = ref(false);
const expandedNodes = reactive(new Set<number>());

const cssColor = (name: string, fallback: string): string => getCssVar(name).trim() || fallback;

const palette = computed(() => {
  const dark = isDark.value;
  return {
    canvas: cssColor("--el-fill-color-lighter", dark ? "#1d1e1f" : "#f5f7fa"),
    surface: cssColor("--el-bg-color-overlay", dark ? "#1d1e1f" : "#ffffff"),
    rootSurface: cssColor("--el-color-primary-light-9", dark ? "#18222d" : "#ecf5ff"),
    primary: cssColor("--el-color-primary", dark ? "#409eff" : "#409eff"),
    primaryBorder: cssColor("--el-color-primary-light-3", dark ? "#337ecc" : "#79bbff"),
    text: cssColor("--el-text-color-primary", dark ? "#e5eaf3" : "#303133"),
    secondary: cssColor("--el-text-color-secondary", dark ? "#a3a6ad" : "#909399"),
    border: cssColor("--el-border-color-light", dark ? "#414243" : "#e4e7ed"),
    edge: cssColor("--el-border-color", dark ? "#4c4d4f" : "#dcdfe6"),
    warning: cssColor("--el-color-warning", dark ? "#e6a23c" : "#e6a23c"),
    danger: cssColor("--el-color-danger", dark ? "#f56c6c" : "#f56c6c"),
  };
});

const chartProfile = (loadedCount: number): ChartProfile => {
  if (loadedCount > 200) return { initialTreeDepth: 2, nodeWidth: 112, fontSize: 9, compact: true };
  if (loadedCount > 60) return { initialTreeDepth: 2, nodeWidth: 132, fontSize: 10, compact: true };
  return { initialTreeDepth: 2, nodeWidth: 168, fontSize: 11, compact: false };
};

const chartHeight = computed(() =>
  Math.min(720, Math.max(460, Math.min(props.maxDepth, 3) * 108 + 180))
);
const zoomLabel = computed(() => `${Math.round(clampZoom(zoomScale.value) * 100)}%`);
const visibleNodeCount = computed(() => countVisibleReferralCanvasNodes(props.tree, expandedNodes));

function clampZoom(value: number): number {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, value));
}

function formatIdentity(node: ReferralCanvasNode): string {
  const nickname = node.nickname?.trim();
  const username = node.username?.trim();
  if (nickname && username && nickname !== username) return `${nickname}（${username}）`;
  return nickname || username || `用户 #${node.user_id}`;
}

function truncateLabel(value: string, maxLength: number): string {
  const characters = Array.from(value);
  return characters.length > maxLength ? `${characters.slice(0, maxLength - 1).join("")}…` : value;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[character] || character;
  });
}

function statusTone(status: number): StatusTone {
  if (status === 0) return "normal";
  if (status === 1) return "disabled";
  if (status === 2) return "frozen";
  return "unknown";
}

function statusLabel(status: number): string {
  return (
    ({ 0: "正常", 1: "禁用", 2: "冻结" } as Record<number, string>)[status] || `状态 ${status}`
  );
}

function statusBorder(status: number): string {
  const tone = statusTone(status);
  if (tone === "disabled") return palette.value.danger;
  if (tone === "frozen") return palette.value.warning;
  return palette.value.border;
}

function resetExpansionState(root: ReferralCanvasNode): void {
  expandedNodes.clear();
  const profile = chartProfile(props.loadedCount);
  const visit = (node: ReferralCanvasNode, level: number) => {
    if (node.children.length > 0 && level < profile.initialTreeDepth)
      expandedNodes.add(node.user_id);
    node.children.forEach((child) => visit(child, level + 1));
  };
  visit(root, 0);
}

function mapNode(
  node: ReferralCanvasNode,
  isRoot: boolean,
  level: number,
  profile: ChartProfile
): CanvasChartNode {
  const displayName = formatIdentity(node);
  const isCollapsed = node.children.length > 0 && !expandedNodes.has(node.user_id);
  const childHint = node.children.length > 0 ? (isCollapsed ? "+ 展开下级" : "− 收起下级") : "";
  const truncationHint = node.is_truncated ? "下级未完整载入" : "";
  const compactIdentity = node.mobile?.trim()
    ? `${truncateLabel(displayName, 14)} · ${node.mobile.trim()}`
    : `${truncateLabel(displayName, 14)} · ID ${node.user_id}`;
  const nodeLabel = isRoot
    ? [
        "当前 Root",
        `${truncateLabel(displayName, 18)} · ID ${node.user_id}`,
        `直属 ${node.direct_count}`,
        childHint,
        truncationHint,
      ].filter(Boolean)
    : profile.compact
      ? [compactIdentity, childHint, truncationHint].filter(Boolean).join("\n")
      : [
          truncateLabel(displayName, 19),
          `ID ${node.user_id}`,
          `直属 ${node.direct_count}`,
          childHint,
          truncationHint,
        ]
          .filter(Boolean)
          .join("\n");
  const nodeWidth = isRoot ? profile.nodeWidth + 20 : profile.nodeWidth;

  return {
    ...node,
    id: String(node.user_id),
    name: displayName,
    user_id: node.user_id,
    displayName,
    mobile: node.mobile,
    status: node.status,
    directCount: node.direct_count,
    hasChildren: node.has_children,
    hasLoadedChildren: node.children.length > 0,
    isRoot,
    level,
    isTruncated: node.is_truncated,
    children: isCollapsed
      ? []
      : node.children.map((child) => mapNode(child, false, level + 1, profile)),
    symbol: "roundRect",
    symbolSize: [nodeWidth, isRoot ? 82 : node.is_truncated || isCollapsed ? 76 : 68],
    collapsed: isCollapsed,
    itemStyle: {
      color: isRoot ? palette.value.rootSurface : palette.value.surface,
      borderColor: isRoot ? palette.value.primary : statusBorder(node.status),
      borderWidth: isRoot ? 2 : 1,
    },
    label: {
      show: true,
      formatter: nodeLabel,
      color: palette.value.text,
      fontSize: profile.fontSize,
      fontWeight: 600,
      lineHeight: profile.fontSize === 9 ? 12 : 15,
      width: nodeWidth - 14,
      overflow: "truncate",
      align: "center",
      verticalAlign: "middle",
    },
  };
}

function getChartNode(data: unknown): CanvasChartNode | null {
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;
  const candidate = data as Partial<CanvasChartNode>;
  return typeof candidate.user_id === "number" ? (data as CanvasChartNode) : null;
}

function tooltipFormatter(params: TooltipComponentFormatterCallbackParams): string {
  const item = Array.isArray(params) ? params[0] : params;
  const node = getChartNode(item?.data);
  if (!node) return "";
  const rows = [
    `<strong>${escapeHtml(node.displayName)}</strong>`,
    `ID ${node.user_id}`,
    node.mobile?.trim() ? `手机号 ${escapeHtml(node.mobile.trim())}` : "",
    `状态 ${escapeHtml(statusLabel(node.status))}`,
    `直属人数 ${node.directCount}`,
    node.isTruncated ? "关系：仅展示部分下级" : "",
  ].filter(Boolean);
  return `<div>${rows.join("<br>")}</div>`;
}

function createOption(source: ReferralCanvasNode): EChartsOption {
  const profile = chartProfile(props.loadedCount);
  const root = mapNode(source, true, 0, profile);
  const treeSeries: TreeSeriesOption = {
    type: "tree",
    data: [root] as unknown as TreeSeriesOption["data"],
    top: "10%",
    left: "3%",
    right: "3%",
    bottom: "10%",
    layout: "orthogonal",
    orient: "TB",
    edgeShape: "polyline",
    edgeForkPosition: "50%",
    lineStyle: { color: palette.value.edge, width: 1.4 },
    roam: "move",
    scaleLimit: { min: ZOOM_MIN, max: ZOOM_MAX },
    nodeScaleRatio: 0.35,
    expandAndCollapse: false,
    initialTreeDepth: profile.initialTreeDepth,
    emphasis: { focus: "descendant", scale: false },
    label: { position: "inside", align: "center", verticalAlign: "middle" },
  };

  return {
    animation: false,
    backgroundColor: palette.value.canvas,
    tooltip: {
      trigger: "item",
      triggerOn: "mousemove",
      confine: true,
      formatter: tooltipFormatter,
      backgroundColor: palette.value.surface,
      borderColor: palette.value.border,
      borderWidth: 1,
      textStyle: { color: palette.value.text, fontSize: 12, lineHeight: 18 },
    },
    series: [treeSeries],
  };
}

function captureView(): ChartView {
  const instance = getChartInstance();
  const option = instance?.getOption() as
    | { series?: Array<{ zoom?: unknown; center?: unknown }> }
    | undefined;
  const series = option?.series?.[0];
  const rawZoom = series?.zoom;
  const zoom =
    typeof rawZoom === "number" && Number.isFinite(rawZoom)
      ? clampZoom(rawZoom)
      : clampZoom(zoomScale.value);
  const centerValues = Array.isArray(series?.center) ? series.center : [];
  const center: [number, number] | null =
    centerValues.length === 2 &&
    centerValues.every((value) => typeof value === "number" && Number.isFinite(value))
      ? [centerValues[0] as number, centerValues[1] as number]
      : null;
  return { zoom, center };
}

function restoreView(view: ChartView): void {
  const instance = getChartInstance();
  if (!instance) return;
  const viewSeries = {
    type: "tree",
    zoom: clampZoom(view.zoom),
    ...(view.center ? { center: view.center } : {}),
  };
  instance.setOption({ series: [viewSeries] } as unknown as EChartsOption, { lazyUpdate: false });
  zoomScale.value = clampZoom(view.zoom);
}

function renderOption(preserveView = false): void {
  const instance = getChartInstance();
  if (!instance) {
    initChart(createOption(props.tree));
    return;
  }
  const view = preserveView ? captureView() : null;
  instance.clear();
  instance.setOption(createOption(props.tree), { notMerge: true, lazyUpdate: false });
  if (view) restoreView(view);
}

function bindChartEvents(): void {
  const instance = getChartInstance();
  if (!instance) return;
  instance.off("click", handleNodeClick);
  instance.on("click", handleNodeClick);
  chartReady.value = true;
}

function handleChartVisible(): void {
  renderOption();
  bindChartEvents();
}

function handleNodeClick(params: ECElementEvent): void {
  const node = getChartNode(params.data);
  if (!node) return;
  const nativeEvent = params.event as unknown as {
    shiftKey?: boolean;
    event?: { shiftKey?: boolean };
  };
  const eventTarget = params.event?.target as unknown as
    | { type?: string; style?: { text?: unknown } }
    | undefined;
  const expansionControl =
    eventTarget?.type === "tspan" &&
    (eventTarget.style?.text === "+ 展开下级" || eventTarget.style?.text === "− 收起下级");
  const action = resolveReferralCanvasClickAction({
    expansionControl,
    shiftKey: Boolean(nativeEvent?.shiftKey || nativeEvent?.event?.shiftKey),
  });
  if (action === "toggle") {
    params.event?.stop();
  }
  if (action === "toggle" && node.hasLoadedChildren) {
    if (expandedNodes.has(node.user_id)) expandedNodes.delete(node.user_id);
    else expandedNodes.add(node.user_id);
    renderOption(true);
  }
  if (action === "toggle") return;
  selectedNode.value = node;
  emit("node-detail", node.user_id);
}

function changeZoom(delta: number): void {
  if (!getChartInstance()) return;
  const view = captureView();
  const nextZoom = clampZoom(Math.round((view.zoom + delta) * 100) / 100);
  if (nextZoom !== view.zoom) restoreView({ ...view, zoom: nextZoom });
}

function zoomIn(): void {
  changeZoom(ZOOM_STEP);
}

function zoomOut(): void {
  changeZoom(-ZOOM_STEP);
}

function resetZoom(): void {
  if (!getChartInstance()) return;
  const view = captureView();
  restoreView({ zoom: 1, center: view.center });
}

function handleWheel(event: WheelEvent): void {
  if (!event.ctrlKey && !event.metaKey) return;
  event.preventDefault();
  event.stopPropagation();
  changeZoom(event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP);
}

function attachWheel(): void {
  if (!chartRef.value || wheelAttached.value) return;
  chartRef.value.addEventListener("wheel", handleWheel, { passive: false });
  wheelAttached.value = true;
}

function detachWheel(): void {
  if (!chartRef.value || !wheelAttached.value) return;
  chartRef.value.removeEventListener("wheel", handleWheel);
  wheelAttached.value = false;
}

function visibleLayout(root: ReferralCanvasNode): { breadth: number; depth: number } {
  let level = [root];
  let breadth = 1;
  let depth = 0;
  while (level.length) {
    breadth = Math.max(breadth, level.length);
    const nextLevel = level.flatMap((node) =>
      expandedNodes.has(node.user_id) ? node.children : []
    );
    if (!nextLevel.length) break;
    depth += 1;
    level = nextLevel;
  }
  return { breadth, depth };
}

function applyView(zoom: number, resetCenter = false): void {
  const instance = getChartInstance();
  if (!instance) return;
  const viewOption = {
    series: [{ type: "tree", zoom: clampZoom(zoom), ...(resetCenter ? { center: null } : {}) }],
  };
  instance.setOption(viewOption as unknown as EChartsOption, { lazyUpdate: false });
  zoomScale.value = clampZoom(zoom);
}

function fitView(): void {
  const instance = getChartInstance();
  if (!instance) return;
  const profile = chartProfile(props.loadedCount);
  const layout = visibleLayout(props.tree);
  const availableWidth = Math.max(instance.getWidth() - 64, 1);
  const availableHeight = Math.max(instance.getHeight() - 64, 1);
  const estimatedWidth = Math.max(
    profile.nodeWidth + 20,
    layout.breadth * (profile.nodeWidth + 16)
  );
  const estimatedHeight = Math.max(88, (layout.depth + 1) * 104);
  const zoom = Math.min(
    1,
    Math.max(ZOOM_MIN, Math.min(availableWidth / estimatedWidth, availableHeight / estimatedHeight))
  );
  applyView(zoom, true);
}

function resetView(): void {
  if (!getChartInstance()) return;
  const view = captureView();
  applyView(view.zoom, true);
}

onMounted(() => {
  chartRef.value?.addEventListener("chartVisible", handleChartVisible);
  attachWheel();
  nextTick(() => {
    resetExpansionState(props.tree);
    initChart(createOption(props.tree));
    bindChartEvents();
    requestAnimationFrame(bindChartEvents);
  });
});

onBeforeUnmount(() => {
  chartRef.value?.removeEventListener("chartVisible", handleChartVisible);
  getChartInstance()?.off("click", handleNodeClick);
  detachWheel();
  chartReady.value = false;
});

watch(
  () => [props.tree, props.loadedCount, props.truncated],
  () => {
    selectedNode.value = null;
    zoomScale.value = 1;
    resetExpansionState(props.tree);
    renderOption();
  },
  { deep: false }
);

watch(isDark, () => {
  if (getChartInstance()) renderOption(true);
});

watch(
  () => props.maximized,
  async () => {
    await nextTick();
    handleResize();
  }
);
</script>

<style scoped lang="scss">
.referral-canvas {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.referral-canvas.is-maximized {
  position: fixed;
  inset: 0;
  z-index: 2000;
  box-sizing: border-box;
  grid-template-rows: auto minmax(0, 1fr) auto;
  width: auto;
  height: auto;
  min-height: 0;
  padding: 18px 24px 24px;
  overflow: hidden;
  background: var(--el-bg-color-page);
}

.referral-canvas__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.referral-canvas__help {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.referral-canvas__direction {
  font-weight: 700;
  color: var(--el-text-color-regular);
}

.referral-canvas__direction span {
  font-size: 16px;
  color: var(--el-color-primary);
}

.referral-canvas__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.referral-canvas__zoom-button,
.referral-canvas__zoom-reset {
  min-width: 34px;
  padding-right: 8px;
  padding-left: 8px;
}

.referral-canvas__zoom-button {
  font-size: 17px;
  line-height: 1;
}

.referral-canvas__zoom-reset {
  min-width: 54px;
}

.referral-canvas__frame {
  position: relative;
  width: 100%;
  min-height: 460px;
  overflow: hidden;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--el-border-radius-base);
}

.referral-canvas__chart {
  width: 100%;
  height: 100%;
  min-height: 460px;
}

.referral-canvas.is-maximized .referral-canvas__frame,
.referral-canvas.is-maximized .referral-canvas__chart {
  min-height: 0;
}

.referral-canvas.is-maximized .referral-canvas__frame {
  height: auto !important;
  border: 0;
}

.referral-canvas__state {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: grid;
  place-items: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  background: color-mix(in srgb, var(--el-fill-color-lighter) 82%, transparent);
}

.referral-canvas__notice {
  padding: 9px 12px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-color-warning-dark-2);
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: var(--el-border-radius-base);
}

.referral-canvas__selection {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

@media (width <= 680px) {
  .referral-canvas__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .referral-canvas__actions {
    justify-content: flex-start;
  }

  .referral-canvas.is-maximized {
    padding: 12px;
  }
}
</style>
