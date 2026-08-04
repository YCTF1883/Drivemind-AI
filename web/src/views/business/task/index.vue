<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NDatePicker,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NProgress,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { usePermissionStore, useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '任务管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userStore = useUserStore()
const permissionStore = usePermissionStore()
const projectOptions = ref([])
const userOptions = ref([])
const onlyMine = ref(false)
const reportVisible = ref(false)
const reportLoading = ref(false)
const currentTask = ref(null)
const reportFormRef = ref(null)
const reportForm = ref(getInitReportForm())

const initForm = {
  title: '',
  desc: '',
  project_id: null,
  assignee_id: null,
  priority: 'medium',
  due_date: null,
  status: 'not_started',
  progress: 0,
  workload: 'normal',
  risk_level: 'low',
  source: 'manual',
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
  name: '任务',
  initForm,
  doCreate: api.createTask,
  doUpdate: api.updateTask,
  doDelete: api.deleteTask,
  refresh: () => $table.value?.handleSearch(),
})

const statusOptions = [
  { label: '未开始', value: 'not_started' },
  { label: '进行中', value: 'in_progress' },
  { label: '阻塞', value: 'blocked' },
  { label: '审核中', value: 'in_review' },
  { label: '已完成', value: 'completed' },
  { label: '已归档', value: 'archived' },
]

const reportStatusOptions = [
  { label: '正常推进', value: 'in_progress' },
  { label: '遇到阻塞', value: 'blocked' },
  { label: '完成待审核', value: 'in_review' },
]

const priorityOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
  { label: '紧急', value: 'urgent' },
]

const workloadOptions = [
  { label: '简单', value: 'simple' },
  { label: '普通', value: 'normal' },
  { label: '复杂', value: 'complex' },
]

const riskOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
]

const statusProgressMap = {
  not_started: 0,
  blocked: 30,
  in_progress: 50,
  in_review: 80,
  completed: 100,
  archived: 0,
}

const statusMap = {
  not_started: { text: '未开始', type: 'default' },
  in_progress: { text: '进行中', type: 'success' },
  blocked: { text: '阻塞', type: 'error' },
  in_review: { text: '审核中', type: 'warning' },
  completed: { text: '已完成', type: 'info' },
  archived: { text: '已归档', type: 'default' },
}

const priorityMap = {
  low: { text: '低', type: 'default' },
  medium: { text: '中', type: 'info' },
  high: { text: '高', type: 'warning' },
  urgent: { text: '紧急', type: 'error' },
}

const workloadMap = {
  simple: { text: '简单', type: 'success' },
  normal: { text: '普通', type: 'info' },
  complex: { text: '复杂', type: 'warning' },
}

const riskMap = {
  low: { text: '低', type: 'success' },
  medium: { text: '中', type: 'warning' },
  high: { text: '高', type: 'error' },
}

const rules = {
  title: [{ required: true, message: '请输入任务标题', trigger: ['input', 'blur'] }],
  project_id: [
    { required: true, type: 'number', message: '请选择所属项目', trigger: ['blur', 'change'] },
  ],
}

const reportRules = {
  task_status: [{ required: true, message: '请选择本次状态', trigger: ['blur', 'change'] }],
  raw_content: [{ required: true, message: '请输入进展留言', trigger: ['input', 'blur'] }],
}

const canListProjects = computed(() => hasApi('get/api/v1/project/list'))
const canListUsers = computed(() => hasApi('get/api/v1/user/list'))
const canCreateTask = computed(() => hasApi('post/api/v1/task/create'))
const canUpdateTask = computed(() => hasApi('post/api/v1/task/update'))
const canConfirmReport = computed(() => hasApi('post/api/v1/report/confirm'))
const reportModalTitle = computed(() => `汇报进展：${currentTask.value?.title || ''}`)

onMounted(async () => {
  onlyMine.value = !canCreateTask.value
  await loadOptions()
  $table.value?.handleSearch()
})

function hasApi(permission) {
  return userStore.isSuperUser || permissionStore.apis.includes(permission)
}

async function loadOptions() {
  if (canListProjects.value) {
    const projectRes = await api.getProjectList({ page: 1, page_size: 9999 })
    projectOptions.value = projectRes.data.map((item) => ({ label: item.name, value: item.id }))
  }

  if (canListUsers.value) {
    const userRes = await api.getUserList({ page: 1, page_size: 9999 })
    userOptions.value = userRes.data.map((item) => ({
      label: item.alias ? `${item.alias}（${item.username}）` : item.username,
      value: item.id,
    }))
  }
}

function getTaskData(params) {
  return onlyMine.value ? api.getMyTaskList(params) : api.getTaskList(params)
}

function handleOnlyMineChange() {
  $table.value?.handleSearch()
}

function getInitReportForm(row = {}) {
  return {
    task_id: row.id,
    task_status:
      row.progress >= 100 ? 'in_review' : row.status === 'blocked' ? 'blocked' : 'in_progress',
    progress_after: row.progress || 0,
    risk_level: row.risk_level || 'low',
    raw_content: '',
    completed_items_text: '',
    problems_text: '',
    support_needed_text: '',
    suggestions_text: '',
  }
}

function handleOpenReport(row) {
  currentTask.value = row
  reportForm.value = getInitReportForm(row)
  reportVisible.value = true
}

function handleReportStatusChange(value) {
  if (value === 'blocked' && reportForm.value.risk_level === 'low') {
    reportForm.value.risk_level = 'medium'
  }
}

function splitLines(value) {
  return String(value || '')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

async function handleSaveReport() {
  reportFormRef.value?.validate(async (err) => {
    if (err) return
    if (reportForm.value.task_status === 'blocked' && !reportForm.value.problems_text.trim()) {
      $message.error('遇到阻塞时请填写具体问题')
      return
    }

    try {
      reportLoading.value = true
      await api.confirmReport({
        task_id: reportForm.value.task_id,
        task_status: reportForm.value.task_status,
        progress_after: currentTask.value?.progress || 0,
        progress_delta: 0,
        risk_level: reportForm.value.risk_level,
        raw_content: reportForm.value.raw_content,
        completed_items: splitLines(reportForm.value.completed_items_text),
        problems: splitLines(reportForm.value.problems_text),
        support_needed: splitLines(reportForm.value.support_needed_text),
        suggestions: splitLines(reportForm.value.suggestions_text),
      })
      $message.success(
        reportForm.value.task_status === 'in_review'
          ? '已提交审核，等待经理确认'
          : '进展已同步给经理'
      )
      reportVisible.value = false
      $table.value?.handleSearch()
    } finally {
      reportLoading.value = false
    }
  })
}

async function handleConfirmComplete(row) {
  await api.updateTask({
    ...row,
    status: 'completed',
  })
  $message.success('已确认任务完成')
  $table.value?.handleSearch()
}

function canReportProgress(row) {
  return (
    canConfirmReport.value &&
    row.assignee_id === userStore.userId &&
    !['in_review', 'completed', 'archived'].includes(row.status)
  )
}

function canConfirmComplete(row) {
  return canUpdateTask.value && row.status === 'in_review'
}

function getEstimatedProgress(status) {
  return statusProgressMap[status] ?? 0
}

function renderTag(map, value) {
  const item = map[value] || { text: value || '-', type: 'default' }
  return h(NTag, { type: item.type, size: 'small' }, { default: () => item.text })
}

function getOptionLabel(options, value, fallback) {
  if (!value) return '-'
  return options.find((item) => item.value === value)?.label || fallback
}

function getLatestReporterText(row) {
  if (
    row.latest_reporter_name &&
    row.latest_reporter_username &&
    row.latest_reporter_name !== row.latest_reporter_username
  ) {
    return `${row.latest_reporter_name}（${row.latest_reporter_username}）`
  }
  return row.latest_reporter_name || row.latest_reporter_username || '暂无汇报'
}

function getLatestReportTags(row) {
  const tags = []
  if (row.status === 'blocked' || row.latest_report_problems?.length) {
    tags.push({ text: '阻塞', type: 'error' })
  }
  if (row.latest_report_support_needed?.length) {
    tags.push({ text: '需支持', type: 'warning' })
  }
  if (row.risk_level === 'high' || row.latest_report_risk_level === 'high') {
    tags.push({ text: '高风险', type: 'error' })
  }
  if (row.status === 'in_review') {
    tags.push({ text: '待审核', type: 'warning' })
  }
  return tags
}

function renderLatestReport(row) {
  if (!row.latest_report_id) {
    return h('div', { class: 'latest-report latest-report--empty' }, '暂无汇报')
  }

  const tags = getLatestReportTags(row)
  return h('div', { class: 'latest-report' }, [
    h('div', { class: 'latest-report__title' }, getLatestReporterText(row)),
    h('div', { class: 'latest-report__content' }, row.latest_report_content || '-'),
    tags.length
      ? h(
          'div',
          { class: 'latest-report__tags' },
          tags.map((tag) => h(NTag, { type: tag.type, size: 'small' }, { default: () => tag.text }))
        )
      : null,
    h('div', { class: 'latest-report__time' }, row.latest_report_time || '-'),
  ])
}

const columns = [
  {
    title: '任务标题',
    key: 'title',
    width: 180,
    ellipsis: { tooltip: true },
  },
  {
    title: '所属项目',
    key: 'project_id',
    width: 140,
    render(row) {
      return getOptionLabel(projectOptions.value, row.project_id, '未命名项目')
    },
  },
  {
    title: '负责人',
    key: 'assignee_id',
    width: 120,
    render(row) {
      const fallback = row.assignee_id === userStore.userId ? '我' : '未知负责人'
      return getOptionLabel(userOptions.value, row.assignee_id, fallback)
    },
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
    title: '优先级',
    key: 'priority',
    width: 80,
    align: 'center',
    render(row) {
      return renderTag(priorityMap, row.priority)
    },
  },
  {
    title: '工作量',
    key: 'workload',
    width: 80,
    align: 'center',
    render(row) {
      return renderTag(workloadMap, row.workload || 'normal')
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
    title: '估算进度',
    key: 'progress',
    width: 150,
    render(row) {
      return h(NProgress, {
        type: 'line',
        percentage: row.progress || 0,
        indicatorPlacement: 'inside',
        processing: row.status === 'in_progress' && row.progress < 100,
      })
    },
  },
  {
    title: '最新汇报',
    key: 'latest_report_content',
    minWidth: 260,
    render(row) {
      return renderLatestReport(row)
    },
  },
  {
    title: '截止日期',
    key: 'due_date',
    width: 110,
    align: 'center',
    render(row) {
      return row.due_date || '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 270,
    align: 'center',
    fixed: 'right',
    render(row) {
      const actions = []

      if (canReportProgress(row)) {
        actions.push(
          h(
            NButton,
            {
              size: 'small',
              type: row.status === 'blocked' ? 'warning' : 'success',
              style: 'margin-right: 8px;',
              onClick: () => handleOpenReport(row),
            },
            {
              default: () => '汇报进展',
              icon: renderIcon('material-symbols:chat-outline', { size: 16 }),
            }
          )
        )
      }

      if (canConfirmComplete(row)) {
        actions.push(
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleConfirmComplete(row),
            },
            {
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'success',
                    style: 'margin-right: 8px;',
                  },
                  {
                    default: () => '确认完成',
                    icon: renderIcon('material-symbols:check-circle-outline', { size: 16 }),
                  }
                ),
              default: () => h('div', {}, '确认该任务已完成吗？'),
            }
          )
        )
      }

      actions.push(
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
          [[vPermission, 'post/api/v1/task/update']]
        )
      )
      actions.push(
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
                [[vPermission, 'delete/api/v1/task/delete']]
              ),
            default: () => h('div', {}, '确定归档该任务吗？'),
          }
        )
      )

      return actions
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="任务管理">
    <template #action>
      <NSpace align="center">
        <span class="text-14">只看我的任务</span>
        <NSwitch v-model:value="onlyMine" @update:value="handleOnlyMineChange" />
        <NButton v-permission="'post/api/v1/task/create'" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建任务
        </NButton>
      </NSpace>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="getTaskData"
      :scroll-x="1530"
    >
      <template #queryBar>
        <QueryBarItem label="标题" :label-width="40">
          <NInput
            v-model:value="queryItems.title"
            clearable
            placeholder="请输入任务标题"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem v-if="canListProjects" label="项目" :label-width="40">
          <NSelect
            v-model:value="queryItems.project_id"
            clearable
            filterable
            :options="projectOptions"
            placeholder="请选择项目"
          />
        </QueryBarItem>
        <QueryBarItem v-if="canListUsers" label="负责人" :label-width="52">
          <NSelect
            v-model:value="queryItems.assignee_id"
            clearable
            filterable
            :options="userOptions"
            placeholder="请选择负责人"
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
        <NFormItem label="任务标题" path="title">
          <NInput v-model:value="modalForm.title" clearable placeholder="请输入任务标题" />
        </NFormItem>
        <NFormItem label="任务描述" path="desc">
          <NInput
            v-model:value="modalForm.desc"
            type="textarea"
            clearable
            placeholder="请输入任务描述"
          />
        </NFormItem>
        <NFormItem label="所属项目" path="project_id">
          <NSelect
            v-model:value="modalForm.project_id"
            filterable
            :options="projectOptions"
            placeholder="请选择所属项目"
          />
        </NFormItem>
        <NFormItem label="负责人" path="assignee_id">
          <NSelect
            v-model:value="modalForm.assignee_id"
            clearable
            filterable
            :options="userOptions"
            placeholder="请选择执行员工"
          />
        </NFormItem>
        <NFormItem label="状态" path="status">
          <NSelect v-model:value="modalForm.status" :options="statusOptions" />
        </NFormItem>
        <NFormItem label="优先级" path="priority">
          <NSelect v-model:value="modalForm.priority" :options="priorityOptions" />
        </NFormItem>
        <NFormItem label="工作量" path="workload">
          <NSelect v-model:value="modalForm.workload" :options="workloadOptions" />
        </NFormItem>
        <NFormItem label="风险等级" path="risk_level">
          <NSelect v-model:value="modalForm.risk_level" :options="riskOptions" />
        </NFormItem>
        <NFormItem label="截止日期" path="due_date">
          <NDatePicker
            v-model:formatted-value="modalForm.due_date"
            type="date"
            value-format="yyyy-MM-dd"
            clearable
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="估算进度">
          <NProgress
            type="line"
            :percentage="getEstimatedProgress(modalForm.status)"
            indicator-placement="inside"
          />
        </NFormItem>
      </NForm>
    </CrudModal>

    <CrudModal
      v-model:visible="reportVisible"
      width="720px"
      :title="reportModalTitle"
      :loading="reportLoading"
      @save="handleSaveReport"
    >
      <NForm
        ref="reportFormRef"
        label-placement="left"
        label-align="left"
        :label-width="110"
        :model="reportForm"
        :rules="reportRules"
      >
        <NFormItem label="本次状态" path="task_status">
          <NSelect
            v-model:value="reportForm.task_status"
            :options="reportStatusOptions"
            @update:value="handleReportStatusChange"
          />
        </NFormItem>
        <NFormItem label="风险等级" path="risk_level">
          <NSelect v-model:value="reportForm.risk_level" :options="riskOptions" />
        </NFormItem>
        <NFormItem label="进展留言" path="raw_content">
          <NInput
            v-model:value="reportForm.raw_content"
            type="textarea"
            clearable
            placeholder="说明现在做到哪里了、遇到了什么情况、希望经理知道什么"
          />
        </NFormItem>
        <NFormItem label="完成事项">
          <NInput
            v-model:value="reportForm.completed_items_text"
            type="textarea"
            clearable
            placeholder="一行一个完成事项"
          />
        </NFormItem>
        <NFormItem label="遇到的问题">
          <NInput
            v-model:value="reportForm.problems_text"
            type="textarea"
            clearable
            placeholder="一行一个问题；如果选择遇到阻塞，这里必须填写"
          />
        </NFormItem>
        <NFormItem label="需要支持">
          <NInput
            v-model:value="reportForm.support_needed_text"
            type="textarea"
            clearable
            placeholder="一行一个支持诉求，例如需要接口权限、需要某同事确认方案"
          />
        </NFormItem>
        <NFormItem label="建议动作">
          <NInput
            v-model:value="reportForm.suggestions_text"
            type="textarea"
            clearable
            placeholder="可选：希望经理怎么协调或下一步建议"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
.latest-report {
  line-height: 1.45;
}

.latest-report--empty {
  color: var(--text-color-3);
}

.latest-report__title {
  font-weight: 500;
}

.latest-report__content {
  display: -webkit-box;
  margin-top: 4px;
  overflow: hidden;
  color: var(--text-color-2);
  font-size: 12px;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.latest-report__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.latest-report__time {
  margin-top: 4px;
  color: var(--text-color-3);
  font-size: 12px;
}
</style>
