from machine import Pin, I2C
import ssd1306


# ESP32 Pin assignment 
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
#Buttons 
button_up = Pin(33, Pin.IN,Pin.PULL_DOWN)
button_confirm = Pin(35, Pin.IN, Pin.PULL_DOWN)
button_down = Pin(32, Pin.IN, Pin.PULL_DOWN)
#Show Menu
#Test Code Below:
#oled.text('Hi', 10, 10)      
#oled.show()

menu_types=[[2,3,4,5,6,8],['Nomral','Texas','Crazy']]
current_item = 0
menu_index=0
def display_menu (current,index,menus): 
    if index == 0: 
        menu = menus[index]
        oled.fill(0)
        oled.text ('Menu_Player',0,0)
        oled.text ('-'*20,0,10)
        for i in range (len (menu)):
            if current>=3:
                for j in range (3, len (menu)):
                    if j == current:
                        oled.text ('> '+str(menu[j]) + ' players', 0, 20+(j-3)*10)
                    else:
                        oled.text (str(menu[j]) + ' players', 0, 20+(j-3)*10)
            else:
                if i == current:
                    oled.text ('> '+str(menu [i]) + ' players', 0, 20+i*10)
                else:
                    oled.text (str(menu [i]) + ' players', 0, 20+i*10)
    elif index == 1:
        menu = menus[index]
        oled.text ('Menu_Modes',0,0)
        oled.text ('-'*20,0,10)
        for i in range (len (menu)):
            if i == current:
                oled.text ('> '+menu [i] + ' Mode', 0, 20+i*10)
            else:
                oled.text (menu [i] + ' Mode', 0, 20+i*10)
    elif index == len (menus):
        oled.text ('Ready?',40,15)   
        oled.text (':D',40,28) 
    oled.show ()
    
def button_up_irq(button_up):
    global menu_index
    global current_item
    global menu_types
    print ("Now is going up ^")
    if button_up.value() == 1:
        if menu_index == 0:
            current_item = (current_item-1) % len (menu_types[0])
        elif menu_index == 1:
            current_item = (current_item-1) % len (menu_types[1])
        oled.fill (0)
        display_menu(current_item,menu_index,menu_types)

def button_down_irq(button_down):
    global menu_index
    global current_item
    global menu_types
    print ("Now is going down v")
    if button_down.value() == 1:
        if menu_index == 0:
            current_item = (current_item+1) % len (menu_types[0])
        elif menu_index == 1:
            current_item = (current_item+1) % len (menu_types[1])
        elif menu_index == len (menu_types):
            menu_index = 0
            current_item = 0
            print ("Now is switching menu :D")
        oled.fill (0)
        display_menu(current_item,menu_index,menu_types)
        

def button_confirm_irq(button_confirm):
    global menu_index
    global current_item
    global menu_types
    menu_index = (menu_index+1)
    print ("Now is switching menu :D")
    if button_confirm.value() == 1:
        if menu_index < len (menu_types):
            current_item = 0
        elif menu_index == len (menu_types) + 1:
            print ("Spreading card")
        oled.fill (0)
        display_menu(current_item,menu_index,menu_types)
        
    
#testing 
display_menu (current_item,menu_index,menu_types)
button_up.irq (button_up_irq, Pin.IRQ_RISING)
button_down.irq (button_down_irq, Pin.IRQ_RISING)
button_confirm.irq (button_confirm_irq, Pin.IRQ_RISING)
