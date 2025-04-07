import sys
import time
import board
from digitalio import DigitalInOut
from analogio import AnalogIn
import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
import countio
from hd44780 import HD44780

STATUS_CODE_FOR_EMPTY_RESPOPNSE = 204 

# Initialize spi interface
import busio
cs = DigitalInOut(board.GP17)
spi_bus = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs)

# # Change Mac Address of the device if multiple Pico boards are connected
# eth.mac_address = bytearray([0x00, 0x08, 0xDC, 0x22, 0x33, 0x71])


#Initialize a requests session
pool = adafruit_connection_manager.get_radio_socketpool(eth)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
requests = adafruit_requests.Session(pool, ssl_context)





try:
    from secrets import secrets
except ImportError:
    print("You need secrets.py to run this program. Please add them to the lib folder.")
    raise


# Set up Client Detail from secrets.py
client_id = secrets["client_id"]
client_secrets = secrets["client_secret"]
redirect_uri = secrets["redirect_uri"]

# Add more scope here if needed
scope_list = ["user-read-private","user-read-currently-playing", "user-modify-playback-state"] 


"""

Obtaining Authorization Code. Remove this line if you have performed for 1 min

"""

auth_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={"%20".join(scope_list)}"
print("Please visit this URL to authorize:", auth_url)

"""

END OF AUTHORIZATION


"""

# Connect to (SCL, SDA) pins
i2c = busio.I2C(board.GP3, board.GP2)
while not i2c.try_lock():
    pass
    
address_all = [hex(x) for x in i2c.scan()]
print(address_all)


    
    

# # # Replace code if token expired 
# # # Turn on this code if need new token

    
# import binascii
# credentials = f"{client_id}:{client_secrets}"
# encoded_credentials = binascii.b2a_base64(credentials.encode('utf-8')).decode('utf-8').strip("\n")
# code = "YOUR_AUTH_CODE_HERE"
# data_4 = {
#     "code":code,
#     "redirect_uri":redirect_uri,
#     "grant_type": "authorization_code"
# }
# headers_response_new = {
#     'content-type': 'application/x-www-form-urlencoded',
#     'Authorization': f'Basic {encoded_credentials}'
# }
# response_new = requests.post('https://accounts.spotify.com/api/token',data = data_4, headers = headers_response_new)

# print(response_new.json()["access_token"])
# print("Scope: ", response_new.json()["scope"])
# # print(response_new.json()["refresh_token"])

# response_new = None
# sys.exit()







# Display Name Function Start 
def start_display_name(auth_token, headers):
 
    name_req = requests.get('https://api.spotify.com/v1/me',  headers=headers)
    my_name = name_req.json()["display_name"]
    display.write("Welcome!", 1)
    display.write(my_name,2)
    name_req = None
    time.sleep(4)
    display.clear()






# Initialize Screen
display = HD44780(i2c,0x27)
auth_token = secrets["auth_token"]

headers = {
    'Authorization': f'Bearer {auth_token}'
}


# Print Name
start_display_name(auth_token = auth_token, headers = headers)

#Set up Joystick
dir_vetical = AnalogIn(board.GP26)
value_intial_ver = dir_vetical.value
pressed_count = countio.Counter(board.GP15, edge = countio.Edge.FALL)

# Initializa Vairiable
function_player = ["Pause", "Start", "Skip", "Off"]
power = True
refresh_timer = -1




#  Display Song Name Once
display.clear()


def interrupt_function():
    
    global pressed_count, refresh_timer, power

    #Initialize
    function_player_choice = 0
    refresh_timer_interrupt = 5
    
    if pressed_count.count > 0:
        refresh_timer = -1
        pressed_count.count = 0
        display.clear()
        display.write(function_player[function_player_choice],1)

        while refresh_timer_interrupt >= 0:
            print("Pressed Count:  Inside" ,pressed_count.count)
            if dir_vetical.value >= 55000:
                
                refresh_timer_interrupt = 5
                function_player_choice = (function_player_choice + 1) % len(function_player)
                display.clear()
                display.write(function_player[function_player_choice],1)
            elif dir_vetical.value <= 5000:
                
                refresh_timer_interrupt = 5
                function_player_choice = (function_player_choice - 1) % len(function_player)
                display.clear()
                display.write(function_player[function_player_choice],1)
                
            if pressed_count.count > 0:
                refresh_timer_interrupt = 0
                pressed_count.count = 0
                print("Choice: ", function_player_choice)

               
                if function_player_choice == 3:   # Choice = Off
                    power = False
                    
                elif function_player_choice == 0: # Choice = Pause/Start
                    headers_choice_pause = {
                        'Authorization': f'Bearer {auth_token}',
                        "Content-Type": "application/json",
                        "Content-length": "0"
                    }
                    print(headers_choice_pause)
                    print(headers)
                    response_put = requests.put(f'https://api.spotify.com/v1/me/player/pause', headers = headers_choice_pause)
                    # print(response_put.text)
                    if response_put.json()["error"]["reason"] == "PREMIUM_REQUIRED":
                        display.clear()
                        display.write("Premium",1)
                        display.write("Needed", 2)
                        time.sleep(3)
                        display.clear()
                    elif response_put.status_code == 204:
                        display.write("Paused", 3)
                        time.sleep(1)
                    response_put = None
                else:
                    print("Back to main func")
                    
    
            pressed_count.count = 0
            refresh_timer_interrupt = refresh_timer_interrupt - 1
            time.sleep(1)
        
    pressed_count.count = 0
    function_player_choice = 0        

   
    
while power:
    interrupt_function()
    
    # Main
    headers_auth = {
        'Authorization': f'Bearer {auth_token}'
    }
    if refresh_timer < 0:
        refresh_timer = 5
        display.clear()
        response_2 = requests.get('https://api.spotify.com/v1/me/player/currently-playing',  headers=headers_auth)
        if response_2.status_code != STATUS_CODE_FOR_EMPTY_RESPOPNSE:
            playstate = response_2.json()["is_playing"]
            song_name = response_2.json()["item"]["name"]
            if (playstate):
                display.write(song_name,1)
            else:
                display.write("Device Off!", 1)  
                time.sleep(2)
        else:
            display.write("Spotify",1)
            display.write("DISCONNECTED",2)
            time.sleep(2)
            power = False
        response_2 = None 
        # display.write("Inside", 1)
    else:
        refresh_timer = refresh_timer - 1
        time.sleep(0.5)








display.clear()
display.write("Turned Off",1)
print("Machine Turned off")




