from models import (
    DBSession,
    User,
    UserGroup,
    Group,
    )
    
# It is used by RootFactory
def group_finder(login, request):
    u = User.get_by_identity(login)
    if not u or not u.status:
        return # None means logout
    if u.id == 1:
        return ['Admin']
    r = []        
    for group_id in UserGroup.get_by_user(u):
        group = DBSession.query(Group).get(group_id)
        r.append('g:%s' % group.group_name)
    return r
        
def get_user(request):
    user_id = request.authenticated_userid
    if user_id:
        return User.get_by_identity(user_id)
