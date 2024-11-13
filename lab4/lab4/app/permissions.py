from rest_framework import permissions
from .redis import session_storage

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
    
class IsAuth(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            session_id = request.COOKIES['session_id']
            if session_id is None:
                return False
            session_storage.get(session_id).decode('utf-8')
        except:
            return False
        return True