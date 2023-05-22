from typing import List, Any
import os.path
import app_config as cfg
from util.logger import log


class I18N:
    file_names: List[Any] = []
    files: List[Any] = []
    objects: List[Any] = []

    def get_resource(self, lang, resource_name):
        file_object = ''
        return_value = ''
        file_name = f'{cfg.BASE}/i18n.{lang}'
        if cfg.os == 'unix':
            file_name = f'{cfg.BASE}/i18nu.{lang}'
        n_objects = 0
        # if cfg.debug:
        #     log.debug(f"I18N. Lang: {lang}, resource_name: {resource_name}, file_name: {file_name}")

        for f_name in self.file_names:
            if f_name == file_name:
                file_object = self.objects[n_objects]
                break
            n_objects = n_objects + 1

        if file_object == '' and os.path.exists(file_name):
            # log.debug(f"---------->  I18N. FILE EXIST : {file_name}")
            file = open(file_name, "r")
            if file is not None:
                self.file_names.append(file_name)
                self.files.append(file)
                file_object = file.read()
                self.objects.append(file_object)

        if file_object != '':
            for line in file_object.splitlines():
                if resource_name in line:
                    return_value = line.split('=', 1)[1]
                    break
        if return_value == '':
            return_value = resource_name
        return return_value

    def close(self):
        if cfg.debug:
            log.debug("I18N. CLOSE")
        for file in self.files:
            file.close()
        self.file_names.clear()
        self.files.clear()
        self.objects.clear()


i18n = I18N()
