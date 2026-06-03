from machine import Pin, I2C
import time
# from Libs.rpimotorlib import A4988Nema  # Left commented out to avoid firmware crash
import Libs.ssd1306 as ssd1306
from Libs.CardSpread import card_spread
from Libs.Motor import DCMotor
from Libs.card_animation import CardAnimation
from Libs.ESP32_Blue import ESP32_BLE
import bluetooth

# ==========================================
# 1. BlueTooth INITIALIZATION
# ==========================================
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_NOTIFY,)
_UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE,)
_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX),)

# ==========================================
# 2. HARDWARE & APP INITIALIZATION
# ==========================================
ble = ESP32_BLE("ESP32_Dealer")
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# SAFE DEVKITC V4 BUTTON PINS 
button_up = Pin(13, Pin.IN, Pin.PULL_DOWN)
button_confirm = Pin(14, Pin.IN, Pin.PULL_DOWN)
button_down = Pin(32, Pin.IN, Pin.PULL_DOWN)

# --- SOFTWARE DEBOUNCE TIMESTAMPS ---
last_press_up = 0
last_press_down = 0
last_press_confirm = 0
DEBOUNCE_DELAY_MS = 250  # Ignore any bounces within 250ms of a real press

menu_types = [[2, 3, 4, 5, 6, 8], ['Normal', 'Texas', 'Crazy']]
current_item = 0
menu_index = 0
player_num = 2
play_mode = 'Normal'
spread = None  

def display_menu(current, index, menus): 
    global player_num 
    global play_mode
    if index == 0: 
        menu = menus[index]
        oled.fill(0)
        oled.text('Menu_Player', 0, 0)
        oled.text('-'*20, 0, 10)
        for i in range(len(menu)):
            if current >= 3:
                for j in range(3, len(menu)):
                    if j == current:
                        player_num = menu[j]
                        oled.text('> ' + str(menu[j]) + ' players', 0, 20 + (j - 3) * 10)
                    else:
                        oled.text(str(menu[j]) + ' players', 0, 20 + (j - 3) * 10)
            else:
                if i == current:
                    player_num = menu[i]
                    oled.text('> ' + str(menu[i]) + ' players', 0, 20 + i * 10)
                else:
                    oled.text(str(menu[i]) + ' players', 0, 20 + i * 10)
    elif index == 1:
        menu = menus[index]
        oled.text('Menu_Modes', 0, 0)
        oled.text('-'*20, 0, 10)
        for i in range(len(menu)):
            if i == current:
                play_mode = menu[i]
                oled.text('> ' + menu[i] + ' Mode', 0, 20 + i * 10)
            else:
                oled.text(menu[i] + ' Mode', 0, 20 + i * 10)
    elif index == len(menus):
        oled.text('Ready?', 20, 15)   
        oled.text(':D', 30, 28) 
    elif index > len(menus)+1 and play_mode == 'Texas':
        oled.fill(0)
        oled.text('"confirm"-> next card', 0, 15) 
        oled.text('"up"-> restart',0,25)
    oled.show()
    
def button_up_irq(button_up):
    global menu_index, current_item, menu_types, last_press_up
    
    # Calculate time since last valid execution
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press_up) < DEBOUNCE_DELAY_MS:
        return  # Drop out early; this is a double-click/bounce
        
    if button_up.value() == 1:
        last_press_up = now  # Valid press confirmed; save timestamp
        print("Now is going up ^")
        if menu_index == 0:
            current_item = (current_item - 1) % len(menu_types[0])
            oled.fill(0)
            display_menu(current_item, menu_index, menu_types)
        elif menu_index == 1:
            current_item = (current_item - 1) % len(menu_types[1])
            oled.fill(0)
            display_menu(current_item, menu_index, menu_types)
        elif menu_index >= (len(menu_types) + 1) or play_mode == 'Crazy':
            end_game()
            
def button_down_irq(button_down):
    global menu_index, current_item, menu_types, last_press_down
    
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press_down) < DEBOUNCE_DELAY_MS:
        return  # Drop out early; noise filtering active
        
    if button_down.value() == 1:
        last_press_down = now  # Save timestamp
        print("Now is going down v")
        if menu_index == 0:
            current_item = (current_item + 1) % len(menu_types[0])
        elif menu_index == 1:
            current_item = (current_item + 1) % len(menu_types[1])
        elif menu_index == len(menu_types):
            menu_index = 0
            current_item = 0
            print("Now is switching menu :D")
        oled.fill(0)
        display_menu(current_item, menu_index, menu_types)

def end_game():
    global menu_index, current_item, menu_types, player_num, play_mode
    menu_index = 0 
    current_item = 0 
    menu_types = [[2, 3, 4, 5, 6, 8], ['Normal', 'Texas', 'Crazy']] 
    player_num = 0 
    play_mode = 'Normal' 
    oled.fill(0)
    oled.text('Game over...', 25, 15) 
    oled.text('Restarting', 25, 28) 
    oled.show()
    time.sleep(5)
    oled.fill(0)
    display_menu(current_item, menu_index, menu_types)

def button_confirm_irq(button_confirm):
    global menu_index, current_item, menu_types, player_num, play_mode, spread, last_press_confirm
    
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press_confirm) < DEBOUNCE_DELAY_MS:
        return  # Reject phantom bouncing inputs
        
    if button_confirm.value() == 1:
        last_press_confirm = now  # Lock time window
        print("confirming")
        menu_index = (menu_index + 1)
        if menu_index < len(menu_types):
            current_item = 0
        oled.fill(0)
        display_menu(current_item, menu_index, menu_types)
        
        if menu_index == len(menu_types) + 1:
            Stepmode = 'Full'
            # SAFE DEVKITC V4 MOTOR PINS
            direction = 18
            step = 4
            mode_pins = [25, 33, 26] 
            pin1 = 19              
            pin2 = 27             
            PWMP1 = 23
            enable = 12
            
            # Detach interrupts before running motor block
            button_confirm.irq(handler=None)
            button_down.irq(handler=None)
            button_up.irq(handler=None)
            
            spread = card_spread(enable, mode_pins, direction, step, pin1, pin2, PWMP1, player_num, play_mode, Stepmode, oled)
            spread.spread_motion(spreaddelay=.1, initdelay=.05)
            
            time.sleep_ms(200) # Give structural noise extra time to clear
            
            # Re-attach clean interrupts on rising edges
            button_up.irq(handler=button_up_irq, trigger=Pin.IRQ_RISING)
            button_down.irq(handler=button_down_irq, trigger=Pin.IRQ_RISING)
            button_confirm.irq(handler=button_confirm_irq, trigger=Pin.IRQ_RISING)
            ble.send("Done Spreading!\n")
            
        elif menu_index > len(menu_types) + 1 and play_mode == 'Texas':
            print('spreadonemore')
            spread.DCmotor_go(spread.DCmotor_one, 100, 0.5)
            time.sleep(1.5)
            
        elif play_mode == 'Crazy':
            time.sleep(2)
            anim = CardAnimation(oled)
            anim.run_n(72)
            time.sleep(0.5)
            end_game()

def main():
    time.sleep_ms(200)
    oled.fill(0)
    
    # Registering hardware interrupt vectors safely on clean Rising Edges
    button_up.irq(handler=button_up_irq, trigger=Pin.IRQ_RISING)
    button_down.irq(handler=button_down_irq, trigger=Pin.IRQ_RISING)
    button_confirm.irq(handler=button_confirm_irq, trigger=Pin.IRQ_RISING)
    
    display_menu(current_item, menu_index, menu_types)
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()