<template>
  <header class="h-12 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-sm border-b border-zinc-200/60 dark:border-zinc-700/60 flex items-center px-4 gap-4 shrink-0">
    <!-- Brand -->
    <div class="flex items-center gap-2 mr-2">
      <svg class="w-4 h-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
      <span class="font-display text-zinc-700 dark:text-zinc-200 text-sm hidden sm:inline">隐私日程</span>
      <span class="text-[8px] text-moss-600 dark:text-moss-400 bg-moss-500/10 px-1.5 py-0.5 rounded-full border border-moss-500/20 privacy-badge hidden sm:inline">LOCAL</span>
    </div>
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
