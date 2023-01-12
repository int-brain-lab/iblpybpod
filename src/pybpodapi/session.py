import logging
from confapp import conf
from datetime import datetime as datetime_now

import pybpodapi
from pybpodapi.com.messaging.trial import Trial
from pybpodapi.com.messaging.state_occurrence import StateOccurrence

from sca.formats import csv

import sys
from pybpodapi.com.stdout_buffer import StdoutBuffer
from pybpodapi.com.stderr_buffer import StderrBuffer

logger = logging.getLogger(__name__)


class StreamsWrapper(object):
    def __init__(self, streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def close(self):
        for stream in self.streams:
            stream.flush()
            stream.close()


class Session(object):
    """
    Stores information about bpod run, including the list of trials.

    :ivar list(Trial) trials: a list of trials
    :ivar int firmware_version: firmware version of Bpod when experiment was run
    :ivar int bpod_version: version of Bpod hardware when experiment was run
    :ivar datetime start_timestamp: it stores session start timestamp

    """

    MSGTYPE_DEBUG = "debug"
    MSGTYPE_ENDTRIAL = "END-TRIAL"
    MSGTYPE_ERROR = "error"
    MSGTYPE_INFO = "INFO"
    MSGTYPE_SOFTCODE = "SOFTCODE"
    MSGTYPE_STDERR = "stderr"
    MSGTYPE_STDOUT = "stdout"
    MSGTYPE_TRIAL = "TRIAL"
    MSGTYPE_WARNING = "warning"
    MSGTYPE_STATE = "STATE"
    MSGTYPE_TRANSITION = "TRANSITION"

    INFO_SESSION_NAME = "SESSION-NAME"
    INFO_SESSION_STARTED = "SESSION-STARTED"
    INFO_SESSION_ENDED = "SESSION-ENDED"
    INFO_SERIAL_PORT = "SERIAL-PORT"
    INFO_NET_PORT = "NET-PORT"
    INFO_BPODAPI_VERSION = "BPOD-API-VERSION"

    INFO_PROTOCOL_NAME = "PROTOCOL-NAME"
    INFO_CREATOR_NAME = "CREATOR-NAME"
    INFO_PROJECT_NAME = "PROJECT-NAME"
    INFO_EXPERIMENT_NAME = "EXPERIMENT-NAME"
    INFO_BOARD_NAME = "BOARD-NAME"
    INFO_SETUP_NAME = "SETUP-NAME"
    INFO_SUBJECT_NAME = "SUBJECT-NAME"
    INFO_BPODGUI_VERSION = "BPOD-GUI-VERSION"

    INFO_TRIAL_BPODTIME = "TRIAL-BPOD-TIME"

    def __init__(self, path=None):
        self.ostdout = sys.stdout
        self.ostderr = sys.stderr

        # the variable will contain a list of streams where the session output
        # should be written.
        streams = []

        self.history = []  # type: list[Trial]
        self.trials = []  # type: list[Trial]
        self.firmware_version = None  # type: int
        self.bpod_version = None  # type: int
        self.start_timestamp = datetime_now.now()  # type: datetime

        self.csvwriter = None
        self._path = path

        # stream data to a file.
        if path:
            streams += [open(path, "w")]

        # stream data to the stdout.
        if conf.PYBPOD_API_STREAM2STDOUT:
            sys.stdout = StdoutBuffer(self)
            sys.stderr = StderrBuffer(self)
            streams += [self.ostdout]


    def __del__(self):
        sys.stdout = self.ostdout
        sys.stderr = self.ostderr

    def __add__(self, msg):
        """
        Add new trial to this session and associate a state machine to it

        :param pybpodapi.model.state_machine sma: state machine associated with this trial
        """

        if isinstance(msg, Trial):
            self.trials.append(msg)
        elif self.current_trial is not None:
            self.current_trial += msg

        self.history.append(msg)

        if self.csvwriter:
            self.csvwriter.writerow(msg.tolist())
            self.csvwriter.flush()

        return self

    def add_trial_events(self):

        current_trial = self.current_trial  # type: Trial
        sma = current_trial.sma

        visitedStates = [0] * current_trial.sma.total_states_added
        # determine unique states while preserving visited order
        uniqueStates = []
        nUniqueStates = 0
        uniqueStateIndexes = [0] * len(current_trial.states)

        for i in range(len(current_trial.states)):
            if current_trial.states[i] in uniqueStates:
                uniqueStateIndexes[i] = uniqueStates.index(current_trial.states[i])
            else:
                uniqueStateIndexes[i] = nUniqueStates
                nUniqueStates += 1
                uniqueStates.append(current_trial.states[i])
                visitedStates[current_trial.states[i]] = 1

        # Create a 2-d matrix for each state in a list
        uniqueStateDataMatrices = [[] for i in range(len(current_trial.states))]

        # Append one matrix for each unique state
        for i in range(len(current_trial.states)):
            if len(current_trial.state_timestamps) > 1:
                uniqueStateDataMatrices[uniqueStateIndexes[i]] += [
                    (
                        current_trial.state_timestamps[i],
                        current_trial.state_timestamps[i + 1],
                    )
                ]

        for i in range(nUniqueStates):
            thisStateName = sma.state_names[uniqueStates[i]]

            for state_dur in uniqueStateDataMatrices[i]:
                self += StateOccurrence(thisStateName, state_dur[0], state_dur[1])

        logger.debug("State names: %s", sma.state_names)
        logger.debug("nPossibleStates: %s", sma.total_states_added)
        for i in range(sma.total_states_added):
            thisStateName = sma.state_names[i]
            if not visitedStates[i]:
                self += StateOccurrence(thisStateName, float("NaN"), float("NaN"))

        logger.debug(
            "Trial states: %s",
            [str(state) for state in current_trial.states_occurrences],
        )

        # save events occurrences on trial
        # current_trial.events_occurrences = sma.raw_data.events_occurrences  # type: list

        logger.debug(
            "Trial events: %s",
            [str(event) for event in current_trial.events_occurrences],
        )

        logger.debug("Trial info: %s", str(current_trial))

    @property
    def current_trial(self):
        """
        Get current trial

        :rtype: Trial
        """
        return self.trials[-1] if len(self.trials) > 0 else None

    @current_trial.setter
    def current_trial(self, value):
        """
        Get current trial

        :rtype: Trial
        """
        self.trials[-1] = value
