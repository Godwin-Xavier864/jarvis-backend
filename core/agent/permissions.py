def get_agent_capabilities(user):
    if user.is_staff:
        return {
            "can_view_all_users": True,
            "can_view_all_tasks": True,
            "can_view_activity": True,
        }
    else:
        return {
            "can_view_own_tasks": True,
            "can_view_notifications": True,
        }
