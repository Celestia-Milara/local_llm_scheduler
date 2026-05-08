<template>
  <main class="flex-1 flex flex-col overflow-hidden p-5">
    <div class="flex-1 relative">
      <CalendarGrid @select-date="openPopover" />
      <Transition name="scale">
        <DayPopover v-if="popoverDate" :date-key="popoverDate" @close="closePopover" />
      </Transition>
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import CalendarGrid from './CalendarGrid.vue'
import DayPopover from './DayPopover.vue'

const popoverDate = ref(null)

function openPopover(dateKey) { popoverDate.value = dateKey }
function closePopover() { popoverDate.value = null }
</script>
