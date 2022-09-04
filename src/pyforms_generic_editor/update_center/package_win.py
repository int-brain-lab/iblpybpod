import subprocess
import sys
import xmlrpc.client
from importlib import reload

import pkg_resources

from pyforms_gui.basewidget import BaseWidget
from pyforms_gui.controls.control_button import ControlButton
from pyforms_gui.controls.control_combo import ControlCombo
from pyforms_gui.controls.control_label import ControlLabel
from pyforms_gui.controls.control_textarea import ControlTextArea


class PackageWindow(BaseWidget):

    pypi = xmlrpc.client.ServerProxy('https://pypi.org')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        local = self.get_current_distribution(self.title)
        new_version, all_versions, description = self.get_pypi_distribution(self.title)
        
        current_version = local.version if local is not None else None

        nlines = len(description.split('\n'))

        self.set_margin(10)
        self.setMinimumHeight(160 if nlines<3 else nlines*20)

        self._version = ControlLabel(
            'Installed version {0}'.format(current_version) if new_version!=current_version else 'Latest installed', 
            visible=current_version is not None, 
            style='font-size:11pt;max-width:200px;min-height:30px;'+ ('color:blue;' if new_version==current_version else 'color:#FF7F50')
        )
        
        self._versions = ControlCombo(
            'Version', 
            items=[ [v] for v in all_versions],
            style='max-width:200px;min-height:30px;'
        )
        
        self._label = ControlLabel(
            self.title, 
            style='font-weight: bold;min-height:30px;font-size:13pt;vertical-align: middle;min-width:200px;'
        )
        
        self._install_btn  = ControlButton(
            'Update' if current_version else 'Install', 
            style='max-width:100px;min-height:30px;'+ ('color:auto;' if current_version is None or new_version==current_version else 'color:#FF7F50'),
            default=self.__install_btn_evt
        )

        self._description  = ControlTextArea(
            default=description, 
            readonly=True, 
            style='background-color: #333; color:white; margin-bottom: 20px;'
        )
        
        self.formset = [
            ('_label','_version',' ','_versions','_install_btn'),
            '_description'
        ]

        """
        if new_version is not False and current_version is False:
            self._install_btn.label = 'Install version {0}'.format(new_version)
        elif new_version is not False and current_version is not False:
            self._install_btn.label = 'Update from {0} to {1}'.format(current_version, new_version)
        else:
            self._install_btn.enabled = False
            self._install_btn.label = 'No updates available'
        """

    def get_current_distribution(self, name):
        try:
            mod = sys.modules.get(name, None)
            if mod: 
                reload(mod)
            dist = pkg_resources.get_distribution(name)
        except pkg_resources.DistributionNotFound:
            dist = None
        return dist


    def get_pypi_distribution(self, name):

        new_version = self.pypi.package_releases(name)
        if not new_version:
            new_version = self.pypi.package_releases(name.capitalize())

        if new_version is None: return new_version

        new_version  = new_version[0]
        all_versions = self.pypi.package_releases(name, True)
        data = self.pypi.release_data(name, new_version)


        return new_version, all_versions, data.get('summary', '')


    def __install_btn_evt(self):
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', self.title+'=='+self._versions.value])
        self.parent_widget.load_packages_list()
