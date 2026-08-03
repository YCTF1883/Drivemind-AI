<template>
  <AppPage>
    <n-result m-auto status="403">
      <template #icon>
        <img :src="errorImg" class="max-w-400px w-80vw" />
      </template>
      <template #footer>
        <n-button type="primary" @click="replace('/')">{{
          $t('views.errors.text_back_to_home')
        }}</n-button>
      </template>
    </n-result>
  </AppPage>
</template>

<script setup>
const errorImg = '/resource/drivemind/error-403.png'

const { replace } = useRouter()
</script>
