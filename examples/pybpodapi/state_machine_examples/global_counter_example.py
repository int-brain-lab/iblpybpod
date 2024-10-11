# !/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Example adapted from Josh Sanders' original version on Sanworks Bpod repository

After poke2 (PWM2) LED turns off, one will have an infinite loop between LED of poke1 (PWM1) and LED of poke3 (PWM1).

To interrupt the infinite loop one have to interrupt poke1 or poke3 a number of times equal to threshold (in this case is 5 times).

"""
from pybpodapi.protocol import Bpod, StateMachine

my_bpod = Bpod()

sma = StateMachine(my_bpod)

sma.set_global_counter(counter_number=1, target_event='Port1In', threshold=5)

sma.add_state(
	state_name='InitialDelay',
	state_timer=2,
	state_change_conditions={Bpod.Events.Tup: 'ResetGlobalCounter1'},
	output_actions=[(Bpod.OutputChannels.PWM2, 255)])

sma.add_state(
	state_name='ResetGlobalCounter1',
	state_timer=0,
	state_change_conditions={Bpod.Events.Tup: 'Port1Lit'},
	output_actions=[(Bpod.OutputChannels.GlobalCounterReset, 1)])

sma.add_state(
	state_name='Port1Lit',  # Infinite loop (with next state). Only a global counter can save us.
	state_timer=.25,
	state_change_conditions={Bpod.Events.Tup: 'Port3Lit', 'GlobalCounter1_End': 'ExitTask'},
	output_actions=[(Bpod.OutputChannels.PWM1, 255)])

sma.add_state(
	state_name='Port3Lit',
	state_timer=.25,
	state_change_conditions={Bpod.Events.Tup: 'Port1Lit', 'GlobalCounter1_End': 'ExitTask'},
	output_actions=[(Bpod.OutputChannels.PWM3, 255)])

sma.add_state(
	state_name='ExitTask',
	state_timer=.25,
	state_change_conditions={Bpod.Events.Tup: 'exit'},
)

my_bpod.send_state_machine(sma)

my_bpod.run_state_machine(sma)

print("Current trial info: {0}".format(my_bpod.session.current_trial))

my_bpod.close()