<script setup>
import { h, onMounted, ref } from 'vue'
import {
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NInput,
  NPopconfirm,
  NProgress,
  NSelect,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '工作汇报' })

const $table = ref(null)
const queryItems = ref({})
const detailVisible = ref(false)
const currentReport = ref({})

const riskOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
]

const riskMap = {
  low: { text: '低', type: 'success' },
  medium: { text: '中', type: 'warning' },
  high: { text: '高', type: 'error' },
}

const taskStatusMap = {
  not_started: { text: '未开始', type: 'default' },
  in_progress: { text: '进行中', type: 'info' },
  blocked: { text: '阻塞', type: 'error' },
  in_review: { text: '审核中', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  archived: { text: '已归档', type: 'default' },
}

onMounted(() => {
  $table.value?.handleSearch()
})

function renderRisk(value) {
  const item = riskMap[value] || { text: value || '-', type: 'default' }
  return h(NTag, { type: item.type, size: 'small' }, { default: () => item.text })
}

function renderTaskStatus(value) {
  const item = taskStatusMap[value] || { text: value || '-', type: 'default' }
  return h(NTag, { type: item.type, size: 'small' }, { default: () => item.text })
}

function renderList(values) {
  if (!values?.length) return '-'
  return values.join('；')
}

function renderTwoLine(primary, secondary) {
  return h('div', { class: 'report-cell' }, [
    h('div', { class: 'report-cell__primary' }, primary || '-'),
    secondary ? h('div', { class: 'report-cell__secondary' }, secondary) : null,
  ])
}

function getReporterText(row) {
  if (row.reporter_name && row.reporter_username && row.reporter_name !== row.reporter_username) {
    return `${row.reporter_name}（${row.reporter_username}）`
  }
  return row.reporter_name || row.reporter_username || '未知提交人'
}

function getAssigneeText(row) {
  if (row.assignee_name && row.assignee_username && row.assignee_name !== row.assignee_username) {
    return `${row.assignee_name}（${row.assignee_username}）`
  }
  return row.assignee_name || row.assignee_username || '未分配'
}

function getSummary(row) {
  return row.raw_content || row.problems?.[0] || row.support_needed?.[0] || '-'
}

function handleView(row) {
  currentReport.value = row
  detailVisible.value = true
}

async function handleDelete(row) {
  await api.deleteReport({ id: row.id })
  $message.success('删除成功')
  $table.value?.handleSearch()
}

const columns = [
  {
    title: '项目',
    key: 'project_name',
    width: 180,
    render(row) {
      const secondary = row.project_code ? `编码：${row.project_code}` : '项目信息未补全'
      return renderTwoLine(row.project_name || '未命名项目', secondary)
    },
  },
  {
    title: '任务',
    key: 'task_title',
    minWidth: 220,
    render(row) {
      return renderTwoLine(
        row.task_title || '未命名任务',
        row.created_at ? `提交时间：${row.created_at}` : '任务信息未补全'
      )
    },
  },
  {
    title: '提交人 / 负责人',
    key: 'reporter_id',
    width: 190,
    render(row) {
      return renderTwoLine(getReporterText(row), `负责人：${getAssigneeText(row)}`)
    },
  },
  {
    title: '状态 / 风险',
    key: 'risk_level',
    width: 120,
    align: 'center',
    render(row) {
      return h('div', { class: 'report-tags' }, [
        renderTaskStatus(row.task_status),
        renderRisk(row.risk_level),
      ])
    },
  },
  {
    title: '估算进度',
    key: 'progress_after',
    width: 180,
    render(row) {
      return h('div', { class: 'report-progress' }, [
        h('div', { class: 'report-cell__secondary' }, `系统估算 ${row.progress_after || 0}%`),
        h(NProgress, {
          type: 'line',
          percentage: row.progress_after || 0,
          indicatorPlacement: 'inside',
        }),
      ])
    },
  },
  {
    title: '汇报摘要',
    key: 'raw_content',
    minWidth: 260,
    ellipsis: { tooltip: true },
    render(row) {
      return getSummary(row)
    },
  },
  {
    title: '提交时间',
    key: 'created_at',
    width: 170,
    align: 'center',
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            onClick: () => handleView(row),
          },
          {
            default: () => '查看',
            icon: renderIcon('material-symbols:visibility-outline', { size: 16 }),
          }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row),
          },
          {
            trigger: () =>
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                },
                {
                  default: () => '删除',
                  icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                }
              ),
            default: () => h('div', {}, '确定删除该汇报吗？'),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="工作汇报">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getReportList"
      :scroll-x="1340"
    >
      <template #queryBar>
        <QueryBarItem label="关键词" :label-width="55">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="项目 / 任务 / 提交人 / 汇报内容"
            style="width: 260px"
            @keypress.enter="$table?.handleSearch()"
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

    <CrudModal v-model:visible="detailVisible" width="860px" title="汇报详情" :show-footer="false">
      <NDescriptions bordered label-placement="left" :column="2">
        <NDescriptionsItem label="项目">
          {{ currentReport.project_name || '未命名项目' }}
          <span v-if="currentReport.project_code" class="detail-sub"
            >（{{ currentReport.project_code }}）</span
          >
        </NDescriptionsItem>
        <NDescriptionsItem label="任务">
          {{ currentReport.task_title || '未命名任务' }}
        </NDescriptionsItem>
        <NDescriptionsItem label="提交人">{{ getReporterText(currentReport) }}</NDescriptionsItem>
        <NDescriptionsItem label="负责人">{{ getAssigneeText(currentReport) }}</NDescriptionsItem>
        <NDescriptionsItem label="任务状态">
          <NTag :type="taskStatusMap[currentReport.task_status]?.type || 'default'" size="small">
            {{ taskStatusMap[currentReport.task_status]?.text || '-' }}
          </NTag>
        </NDescriptionsItem>
        <NDescriptionsItem label="风险">
          <NTag :type="riskMap[currentReport.risk_level]?.type || 'default'" size="small">
            {{ riskMap[currentReport.risk_level]?.text || '-' }}
          </NTag>
        </NDescriptionsItem>
        <NDescriptionsItem label="估算进度">
          汇报后系统估算 {{ currentReport.progress_after || 0 }}%
        </NDescriptionsItem>
        <NDescriptionsItem label="提交时间">{{
          currentReport.created_at || '-'
        }}</NDescriptionsItem>
        <NDescriptionsItem label="原始留言" :span="2">{{
          currentReport.raw_content || '-'
        }}</NDescriptionsItem>
        <NDescriptionsItem label="完成事项" :span="2">
          {{ renderList(currentReport.completed_items) }}
        </NDescriptionsItem>
        <NDescriptionsItem label="遇到的问题" :span="2">
          {{ renderList(currentReport.problems) }}
        </NDescriptionsItem>
        <NDescriptionsItem label="需要支持" :span="2">
          {{ renderList(currentReport.support_needed) }}
        </NDescriptionsItem>
        <NDescriptionsItem label="建议动作" :span="2">
          {{ renderList(currentReport.suggestions) }}
        </NDescriptionsItem>
      </NDescriptions>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
.report-cell {
  line-height: 1.5;
}

.report-cell__primary {
  font-weight: 500;
}

.report-cell__secondary {
  margin-top: 2px;
  color: var(--text-color-3);
  font-size: 12px;
}

.report-tags {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.report-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-sub {
  color: var(--text-color-3);
}
</style>
