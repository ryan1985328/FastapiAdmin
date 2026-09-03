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
      <div class="login-form-field">
        <p class="login-form-field__label">{{ $t("login.fields.username") }}</p>
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
      </div>

      <div class="login-form-field">
        <p class="login-form-field__label">{{ $t("login.fields.password") }}</p>
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
      </div>

      <div class="login-form-tail">
        <div v-if="captchaEnabled" class="login-form-field login-form-field--captcha">
          <p class="login-form-field__label">{{ $t("login.fields.captcha") }}</p>
          <div class="login-captcha-shell" :class="{ 'is-error': !isPassing && isClickPass }">
            <FaDragVerify
              ref="dragVerifyRef"
              v-model:value="isPassing"
              :height="52"
              :text="$t('login.sliderText')"
              :text-color="dragVerifyTextColor"
              :success-text="$t('login.sliderSuccessText')"
              progress-bar-bg="var(--el-color-success)"
              background="transparent"
              handler-bg="var(--default-box-color)"
            />
            <p class="login-captcha-error" :class="{ 'is-visible': !isPassing && isClickPass }">
              {{ $t("login.placeholder.slider") }}
            </p>
          </div>
        </div>

        <div class="login-options-row">
          <ElCheckbox v-model="loginForm.remember" class="login-remember">
            {{ $t("login.rememberPwd") }}
          </ElCheckbox>
        </div>

        <div>
          <ElButton
            class="login-submit"
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
  captchaEnabled: boolean;
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
