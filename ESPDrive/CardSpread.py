from machine import Pin, PWM
import time
from rpimotorlib import A4988Nema
import math
from Motor import DCMotor
from card_animation import CardAnimation


class card_spread(object):
    # Ver1 -- motor for spreading card is not added now 
    def __init__(self, pinM, pinD, pinS, pin1, pin2, PWMP, Player, Mode, Step_mode,screen):
        self.direction = pinD
        self.mode_pins = pinM
        self.step = pinS
        self.motor11 = pin1
        self.motor12 = pin2
        self.PWMP1 = PWMP
        self.num_player = Player
        self.play_mode = Mode
        self.step_mode = Step_mode
        self.oled = screen
        self.mymotortest = A4988Nema(self.direction, self.step, self.mode_pins, "A4988")
        self.DCmotor_one = self.motor_setup(self.motor11, self.motor12, self.PWMP1)

    def motor_setup(self, Pin1, Pin2, PWMP, freq=15000, duty=512):
        pin1 = Pin(Pin1, Pin.OUT)
        pin2 = Pin(Pin2, Pin.OUT)
        PWMP = Pin(PWMP, Pin.OUT)
        
        # FIXED: Explicit keyword arguments for MicroPython PWM compliance
        pwm = PWM(PWMP, freq=freq, duty=duty) 
        
        # Note: Ensure DCMotor class is imported from your Motor module
        motor_num = DCMotor(pin1, pin2, pwm, 750, 1023)
        return motor_num

    # FIXED: Added missing 'self' parameter to the method definition
    def DCmotor_go(self, motor_fun, speed=100, sleep_time=0.5):
        motor_fun.forward(speed)
        time.sleep(sleep_time)
        motor_fun.stop()    

    def angle_step(self, angle_mode):
        degree_value = {'Full': 1.8,
                        'Half': 0.9,
                        '1/4': .45,
                        '1/8': .225,
                        '1/16': 0.1125,
                        '1/32': 0.05625,
                        '1/64': 0.028125,
                        '1/128': 0.0140625}
        return (math.ceil(angle_mode / degree_value[self.step_mode]))
    
    def spread_motion(self, spreaddelay=0.1, initdelay=.5):
        step = 0
        
        if self.play_mode == 'Normal':
            angle = 360 / self.num_player
            step = self.angle_step(angle)
            print(self.play_mode, step)
            time.sleep(initdelay)
            step_count = 0
            self.oled.fill (0)
            self.oled.text('Spreading...', 10, 15)
            self.oled.show()
            for i in range(0, 6): 
                angle_zero = 0 
                if (step_count + step) < 200:
                    print('cardspread by upper motors')
                    # FIXED: Referenced self.DCmotor_one with 'self.' prefix
                    self.DCmotor_go(self.DCmotor_one, speed=100, sleep_time=0.5)
                    time.sleep(spreaddelay)
                    self.mymotortest.motor_go(0, self.step_mode, step, .01, True, .05)
                    time.sleep(spreaddelay)
                    step_count += step
                else: 
                    step_count = 200 - step_count
                    print('cardspread by upper motors')
                    # FIXED: Referenced self.DCmotor_one with 'self.' prefix
                    self.DCmotor_go(self.DCmotor_one, speed=100, sleep_time=0.5)
                    time.sleep(spreaddelay)
                    self.mymotortest.motor_go(0, self.step_mode, step_count, .01, True, .05)
                    time.sleep(spreaddelay)
                    step_count = 0
            step_back = step_count % 200
            self.mymotortest.motor_go(1, self.step_mode, step_back, .01, True, .05)
            time.sleep (0.05)
            self.oled.fill(0)
            self.oled.text('Spread over...', 5, 15) 
            self.oled.text('"up"-> restart', 0, 28)
            self.oled.show()        

        elif self.play_mode == 'Texas':
            angle = 180 / (self.num_player - 1)
            step = self.angle_step(angle)
            step_init = self.angle_step(90)
            time.sleep(initdelay)
            self.oled.fill (0)
            self.oled.text('Spreading...', 10, 15)
            self.oled.show()
            time.sleep(spreaddelay)
            self.mymotortest.motor_go(1, self.step_mode, step_init, .01, True, .05)
            time.sleep(spreaddelay)
            # FIXED: Referenced self.DCmotor_one with 'self.' prefix
            self.DCmotor_go(self.DCmotor_one, speed=100, sleep_time=0.5)
            time.sleep(spreaddelay)
            # FIXED: Explicitly initialized step_count locally before modifying it in the loops
            step_count = 0 
            for i in range(0, 3):
                print('spread card')
                # FIXED: Referenced self.DCmotor_one with 'self.' prefix
                self.DCmotor_go(self.DCmotor_one, speed=100, sleep_time=0.5)
                time.sleep(spreaddelay)
            self.mymotortest.motor_go(0, self.step_mode, step_init, .01, True, .05)
            time.sleep(spreaddelay)
            for i in range(0, self.num_player - 1):
                for j in range(0, 2): 
                    print('spread card' + str(j))
                    # FIXED: Referenced self.DCmotor_one with 'self.' prefix
                    self.DCmotor_go(self.DCmotor_one, speed=100, sleep_time=0.5)
                    time.sleep(spreaddelay)
                if (step_count+step) > 100:
                    step = 100-step_count
                self.mymotortest.motor_go(0, self.step_mode, step, .01, True, .05)
                time.sleep(spreaddelay)  
                step_count += step  
            for k in range(0, 2): 
                print('spread card' + str(k))
                self.DCmotor_go(self.DCmotor_one, speed=100, sleep_time=0.5)
                time.sleep(spreaddelay)
            time.sleep(spreaddelay)    
            self.mymotortest.motor_go(1, self.step_mode, step_count, .01, True, .05)
            self.oled.fill(0)
            self.oled.text('"confirm"-> next card', 0, 15) 
            self.oled.text('"up"-> restart',0,25)
            self.oled.show()