from ldap3 import Server, Connection, SUBTREE
from flask import session

from main_app import log
from app_config import ldap_admins, ldap_server, ldap_user, ldap_password, ldap_ignore_ou, ldap_boss


# from db.ldap_login import get_connect, find_value

def find_value(src_string:str, key:str):
    elements = src_string.split(',')
    for element in elements:
        key_field, value = element.split('=')
        if key_field==key:
            return value


def get_connect(username:str, password:str):
    try:
        server = Server(ldap_server)
        log.info(f'CONNECTED to SERVER {ldap_server} SUCCESS')    
        conn = Connection(server, user=username, password=password, auto_bind=True)
        log.info(f'SUCCESS CONNECTED as user: {username}')    
    except:
        log.error(f'MISTAKE connect as user: {username}, password: {password}')    
        return ''
    return conn


def connect_ldap(username:str, password:str):
    status, user_info = ldap_user_info(username)
    
    if status==1:
        principalName = user_info['principalName']
        log.debug(f'NOW CONNECT as {principalName} : {password}')
        conn_usr = get_connect(principalName, password)

        if conn_usr:
            log.debug(f'CONNECT LDAP. SUCCESS. USER_INFO: {user_info}')
            return 1, user_info
        
    log.info(f'---\nUSER NOT FOUND user: {username}\nMISTAKE !!!\n---------------------------')
    return 0,''


def search_user(username:str):
    conn_src = get_connect(ldap_user, ldap_password)

    if not conn_src:
        return 0,'',''
    
    log.debug(f'NOW search username: {username}')
    conn_src.search(search_base='dc=gfss,dc=kz', 
                # search_filter=f'(&(objectclass=person)(cn=*))', 
                search_filter=f'(&(objectclass=person)(| (cn={username}*) (displayname={username}*) (telephoneNumber={username}*) ))', 
                attributes=['distinguishedName', 'userPrincipalName', 'cn', 'sAMAccountName', 'description', 'memberof', 'telephoneNumber', 'employeeNumber', '*'],
                # attributes=['distinguishedName', 'userPrincipalName', 'cn', 'displayName', 'description', 'memberof', 'telephoneNumber'],
                search_scope=SUBTREE,
                paged_size=3)
    users_list = conn_src.entries
    conn_src.unbind()
    # Connection closed
    if len(users_list)>1:
        log.debug(f'SEARCH USER. ERROR. TOO MANY USERS. count: {len(users_list)}, username: {username}')

    for user in users_list:
        dn = user['distinguishedName']
        ou = find_value(str(dn), 'OU')
        if ou not in ldap_ignore_ou:
            principalName = ''
            full_name = ''
            post = ''
            if  'userPrincipalName' in user:
                principalName = str(user['userPrincipalName'])            
            if 'displayName' in user:
                full_name = str(user['displayName'])
            if 'description' in user:
                post = str(user['description'])
            user_info = {"principalName": principalName, "fio": full_name, "post": post}            
            return ou, user_info
    
    return '', {}


def search_dep(ou: str):
    conn_src = get_connect(ldap_user, ldap_password)

    conn_src.search(search_base=f'OU={ou},dc=gfss,dc=kz', 
                search_filter=f'(objectClass=OrganizationalUnit)', 
                # attributes=['name', 'description', '*'],
                attributes=['name', 'description'],
                search_scope=SUBTREE,
                paged_size=3)

    deps_entry = conn_src.entries    
    conn_src.unbind()
        
    for dep in deps_entry:
        dep_name = dep['description']
        if dep_name:
            ou_name = dep['name']
            dep_one = { 'ou_name': str(ou_name), 'dep_name': str(dep_name)}
            return dep_one
    return {}
    
    
def ldap_user_info(username:str):
    if not username:
        log.info(f'\n---\nLDAP_USER_INFO\n\tEMPTY USER_NAME!!!\n---')
    if username:
        log.debug(f'\n---\nLDAP_USER_INFO\n\tNOW SEARCH_USER: {username}\n---')
        ou, user_info = search_user(username)
        log.debug(f'\n---\nLDAP_USER_INFO\n\tFOUND USERS: {len(user_info)}\n\t{user_info}\n---')
        dep=''
        if user_info:
            dep = search_dep(ou)
            if dep:
                user_info['ou_name']=dep['ou_name']
                user_info['dep_name']=dep['dep_name']
                log.debug(f'\n---\nLDAP_USER_INFO. {user_info}, DEPS: {dep}\n---')
                return 1, user_info
            
        log.info(f'ERROR. LDAP_USER_INFO. ou: {ou}, user: {user_info}, dep: {dep}')
    return 0,''
