import { computed } from "vue";
import { useConfigStore } from "@stores";
import { resolveAdminBranding } from "@/utils/branding";

/** Admin 品牌的响应式入口，避免 Login、Sidebar、Header 各自实现 fallback。 */
export function useAdminBranding() {
  const configStore = useConfigStore();
  const branding = computed(() => resolveAdminBranding(configStore.configData));

  return {
    branding,
    systemLogo: computed(() => branding.value.systemLogo),
    resolvedAdminName: computed(() => branding.value.resolvedAdminName),
    resolvedAdminLogo: computed(() => branding.value.resolvedAdminLogo),
  };
}
