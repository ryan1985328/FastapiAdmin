import type { AppUserReferralNode } from "@/api/module_system/app_user";

export const REFERRAL_CANVAS_DEFAULT_DEPTH = 2;
export const REFERRAL_CANVAS_MAX_DEPTH = 3;
export const REFERRAL_CANVAS_NODE_BUDGET = 500;
export const REFERRAL_CANVAS_PAGE_SIZE = 100;

export interface ReferralCanvasNode extends AppUserReferralNode {
  children: ReferralCanvasNode[];
  level: number;
  is_truncated: boolean;
}

export interface ReferralCanvasChildrenPage {
  items: AppUserReferralNode[];
  has_next?: boolean | null;
}

export type ReferralCanvasChildrenLoader = (
  userId: number,
  pageNo: number,
  pageSize: number
) => Promise<ReferralCanvasChildrenPage>;

export interface LoadReferralCanvasTreeOptions {
  maxDepth?: number;
  nodeBudget?: number;
  pageSize?: number;
  shouldCancel?: () => boolean;
}

export interface ReferralCanvasTreeResult {
  tree: ReferralCanvasNode;
  loadedCount: number;
  skippedCount: number;
  truncated: boolean;
  cancelled: boolean;
}

export type ReferralCanvasClickAction = "detail" | "toggle";

export function resolveReferralCanvasClickAction(options: {
  expansionControl: boolean;
  shiftKey: boolean;
}): ReferralCanvasClickAction {
  return options.expansionControl || options.shiftKey ? "toggle" : "detail";
}

/**
 * Count only the nodes that the canvas currently renders for the given
 * expansion state. Nodes below a collapsed branch remain loaded in memory,
 * but are intentionally excluded from this count.
 */
export function countVisibleReferralCanvasNodes(
  root: ReferralCanvasNode,
  expandedUserIds: ReadonlySet<number>
): number {
  let count = 1;

  const visit = (node: ReferralCanvasNode) => {
    if (!expandedUserIds.has(node.user_id)) return;
    node.children.forEach((child) => {
      count += 1;
      visit(child);
    });
  };

  visit(root);
  return count;
}

interface PendingReferralCanvasNode {
  node: ReferralCanvasNode;
  ancestorIds: Set<number>;
}

function isValidUserId(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
}

function boundedPositiveInteger(
  value: number | undefined,
  fallback: number,
  maximum: number
): number {
  if (!Number.isSafeInteger(value) || value === undefined || value < 1) return fallback;
  return Math.min(value, maximum);
}

function cloneNode(node: AppUserReferralNode, level: number): ReferralCanvasNode {
  return {
    ...node,
    children: [],
    level,
    is_truncated: false,
  };
}

/**
 * Build the bounded nested data required by ECharts from the existing
 * paginated direct-children API. This function only reads and never mutates
 * the API nodes or the referral relationship.
 */
export async function loadReferralCanvasTree(
  root: AppUserReferralNode,
  loadChildren: ReferralCanvasChildrenLoader,
  options: LoadReferralCanvasTreeOptions = {}
): Promise<ReferralCanvasTreeResult> {
  if (!isValidUserId(root.user_id)) throw new Error("推荐关系根用户 ID 无效");

  const maxDepth = boundedPositiveInteger(
    options.maxDepth,
    REFERRAL_CANVAS_DEFAULT_DEPTH,
    REFERRAL_CANVAS_MAX_DEPTH
  );
  const nodeBudget = boundedPositiveInteger(
    options.nodeBudget,
    REFERRAL_CANVAS_NODE_BUDGET,
    REFERRAL_CANVAS_NODE_BUDGET
  );
  const pageSize = boundedPositiveInteger(options.pageSize, REFERRAL_CANVAS_PAGE_SIZE, 100);
  const shouldCancel = options.shouldCancel || (() => false);
  const tree = cloneNode(root, 0);
  const visited = new Set<number>([root.user_id]);
  let frontier: PendingReferralCanvasNode[] = [
    { node: tree, ancestorIds: new Set([root.user_id]) },
  ];
  let loadedCount = 1;
  let skippedCount = 0;
  let truncated = false;

  const cancelled = (): ReferralCanvasTreeResult => ({
    tree,
    loadedCount,
    skippedCount,
    truncated,
    cancelled: true,
  });

  const markTruncated = (parent: ReferralCanvasNode) => {
    parent.is_truncated = true;
    truncated = true;
  };

  while (frontier.length) {
    if (shouldCancel()) return cancelled();
    const nextFrontier: PendingReferralCanvasNode[] = [];

    for (let index = 0; index < frontier.length; index += 1) {
      const pending = frontier[index];
      if (!pending) continue;
      const parent = pending.node;
      if (parent.level >= maxDepth) {
        if (parent.has_children) markTruncated(parent);
        continue;
      }
      if (!parent.has_children) continue;

      if (loadedCount >= nodeBudget) {
        markTruncated(parent);
        truncated = true;
        break;
      }

      let pageNo = 1;
      let budgetReached = false;
      while (true) {
        if (shouldCancel()) return cancelled();
        const response = await loadChildren(parent.user_id, pageNo, pageSize);
        if (shouldCancel()) return cancelled();

        const page =
          response && typeof response === "object" && !Array.isArray(response) ? response : null;
        const items = page && Array.isArray(page.items) ? page.items : [];
        if (!page || (parent.has_children && items.length === 0)) {
          markTruncated(parent);
          break;
        }

        for (const item of items) {
          const childId = item?.user_id;
          if (!isValidUserId(childId)) {
            skippedCount += 1;
            markTruncated(parent);
            continue;
          }
          if (pending.ancestorIds.has(childId) || visited.has(childId)) {
            skippedCount += 1;
            markTruncated(parent);
            continue;
          }
          if (loadedCount >= nodeBudget) {
            markTruncated(parent);
            budgetReached = true;
            break;
          }

          const child = cloneNode(item, parent.level + 1);
          parent.children.push(child);
          visited.add(childId);
          loadedCount += 1;
          nextFrontier.push({
            node: child,
            ancestorIds: new Set([...pending.ancestorIds, childId]),
          });
        }

        if (budgetReached || !page.has_next) break;
        pageNo += 1;
        // A non-progressing/malformed API response must not keep a page walk
        // alive forever. A valid page can contain at least one new node while
        // the global node budget remains available.
        if (pageNo > nodeBudget) {
          markTruncated(parent);
          break;
        }
      }

      if (budgetReached) {
        truncated = true;
        break;
      }

      if (loadedCount >= nodeBudget) {
        const pendingAfterBudget = [...nextFrontier, ...frontier.slice(index + 1)];
        const hasUnloadedChildren = pendingAfterBudget.some((entry) => entry.node.has_children);
        pendingAfterBudget.forEach((entry) => {
          if (entry.node.has_children) entry.node.is_truncated = true;
        });
        if (hasUnloadedChildren) truncated = true;
        break;
      }
    }

    if (loadedCount >= nodeBudget) break;
    frontier = nextFrontier;
  }

  return {
    tree,
    loadedCount,
    skippedCount,
    truncated,
    cancelled: false,
  };
}
