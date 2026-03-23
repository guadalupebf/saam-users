from rest_framework import permissions


class OnlySuperUserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if user and (user.is_staff or user.is_superuser):
            return True
        elif request.GET.get('org', 0):
            return True
        else:
            return False



class IsOrgMember(permissions.BasePermission):
    def has_permission(self, request, view):
        org_request = int(request.GET.get('org', 0))
        if request.user.is_superuser:
            return True
        org_usuario = request.user.userinfo.org.id
        if org_usuario != org_request:
            return False
        else:
            return True 

class IsOrgMemberChar(permissions.BasePermission):
    def has_permission(self, request, view):
        org_request = request.GET.get('org', '')
        if request.user.is_superuser:
            return True
        org_usuario = request.user.userinfo.org.urlname
        if org_usuario != org_request:
            return False
        else:
            return True 