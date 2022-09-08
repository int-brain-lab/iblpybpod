import loggingbootstrap
import logging
import traceback
import sys
import os
from pathlib import Path

# IMPORTANT: used to import the user_settings.py file
sys.path.insert(0, os.getcwd())

try:
    from confapp import conf

    # Initiating logging for pyforms. It has to be initiated manually here because we don't know yet
    # the logger filename as specified on settings
    loggingbootstrap.create_double_logger("pyforms", logging.INFO, 'app.log', logging.INFO)

except ImportError as err:
    logging.getLogger().critical(str(err), exc_info=True)
    exit("Could not load pyforms! Is it installed?")

try:
    # pyforms is imported here first time through pyforms
    try:
        import user_settings
    except ModuleNotFoundError:
        home = str(Path.home())
        home_settings_file = os.path.join(home, 'user_settings.py')

        if not os.path.isfile(home_settings_file):
            with open(home_settings_file, 'w') as out:
                out.write("SETTINGS_PRIORITY = 0\n\n")
                out.write("GENERIC_EDITOR_PLUGINS_LIST = ['pybpodgui_plugin']")

        sys.path.insert(0, home)
        import user_settings

    conf += user_settings

    from pyforms_generic_editor import settings

    loggingbootstrap.create_double_logger(
        "pyforms_generic_editor",
        conf.APP_LOG_HANDLER_CONSOLE_LEVEL,
        conf.APP_LOG_FILENAME,
        conf.APP_LOG_HANDLER_FILE_LEVEL
    )

    loggingbootstrap.create_double_logger(
        "pyforms",
        conf.APP_LOG_HANDLER_CONSOLE_LEVEL,
        conf.APP_LOG_FILENAME,
        conf.APP_LOG_HANDLER_FILE_LEVEL
    )

    # pyforms.controls is imported here first time
    from pyforms_generic_editor.editor.base_editor import BaseEditor as Editor

except Exception as err:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logging.getLogger("pyforms_generic_editor").critical(str(err), exc_info=True)
    conf.GENERIC_EDITOR_LOAD_EXCEPTION_TRACEBACK = traceback.format_exc()
    conf.GENERIC_EDITOR_LOAD_EXCEPTION_LINE = exc_traceback.tb_lineno
    settings.GENERIC_EDITOR_TITLE = 'PLEASE EDIT USER SETTINGS AND RESTART APP'

    from pyforms_generic_editor.editor.safe_mode_editor import SafeModeEditor as Editor


def start():
    import logging.config
    current_dir = Path(__file__).parent
    src_dir = current_dir.parent
    logging_yml_loc = src_dir / "logger.yml"
    logging.config.dictConfig(logging_yml_loc)
    logger = logging.getLogger("iblpybpod")

    # 'application' code
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')

    import pyforms
    pyforms.start_app(Editor, conf.GENERIC_EDITOR_WINDOW_GEOMETRY)


if __name__ == '__main__':
    start()
