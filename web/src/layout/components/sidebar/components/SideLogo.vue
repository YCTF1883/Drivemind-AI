<template>
  <router-link h-60 f-c-c to="/">
    <img :src="logoImg" class="h-36 w-36 object-contain" />
    <h2
      v-show="!appStore.collapsed"
      ml-2
      mr-8
      max-w-150
      flex-shrink-0
      text-16
      font-bold
      color-primary
    >
      {{ title }}
    </h2>
  </router-link>
</template>

<script setup>
import { useAppStore } from '@/store'
const logoImg = '/resource/drivemind/logo.png'
const title = import.meta.env.VITE_TITLE

const appStore = useAppStore()
</script>
