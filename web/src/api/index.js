import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  cleanupAuditLogs: (params = {}) => request.delete('/auditlog/cleanup', { params }),
  // projects
  getProjectList: (params = {}) => request.get('/project/list', { params }),
  getProjectById: (params = {}) => request.get('/project/get', { params }),
  createProject: (data = {}) => request.post('/project/create', data),
  updateProject: (data = {}) => request.post('/project/update', data),
  deleteProject: (params = {}) => request.delete('/project/delete', { params }),
  // tasks
  getTaskList: (params = {}) => request.get('/task/list', { params }),
  getMyTaskList: (params = {}) => request.get('/task/my', { params }),
  getTaskById: (params = {}) => request.get('/task/get', { params }),
  createTask: (data = {}) => request.post('/task/create', data),
  batchCreateTask: (data = {}) => request.post('/task/batch_create', data),
  updateTask: (data = {}) => request.post('/task/update', data),
  updateTaskProgress: (data = {}) => request.post('/task/progress', data),
  deleteTask: (params = {}) => request.delete('/task/delete', { params }),
  // reports
  getReportList: (params = {}) => request.get('/report/list', { params }),
  getReportById: (params = {}) => request.get('/report/get', { params }),
  confirmReport: (data = {}) => request.post('/report/confirm', data),
  deleteReport: (params = {}) => request.delete('/report/delete', { params }),
  analyzeReport: (data = {}) => request.post('/ai/report_analyze', data),
  askManagerQuestion: (data = {}) => request.post('/ai/manager_question', data),
  getManagerHistory: (params = {}) => request.get('/ai/manager_history', { params }),
  deleteManagerHistory: (params = {}) => request.delete('/ai/manager_history', { params }),
}
