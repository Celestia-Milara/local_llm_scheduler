<template>
  <header class="h-12 bg-slate-900 border-b border-slate-800 flex items-center px-4 gap-4 shrink-0">
    <DateNavigator />
    <ViewSwitcher />
    <div class="flex-1"></div>
    <HeaderActions @logout="$emit('logout')" />
  </header>
</template>

<script setup>
defineEmits(['logout'])
import DateNavigator from './DateNavigator.vue'
import ViewSwitcher from './ViewSwitcher.vue'
import HeaderActions from './HeaderActions.vue'
</script>
