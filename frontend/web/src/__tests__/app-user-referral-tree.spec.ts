import { describe, expect, it, vi } from "vitest";
import type { AppUserReferralNode } from "@/api/module_system/app_user";
import { loadReferralCanvasTree } from "@/utils/app-user-referral-tree";

function node(userId: number, hasChildren = false): AppUserReferralNode {
  return {
    user_id: userId,
    username: `user-${userId}`,
    nickname: `用户-${userId}`,
    mobile: null,
    referral_code: `REF-${userId}`,
    status: 0,
    kyc_status: "unverified",
    direct_count: hasChildren ? 1 : 0,
    has_children: hasChildren,
    referrer_bound_at: null,
  };
}

type Page = { items: AppUserReferralNode[]; has_next?: boolean };

function loaderFrom(pages: Record<string, Page>) {
  return vi.fn(async (userId: number, pageNo: number): Promise<Page> => {
    return pages[`${userId}:${pageNo}`] || { items: [], has_next: false };
  });
}

describe("App User referral canvas loader", () => {
  it("builds a normal bounded hierarchy without mutating API nodes", async () => {
    const root = node(1, true);
    const child = node(2, true);
    const grandchild = node(3);
    const loadChildren = loaderFrom({
      "1:1": { items: [child], has_next: false },
      "2:1": { items: [grandchild], has_next: false },
    });

    const result = await loadReferralCanvasTree(root, loadChildren, { maxDepth: 3 });

    expect(result).toMatchObject({
      loadedCount: 3,
      skippedCount: 0,
      truncated: false,
      cancelled: false,
    });
    expect(result.tree.children[0]?.children[0]?.user_id).toBe(3);
    expect(root).not.toHaveProperty("children");
  });

  it("follows every page of direct children", async () => {
    const root = node(1, true);
    const loadChildren = loaderFrom({
      "1:1": { items: [node(2)], has_next: true },
      "1:2": { items: [node(3)], has_next: false },
    });

    const result = await loadReferralCanvasTree(root, loadChildren, { maxDepth: 1 });

    expect(result.tree.children.map((item) => item.user_id)).toEqual([2, 3]);
    expect(loadChildren.mock.calls.map((call) => call.slice(0, 2))).toEqual([
      [1, 1],
      [1, 2],
    ]);
  });

  it("stops automatic loading at the maximum depth and marks hidden descendants", async () => {
    const root = node(1, true);
    const child = node(2, true);
    const loadChildren = loaderFrom({
      "1:1": { items: [child], has_next: false },
      "2:1": { items: [node(3)], has_next: false },
    });

    const result = await loadReferralCanvasTree(root, loadChildren, { maxDepth: 1 });

    expect(result.truncated).toBe(true);
    expect(result.tree.children[0]).toMatchObject({ user_id: 2, is_truncated: true, children: [] });
    expect(loadChildren).toHaveBeenCalledTimes(1);
  });

  it("enforces the node budget and reports truncation", async () => {
    const root = node(1, true);
    const loadChildren = loaderFrom({
      "1:1": { items: [node(2), node(3)], has_next: false },
    });

    const result = await loadReferralCanvasTree(root, loadChildren, { maxDepth: 1, nodeBudget: 2 });

    expect(result.loadedCount).toBe(2);
    expect(result.tree.children.map((item) => item.user_id)).toEqual([2]);
    expect(result.tree.is_truncated).toBe(true);
    expect(result.truncated).toBe(true);
  });

  it("guards cycles and duplicate IDs without duplicating rendered nodes", async () => {
    const root = node(1, true);
    const loadChildren = loaderFrom({
      "1:1": { items: [node(1), node(2), node(2)], has_next: false },
    });

    const result = await loadReferralCanvasTree(root, loadChildren, { maxDepth: 1 });

    expect(result.loadedCount).toBe(2);
    expect(result.skippedCount).toBe(2);
    expect(result.tree.children.map((item) => item.user_id)).toEqual([2]);
    expect(result.truncated).toBe(true);
  });

  it("fails closed on malformed or non-progressing pages", async () => {
    const root = node(1, true);
    const malformedLoader = vi.fn(async () => null as unknown as Page);

    const malformedResult = await loadReferralCanvasTree(root, malformedLoader, { maxDepth: 1 });

    expect(malformedResult).toMatchObject({ loadedCount: 1, truncated: true, cancelled: false });
    expect(malformedLoader).toHaveBeenCalledTimes(1);

    const repeatedLoader = vi.fn(
      async (): Promise<Page> => ({
        items: [node(1)],
        has_next: true,
      })
    );
    const repeatedResult = await loadReferralCanvasTree(root, repeatedLoader, {
      maxDepth: 1,
      nodeBudget: 2,
    });

    expect(repeatedResult.truncated).toBe(true);
    expect(repeatedLoader).toHaveBeenCalledTimes(2);

    const emptyResult = await loadReferralCanvasTree(
      root,
      vi.fn(async (): Promise<Page> => ({ items: [], has_next: false })),
      { maxDepth: 1 }
    );

    expect(emptyResult).toMatchObject({ loadedCount: 1, truncated: true, cancelled: false });
  });

  it("stops stale work before applying later pages", async () => {
    const root = node(1, true);
    let cancelled = false;
    const loadChildren = vi.fn(async (): Promise<Page> => {
      cancelled = true;
      return { items: [node(2)], has_next: true };
    });

    const result = await loadReferralCanvasTree(root, loadChildren, {
      maxDepth: 2,
      shouldCancel: () => cancelled,
    });

    expect(result.cancelled).toBe(true);
    expect(loadChildren).toHaveBeenCalledTimes(1);
  });
});
