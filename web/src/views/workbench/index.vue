<template>
  <AppPage :show-footer="false">
    <n-spin :show="loading">
      <div class="workbench-page">
        <n-card rounded-10>
          <div class="hero-card">
            <div class="hero-user">
              <img rounded-full width="60" :src="userStore.avatar" />
              <div ml-10>
                <p text-20 font-semibold>
                  {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
                </p>
                <p mt-5 text-14 op-60>
                  这里是 DriveMind AI 的研发运营总览，帮你快速掌握项目进度、任务风险和团队反馈。
                </p>
              </div>
            </div>
            <n-space :size="12" :wrap="false" class="hero-stats">
              <n-statistic
                v-for="item in statisticData"
                :key="item.id"
                :label="item.label"
                :value="item.value"
              />
            </n-space>
          </div>
        </n-card>

        <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
          <n-gi v-for="card in metricCards" :key="card.key" span="4 s:2 l:1">
            <n-card class="metric-card" :bordered="false">
              <div class="metric-card__label">{{ card.label }}</div>
              <div class="metric-card__value">{{ card.value }}</div>
              <div class="metric-card__desc">{{ card.desc }}</div>
            </n-card>
          </n-gi>
        </n-grid>

        <n-grid :cols="12" :x-gap="16" :y-gap="16" responsive="screen">
          <n-gi :span="12" :lg="7">
            <n-card title="任务状态分布" rounded-10>
              <div v-if="taskStatusItems.length" class="distribution-list">
                <div v-for="item in taskStatusItems" :key="item.status" class="distribution-item">
                  <div class="distribution-item__head">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.count }}</strong>
                  </div>
                  <n-progress
                    type="line"
                    :percentage="item.percent"
                    :show-indicator="false"
                    :status="item.progressStatus"
                  />
                </div>
              </div>
              <n-empty v-else description="暂无任务数据" />
            </n-card>
          </n-gi>

          <n-gi :span="12" :lg="5">
            <n-card title="风险概况" rounded-10>
              <div v-if="riskItems.length" class="risk-list">
                <div v-for="item in riskItems" :key="item.risk_level" class="risk-item">
                  <div class="risk-item__main">
                    <n-tag :type="item.tagType" size="small">{{ item.label }}</n-tag>
                    <span>{{ item.count }} 个任务</span>
                  </div>
                  <n-progress
                    type="line"
                    :percentage="item.percent"
                    :show-indicator="false"
                    :status="item.progressStatus"
                  />
                </div>
              </div>
              <n-empty v-else description="暂无风险数据" />
            </n-card>
          </n-gi>
        </n-grid>

        <n-grid :cols="12" :x-gap="16" :y-gap="16" responsive="screen">
          <n-gi :span="12" :lg="7">
            <n-card title="重点项目进度" rounded-10>
              <div v-if="projectProgress.length" class="project-list">
                <div v-for="project in projectProgress" :key="project.id" class="project-item">
                  <div class="project-item__head">
                    <div>
                      <div class="item-title">{{ project.name || '未命名项目' }}</div>
                      <div class="item-sub">{{ project.code || '暂无编码' }}</div>
                    </div>
                    <div class="tag-group">
                      <n-tag :type="getProjectStatus(project.status).type" size="small">
                        {{ getProjectStatus(project.status).text }}
                      </n-tag>
                      <n-tag :type="getRisk(project.risk_level).type" size="small">
                        {{ getRisk(project.risk_level).text }}
                      </n-tag>
                    </div>
                  </div>
                  <n-progress
                    type="line"
                    :percentage="project.progress || 0"
                    indicator-placement="inside"
                    :processing="project.status === 'active' && project.progress < 100"
                  />
                </div>
              </div>
              <n-empty v-else description="暂无项目数据" />
            </n-card>
          </n-gi>

          <n-gi :span="12" :lg="5">
            <n-card title="待处理事项" rounded-10>
              <div v-if="actionItems.length" class="action-list">
                <div v-for="item in actionItems" :key="item.id" class="action-item">
                  <div class="action-item__head">
                    <div class="item-title">{{ item.title || '未命名任务' }}</div>
                    <n-tag :type="getTaskStatus(item.status).type" size="small">
                      {{ getTaskStatus(item.status).text }}
                    </n-tag>
                  </div>
                  <div class="item-sub">
                    {{ item.project_name || '未命名项目' }} · 负责人：{{
                      item.assignee_name || '未分配'
                    }}
                  </div>
                  <div class="action-item__meta">
                    <n-tag :type="getRisk(item.risk_level).type" size="small">
                      {{ getRisk(item.risk_level).text }}
                    </n-tag>
                    <span>{{ item.due_date ? `截止：${item.due_date}` : '暂无截止日期' }}</span>
                  </div>
                </div>
              </div>
              <n-empty v-else description="暂无待处理事项" />
            </n-card>
          </n-gi>
        </n-grid>

        <n-card title="最近工作汇报" rounded-10>
          <div v-if="recentReports.length" class="report-list">
            <div v-for="report in recentReports" :key="report.id" class="report-item">
              <div class="report-item__main">
                <div class="item-title">{{ report.task_title || '未命名任务' }}</div>
                <div class="item-sub">
                  {{ report.project_name || '未命名项目' }} ·
                  {{ report.reporter_name || '未知提交人' }} · {{ report.created_at || '-' }}
                </div>
                <div class="report-content">{{ report.raw_content || '-' }}</div>
              </div>
              <div class="report-item__side">
                <n-tag :type="getRisk(report.risk_level).type" size="small">
                  {{ getRisk(report.risk_level).text }}
                </n-tag>
                <span>进度 {{ report.progress_after || 0 }}%</span>
              </div>
            </div>
          </div>
          <n-empty v-else description="暂无工作汇报" />
        </n-card>
      </div>
    </n-spin>
  </AppPage>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUserStore } from '@/store'
import api from '@/api'

const userStore = useUserStore()
const loading = ref(false)
const dashboard = ref({})

const defaultSummary = {
  project_total: 0,
  active_projects: 0,
  task_total: 0,
  active_tasks: 0,
  review_tasks: 0,
  blocked_tasks: 0,
  risk_tasks: 0,
  weekly_reports: 0,
}

const taskStatusMap = {
  not_started: { text: '未开始', type: 'default', progressStatus: 'default' },
  in_progress: { text: '进行中', type: 'info', progressStatus: 'info' },
  blocked: { text: '阻塞', type: 'error', progressStatus: 'error' },
  in_review: { text: '审核中', type: 'warning', progressStatus: 'warning' },
  completed: { text: '已完成', type: 'success', progressStatus: 'success' },
  archived: { text: '已归档', type: 'default', progressStatus: 'default' },
}

const projectStatusMap = {
  active: { text: '进行中', type: 'success' },
  paused: { text: '暂停', type: 'warning' },
  completed: { text: '已完成', type: 'info' },
  archived: { text: '已归档', type: 'default' },
}

const riskMap = {
  low: { text: '低风险', type: 'success', progressStatus: 'success' },
  medium: { text: '中风险', type: 'warning', progressStatus: 'warning' },
  high: { text: '高风险', type: 'error', progressStatus: 'error' },
}

const summary = computed(() => ({ ...defaultSummary, ...(dashboard.value.summary || {}) }))
const projectProgress = computed(() => dashboard.value.project_progress || [])
const actionItems = computed(() => dashboard.value.action_items || [])
const recentReports = computed(() => dashboard.value.recent_reports || [])

const statisticData = computed(() => [
  { id: 0, label: '项目总数', value: summary.value.project_total },
  { id: 1, label: '任务总数', value: summary.value.task_total },
  { id: 2, label: '高风险任务', value: summary.value.risk_tasks },
  { id: 3, label: '待审核任务', value: summary.value.review_tasks },
])

const metricCards = computed(() => [
  {
    key: 'active_projects',
    label: '进行中项目',
    value: summary.value.active_projects,
    desc: `共 ${summary.value.project_total} 个可见项目`,
  },
  {
    key: 'active_tasks',
    label: '进行中任务',
    value: summary.value.active_tasks,
    desc: `共 ${summary.value.task_total} 个可见任务`,
  },
  {
    key: 'risk_tasks',
    label: '高风险任务',
    value: summary.value.risk_tasks,
    desc: summary.value.risk_tasks ? '建议优先排查阻塞原因' : '当前无高风险任务',
  },
  {
    key: 'weekly_reports',
    label: '本周汇报',
    value: summary.value.weekly_reports,
    desc: `待审核 ${summary.value.review_tasks} 个，阻塞 ${summary.value.blocked_tasks} 个`,
  },
])

const taskStatusItems = computed(() => {
  const items = dashboard.value.task_status_distribution || []
  const total = Math.max(summary.value.task_total, 0)
  return items
    .filter((item) => item.count > 0)
    .map((item) => {
      const meta = getTaskStatus(item.status)
      return {
        ...item,
        label: meta.text,
        percent: getPercent(item.count, total),
        progressStatus: meta.progressStatus,
      }
    })
})

const riskItems = computed(() => {
  const items = dashboard.value.risk_distribution || []
  const total = Math.max(summary.value.task_total, 0)
  return items.map((item) => {
    const meta = getRisk(item.risk_level)
    return {
      ...item,
      label: meta.text,
      tagType: meta.type,
      percent: getPercent(item.count, total),
      progressStatus: meta.progressStatus,
    }
  })
})

onMounted(() => {
  loadDashboard()
})

async function loadDashboard() {
  loading.value = true
  try {
    const res = await api.getDashboardSummary()
    dashboard.value = res?.data || {}
  } finally {
    loading.value = false
  }
}

function getTaskStatus(value) {
  return taskStatusMap[value] || { text: value || '-', type: 'default', progressStatus: 'default' }
}

function getProjectStatus(value) {
  return projectStatusMap[value] || { text: value || '-', type: 'default' }
}

function getRisk(value) {
  return riskMap[value] || { text: value || '-', type: 'default', progressStatus: 'default' }
}

function getPercent(count, total) {
  if (!total) return 0
  return Math.round((count / total) * 100)
}
</script>

<style scoped>
.workbench-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero-user {
  display: flex;
  align-items: center;
  min-width: 0;
}

.metric-card {
  height: 100%;
  border-radius: 12px;
}

.metric-card__label,
.item-sub,
.action-item__meta,
.report-item__side {
  color: var(--n-text-color-3);
  font-size: 13px;
}

.metric-card__value {
  margin: 8px 0 4px;
  color: var(--n-text-color);
  font-size: 30px;
  font-weight: 700;
}

.metric-card__desc {
  color: var(--n-text-color-2);
  font-size: 13px;
}

.distribution-list,
.risk-list,
.project-list,
.action-list,
.report-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.distribution-item__head,
.project-item__head,
.action-item__head,
.report-item,
.risk-item__main,
.action-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.distribution-item__head,
.risk-item__main {
  margin-bottom: 6px;
}

.project-item,
.action-item,
.report-item {
  padding: 12px;
  background: var(--n-color-embedded);
  border-radius: 10px;
}

.item-title {
  color: var(--n-text-color);
  font-weight: 600;
}

.tag-group {
  display: flex;
  flex-shrink: 0;
  gap: 6px;
}

.action-item__head {
  margin-bottom: 6px;
}

.action-item__meta {
  justify-content: flex-start;
  margin-top: 8px;
}

.report-item__main {
  min-width: 0;
}

.report-content {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: var(--n-text-color-2);
  line-height: 1.6;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.report-item__side {
  flex-shrink: 0;
  align-items: flex-end;
  flex-direction: column;
}

@media (max-width: 900px) {
  .hero-card,
  .report-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-stats {
    width: 100%;
    overflow-x: auto;
  }

  .report-item__side {
    align-items: flex-start;
  }
}
</style>
