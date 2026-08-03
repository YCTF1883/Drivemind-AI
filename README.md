# DriveMind AI

面向企业研发团队的 AI 智能研发运营管理平台。

DriveMind AI 基于 FastAPI、Vue 3、Naive UI、MySQL、LangGraph 和 DeepSeek API 构建，聚焦“项目管理 + 任务协作 + 工作汇报 + AI 辅助决策”的完整业务闭环，适合用于 AI 应用工程师 / 大模型应用开发方向的项目展示与面试讲解。

## 项目定位

传统项目管理系统往往只记录任务状态，员工遇到阻塞时仍需要线下沟通，管理者也难以及时看到项目真实风险。DriveMind AI 的目标是把研发团队中的任务派发、进展沟通、问题暴露和管理问答统一到一个系统内：

```text
项目经理创建项目
↓
AI 拆解任务
↓
项目经理派发任务给员工
↓
员工查看自己的任务
↓
员工提交自然语言进展 / 问题 / 支持诉求
↓
AI 结构化分析工作汇报
↓
任务和项目进度更新
↓
管理者通过 AI 问答查看项目状态
```

核心原则：

```text
完整业务闭环 > 面试可讲清 > 工程结构规范 > 高级功能堆叠
```

## 已实现功能

### 1. 项目管理

- 创建、编辑、归档研发项目。
- 支持项目状态、风险等级、开始/结束日期、项目经理、创建人等字段。
- 项目软删除后，历史编码不再阻塞新项目创建。
- 项目归档时自动归档项目下任务，避免任务列表继续显示已删除项目的任务。

### 2. 任务管理

- 项目经理可为项目创建任务，并选择具体执行员工。
- 员工登录后默认查看自己的任务。
- 支持任务状态：未开始、进行中、阻塞、审核中、已完成、已归档。
- 员工不能直接完成任务，只能提交进展或提交审核；经理确认后任务才进入已完成。
- 任务列表展示最新工作汇报、阻塞标签、需支持标签、高风险标签和待审核标签。

### 3. 工作汇报与异步协作

- 员工可在任务下提交自然语言汇报。
- 汇报内容支持：完成事项、遇到的问题、风险等级、所需支持、建议动作、进度变化。
- 经理和管理员可查看项目、任务、提交人、负责人、汇报详情等业务化信息。
- 工作汇报支持关键词搜索，能按项目、任务、提交人、汇报内容检索。
- 汇报记录可删除，避免测试数据长期堆积。

### 4. AI 辅助能力

- 基于 DeepSeek API 的 OpenAI-compatible 接口调用。
- 使用 LangGraph 做最小化 AI 编排。
- 支持 AI 任务拆解：根据项目目标生成任务建议。
- 支持 AI 汇报分析：把员工自然语言汇报结构化为完成事项、问题、风险、支持诉求和建议。
- 支持管理问答：管理者用自然语言查询项目状态、风险和任务进展。
- AI 只生成建议，不直接越权写数据库；关键数据仍由用户确认后落库。
- DeepSeek Key 未配置时，系统保留本地规则 fallback，保证演示稳定。

### 5. 权限与系统基础能力

- JWT 登录认证。
- RBAC 角色权限。
- 动态菜单。
- API 级权限控制。
- 审计日志中间件。
- MySQL 持久化。
- 前后端分离部署结构。

## 技术栈

### 后端

- Python 3.11
- FastAPI
- Uvicorn
- Tortoise ORM
- MySQL / asyncmy
- Pydantic v2
- pydantic-settings
- LangGraph
- httpx
- DeepSeek API

### 前端

- Vue 3
- Vite
- Naive UI
- Pinia
- Vue Router
- Axios
- UnoCSS

## 本地启动

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd drivemind-ai
```

### 2. 后端环境

建议使用 Python 3.11。

```bash
pip install -r requirements.txt
```

或使用项目中的 `pyproject.toml` / `uv.lock` 管理依赖。

### 3. 配置环境变量

复制示例文件：

```bash
cp .env.example .env
```

按本机环境填写 `.env`。不要把 `.env` 提交到 GitHub。

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=drivemind

DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=2048
DEEPSEEK_TIMEOUT=30
```

### 4. 启动后端

```bash
python run.py
```

后端默认地址：

```text
http://localhost:9999
```

API 文档：

```text
http://localhost:9999/docs
```

### 5. 启动前端

```bash
cd web
npm install
npm run dev
```

前端默认地址以 Vite 输出为准。

## 默认账号

开发初始化会创建默认超级管理员：

```text
username: admin
password: 123456
```

该账号只用于本地开发和演示。部署到公开环境前请务必修改默认密码，并妥善配置数据库密码和 API Key。

## 项目目录

```text
├── app                    # FastAPI 后端应用
│   ├── ai                 # AI 工作流与 DeepSeek 调用
│   ├── api                # API 路由
│   ├── controllers        # 业务控制器
│   ├── core               # 中间件、异常、CRUD 基类等核心能力
│   ├── models             # 数据模型
│   ├── schemas            # Pydantic Schema
│   └── settings           # 配置管理
├── deploy                 # 部署配置
├── web                    # Vue 3 前端应用
│   ├── public             # 公共资源
│   └── src                # 前端源码
└── PROJECT_CONTEXT.md     # 项目定位与阶段目标
```

## 面试讲解重点

可以围绕以下主线讲解：

1. 为什么不是单纯后台 CRUD，而是围绕研发管理闭环设计业务模型。
2. 如何把“员工进展汇报”抽象成结构化 `WorkReport`，解决远程协作中的信息不透明问题。
3. 为什么 AI 只做结构化建议，不直接自动写库，降低不可控风险。
4. 如何用 RBAC、动态菜单、对象级数据权限区分管理员、项目经理和员工视角。
5. SQLite 切换到 MySQL、环境变量配置、审计日志、软删除唯一性等工程化问题如何处理。

## License 与来源说明

本项目基于 [vue-fastapi-admin](https://github.com/mizhexiaoxiao/vue-fastapi-admin)（MIT License）进行二次开发，并保留原项目许可证要求的版权和许可声明。

DriveMind AI 的研发运营业务模块、AI 工作流、DeepSeek 集成、项目/任务/工作汇报闭环以及相关前端页面为本项目新增或重构内容。

本项目继续采用 MIT License，详见 [LICENSE](LICENSE)。
