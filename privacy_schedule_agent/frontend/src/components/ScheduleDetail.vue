<template>
  <Teleport to="body">
    <Transition name="scale">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="close">
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-700/80 rounded-2xl shadow-2xl shadow-black/10 w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto">

          <!-- ============ VIEW MODE ============ -->
          <template v-if="mode === 'view'">
            <!-- Header -->
            <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-zinc-200/50 dark:border-zinc-700/50">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2">
                  <h2 class="font-display text-xl font-semibold text-zinc-800 dark:text-zinc-200">{{ schedule.title }}</h2>
                  <span v-if="schedule.category"
                    class="text-[10px] px-2 py-0.5 rounded-full border shrink-0"
                    :class="categoryClass(schedule.category)">{{ schedule.category }}</span>
                  <span v-if="schedule.privacy_level && schedule.privacy_level > 1"
                    class="text-[10px] px-2 py-0.5 rounded-full border shrink-0"
                    :class="privacyClass(schedule.privacy_level)">
                    {{ privacyLabel(schedule.privacy_level) }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <span v-if="schedule.status === 'conflicted'"
                    class="text-[10px] text-danger-600 bg-danger-400/10 px-1.5 py-0.5 rounded-full border border-danger-400/20">冲突</span>
                  <span v-if="schedule.recurrence_rule"
                    class="text-[10px] text-zinc-500 bg-surface-100 px-1.5 py-0.5 rounded-full border border-zinc-200">↻ {{ recurrenceLabel }}</span>
                  <span class="text-[10px] text-zinc-400">ID: {{ schedule.id }}</span>
                </div>
              </div>
              <button @click="close" class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors shrink-0 ml-4">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Body -->
            <div class="px-6 py-5 space-y-4">
              <!-- Time -->
              <div class="flex items-center gap-3 text-sm">
                <svg class="w-4 h-4 text-primary-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                </svg>
                <span class="text-zinc-700 dark:text-zinc-200">{{ formattedDate }}</span>
                <span class="text-zinc-300 dark:text-zinc-600">·</span>
                <span class="text-zinc-500 dark:text-zinc-400">{{ formattedTime }}</span>
              </div>

              <!-- Location -->
              <div v-if="schedule.location" class="flex items-center gap-3 text-sm">
                <svg class="w-4 h-4 text-primary-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
                <span class="text-zinc-700 dark:text-zinc-200">{{ schedule.location }}</span>
              </div>

              <!-- Description -->
              <div v-if="schedule.description" class="pl-7">
                <p class="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed whitespace-pre-wrap">{{ schedule.description }}</p>
              </div>

              <!-- No description -->
              <div v-else class="pl-7">
                <p class="text-sm text-zinc-300 dark:text-zinc-600 italic">暂无描述</p>
              </div>
            </div>

            <!-- Footer actions -->
            <div class="flex items-center justify-between px-6 pb-6 pt-2 border-t border-zinc-200/30 dark:border-zinc-700/30">
              <button @click="confirmDelete" class="px-4 py-2 rounded-xl text-sm text-zinc-400 dark:text-zinc-500 hover:text-danger-500 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors">
                删除
              </button>
              <div class="flex items-center gap-2">
                <button @click="close" class="px-4 py-2 rounded-xl text-sm text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors">
                  关闭
                </button>
                <button @click="enterEditMode" class="bg-primary-500 hover:bg-primary-400 active:bg-primary-600 px-5 py-2 rounded-xl text-sm font-medium text-white transition-all">
                  编辑
                </button>
              </div>
            </div>
          </template>

          <!-- ============ EDIT MODE ============ -->
          <template v-else>
            <!-- Header -->
            <div class="flex items-center justify-between px-6 pt-6 pb-4 border-b border-zinc-200/50 dark:border-zinc-700/50">
              <h2 class="font-display text-xl font-semibold text-zinc-800 dark:text-zinc-200">编辑日程</h2>
              <button @click="cancelEdit" class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors shrink-0">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Edit form -->
            <div class="px-6 py-5 space-y-4">
              <div>
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">标题</label>
                <input v-model="editForm.title"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50"
                  placeholder="日程标题">
              </div>

              <div>
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">分类</label>
                <select v-model="editForm.category"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                  <option value="">无分类</option>
                  <option value="工作">工作</option>
                  <option value="学习">学习</option>
                  <option value="生活">生活</option>
                </select>
              </div>

              <div>
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">隐私级别</label>
                <select v-model="editForm.privacy_level"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                  <option :value="1">公开</option>
                  <option :value="2">内部</option>
                  <option :value="3">绝密</option>
                </select>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">开始日期</label>
                  <input type="date" v-model="editStartDate"
                    class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                </div>
                <div>
                  <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">开始时间</label>
                  <input type="time" v-model="editStartTime" step="60"
                    @keyup.up.prevent="adjustTime('start', 1)"
                    @keyup.down.prevent="adjustTime('start', -1)"
                    class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">结束日期</label>
                  <input type="date" v-model="editEndDate"
                    class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                </div>
                <div>
                  <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">结束时间</label>
                  <input type="time" v-model="editEndTime" step="60"
                    @keyup.up.prevent="adjustTime('end', 1)"
                    @keyup.down.prevent="adjustTime('end', -1)"
                    class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                </div>
              </div>

              <div>
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">地点</label>
                <input v-model="editForm.location"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50"
                  placeholder="地点">
              </div>

              <div>
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">描述</label>
                <textarea v-model="editForm.description" rows="3"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50 resize-none"
                  placeholder="日程描述（可选）"></textarea>
              </div>

              <div>
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">重复</label>
                <select v-model="editForm.recurrence_rule"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
                  <option value="">不重复</option>
                  <option value="daily">每天</option>
                  <option value="weekdays">工作日</option>
                  <option value="weekly">每周</option>
                  <option value="monthly">每月</option>
                </select>
              </div>

              <div v-if="editForm.recurrence_rule">
                <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">重复截止</label>
                <input type="date" v-model="editRecurrenceEnd"
                  class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
              </div>

              <!-- Delete in edit mode -->
              <div class="pt-2">
                <button @click="confirmDelete" class="text-xs text-zinc-400 dark:text-zinc-500 hover:text-danger-500 transition-colors">
                  删除此日程
                </button>
              </div>
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-end gap-2 px-6 pb-6 pt-2 border-t border-zinc-200/30 dark:border-zinc-700/30">
              <button @click="cancelEdit" class="px-4 py-2 rounded-xl text-sm text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors">取消</button>
              <button @click="saveEdit"
                class="bg-primary-500 hover:bg-primary-400 active:bg-primary-600 px-5 py-2 rounded-xl text-sm font-medium text-white transition-all"
                :disabled="!editForm.title.trim()">保存</button>
            </div>
          </template>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({
  schedule: { type: Object, required: true },
  visible: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'update'])

const { updateSchedule, deleteSchedule } = useSchedules()
const { userId } = useAuth()

const mode = ref('view')

const editForm = reactive({ title: '', category: '', location: '', description: '', recurrence_rule: '', privacy_level: 1 })
const editStartDate = ref('')
const editStartTime = ref('')
const editEndDate = ref('')
const editEndTime = ref('')
const editRecurrenceEnd = ref('')

const RECURRENCE_LABELS = { daily: '每天', weekdays: '工作日', weekly: '每周', monthly: '每月' }
const recurrenceLabel = computed(() => RECURRENCE_LABELS[props.schedule.recurrence_rule] || props.schedule.recurrence_rule)

function parseDatetime(dt) {
  const parts = (dt || ' ').split(' ')
  return [parts[0] || '', (parts[1] || '').slice(0, 5)]
}

function initEditForm() {
  editForm.title = props.schedule.title
  editForm.category = props.schedule.category || ''
  editForm.location = props.schedule.location || ''
  editForm.description = props.schedule.description || ''
  editForm.recurrence_rule = props.schedule.recurrence_rule || ''
  editForm.privacy_level = props.schedule.privacy_level || 1
  const [sd, st] = parseDatetime(props.schedule.start_time)
  editStartDate.value = sd
  editStartTime.value = st
  const [ed, et] = parseDatetime(props.schedule.end_time)
  editEndDate.value = ed
  editEndTime.value = et
  editRecurrenceEnd.value = props.schedule.recurrence_end ? props.schedule.recurrence_end.slice(0, 10) : ''
}

watch(() => props.visible, (v) => {
  if (v) { mode.value = 'view'; initEditForm() }
})

const formattedDate = computed(() => {
  const s = props.schedule.start_time || ''
  const parts = s.split(' ')[0]?.split('-')
  if (!parts || parts.length < 3) return s
  return `${parts[0]}年${parseInt(parts[1])}月${parseInt(parts[2])}日`
})

const formattedTime = computed(() => {
  const s = (props.schedule.start_time || '').split(' ')[1]?.slice(0, 5) || ''
  const e = (props.schedule.end_time || '').split(' ')[1]?.slice(0, 5) || ''
  return s ? `${s} - ${e}` : ''
})

function close() { mode.value = 'view'; emit('close') }
function enterEditMode() { mode.value = 'edit' }
function cancelEdit() { mode.value = 'view'; initEditForm() }

function adjustTime(which, dir) {
  const ref = which === 'start' ? editStartTime : editEndTime
  const [h, m] = (ref.value || '00:00').split(':').map(Number)
  const d = new Date()
  d.setHours(h + dir, m)
  ref.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function saveEdit() {
  const updates = {
    title: editForm.title.trim(),
    category: editForm.category || null,
    location: editForm.location || null,
    description: editForm.description || null,
    privacy_level: editForm.privacy_level || 1,
    start_time: `${editStartDate.value} ${editStartTime.value}:00`,
    end_time: `${editEndDate.value} ${editEndTime.value}:00`,
    recurrence_rule: editForm.recurrence_rule || null,
    recurrence_end: editForm.recurrence_rule && editRecurrenceEnd.value ? `${editRecurrenceEnd.value} 23:59:59` : null
  }
  if (!updates.title || !updates.start_time) return
  try {
    await updateSchedule(props.schedule.id, updates, userId.value)
    emit('update')
    close()
  } catch { alert('保存失败，请重试') }
}

async function confirmDelete() {
  if (confirm(`确认删除「${props.schedule.title}」？`)) {
    await deleteSchedule(props.schedule.id, userId.value)
    emit('update')
    close()
  }
}

function categoryClass(cat) {
  const map = {
    '工作': 'bg-cat-work-50 text-cat-work-600 border-cat-work-400/20',
    '学习': 'bg-cat-study-50 text-cat-study-600 border-cat-study-400/20',
    '生活': 'bg-cat-life-50 text-cat-life-600 border-cat-life-400/20'
  }
  return map[cat] || 'text-zinc-500 bg-cat-default-50 border-cat-default-400/20'
}

function privacyLabel(level) {
  const map = { 1: '公开', 2: '内部', 3: '绝密' }
  return map[level] || '公开'
}

function privacyClass(level) {
  const map = {
    1: 'bg-green-400/10 text-green-600 border-green-400/20',
    2: 'bg-amber-400/10 text-amber-600 border-amber-400/20',
    3: 'bg-rose-400/10 text-rose-600 border-rose-400/20'
  }
  return map[level] || ''
}
</script>
