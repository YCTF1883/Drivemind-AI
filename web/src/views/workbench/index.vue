<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>{{ $t('views.workbench.text_welcome') }}</p>
            </div>
          </div>
          <n-space :size="12" :wrap="false">
            <n-statistic v-for="item in statisticData" :key="item.id" v-bind="item"></n-statistic>
          </n-space>
        </div>
      </n-card>

      <n-card
        :title="$t('views.workbench.label_project')"
        size="small"
        :segmented="true"
        mt-15
        rounded-10
      >
        <template #header-extra>
          <n-button text type="primary">{{ $t('views.workbench.label_more') }}</n-button>
        </template>
        <div flex flex-wrap justify-between>
          <n-card
            v-for="item in capabilityCards"
            :key="item.title"
            class="mb-10 mt-10 w-300 cursor-pointer"
            hover:card-shadow
            :title="item.title"
            size="small"
          >
            <p op-60>{{ item.desc }}</p>
          </n-card>
        </div>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'

const capabilityCards = [
  {
    title: '项目进度分析',
    desc: '汇总研发项目状态、阶段进度、负责人和关键节点。',
  },
  {
    title: 'AI任务拆解',
    desc: '根据研发目标自动拆分阶段、任务和执行建议。',
  },
  {
    title: '员工汇报分析',
    desc: '将自然语言日报解析为进度、问题、风险和所需支持。',
  },
  {
    title: '知识库问答',
    desc: '基于企业文档、会议纪要和项目资料提供研发知识检索。',
  },
  {
    title: '风险预警',
    desc: '识别延期风险、任务阻塞、人员负载和资源瓶颈。',
  },
  {
    title: '自动报告',
    desc: '自动生成项目周报、部门月报和管理层风险报告。',
  },
]

const { t } = useI18n({ useScope: 'global' })

const statisticData = computed(() => [
  {
    id: 0,
    label: t('views.workbench.label_number_of_items'),
    value: '25',
  },
  {
    id: 1,
    label: t('views.workbench.label_upcoming'),
    value: '46',
  },
  {
    id: 2,
    label: t('views.workbench.label_risk_tasks'),
    value: '5',
  },
  {
    id: 3,
    label: t('views.workbench.label_pending_reports'),
    value: '12',
  },
])

const userStore = useUserStore()
</script>
