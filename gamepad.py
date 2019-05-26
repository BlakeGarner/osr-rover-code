#!/usr/bin/env python
from evdev import InputDevice, util, ecodes
import time

CONTROLLER_NAME = "Xbox Wireless Controller"
#CONTROLLER_NAME = "Razer Sabertooth"
DEV_INPUT_PATH = "/dev/input"

BUTTONS_TIMEOUT = 60
AXIS_TIMEOUT = 15

# TODO: Make these the overridable
BUTTON_CODES = {304: 'A',
                305: 'B',
                307: 'X',
                308: 'Y',
                310: 'LBumper',
                311: 'RBumper',
                158: 'View',
                172: 'XBox',
                314: 'Back',
                315: 'Menu',
                317: 'LStick',
                318: 'RStick'}


AXIS_CODES = {00: 'LStick_X',
              01: 'LStick_Y',
#              03: 'RStick_X', # Xbox 360
#              04: 'RStick_Y', # XBox 360
#              02: 'LTrigger', # XBox 360
#              05: 'RTrigger', # XBox 360
              02: 'RStick_X', # XBox One S 0 = Left, 65535 = Right
              05: 'RStick_Y', # XBox One S 0 = Up, 65535 = Down
               9: 'RTrigger', # XBox One S 0 = Released, 1023 = Pushed
              10: 'LTrigger', # XBox One S
              16: 'DPad_X',   # -1 = Left, 0 = Center, 1 = Right
              17: 'DPad_Y'}   # -1 = Up, 0 = Center, 1 = Down

class Gamepad:
    """
    Creates a new instance of the gamepad.
    Connects to the first gamepad if any found.
    """
    def __init__(self,refreshRate = 30):
        self.refreshTime = 0
        self.refreshDelay = 1.0 / refreshRate

        self._buttons = {}
        self._axis = {}

        self._isConnected = False

        self._connect()

    
    def _connect(self):
        if(not self._isConnected):
            for eventPath in util.list_devices(DEV_INPUT_PATH):
                if util.is_device(eventPath):
                    device = InputDevice(eventPath)
                    if device.name == CONTROLLER_NAME:
                        print("Controller found: " + device.name)
                        self.gamepad = device
                        self._isConnected = True
                    else:
                        print("Wrong controller: " + device.name)
                        device.close()


    """
    If connected, reads the axis and buttons from the controller.
    If not connected, attempts to connect to the first gamepad found.
    If controller disconnected, exits and reverts to a not-connected state.
    """
    def refresh(self):
        event = None
        if self._isConnected:
            try:
                event = self.gamepad.read_one()
            except IOError:
                # Joystick disconnected.
                self._isConnected = False

            while event != None:
                self._processEvent(event)
                try:
                    event = self.gamepad.read_one()
                except IOError:
                    event = None
                    self._isConnected = False

        if not self._isConnected:
            self._buttons.clear()
            self._axis.clear()
            self._connect()

        self._checkTimeouts()

#        while event != None:
#            self.processEvent(event)
#            event = self.gamepad.read_one()

    def connected(self):
        return self._isConnected

    def _processEvent(self, event):
        # Check for button pushes.
        if event.type == ecodes.EV_KEY:
            code = event.code
            
            try:
                self._buttons[BUTTON_CODES[code]] = (int(event.value), time.time())
            except KeyError:
                print("Unknown key (" + str(code) + ")")

        # Check for axis changes.
        if event.type == ecodes.EV_ABS:
            code = event.code
            try:
                self._axis[AXIS_CODES[code]] = (int(event.value), time.time())
            except KeyError:
                print("Unknown axis (" + str(code) + ")")

    def _checkTimeouts(self):
        for k,v in self._axis.iteritems():
            if v[1] + AXIS_TIMEOUT < time.time():
                self._axis[k] = (32767, time.time())
        for k,v in self._buttons.iteritems():
            if v[1] + BUTTONS_TIMEOUT < time.time():
                self._buttons[k] = (0, time.time())

    """
    Gets the Left stick's X axis as a value between -1.0 (left) and 1.0 (right)
    """
    def leftX(self,deadzone=4000):
        return self._lookupStickPosition('LStick_X', deadzone)

    """
    Gets the Left stick's Y axis as a value between -1.0 (up) and 1.0 (down)
    """
    def leftY(self, deadzone=4000):
        return self._lookupStickPosition('LStick_Y', deadzone)

    """
    Gets the Right stick's X axis as a value between -1.0 (left) and 1.0 (right)
    """
    def rightX(self,deadzone=4000):
        return self._lookupStickPosition('RStick_X', deadzone)

    """
    Gets the right stick's Y axis as a value between -1.0 (up) and 1.0 (down)
    """
    def rightY(self,deadzone=4000):
        return self._lookupStickPosition('RStick_Y', deadzone)
    
    def _lookupStickPosition(self, axisName, deadzone):
        self.refresh()
        try:
            return self._axisScale(self._axis[axisName][0], deadzone)
        except KeyError:
            return 0.0

    def _axisScale(self, raw, deadzone):
        raw_offset = raw - (65535 // 2)
        if abs(raw_offset) < deadzone:
            return 0.0
        else:
            if raw_offset < 0:
                return (raw_offset + deadzone) / (32767.0 - deadzone)
            else:
                return (raw_offset - deadzone) / (32768.0 - deadzone)

    """
    Get the current state of the DPad's Up arrow
    Returns: 0 for released, 1 for pushed
    """ 
    def dpadUp(self):
        self.refresh()
        try:
            if self._axis['DPad_Y'][0] < 0:
                return 1
            else:
                return 0
        except KeyError:
            return 0

    """
    Get the current state of the DPad's Down arrow
    Returns: 0 for released, 1 for pushed
    """
    def dpadDown(self):
        self.refresh()
        try:
            if self._axis['DPad_Y'][0] > 0:
                return 1
            else:
                return 0
        except KeyError:
            return 0

    """
    Get the current state of the DPad's Left arrow
    Returns: 0 for released, 1 for pushed
    """
    def dpadLeft(self):
        self.refresh()
        try:
            if self._axis['DPad_X'][0] < 0:
                return 1
            else:
                return 0
        except KeyError:
            return 0

    """
    Get the current state of the DPad's Right arrow
    Returns: 0 for released, 1 for pushed
    """
    def dpadRight(self):
        self.refresh()
        try:
            if self._axis['DPad_X'][0] > 0:
                return 1
            else:
                return 0
        except KeyError:
            return 0

    """
    Get the current state of the left trigger.
    Returns: a value between 0.0 (released) and 1.0 (fully pressed)
    """
    def leftTrigger(self):
        self.refresh()
        try:
            return self._axis['LTrigger'][0] / 1023.0
        except KeyError:
            return 0.0

    """
    Get the current state of the right trigger.
    Returns: a value between 0.0 (released) and 1.0 (fully pressed)
    """
    def rightTrigger(self):
        self.refresh()
        try:
            return self._axis['RTrigger'][0] / 1023.0
        except KeyError:
            return 0.0

    """
    Get current state of the A button
    
    Returns: 1 or 0 for pushed or released respectively.
    """
    def A(self):
        return self._lookupKeyPress('A')

    """
    Get current state of the B button

    Returns: 1 or 0 for pushed or released respectively.
    """
    def B(self):
        return self._lookupKeyPress('B')

    """
    Get current state of the X button

    Returns: 1 or 0 for pushed or released respectively.
    """
    def X(self):
        return self._lookupKeyPress('X')
    
    """
    Get current state of the Y button

    Returns: 1 or 0 for pushed or released respectively.
    """
    def Y(self):
        return self._lookupKeyPress('Y')

    """
    Get current state of the Left Bumper

    Returns: 1 or 0 for pushed or released respectively.
    """
    def leftBumper(self):
        return self._lookupKeyPress('LBumper')

    """
    Get current state of the Right Bumper

    Returns: 1 or 0 for pushed or released respectively.
    """
    def rightBumper(self):
        return self._lookupKeyPress('RBumper')

    def _lookupKeyPress(self, keyName):
        self.refresh()
        try:
            return self._buttons[keyName][0]
        except KeyError:
            return 0

    def close(self):
        self._isConnected = False
        if self.gamepad != None:
            self.gamepad.close()

