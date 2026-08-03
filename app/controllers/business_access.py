from app.models.admin import User


BUSINESS_MANAGER_API_RULES = {
    ("POST", "/api/v1/project/create"),
    ("POST", "/api/v1/task/create"),
    ("POST", "/api/v1/task/update"),
    ("DELETE", "/api/v1/task/delete"),
}


async def is_business_manager(user: User) -> bool:
    if user.is_superuser:
        return True
    roles = await user.roles.all()
    for role in roles:
        apis = await role.apis.all()
        for api in apis:
            if (str(api.method), api.path) in BUSINESS_MANAGER_API_RULES:
                return True
    return False
