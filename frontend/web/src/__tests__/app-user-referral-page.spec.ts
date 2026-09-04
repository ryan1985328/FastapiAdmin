import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { h, type SetupContext } from "vue";
import type { AppUserReferralNode, AppUserReferralSummary } from "@/api/module_system/app_user";

const {
  mockGetDict,
  mockGetReferralChildren,
  mockGetAppUserDetail,
  mockGetReferralSummary,
  mockSearchReferralUsers,
} = vi.hoisted(() => ({
  mockGetDict: vi.fn(),
  mockGetAppUserDetail: vi.fn(),
  mockGetReferralChildren: vi.fn(),
  mockGetReferralSummary: vi.fn(),
  mockSearchReferralUsers: vi.fn(),
}));

vi.mock("@stores", () => ({
  useDictStore: () => ({
    dictData: {},
    getDict: mockGetDict,
  }),
}));

vi.mock("@/utils/checkPerm", () => ({
  checkPerm: () => true,
}));

vi.mock("@utils", () => ({
  formatToDateTime: (value: string) => value,
}));

vi.mock("@/api/module_system/app_user", () => ({
  default: {
    getAppUserDetail: mockGetAppUserDetail,
    getReferralChildren: mockGetReferralChildren,
    getReferralSummary: mockGetReferralSummary,
    searchReferralUsers: mockSearchReferralUsers,
  },
}));

vi.mock("@/components/charts/fa-referral-tree/index.vue", () => ({
  default: {
    name: "AppUserReferralCanvas",
    emits: ["node-detail"],
    template:
      '<div data-test="canvas-stub"><button type="button" data-test="canvas-node" @click="$emit(\'node-detail\', 9)">节点 ID 9</button><button type="button" data-test="canvas-selected" @click="$emit(\'node-detail\', 9)">选中节点查看用户</button></div>',
  },
}));

vi.mock("@/components/modal/fa-dialog/index.vue", () => ({
  default: {
    name: "FaDialog",
    props: {
      modelValue: Boolean,
    },
    emits: ["update:modelValue", "close"],
    template:
      '<div v-if="modelValue" role="dialog"><slot /><button type="button" @click="$emit(\'close\')">确定</button></div>',
  },
}));

vi.mock("@/views/module_system/app_user/AppUserDetailContent.vue", () => ({
  default: {
    name: "AppUserDetailContent",
    props: {
      data: {
        type: Object,
        default: () => ({}),
      },
    },
    template: '<div data-test="detail-content">用户 ID {{ data.id }}</div>',
  },
}));

vi.mock("@/components/display/fa-status-tag/index.vue", () => ({
  default: {
    name: "FaStatusTag",
    render: () => null,
  },
}));

import ReferralPage from "@/views/module_system/app_user/referral.vue";

const ElCardStub = {
  name: "ElCard",
  template: "<section><slot /></section>",
};

const ElButtonStub = {
  name: "ElButton",
  emits: ["click"],
  template: '<button type="button" @click="$emit(\'click\', $event)"><slot /></button>',
};

const ElInputStub = {
  name: "ElInput",
  props: {
    modelValue: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue"],
  template:
    '<label><input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /><slot name="prefix" /></label>',
};

const ElEmptyStub = {
  name: "ElEmpty",
  props: {
    description: {
      type: String,
      default: "",
    },
  },
  template: '<div class="el-empty">{{ description }}</div>',
};

const ElIconStub = {
  name: "ElIcon",
  template: "<span><slot /></span>",
};

const ElTabsStub = {
  name: "ElTabs",
  emits: ["tab-change"],
  template:
    '<div><button type="button" data-test="activate-canvas" @click="$emit(\'tab-change\', \'canvas\')">打开画布</button><slot /></div>',
};

const ElTabPaneStub = {
  name: "ElTabPane",
  template: "<div><slot /></div>",
};

const ElTreeStub = {
  name: "ElTree",
  props: {
    data: {
      type: Array,
      default: () => [],
    },
  },
  setup(props: { data?: Array<{ user_id: number }> }, { expose, slots }: SetupContext) {
    expose({
      getNode: () => ({ expand: vi.fn() }),
    });
    return () =>
      h(
        "div",
        {},
        (props.data || []).map((item) =>
          h("div", { key: item.user_id }, slots.default?.({ data: item }) || [])
        )
      );
  },
};

const globalOptions = {
  stubs: {
    ElButton: ElButtonStub,
    ElCard: ElCardStub,
    ElEmpty: ElEmptyStub,
    ElIcon: ElIconStub,
    ElInput: ElInputStub,
    ElTabPane: ElTabPaneStub,
    ElTabs: ElTabsStub,
    ElTree: ElTreeStub,
  },
  directives: {
    loading: {},
  },
};

function referralNode(userId: number, nickname: string, directCount = 0): AppUserReferralNode {
  return {
    user_id: userId,
    username: `user-${userId}`,
    nickname,
    mobile: `139****${String(userId).padStart(4, "0")}`,
    referral_code: `REF-${userId}`,
    status: 0,
    kyc_status: "unverified",
    direct_count: directCount,
    has_children: directCount > 0,
    referrer_bound_at: null,
  };
}

function referralSummary(userId: number): AppUserReferralSummary {
  const hasChildren = userId === 1 || userId === 8;
  return {
    ...referralNode(userId, `用户-${userId}`, hasChildren ? 2 : 0),
    referrer_id: null,
    referrer: null,
    total_descendant_count: hasChildren ? 4 : 0,
  };
}

function page(items: AppUserReferralNode[]) {
  return {
    data: {
      data: {
        page_no: 1,
        page_size: 20,
        total: items.length,
        has_next: false,
        items,
      },
    },
  };
}

async function search(wrapper: ReturnType<typeof mount>, value: string) {
  const input = wrapper.get(".referral-search-form input");
  await input.setValue(value);
  await wrapper.get(".referral-search-form button").trigger("click");
  await flushPromises();
}

describe("Referral page density state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDict.mockResolvedValue({});
    mockGetAppUserDetail.mockResolvedValue({
      data: { data: { id: 9 } },
    });
    mockGetReferralChildren.mockResolvedValue(page([]));
    mockGetReferralSummary.mockImplementation(async (userId: number) => ({
      data: { data: referralSummary(userId) },
    }));
  });

  it("keeps results visible during search and collapses them after selecting a user", async () => {
    const users = [referralNode(1, "用户一", 2), referralNode(2, "用户二")];
    mockSearchReferralUsers.mockResolvedValueOnce(page(users));
    const wrapper = mount(ReferralPage, { global: globalOptions });

    expect(wrapper.find(".referral-search-form").exists()).toBe(true);
    expect(wrapper.find(".referral-search-results").exists()).toBe(false);
    expect(wrapper.find(".referral-tree-card").exists()).toBe(false);

    await search(wrapper, "用户");

    expect(wrapper.find(".referral-search-results").exists()).toBe(true);
    expect(wrapper.find(".referral-search-results__header").text()).toContain("共 2 条");
    expect(wrapper.findAll(".referral-search-result")).toHaveLength(2);

    await wrapper.get(".referral-search-result").trigger("click");
    await flushPromises();

    expect(wrapper.find(".referral-search-results").exists()).toBe(false);
    expect(wrapper.find(".referral-summary-card").exists()).toBe(true);
    expect(wrapper.find(".referral-summary-card").text()).toContain("ID 1");
    expect(wrapper.find(".referral-summary-card").text()).toContain("直属下级");
    expect(wrapper.find(".referral-summary-card").text()).toContain("切换用户");
    expect(wrapper.find(".referral-metrics").exists()).toBe(false);
  });

  it("reopens selection on switch and keeps the current root until another result is selected", async () => {
    const firstUsers = [referralNode(1, "用户一", 2), referralNode(2, "用户二")];
    const nextUsers = [referralNode(3, "用户三"), referralNode(4, "用户四")];
    mockSearchReferralUsers
      .mockResolvedValueOnce(page(firstUsers))
      .mockResolvedValueOnce(page(nextUsers));
    const wrapper = mount(ReferralPage, { global: globalOptions });

    await search(wrapper, "用户");
    await wrapper.get(".referral-search-result").trigger("click");
    await flushPromises();

    await wrapper.get(".referral-switch-user").trigger("click");
    expect(wrapper.find(".referral-search-results").exists()).toBe(true);
    expect(wrapper.findAll(".referral-search-result")).toHaveLength(2);

    await wrapper.get(".referral-search-form input").setValue("用户三");
    expect(wrapper.find(".referral-summary-card").text()).toContain("ID 1");

    await wrapper.get(".referral-search-form button").trigger("click");
    await flushPromises();
    expect(wrapper.find(".referral-search-results").exists()).toBe(true);
    expect(wrapper.find(".referral-summary-card").text()).toContain("ID 1");
    expect(wrapper.findAll(".referral-search-result")).toHaveLength(2);

    await wrapper.get(".referral-search-result").trigger("click");
    await flushPromises();

    expect(wrapper.find(".referral-summary-card").text()).toContain("ID 3");
    expect(wrapper.find(".referral-summary-card").text()).not.toContain("ID 1");
    expect(wrapper.find(".referral-search-results").exists()).toBe(false);

    await wrapper.get(".referral-view-user").trigger("click");
    await flushPromises();
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=detail-content]").text()).toContain("用户 ID 9");
    expect(wrapper.find(".referral-search-results").exists()).toBe(false);

    await wrapper.get('[role="dialog"] button').trigger("click");
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
  });

  it("keeps Referral-local canvas and hierarchy inspection in the local detail dialog", async () => {
    mockSearchReferralUsers.mockResolvedValueOnce(page([referralNode(8, "根用户", 2)]));
    const wrapper = mount(ReferralPage, { global: globalOptions });

    await search(wrapper, "根用户");

    const hierarchyViewButton = wrapper
      .findAll(".referral-tree-node button")
      .find((button) => button.text() === "查看用户");
    expect(hierarchyViewButton).toBeDefined();
    await hierarchyViewButton?.trigger("click");
    await flushPromises();
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=detail-content]").text()).toContain("用户 ID 9");
    expect(wrapper.find(".referral-search-results").exists()).toBe(false);

    await wrapper.get('[role="dialog"] button').trigger("click");
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);

    await wrapper.get("[data-test=activate-canvas]").trigger("click");
    await flushPromises();

    await wrapper.get("[data-test=canvas-node]").trigger("click");
    await flushPromises();

    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=detail-content]").text()).toContain("用户 ID 9");

    await wrapper.get('[role="dialog"] button').trigger("click");
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);

    await wrapper.get("[data-test=canvas-selected]").trigger("click");
    await flushPromises();
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=detail-content]").text()).toContain("用户 ID 9");
  });
});
