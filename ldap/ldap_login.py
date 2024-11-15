from flask import session

from app_config import ldap_admins, ldap_server, ldap_user, ldap_password, ldap_ignore_ou, ldap_boss
from util.ip_addr import ip_addr
from util.logger import log
from ldap.ldap_user_info import connect_ldap

       
class LDAP_User:
    def get_user_by_name(self, src_user):
        ip = ip_addr()
        self.src_user = src_user
        session['admin']=0
        if 'password' in session:
            self.password = session['password']
        if src_user:
            success, user_info = connect_ldap(src_user, self.password)
            log.debug(f'LM. success: {success}, html_user: {src_user}, password: {self.password}, user_info: {user_info}')
            if success > 0:
                login_name=''
                full_name=''
                post=''
                dep_name=''
                ou=''
                if 'principalName' in user_info:
                    login_name = user_info['principalName']
                if 'fio' in user_info:
                    full_name = user_info['fio']
                if 'post' in user_info:
                    post = user_info['post']
                if 'dep_name' in user_info:
                    dep_name = user_info['dep_name']
                if 'ou' in user_info:
                    ou = user_info['ou']
            
                self.username = login_name
                session['username'] = login_name
                self.full_name = full_name
                session['full_name'] = full_name 
                self.post = post
                session['post'] = post
                self.dep_name = dep_name
                session['dep_name'] = dep_name
                self.ou = ou
                session['ou'] = ou
                
                # log.debug(f'ldap_admins: {ldap_admins}')
                
                if session['full_name'] in ldap_admins:
                    session['admin']=1
                
                self.ip_addr = ip
                log.info(f"LM. SUCCESS. USERNAME: {self.username}, ip_addr: {self.ip_addr}\n\tFIO: {self.full_name}\n\tadmin: {session['admin']}")
                return self
        log.info(f"LM. FAIL. USERNAME: {src_user}, ip_addr: {ip}, password: {session['password']}, admin: {session['admin']}")
        return None

    def have_role(self, role_name):
        if hasattr(self, 'username'):
            return role_name in self.roles

    def is_authenticated(self):
        if not hasattr(self, 'username'):
            return False
        else:
            return True

    def is_active(self):
        if hasattr(self, 'username'):
            return True
        else:
            return False

    def is_anonymous(self):
        if not self.username:
            return True
        else:
            return False

    def get_id(self):
        log.debug(f'LDAP_User. GET_ID. self.src_user: {self.src_user}, self.username: {self.username}')
        if hasattr(self, 'src_user'):
            return self.src_user
        else: 
            return None


if __name__ == "__main__":
    #'bind_dn'       => 'cn=ldp,ou=admins,dc=gfss,dc=kz',
    #'bind_pass'     => 'hu89_fart7',    
    connect_ldap('Гусейнов', '123')
