<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NAlert,
  NButton,
  NDatePicker,
  NDivider,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NProgress,
  NSelect,
  NSpin,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '项目管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userOptions = ref([])
const weeklyReportVisible = ref(false)
const weeklyReportLoading = ref(false)
const weeklyReportDownloading = ref(false)
const currentWeeklyProject = ref(null)
const weeklyReport = ref(null)

const initForm = {
  name: '',
  code: '',
  desc: '',
  status: 'active',
  start_date: null,
  end_date: null,
  progress: 0,
  risk_level: 'low',
  manager_id: null,
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '项目',
  initForm,
  doCreate: api.createProject,
  doUpdate: api.updateProject,
  doDelete: api.deleteProject,
  refresh: () => $table.value?.handleSearch(),
})

const statusOptions = [
  { label: '进行中', value: 'active' },
  { label: '暂停', value: 'paused' },
  { label: '已完成', value: 'completed' },
  { label: '已归档', value: 'archived' },
]

const riskOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
]

const statusMap = {
  active: { text: '进行中', type: 'success' },
  paused: { text: '暂停', type: 'warning' },
  completed: { text: '已完成', type: 'info' },
  archived: { text: '已归档', type: 'default' },
}

const riskMap = {
  low: { text: '低', type: 'success' },
  medium: { text: '中', type: 'warning' },
  high: { text: '高', type: 'error' },
}

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: ['input', 'blur'] }],
  code: [{ required: true, message: '请输入项目编码', trigger: ['input', 'blur'] }],
}

onMounted(async () => {
  $table.value?.handleSearch()
  const res = await api.getUserList({ page: 1, page_size: 9999 })
  userOptions.value = res.data.map((item) => ({
    label: item.alias ? `${item.alias}（${item.username}）` : item.username,
    value: item.id,
  }))
})

function renderTag(map, value) {
  const item = map[value] || { text: value || '-', type: 'default' }
  return h(NTag, { type: item.type, size: 'small' }, { default: () => item.text })
}

function getTodayText() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

function isBeforeToday(value) {
  if (!value) return false
  return String(value).slice(0, 10) < getTodayText()
}

function isProjectOverdue(row) {
  return isBeforeToday(row.end_date) && !['completed', 'archived'].includes(row.status)
}

function renderDateWithOverdue(value, overdue) {
  return h('div', { class: 'deadline-cell' }, [
    h('div', {}, value || '-'),
    overdue
      ? h(
          NTag,
          { type: 'error', size: 'small', style: 'margin-top: 4px;' },
          { default: () => '已逾期' }
        )
      : null,
  ])
}

async function handleWeeklyReport(row) {
  currentWeeklyProject.value = row
  weeklyReport.value = null
  weeklyReportVisible.value = true
  weeklyReportLoading.value = true
  try {
    const res = await api.generateProjectWeeklyReport({ project_id: row.id })
    weeklyReport.value = res.data
  } finally {
    weeklyReportLoading.value = false
  }
}

function resolveDownloadFilename(response) {
  const disposition = response.headers?.['content-disposition'] || ''
  const filenameMatch = disposition.match(/filename\*=UTF-8''([^;]+)/)
  if (filenameMatch?.[1]) {
    return decodeURIComponent(filenameMatch[1])
  }
  const projectName = weeklyReport.value?.project_name || currentWeeklyProject.value?.name || '项目'
  return `${projectName}-项目周报.docx`
}

async function handleDownloadWeeklyReport() {
  if (!currentWeeklyProject.value) return
  weeklyReportDownloading.value = true
  try {
    const response = await api.downloadProjectWeeklyReport({
      project_id: currentWeeklyProject.value.id,
    })
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = resolveDownloadFilename(response)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } finally {
    weeklyReportDownloading.value = false
  }
}

function renderReportList(items) {
  if (!items?.length) return ['暂无内容']
  return items
}

const columns = [
  {
    title: '项目名称',
    key: 'name',
    width: 160,
    ellipsis: { tooltip: true },
  },
  {
    title: '项目编码',
    key: 'code',
    width: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    align: 'center',
    render(row) {
      return renderTag(statusMap, row.status)
    },
  },
  {
    title: '风险',
    key: 'risk_level',
    width: 80,
    align: 'center',
    render(row) {
      return renderTag(riskMap, row.risk_level)
    },
  },
  {
    title: '进度',
    key: 'progress',
    width: 150,
    render(row) {
      return h(NProgress, {
        type: 'line',
        percentage: row.progress || 0,
        indicatorPlacement: 'inside',
        processing: row.status === 'active' && row.progress < 100,
      })
    },
  },
  {
    title: '开始日期',
    key: 'start_date',
    width: 110,
    align: 'center',
    render(row) {
      return row.start_date || '-'
    },
  },
  {
    title: '结束日期',
    key: 'end_date',
    width: 110,
    align: 'center',
    render(row) {
      return renderDateWithOverdue(row.end_date, isProjectOverdue(row))
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/project/update']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'info',
              style: 'margin-right: 8px;',
              onClick: () => handleWeeklyReport(row),
            },
            {
              default: () => 'AI 周报',
              icon: renderIcon('material-symbols:description-outline', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/ai/project_weekly_report']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                  },
                  {
                    default: () => '归档',
                    icon: renderIcon('material-symbols:archive-outline', { size: 16 }),
                  }
                ),
                [[vPermission, 'delete/api/v1/project/delete']]
              ),
            default: () => h('div', {}, '确定归档该项目吗？'),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="项目管理">
    <template #action>
      <NButton v-permission="'post/api/v1/project/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建项目
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getProjectList"
      :scroll-x="1100"
    >
      <template #queryBar>
        <QueryBarItem label="名称" :label-width="40">
          <NInput
            v-model:value="queryItems.name"
            clearable
            placeholder="请输入项目名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="编码" :label-width="40">
          <NInput
            v-model:value="queryItems.code"
            clearable
            placeholder="请输入项目编码"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect
            v-model:value="queryItems.status"
            clearable
            :options="statusOptions"
            placeholder="请选择状态"
          />
        </QueryBarItem>
        <QueryBarItem label="风险" :label-width="40">
          <NSelect
            v-model:value="queryItems.risk_level"
            clearable
            :options="riskOptions"
            placeholder="请选择风险"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="90"
        :model="modalForm"
        :rules="rules"
      >
        <NFormItem label="项目名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入项目名称" />
        </NFormItem>
        <NFormItem label="项目编码" path="code">
          <NInput v-model:value="modalForm.code" clearable placeholder="例如 DRIVEMIND-MVP" />
        </NFormItem>
        <NFormItem label="项目描述" path="desc">
          <NInput
            v-model:value="modalForm.desc"
            type="textarea"
            clearable
            placeholder="请输入项目目标和范围"
          />
        </NFormItem>
        <NFormItem label="状态" path="status">
          <NSelect v-model:value="modalForm.status" :options="statusOptions" />
        </NFormItem>
        <NFormItem label="风险等级" path="risk_level">
          <NSelect v-model:value="modalForm.risk_level" :options="riskOptions" />
        </NFormItem>
        <NFormItem label="项目进度" path="progress">
          <NInputNumber
            v-model:value="modalForm.progress"
            :min="0"
            :max="100"
            clearable
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="项目经理" path="manager_id">
          <NSelect
            v-model:value="modalForm.manager_id"
            clearable
            filterable
            :options="userOptions"
            placeholder="请选择项目经理"
          />
        </NFormItem>
        <NFormItem label="开始日期" path="start_date">
          <NDatePicker
            v-model:formatted-value="modalForm.start_date"
            clearable
            type="date"
            value-format="yyyy-MM-dd"
            placeholder="请选择开始日期"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="结束日期" path="end_date">
          <NDatePicker
            v-model:formatted-value="modalForm.end_date"
            clearable
            type="date"
            value-format="yyyy-MM-dd"
            placeholder="请选择结束日期"
            style="width: 100%"
          />
        </NFormItem>
      </NForm>
    </CrudModal>

    <CrudModal
      v-model:visible="weeklyReportVisible"
      title="AI 项目周报"
      width="820px"
      :loading="weeklyReportDownloading"
      :show-footer="true"
    >
      <NSpin :show="weeklyReportLoading">
        <template v-if="weeklyReport">
          <NAlert type="info" :bordered="false" class="mb-16">
            AI
            周报基于当前项目、任务状态、风险等级和近期工作汇报生成。下载路径由浏览器下载设置决定，如需每次选择路径，请开启浏览器“下载前询问保存位置”。
          </NAlert>
          <div class="weekly-report">
            <h2>{{ weeklyReport.title }}</h2>
            <p class="weekly-report-meta">
              {{ weeklyReport.project_name }}｜{{ weeklyReport.project_code || '-' }}｜{{
                weeklyReport.period
              }}
            </p>

            <NDivider />
            <h3>一、本周整体进展</h3>
            <p>{{ weeklyReport.overall_summary }}</p>
            <h3>二、项目进度</h3>
            <p>{{ weeklyReport.progress_summary }}</p>

            <template
              v-for="section in [
                ['三、已完成工作', weeklyReport.completed_work],
                ['四、进行中任务', weeklyReport.ongoing_tasks],
                ['五、风险与阻塞', weeklyReport.blocked_or_risky_items],
                ['六、近期汇报摘要', weeklyReport.recent_reports_summary],
                ['七、下周计划', weeklyReport.next_week_plan],
                ['八、AI 管理建议', weeklyReport.management_suggestions],
              ]"
              :key="section[0]"
            >
              <h3>{{ section[0] }}</h3>
              <ul>
                <li v-for="item in renderReportList(section[1])" :key="item">{{ item }}</li>
              </ul>
            </template>
          </div>
        </template>
      </NSpin>
      <template #footer>
        <NButton @click="weeklyReportVisible = false">关闭</NButton>
        <NButton
          type="primary"
          :loading="weeklyReportDownloading"
          :disabled="!weeklyReport"
          style="margin-left: 12px"
          @click="handleDownloadWeeklyReport"
        >
          下载 Word
        </NButton>
      </template>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
.weekly-report h2 {
  margin: 0;
  text-align: center;
}

.weekly-report h3 {
  margin: 18px 0 8px;
  font-weight: 600;
}

.weekly-report p {
  line-height: 1.8;
}

.weekly-report ul {
  margin: 0;
  padding-left: 20px;
}

.weekly-report li {
  margin-bottom: 6px;
  line-height: 1.7;
}

.weekly-report-meta {
  color: #666;
  text-align: center;
}
</style>
