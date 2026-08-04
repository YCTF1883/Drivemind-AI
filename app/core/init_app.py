from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise, connections
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.ai_context import ai_context_controller
from app.controllers.api import api_controller
from app.controllers.auditlog import audit_log_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)


async def init_business_menus():
    parent_menu = await Menu.filter(path="/business", parent_id=0).first()
    if not parent_menu:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="研发运营",
            path="/business",
            order=2,
            parent_id=0,
            icon="carbon:development",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/business/project",
        )

    business_menus = [
        {
            "name": "项目管理",
            "path": "project",
            "order": 1,
            "icon": "material-symbols:folder-managed-outline",
            "component": "/business/project",
        },
        {
            "name": "任务管理",
            "path": "task",
            "order": 2,
            "icon": "carbon:task",
            "component": "/business/task",
        },
        {
            "name": "工作汇报",
            "path": "report",
            "order": 3,
            "icon": "carbon:report",
            "component": "/business/report",
        },
        {
            "name": "管理问答",
            "path": "manager",
            "order": 4,
            "icon": "carbon:chat-bot",
            "component": "/ai/manager",
        },
    ]
    for item in business_menus:
        menu = await Menu.filter(parent_id=parent_menu.id, path=item["path"]).first()
        if menu:
            await menu.update_from_dict(item).save()
        else:
            await Menu.create(
                menu_type=MenuType.MENU,
                parent_id=parent_menu.id,
                is_hidden=False,
                keepalive=False,
                **item,
            )


async def init_apis():
    await api_controller.refresh_api()


async def init_db():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    await patch_business_schema()


async def patch_business_schema():
    connection = connections.get("mysql")
    columns = await connection.execute_query_dict("SHOW COLUMNS FROM `task` LIKE 'workload'")
    if not columns:
        await connection.execute_script("ALTER TABLE `task` ADD COLUMN `workload` VARCHAR(20) NOT NULL DEFAULT 'normal'")
        logger.info("Business schema patched: added task.workload")


async def _add_missing_menus(role: Role, menus: list[Menu]):
    existing_menus = await role.menus
    existing_ids = {menu.id for menu in existing_menus}
    missing_menus = [menu for menu in menus if menu.id not in existing_ids]
    if missing_menus:
        await role.menus.add(*missing_menus)


async def _add_missing_apis(role: Role, apis: list[Api]):
    existing_apis = await role.apis
    existing_ids = {api.id for api in existing_apis}
    missing_apis = [api for api in apis if api.id not in existing_ids]
    if missing_apis:
        await role.apis.add(*missing_apis)


async def init_business_roles():
    business_parent = await Menu.filter(path="/business", parent_id=0).first()
    business_menus = await Menu.filter(Q(id=business_parent.id) | Q(parent_id=business_parent.id)) if business_parent else []
    manager_menu_names = ["研发运营", "项目管理", "任务管理", "工作汇报", "管理问答"]
    employee_menu_names = ["研发运营", "任务管理", "工作汇报"]
    manager_menus = [menu for menu in business_menus if menu.name in manager_menu_names]
    employee_menus = [menu for menu in business_menus if menu.name in employee_menu_names]

    business_apis = await Api.filter(
        Q(path__startswith="/api/v1/project")
        | Q(path__startswith="/api/v1/task")
        | Q(path__startswith="/api/v1/report")
        | Q(path__startswith="/api/v1/ai")
        | Q(path__startswith="/api/v1/dashboard")
    )
    user_list_api = await Api.filter(method="GET", path="/api/v1/user/list")
    manager_apis = list(business_apis) + list(user_list_api)
    employee_api_rules = [
        ("GET", "/api/v1/dashboard/summary"),
        ("GET", "/api/v1/task/list"),
        ("GET", "/api/v1/task/my"),
        ("GET", "/api/v1/task/get"),
        ("POST", "/api/v1/task/progress"),
        ("GET", "/api/v1/report/list"),
        ("GET", "/api/v1/report/get"),
        ("POST", "/api/v1/report/confirm"),
        ("DELETE", "/api/v1/report/delete"),
        ("POST", "/api/v1/ai/report_analyze"),
    ]
    employee_apis = [api for api in business_apis if (api.method, api.path) in employee_api_rules]

    manager_role, _ = await Role.get_or_create(name="项目经理", defaults={"desc": "研发项目管理角色"})
    employee_role, _ = await Role.get_or_create(name="员工", defaults={"desc": "研发任务执行角色"})
    await _add_missing_menus(manager_role, manager_menus)
    await _add_missing_apis(manager_role, manager_apis)
    await _add_missing_menus(employee_role, employee_menus)
    await _add_missing_apis(employee_role, employee_apis)

    admin_role = await Role.filter(name="管理员").first()
    if admin_role:
        all_menus = await Menu.all()
        all_apis = await Api.all()
        await _add_missing_menus(admin_role, all_menus)
        await _add_missing_apis(admin_role, all_apis)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_audit_log_retention():
    deleted_count, before_time = await audit_log_controller.cleanup_expired(settings.AUDIT_LOG_RETENTION_DAYS)
    if deleted_count:
        logger.info(
            "Audit log retention cleaned {} records before {}",
            deleted_count,
            before_time.strftime(settings.DATETIME_FORMAT),
        )


async def init_ai_context_retention():
    deleted_count, before_time = await ai_context_controller.cleanup_expired(settings.AI_CONTEXT_RETENTION_DAYS)
    if deleted_count:
        logger.info(
            "AI context retention cleaned {} records before {}",
            deleted_count,
            before_time.strftime(settings.DATETIME_FORMAT),
        )


async def init_data():
    await init_db()
    await init_audit_log_retention()
    await init_ai_context_retention()
    await init_superuser()
    await init_menus()
    await init_business_menus()
    await init_apis()
    await init_roles()
    await init_business_roles()
