<template>
  <aside class="w-12 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-3 gap-4 shrink-0">
    <CreateButton />
    <div class="border-t border-slate-800 w-6 my-1"></div>
    <MiniCalendar />
    <div class="flex-1"></div>
    <PrivacyStatus />
  </aside>
</template>

<script setup>
import CreateButton from './CreateButton.vue'
import MiniCalendar from './MiniCalendar.vue'
import PrivacyStatus from './PrivacyStatus.vue'
</script>
