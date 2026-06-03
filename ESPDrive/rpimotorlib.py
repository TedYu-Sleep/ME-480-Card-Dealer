import sys
import time
from machine import Pin
# ==================== CLASS SECTION ===============================

class StopMotorInterrupt(Exception):
    """ Stop the motor """
    pass
class A4988Nema(object):
    """ Class to control a Nema bi-polar stepper motor with a A4988 also tested with DRV8825"""
    def __init__(self, direction_pin, step_pin, mode_pins, motor_type="A4988"):
        """ class init method 3 inputs
        (1) direction type=int , help=GPIO pin connected to DIR pin of IC
        (2) step_pin type=int , help=GPIO pin connected to STEP of IC
        (3) mode_pins type=tuple of 3 ints, help=GPIO pins connected to
        Microstep Resolution pins MS1-MS3 of IC, can be set to (-1,-1,-1) to turn off
        GPIO resolution.
        (4) motor_type type=string, help=Type of motor two options: A4988 or DRV8825
        """
        self.motor_type = motor_type
        self.direction_pin = direction_pin
        self.step_pin = step_pin
        

        if mode_pins[0] != -1 and len(mode_pins)==3:
            self.mode_pins = mode_pins
            self.MS1 = Pin(mode_pins[0],Pin.OUT)
            self.MS2 = Pin(mode_pins[1],Pin.OUT)
            self.MS3 = Pin(mode_pins[2],Pin.OUT)
        else:
            self.mode_pins = False
        
        self.stop_motor = False
        #GPIO.setwarnings(False)
        #GPIO.setmode(GPIO.BCM)

    def motor_stop(self):
        """ Stop the motor """
        self.stop_motor = True

    def resolution_set(self, steptype):
        """ method to calculate step resolution
        based on motor type and steptype"""
        if self.motor_type == "A4988":
            resolution = {'Full': (0, 0, 0),
                          'Half': (1, 0, 0),
                          '1/4': (0, 1, 0),
                          '1/8': (1, 1, 0),
                          '1/16': (1, 1, 1)}
        elif self.motor_type == "DRV8825":
            resolution = {'Full': (0, 0, 0),
                          'Half': (1, 0, 0),
                          '1/4': (0, 1, 0),
                          '1/8': (1, 1, 0),
                          '1/16': (0, 0, 1),
                          '1/32': (1, 0, 1)}
        elif self.motor_type == "LV8729":
            resolution = {'Full': (0, 0, 0),
                          'Half': (1, 0, 0),
                          '1/4': (0, 1, 0),
                          '1/8': (1, 1, 0),
                          '1/16': (0, 0, 1),
                          '1/32': (1, 0, 1),
                          '1/64': (0, 1, 1),
                          '1/128': (1, 1, 1)}
        else:
            print("Error invalid motor_type: {}".format(self.motor_type))
            quit()

        # error check stepmode
        if steptype in resolution:
            return resolution.get(steptype)
        else:
                print("Error invalid steptype: {}".format(steptype))
                quit()

    def motor_go(self, CCW, steptype,
                 steps=200, stepdelay=.005, verbose=False, initdelay=.05):
        """ motor_go,  moves stepper motor based on 6 inputs
         (1) clockwise, type=bool default=False
         help="Turn stepper counterclockwise"
         (2) steptype, type=string , default=Full help= type of drive to
         step motor 5 options
            (Full, Half, 1/4, 1/8, 1/16) 1/32 for DRV8825 only
         (3) steps, type=int, default=200, help=Number of steps sequence's
         to execute. Default is one revolution , 200 in Full mode.
         (4) stepdelay, type=float, default=0.05, help=Time to wait
         (in seconds) between steps.
         (5) verbose, type=bool  type=bool default=False
         help="Write pin actions",
         (6) initdelay, type=float, default=1mS, help= Intial delay after
         GPIO pins initialized but before motor is moved.
        """
        self.stop_motor = False
        ''' 
        setup GPIO
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.output(self.direction_pin, clockwise)
        '''
        self.direction_pincond = Pin(self.direction_pin,Pin.OUT,value=CCW)
        self.step_pincond = Pin(self.step_pin,Pin.OUT)
        if self.mode_pins != False:
            #GPIO.setup(self.mode_pins, GPIO.OUT)
            self.MS1.value(self.resolution_set(steptype)[0])
            self.MS2.value(self.resolution_set(steptype)[1])
            self.MS3.value(self.resolution_set(steptype)[2])
            print (self.MS1.value(),self.MS2.value())
        try:
            time.sleep(initdelay)
            for i in range(steps):
                #GPIO.output(self.step_pin, False)
                self.step_pincond.value(1)
                time.sleep(stepdelay)
                #GPIO.output(self.step_pin, False)
                self.step_pincond.value(0)
                time.sleep(stepdelay)
                if verbose==True:
                    print("Steps count {}".format(i+1), end="\r")

        except KeyboardInterrupt:
            print("User Keyboard Interrupt : RpiMotorLib:")
        except StopMotorInterrupt:
            print("Stop Motor Interrupt : RpiMotorLib: ")
        else:
            # print report status
            if verbose:
                print("\nESP32Control, Motor Run finished, Details:")
                print("Motor type = {}".format(self.motor_type))
                print("Counter-Clockwise = {}".format(CCW))
                print("Step Type = {}".format(steptype))
                print("Number of steps = {}".format(steps))
                print("Step Delay = {}".format(stepdelay))
                print("Intial delay = {}".format(initdelay))
                print("Size of turn in degrees = {}"
                      .format(degree_calc(steps, steptype)))
        finally:
            '''cleanup
            GPIO.output(self.step_pin, False)
            GPIO.output(self.direction_pin, False)
            '''
            self.step_pincond.value(0) 
            self.direction_pincond.value(0) 
            
            if self.mode_pins != False:
                #for pin in self.mode_pins:
                    #GPIO.output(pin, False)
                self.MS1.value(0)
                self.MS2.value(0)
                self.MS3.value(0)
                
def degree_calc(steps, steptype):
    """ calculate and returns size of turn in degree
    , passed number of steps and steptype"""
    degree_value = {'Full': 1.8,
                    'Half': 0.9,
                    '1/4': .45,
                    '1/8': .225,
                    '1/16': 0.1125,
                    '1/32': 0.05625,
                    '1/64': 0.028125,
                    '1/128': 0.0140625}
    degree_value = (steps*degree_value[steptype])
    return degree_value

def importtest(text):
    """ testing import """
    # print(text)
    text = " "

# ===================== MAIN ===============================


if __name__ == '__main__':
    importtest("main")
else:
    importtest("Imported {}".format(__name__))


# ===================== END ===============================