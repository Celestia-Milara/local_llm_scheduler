<template>
  <div class="h-screen flex flex-col bg-slate-950 text-slate-200">
    <Toolbar @logout="$emit('logout')" />
    <div class="flex flex-1 overflow-hidden">
      <Sidebar />
      <MonthView class="flex-1" />
      <AiPanel />
    </div>
  </div>
</template>

<script setup>
defineEmits(['logout'])
import Toolbar from './Toolbar.vue'
import Sidebar from './Sidebar.vue'
import MonthView from './MonthView.vue'
import AiPanel from './AiPanel.vue'
</script>
