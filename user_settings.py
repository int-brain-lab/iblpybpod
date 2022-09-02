"""
Sample user_settings.py file
"""
import logging

SETTINGS_PRIORITY = 0
# THESE SETTINGS ARE NEEDED FOR PYSETTINGS
APP_LOG_FILENAME = "app.log"
APP_LOG_HANDLER_CONSOLE_LEVEL = logging.WARNING
APP_LOG_HANDLER_FILE_LEVEL = logging.WARNING

PYBPOD_API_LOG_LEVEL = logging.ERROR

CONTROL_EVENTS_GRAPH_DEFAULT_SCALE = 100
BOARD_LOG_WINDOW_REFRESH_RATE = 1000
SESSIONLOG_PLUGIN_REFRESH_RATE = 500
TIMELINE_PLUGIN_REFRESH_RATE = 500
# timer for thread look for events (seconds)
PYBOARD_COMMUNICATION_THREAD_REFRESH_TIME = 1
# timer for process look for events (seconds)
PYBOARD_COMMUNICATION_PROCESS_REFRESH_TIME = 1
# wait before killing process (seconds)
PYBOARD_COMMUNICATION_PROCESS_TIME_2_LIVE = 0

USE_MULTIPROCESSING = True

PYFORMS_MAINWINDOW_MARGIN = 0
PYFORMS_STYLESHEET = ""
PYFORMS_STYLESHEET_DARWIN = ""
PYFORMS_SILENT_PLUGINS_FINDER = True

PYFORMS_MATPLOTLIB_ENABLED = True
PYFORMS_WEB_ENABLED = True
PYFORMS_GL_ENABLED = True
PYFORMS_VISVIS_ENABLED = False

GENERIC_EDITOR_TITLE = "IBL"
GENERIC_EDITOR_PLUGINS_PATH = "C:\\iblrig_params\\plugins"
GENERIC_EDITOR_PLUGINS_LIST = [
    "pybpodgui_plugin",
    "pybpodgui_plugin_timeline",
    "pybpodgui_plugin_trial_timeline",
    "pybpodgui_plugin_session_history",
    "pybpod_rotaryencoder_module",
    "pybpod_gui_plugin_emulator",
    "pybpod_soundcard_module",
]

PYBPODGUI_API_AUTO_SAVE_PROJECT_ON_RUN = True

TARGET_BPOD_FIRMWARE_VERSION = "22"

DEFAULT_PROJECT_PATH = "C:\\iblrig_params\\IBL"
PYBPOD_EXTRA_INFO = {"Users", "Subjects"}
