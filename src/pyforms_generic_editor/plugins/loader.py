import logging
import os
import importlib
import sys
from pathlib import Path
from confapp import conf

logger = logging.getLogger(__name__)


def install_plugins(main_window):
    """ Load plugins from plugins folder. These plugins should inherit from BaseWidget """
    logger.info("------------- LOADING PLUGINS FOR IBLPYBPOD -------------")
    plugins_list = conf.GENERIC_EDITOR_PLUGINS_LIST

    plugin_locations = []
    src_dir = Path(__file__).parent.parent.parent
    for plugin in plugins_list:
        plugin_path = src_dir / plugin
        plugin_locations.append(plugin_path)

    for plugin_dir in plugin_locations:
        for filename in os.listdir(plugin_dir):
            if not filename.startswith('.'):
                if filename.endswith('.py') \
                        or filename.endswith('.zip') \
                        or os.path.isdir(os.path.realpath(os.path.join(plugin_dir, filename))):
                    plugin_folder = os.path.realpath(os.path.join(plugin_dir, filename))
                    sys.path.insert(0, os.path.realpath(plugin_folder))
                    logger.info("Added user plugin: %s", plugin_folder)
                    logger.debug("Sys path now: %s", sys.path)

    # if plugins_path:
    #     if os.path.exists(plugins_path):
    #         for filename in os.listdir(plugins_path):
    #             if not filename.startswith('.'):
    #                 if filename.endswith('.py') \
    #                         or filename.endswith('.zip') \
    #                         or os.path.isdir(os.path.realpath(os.path.join(plugins_path, filename))):
    #                     plugin_folder = os.path.realpath(os.path.join(plugins_path, filename))
    #                     sys.path.insert(0, os.path.realpath(plugin_folder))
    #                     logger.info("Added user plugin: %s", plugin_folder)
    #                     logger.debug("Sys path now: %s", sys.path)
    #     else:
    #         logger.warning("Plugins path does not exists")
    #
    # else:
    #     logger.warning("Plugins path was not defined by user")

    # plugins_2_load = plugins_2_load + plugins_list

    for plugin_name in plugins_list:
        logger.info("Installing plugin: {0}".format(plugin_name))
        try:
            m = importlib.import_module(plugin_name)
            conf.GENERIC_EDITOR_PLUGINS_FINDER += plugin_name
            main_window.plugins_classes.append(m)
        except Exception as err:
            logger.warning("Skiping bad plugin: %s", err, exc_info=True)

    logger.info("------------- END LOADING FOR IBLPYBPOD PLUGINS -------------")


# def install_plugins(main_window):
# 	""" Load plugins from plugins folder. These plugins should
# 	inherit from BaseWidget """
#
# 	logger.info("------------- LOADING PLUGINS -------------")
#
# 	plugins_path = conf.GENERIC_EDITOR_PLUGINS_PATH
# 	plugins_list = conf.GENERIC_EDITOR_PLUGINS_LIST
#
# 	# plugins_2_load = []
#
# 	if plugins_path:
# 		if os.path.exists(plugins_path):
# 			for filename in os.listdir(plugins_path):
# 				if not filename.startswith('.'):
# 					if filename.endswith('.py') \
# 							or filename.endswith('.zip') \
# 							or os.path.isdir(os.path.realpath(os.path.join(plugins_path, filename))):
# 						plugin_folder = os.path.realpath(os.path.join(plugins_path, filename))
# 						sys.path.insert(0, os.path.realpath(plugin_folder))
# 						logger.info("Added user plugin: %s", plugin_folder)
# 						logger.debug("Sys path now: %s", sys.path)
# 		else:
# 			logger.warning("Plugins path does not exists")
#
# 	else:
# 		logger.warning("Plugins path was not defined by user")
#
# 	# plugins_2_load = plugins_2_load + plugins_list
#
# 	for plugin_name in plugins_list:
# 		logger.info("Installing plugin: {0}".format(plugin_name))
# 		try:
# 			m = importlib.import_module(plugin_name)
# 			conf.GENERIC_EDITOR_PLUGINS_FINDER += plugin_name
# 			main_window.plugins_classes.append(m)
# 		except Exception as err:
# 			logger.warning("Skiping bad plugin: %s", err, exc_info=True)
#
# 	logger.info("------------- END LOADING PLUGINS -------------")
