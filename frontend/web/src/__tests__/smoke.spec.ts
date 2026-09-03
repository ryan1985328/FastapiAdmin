/**
 * 前端关键模块烟雾测试
 * 验证运行时枚举、类型定义的完整性和正确性。
 *
 * 注意：const enum（ThemeMode/DeviceEnum/LayoutMode/ResultEnum 等）
 * 在 TypeScript isolatedModules 模式下会被内联为常量，无法在运行时访问。
 * MenuTypeEnum 为常规 enum，下列代码生成枚举也为常规 enum。
 */

import { describe, it, expect } from "vitest";
import {
  DEFAULT_ADMIN_BRAND_NAME,
  DEFAULT_ADMIN_BRAND_LOGO,
  resolveAdminBranding,
} from "@/utils/branding";

// ══════════════════ Admin 品牌解析 ══════════════════
describe("Admin branding resolver", () => {
  it("should use the Starter defaults when no runtime branding is configured", () => {
    const branding = resolveAdminBranding({});

    expect(branding.resolvedAdminName).toBe(DEFAULT_ADMIN_BRAND_NAME);
    expect(branding.resolvedAdminLogo).toBe(DEFAULT_ADMIN_BRAND_LOGO);
  });

  it("should prefer Admin overrides and fall back to the System brand", () => {
    const systemBranding = resolveAdminBranding({
      sys_name: { config_value: "System Console" },
      logo_url: { config_value: "/system-logo.svg" },
    });
    expect(systemBranding.resolvedAdminName).toBe("System Console");
    expect(systemBranding.resolvedAdminLogo).toBe("/system-logo.svg");

    const adminBranding = resolveAdminBranding({
      sys_name: { config_value: "System Console" },
      logo_url: { config_value: "/system-logo.svg" },
      admin_name: { config_value: "Operations Console" },
      admin_logo_url: { config_value: "/admin-logo.svg" },
    });
    expect(adminBranding.resolvedAdminName).toBe("Operations Console");
    expect(adminBranding.resolvedAdminLogo).toBe("/admin-logo.svg");
  });
});

// ══════════════════ 菜单类型枚举 ══════════════════
describe("MenuTypeEnum — 菜单类型", () => {
  it("should define 4 menu types with correct values", async () => {
    const { MenuTypeEnum } = await import("@/enums/system/menu.enum");
    expect(MenuTypeEnum.CATALOG).toBe(1);
    expect(MenuTypeEnum.MENU).toBe(2);
    expect(MenuTypeEnum.BUTTON).toBe(3);
    expect(MenuTypeEnum.EXTLINK).toBe(4);
  });
});

// ══════════════════ 代码生成枚举 ══════════════════
describe("代码生成枚举 — 完整性", () => {
  it("FormRuleType should be importable", async () => {
    const mod = await import("@/enums/codegen/form.enum");
    expect(mod).toBeDefined();
  });

  it("QueryRuleType should be importable", async () => {
    const mod = await import("@/enums/codegen/query.enum");
    expect(mod).toBeDefined();
  });
});
