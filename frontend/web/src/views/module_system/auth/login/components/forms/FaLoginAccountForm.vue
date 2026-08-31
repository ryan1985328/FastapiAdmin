<!-- Admin 账号密码登录表单（含现有验证码滑块与记住密码） -->
<template>
  <div>
    <ElForm
      ref="formRef"
      :model="loginForm"
      :rules="rules"
      :key="formKey"
      class="login-page-form"
      :validate-on-rule-change="false"
      @keyup.enter="$emit('submit')"
    >
      <ElFormItem prop="username">
        <ElInput
          class="custom-height"
          v-model.trim="loginForm.username"
          clearable
          :placeholder="$t('login.placeholder.username')"
        >
          <template #prefix>
            <ElIcon><User /></ElIcon>
          </template>
        </ElInput>
      </ElFormItem>

      <ElTooltip :visible="isCapsLock" :content="$t('login.capsLock')" placement="right">
        <ElFormItem prop="password">
          <ElInput
            class="custom-height"
            v-model.trim="loginForm.password"
            type="password"
            autocomplete="off"
            show-password
            clearable
            :placeholder="$t('login.placeholder.password')"
            @keyup="onPasswordKeyup"
          >
            <template #prefix>
              <ElIcon><Lock /></ElIcon>
            </template>
          </ElInput>
        </ElFormItem>
      </ElTooltip>

      <div class="login-form-tail flex flex-col gap-[1.1rem]">
        <div class="relative pb-3">
          <div
            class="relative z-2 overflow-hidden select-none rounded-lg border border-transparent transition duration-300"
            :class="{ 'border-[#FF4E4F]!': !isPassing && isClickPass }"
          >
            <FaDragVerify
              ref="dragVerifyRef"
              v-model:value="isPassing"
              :text="$t('login.sliderText')"
              :text-color="dragVerifyTextColor"
              :success-text="$t('login.sliderSuccessText')"
              progress-bar-bg="var(--el-color-success)"
              :background="isDark ? '#26272F' : 'var(--el-border-color-light)'"
              handler-bg="var(--default-box-color)"
            />
          </div>
          <p
            class="absolute top-0 z-1 mt-2 px-px text-xs text-[#f56c6c] transition duration-300"
            :class="{ 'translate-y-10': !isPassing && isClickPass }"
          >
            {{ $t("login.placeholder.slider") }}
          </p>
        </div>

        <div class="login-options-row flex items-center justify-between text-sm">
          <ElCheckbox v-model="loginForm.remember" class="login-remember">
            {{ $t("login.rememberPwd") }}
          </ElCheckbox>
        </div>

        <div>
          <ElButton
            class="h-11 w-full rounded-lg! text-base font-medium"
            type="primary"
            :loading="loading"
            v-ripple
            @click="$emit('submit')"
          >
            {{ $t("login.btnText") }}
          </ElButton>
        </div>
      </div>
    </ElForm>
  </div>
</template>

<script setup lang="ts">
import { Lock, User } from "@element-plus/icons-vue";
import type { LoginFormData } from "@/api/module_system/auth";
import type { FormRules } from "element-plus";

const loginForm = defineModel<LoginFormData>("loginForm", { required: true });

defineOptions({ name: "FaLoginAccountForm" });

interface Props {
  rules: FormRules;
  formKey: number | string;
  isDark: boolean;
  dragVerifyTextColor: string;
  loading: boolean;
}

withDefaults(defineProps<Props>(), {});

const isPassing = defineModel<boolean>("isPassing", { required: true });
const isClickPass = defineModel<boolean>("isClickPass", { required: true });

interface Emits {
  submit: [];
}

const emit = defineEmits<Emits>();

const formRef = ref();
const dragVerifyRef = ref<{ reset?: () => void } | null>(null);
const isCapsLock = ref(false);

function onPasswordKeyup(event: KeyboardEvent) {
  if (event instanceof KeyboardEvent) {
    isCapsLock.value = event.getModifierState("CapsLock");
    if (event.key === "Enter") {
      emit("submit");
    }
  }
}

defineExpose({
  validate: () => formRef.value?.validate?.(),
  clearValidate: () => formRef.value?.clearValidate?.(),
  resetDragVerify: () => dragVerifyRef.value?.reset?.(),
});
</script>
