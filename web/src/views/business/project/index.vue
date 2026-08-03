<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NDatePicker,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NProgress,
  NSelect,
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
      return row.end_date || '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
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
      :scroll-x="980"
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
  </CommonPage>
</template>
