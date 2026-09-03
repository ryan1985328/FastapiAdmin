<!-- 按钮组件 -->
<template>
  <component
    :is="asButton ? 'button' : 'div'"
    class="fa-icon-button size-8.5 inline-flex items-center justify-center cursor-pointer text-g-600 dark:text-g-800 text-xl rounded transition duration-300 hover:bg-hover-color"
    :class="{ 'rounded-full': circle, 'is-disabled': disabled }"
    :type="asButton ? 'button' : undefined"
    :disabled="asButton ? disabled : undefined"
    :aria-label="ariaLabel"
    :title="title"
  >
    <FaSvgIcon :icon="icon"></FaSvgIcon>
    <slot></slot>
  </component>
</template>

<script lang="ts" setup>
defineOptions({ name: "FaIconButton" });

interface Props {
  /** 图标名称 */
  icon: string;
  /** 圆角按钮 */
  circle?: boolean;
  /** 是否使用原生 button 元素 */
  asButton?: boolean;
  /** 无障碍名称 */
  ariaLabel?: string;
  /** 原生提示文本 */
  title?: string;
  /** 是否禁用 */
  disabled?: boolean;
}

withDefaults(defineProps<Props>(), {});
</script>

<style lang="scss" scoped>
.fa-icon-button {
  &:hover :deep(.fa-svg-icon) {
    color: var(--el-color-primary);
  }

  &.is-disabled {
    pointer-events: none;
    cursor: not-allowed;
    opacity: 0.5;
  }
}
</style>
