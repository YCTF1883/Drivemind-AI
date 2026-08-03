<script setup>
import { onMounted, ref } from 'vue'
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NInput,
  NPagination,
  NPopconfirm,
  NProgress,
  NSpin,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import api from '@/api'

defineOptions({ name: '管理问答' })

const question = ref('')
const asking = ref(false)
const historyLoading = ref(false)
const currentAnswer = ref(null)
const historyList = ref([])
const pagination = ref({ page: 1, pageSize: 6, total: 0 })
const sessionId = 'manager-default'

const quickQuestions = [
  '当前有哪些高风险任务？',
  '哪些任务等待我审核？',
  '哪些员工遇到了阻塞？',
  '项目整体进度怎么样？',
]

const evidenceTypeMap = {
  project: { text: '项目', type: 'info' },
  task: { text: '任务', type: 'warning' },
  report: { text: '汇报', type: 'success' },
}

const statusMap = {
  active: { text: '进行中', type: 'info' },
  paused: { text: '已暂停', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  archived: { text: '已归档', type: 'default' },
  not_started: { text: '未开始', type: 'default' },
  in_progress: { text: '进行中', type: 'info' },
  blocked: { text: '阻塞', type: 'error' },
  in_review: { text: '审核中', type: 'warning' },
}

const riskMap = {
  low: { text: '低风险', type: 'success' },
  medium: { text: '中风险', type: 'warning' },
  high: { text: '高风险', type: 'error' },
}

onMounted(() => {
  loadHistory()
})

function getEvidenceType(type) {
  return evidenceTypeMap[type] || { text: type || '证据', type: 'default' }
}

function getStatus(value) {
  return statusMap[value] || { text: value || '-', type: 'default' }
}

function getRisk(value) {
  return riskMap[value] || { text: value || '-', type: 'default' }
}

function formatList(value) {
  if (!value?.length) return '-'
  return Array.isArray(value) ? value.join('；') : value
}

function getEvidenceTitle(item) {
  const data = item.data || {}
  if (item.type === 'project') return data.name || '未命名项目'
  if (item.type === 'task') return data.title || '未命名任务'
  if (item.type === 'report') return data.task_title || data.raw_content?.slice(0, 20) || '工作汇报'
  return data.name || data.title || '业务证据'
}

function getEvidenceDesc(item) {
  const data = item.data || {}
  if (item.type === 'project') return data.code ? `编码：${data.code}` : '项目状态证据'
  if (item.type === 'task')
    return data.project_name ? `所属项目：${data.project_name}` : '任务状态证据'
  if (item.type === 'report')
    return data.reporter_name ? `提交人：${data.reporter_name}` : '员工汇报证据'
  return ''
}

function pickHistory(item) {
  currentAnswer.value = {
    id: item.id,
    question: item.question,
    answer: item.answer,
    evidences: item.evidences || [],
    created_at: item.created_at,
  }
}

async function loadHistory(page = pagination.value.page) {
  historyLoading.value = true
  try {
    const res = await api.getManagerHistory({ page, page_size: pagination.value.pageSize })
    historyList.value = res?.data || []
    pagination.value.page = res?.page || page
    pagination.value.total = res?.total || 0
  } finally {
    historyLoading.value = false
  }
}

async function handleDeleteHistory(item) {
  await api.deleteManagerHistory({ id: item.id })
  $message.success('历史问答已删除')
  if (currentAnswer.value?.id === item.id) {
    currentAnswer.value = null
  }
  await loadHistory(
    historyList.value.length === 1 && pagination.value.page > 1
      ? pagination.value.page - 1
      : pagination.value.page
  )
}

async function submitQuestion(content = question.value) {
  const text = content.trim()
  if (!text) {
    $message.warning('请输入要询问的项目管理问题')
    return
  }

  asking.value = true
  try {
    const res = await api.askManagerQuestion({ question: text, session_id: sessionId })
    currentAnswer.value = {
      question: text,
      ...(res?.data || {}),
    }
    question.value = ''
    await loadHistory(1)
  } finally {
    asking.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="管理问答">
    <div class="manager-page">
      <NAlert type="info" show-icon class="manager-intro">
        管理问答用于项目经理通过自然语言查看项目状态、任务风险、员工阻塞和待审核事项。AI
        回答只基于系统内项目、任务和工作汇报数据，并在下方展示引用证据。
      </NAlert>

      <div class="manager-layout">
        <div class="manager-main">
          <NCard title="向 DriveMind AI 提问" :bordered="false" class="manager-card">
            <div class="quick-questions">
              <NButton
                v-for="item in quickQuestions"
                :key="item"
                size="small"
                secondary
                type="primary"
                :disabled="asking"
                @click="submitQuestion(item)"
              >
                {{ item }}
              </NButton>
            </div>

            <NInput
              v-model:value="question"
              type="textarea"
              :autosize="{ minRows: 4, maxRows: 8 }"
              placeholder="例如：当前哪些任务存在阻塞？本周有哪些事项需要我优先处理？"
              @keydown.ctrl.enter.prevent="submitQuestion()"
            />

            <div class="ask-actions">
              <span class="ask-tip">Ctrl + Enter 快速发送</span>
              <NButton type="primary" :loading="asking" @click="submitQuestion()">发送问题</NButton>
            </div>
          </NCard>

          <NCard v-if="currentAnswer" :bordered="false" class="manager-card answer-card">
            <template #header>
              <div class="answer-header">
                <span>AI 回答</span>
                <NTag v-if="currentAnswer.created_at" size="small" round>
                  {{ currentAnswer.created_at }}
                </NTag>
              </div>
            </template>

            <div class="question-box">{{ currentAnswer.question }}</div>
            <div class="answer-text">{{ currentAnswer.answer }}</div>

            <div class="evidence-title">引用证据</div>
            <div v-if="currentAnswer.evidences?.length" class="evidence-grid">
              <div
                v-for="(item, index) in currentAnswer.evidences"
                :key="index"
                class="evidence-item"
              >
                <div class="evidence-head">
                  <NTag :type="getEvidenceType(item.type).type" size="small">
                    {{ getEvidenceType(item.type).text }}
                  </NTag>
                  <div class="evidence-name">
                    <div class="evidence-name__primary">{{ getEvidenceTitle(item) }}</div>
                    <div class="evidence-name__secondary">{{ getEvidenceDesc(item) }}</div>
                  </div>
                </div>

                <template v-if="item.type === 'project'">
                  <div class="evidence-row">
                    <span>状态</span>
                    <NTag :type="getStatus(item.data?.status).type" size="small">
                      {{ getStatus(item.data?.status).text }}
                    </NTag>
                  </div>
                  <div class="evidence-row">
                    <span>风险</span>
                    <NTag :type="getRisk(item.data?.risk_level).type" size="small">
                      {{ getRisk(item.data?.risk_level).text }}
                    </NTag>
                  </div>
                  <NProgress
                    type="line"
                    :percentage="item.data?.progress || 0"
                    indicator-placement="inside"
                  />
                </template>

                <template v-else-if="item.type === 'task'">
                  <div class="evidence-row">
                    <span>负责人</span>
                    <strong>{{ item.data?.assignee_name || '未分配' }}</strong>
                  </div>
                  <div class="evidence-row">
                    <span>状态</span>
                    <NTag :type="getStatus(item.data?.status).type" size="small">
                      {{ getStatus(item.data?.status).text }}
                    </NTag>
                  </div>
                  <div class="evidence-row">
                    <span>风险</span>
                    <NTag :type="getRisk(item.data?.risk_level).type" size="small">
                      {{ getRisk(item.data?.risk_level).text }}
                    </NTag>
                  </div>
                  <NProgress
                    type="line"
                    :percentage="item.data?.progress || 0"
                    indicator-placement="inside"
                  />
                </template>

                <template v-else-if="item.type === 'report'">
                  <div class="report-content">{{ item.data?.raw_content || '-' }}</div>
                  <div class="evidence-row">
                    <span>问题</span>
                    <strong>{{ formatList(item.data?.problems) }}</strong>
                  </div>
                  <div class="evidence-row">
                    <span>所需支持</span>
                    <strong>{{ formatList(item.data?.support_needed) }}</strong>
                  </div>
                  <div class="evidence-row">
                    <span>风险</span>
                    <NTag :type="getRisk(item.data?.risk_level).type" size="small">
                      {{ getRisk(item.data?.risk_level).text }}
                    </NTag>
                  </div>
                </template>
              </div>
            </div>
            <NEmpty v-else description="本次回答没有返回引用证据" />
          </NCard>

          <NEmpty
            v-else
            class="empty-answer"
            description="输入问题后，这里会显示 AI 回答和引用证据"
          />
        </div>

        <NCard title="历史问答" :bordered="false" class="manager-history">
          <NSpin :show="historyLoading">
            <NEmpty v-if="!historyList.length" description="暂无历史问答" />
            <div v-else class="history-list">
              <div
                v-for="item in historyList"
                :key="item.id"
                class="history-item"
                role="button"
                tabindex="0"
                @click="pickHistory(item)"
                @keydown.enter="pickHistory(item)"
              >
                <div class="history-item__header">
                  <div class="history-question">{{ item.question }}</div>
                  <NPopconfirm @positive-click="handleDeleteHistory(item)">
                    <template #trigger>
                      <NButton
                        size="tiny"
                        quaternary
                        type="error"
                        class="history-delete"
                        @click.stop
                      >
                        删除
                      </NButton>
                    </template>
                    确认删除这条历史问答吗？
                  </NPopconfirm>
                </div>
                <div class="history-answer">{{ item.answer }}</div>
                <div class="history-time">{{ item.created_at }}</div>
              </div>
            </div>
          </NSpin>

          <NPagination
            v-if="pagination.total > pagination.pageSize"
            v-model:page="pagination.page"
            class="history-pagination"
            :page-size="pagination.pageSize"
            :item-count="pagination.total"
            simple
            @update:page="loadHistory"
          />
        </NCard>
      </div>
    </div>
  </CommonPage>
</template>

<style scoped>
.manager-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.manager-intro {
  border-radius: 10px;
}

.manager-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
}

.manager-main {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 16px;
}

.manager-card,
.manager-history {
  border-radius: 12px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.ask-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
}

.ask-tip,
.evidence-name__secondary,
.history-answer,
.history-time {
  color: var(--n-text-color-3);
  font-size: 12px;
}

.answer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.question-box {
  padding: 12px 14px;
  margin-bottom: 14px;
  color: var(--n-text-color);
  background: var(--n-color-embedded);
  border-radius: 10px;
}

.answer-text {
  margin-bottom: 18px;
  color: var(--n-text-color);
  line-height: 1.8;
  white-space: pre-wrap;
}

.evidence-title {
  margin-bottom: 12px;
  font-weight: 600;
}

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.evidence-item {
  padding: 14px;
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 10px;
}

.evidence-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.evidence-name {
  min-width: 0;
}

.evidence-name__primary {
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: var(--n-text-color-2);
}

.evidence-row strong {
  color: var(--n-text-color);
  font-weight: 500;
  text-align: right;
}

.report-content {
  display: -webkit-box;
  margin-bottom: 10px;
  overflow: hidden;
  color: var(--n-text-color);
  line-height: 1.6;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.empty-answer {
  padding: 48px 0;
  background: var(--card-color);
  border-radius: 12px;
}

.manager-history {
  align-self: flex-start;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  width: 100%;
  padding: 12px;
  text-align: left;
  cursor: pointer;
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 10px;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: var(--primary-color);
}

.history-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.history-delete {
  flex-shrink: 0;
}

.history-question {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: var(--n-text-color);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-answer {
  display: -webkit-box;
  margin-bottom: 8px;
  overflow: hidden;
  line-height: 1.5;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.history-time {
  text-align: right;
}

.history-pagination {
  justify-content: flex-end;
  margin-top: 14px;
}

@media (max-width: 1200px) {
  .manager-layout {
    grid-template-columns: 1fr;
  }

  .manager-history {
    width: 100%;
  }
}
</style>
