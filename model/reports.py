from main_app import log
from db.connect import plsql_proc_s, select_one

class Reports():
    def  add(self, name_report, path_report):
        rep = {"name": name_report, "status": 0, "path": path_report}
        if not hasattr(self,'list_reports'):
            list_reports = []
            log.info(f'TYPE: {type(list_reports)}')
            list_reports.append(rep)
            self.list_reports = list_reports
        else:
            self.list_reports.append(rep)
   
    def list(self):
        if hasattr(self,'list_reports'):
            log.info(f'===\nReports. LIST: {self.list_reports}\n===')
            return self.list_reports
        else:
            return None

    def get_status(self, name_report):
        if hasattr(self,'list_reports'):
            for rep in self.list_reports:
                if rep['name'] == name_report:
                    return rep['status']
        return None

    def set_status(self, name_report, status):
        if hasattr(self,'list_reports'):
            for rep in self.list_reports:
                if rep['name'] == name_report:
                    rep['status'] = status

    def remove(self, path):
        if hasattr(self,'list_reports'):
            for rep in self.list_reports:
                if rep['path'] == path:
                    self.list_reports.remove(rep)
                    remove_by_file_name(path)


reps = Reports()


def remove_by_file_name(full_file_path):
    plsql_proc_s('REMOVE BY FILE NAME', 'reports.reps.remove', [full_file_path])
    log.info(f'REMOVE BY FILE NAME')


def get_status(full_file_path):
    stmt = f"select st.status from load_report_status st where st.file_path = '{full_file_path}'"
    log.info(f'GET STATUS. STMT: {stmt}')
    mistake, rec, err_mess = select_one(stmt, [])
    log.info(f'GET STATUS. STMT: {stmt}, rec: {rec}')
    if mistake == 0: 
        return rec[0]
    else:
        log.error(f'ERROR GET STATUS. err_mess: {err_mess}')
        return -100

def check_reps_status():
    if hasattr(reps, 'list_reports'):
        for rep in reps.list():
            status = get_status(rep['path'])
            if status != -100:
                log.info(f'CHECK REPS STATUS. STATUS: {status}')
                rep['status'] = status
        log.info(f'CHECK REPS STATUS. reps.list: {reps.list()}')
