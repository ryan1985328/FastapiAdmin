import type { ConfigTable } from "@/api/module_system/params";
import defaultLogoUrl from "@/assets/fa_imgs/logo.svg";

/** 默认 Starter 品牌；运行时参数可覆盖，但不能让壳层退化为空品牌。 */
export const DEFAULT_ADMIN_BRAND_NAME = "FastAPI Admin Starter";
export const DEFAULT_ADMIN_BRAND_LOGO = defaultLogoUrl;

export interface AdminBranding {
  systemName: string;
  systemLogo: string;
  adminName: string;
  adminLogo: string;
  resolvedAdminName: string;
  resolvedAdminLogo: string;
}

type ConfigData = Readonly<Record<string, Pick<ConfigTable, "config_value"> | undefined>>;

function normalize(value: string | null | undefined): string {
  return typeof value === "string" ? value.trim() : "";
}

/**
 * 统一解析登录页与 Admin Shell 使用的品牌。
 *
 * Admin override → System brand → bundled Starter default。
 * `systemLogo` 始终包含可用的内置默认值，便于图片资源损坏时继续降级。
 */
export function resolveAdminBranding(configData: ConfigData): AdminBranding {
  const configuredSystemName = normalize(configData.sys_name?.config_value);
  const configuredSystemLogo = normalize(configData.logo_url?.config_value);
  const configuredAdminName = normalize(configData.admin_name?.config_value);
  const configuredAdminLogo = normalize(configData.admin_logo_url?.config_value);

  const systemName = configuredSystemName || DEFAULT_ADMIN_BRAND_NAME;
  const systemLogo = configuredSystemLogo || DEFAULT_ADMIN_BRAND_LOGO;

  return {
    systemName,
    systemLogo,
    adminName: configuredAdminName,
    adminLogo: configuredAdminLogo,
    resolvedAdminName: configuredAdminName || systemName || DEFAULT_ADMIN_BRAND_NAME,
    resolvedAdminLogo: configuredAdminLogo || systemLogo || DEFAULT_ADMIN_BRAND_LOGO,
  };
}
