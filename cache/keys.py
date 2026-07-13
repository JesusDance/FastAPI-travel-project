def projects_key(user_id: int) -> str:
    return f"cache_projects:{user_id}"

def project_key(user_id: int, project_id: int) -> str:
    return f"cache_project:{user_id}:{project_id}"

def places_key(user_id: int, project_id: int) -> str:
    return f"cache_places:{user_id}:{project_id}"

def place_key(user_id: int, project_id: int, place_id: int) -> str:
    return f"cache_place:{user_id}:{project_id}:{place_id}"

def project_pattern(user_id: int) -> str:
    return f"cache_project:{user_id}:*"

def place_pattern(user_id: int, project_id: int) -> str:
    return f"cache_place:{user_id}:{project_id}:*"
