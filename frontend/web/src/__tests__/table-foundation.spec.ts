import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@stores", () => ({
  useTableStore: () => ({
    isBorder: false,
    isZebra: false,
    tableSize: "default",
    isFullScreen: false,
    isHeaderBackground: false,
    isRowDrag: false,
    highlightCurrentRow: false,
  }),
  useMenuStore: () => ({ getHomePath: () => "/dashboard/workplace" }),
  useSettingsStore: () => ({ reload: vi.fn() }),
}));

vi.mock("vue-router", () => ({
  useRoute: () => ({ path: "/test" }),
}));

import FaButtonTable from "@/components/forms/fa-button-table/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import {
  ENABLED_STATUS_MAP,
  LOGIN_RESULT_STATUS_MAP,
  resolveStatusColumns,
} from "@/utils/table/statusFormatter";
import StatusTag from "@/components/display/fa-status-tag/index.vue";

beforeEach(() => {
  setActivePinia(createPinia());
  vi.stubGlobal("useResizeObserver", () => undefined);
});

describe("table interaction foundation", () => {
  it("renders row actions as labelled native buttons", () => {
    const wrapper = mount(FaButtonTable, {
      props: {
        type: "delete",
        label: "删除",
      },
      global: {
        stubs: {
          FaSvgIcon: true,
        },
      },
    });

    expect(wrapper.element.tagName).toBe("BUTTON");
    expect(wrapper.attributes("type")).toBe("button");
    expect(wrapper.attributes("aria-label")).toBe("删除");
  });

  it("keeps disabled row actions disabled", () => {
    const wrapper = mount(FaButtonTable, {
      props: {
        type: "delete",
        label: "删除",
        disabled: true,
      },
      global: {
        stubs: {
          FaSvgIcon: true,
        },
      },
    });

    expect(wrapper.attributes("disabled")).toBeDefined();
    expect(wrapper.classes()).toContain("opacity-40");
  });
});

describe("shared status maps", () => {
  it("renders the generic enabled/disabled mapping through StatusTag", () => {
    const columns = resolveStatusColumns(() => [
      { prop: "status", label: "状态", status: ENABLED_STATUS_MAP },
    ])();
    const vnode = columns[0]?.formatter?.({ status: 0 });

    expect(vnode?.type).toBe(StatusTag);
    expect(vnode?.props).toMatchObject({ type: "success", label: "启用" });
  });

  it("keeps login success/failure semantics separate from enabled state", () => {
    expect(LOGIN_RESULT_STATUS_MAP[1]!).toMatchObject({ type: "success", text: "成功" });
    expect(LOGIN_RESULT_STATUS_MAP[0]!).toMatchObject({ type: "danger", text: "失败" });
  });
});

describe("shared table state", () => {
  it("renders request errors separately and emits retry", async () => {
    const wrapper = mount(FaTable, {
      props: {
        columns: [],
        data: [],
        error: new Error("request failed"),
      },
      global: {
        stubs: {
          ElButton: {
            emits: ["click"],
            template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
          },
        },
      },
    });

    expect(wrapper.get('[role="alert"]').text()).toContain("加载失败，请重试");
    expect(wrapper.get("button").text()).toBe("重试");
    expect(wrapper.find(".el-empty").exists()).toBe(false);

    await wrapper.get("button").trigger("click");

    expect(wrapper.emitted("retry")).toHaveLength(1);
  });
});
