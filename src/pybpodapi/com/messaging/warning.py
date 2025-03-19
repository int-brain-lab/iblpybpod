# !/usr/bin/python3
# -*- coding: utf-8 -*-
from logging import getLogger

from pybpodapi.com.messaging.base_message import BaseMessage

logger = getLogger(__name__)

class WarningMessage(BaseMessage):

    """ Message that represents an error """

    MESSAGE_TYPE_ALIAS = "warning"
    MESSAGE_COLOR = (255, 100, 0)

    def __init__(self, *args, **kwargs):
        logger.error(args[0], stacklevel=2)
        super().__init__(*args, **kwargs)
