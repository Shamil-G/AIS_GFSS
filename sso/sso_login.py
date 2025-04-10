from ldap3 import Server, Connection, SUBTREE
from flask import session
from util.ip_addr import ip_addr
from util.logger import log
from app_config import ldap_admins, permit_deps

     
class SSO_User:
    def get_user_by_name(self, src_user):
        ip = ip_addr()
        self.src_user = src_user
        self.post=''
        self.dep_name=''

        if 'password' in session:
            self.password = session['password']
        if src_user and 'login_name' in src_user:
            log.info(f'SSO_USER. src_user: {src_user}')

            principalName = src_user['principalName']
            self.principal_name = principalName

            full_name = src_user['fio']
            self.full_name = full_name
            
            login_name = src_user['login_name']
            self.username = login_name
            session['username'] = login_name

            if 'post' in src_user:
                self.post = src_user['post']
                session['post']=self.post

            if 'dep_name' in src_user:
                self.depname = src_user['dep_name']
                session['depname']=self.depname

            if src_user['fio'] in ldap_admins:
                log.info(f'----------------\n\tUSER {session['username']} are Admin\n----------------')
                self.roles='admin'
            else:
                self.roles='operator'
            session['roles'] = self.roles
            
            if src_user['dep_name'] not in permit_deps:
                log.info(f'----------------\n\tUSER {self.full_name} not Registred\n----------------')
                return None

            if 'roles' in src_user:
                self.roles = src_user['roles']
                session['roles']=self.roles
                
            self.full_name = full_name
            session['full_name'] = full_name 

            self.ip_addr = ip
            log.info(f"LM SSO. SUCCESS. USERNAME: {self.username}, ip_addr: {self.ip_addr}\n\tFIO: {self.full_name}, roles: {self.roles} ")
            return self
        log.info(f"LM SSO. F`AIL. USERNAME: {src_user}, ip_addr: {ip}, password: {session['password']}")
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
    #connect_ldap('Гусейнов', '123')
    log.debug(f'__main__ function')
