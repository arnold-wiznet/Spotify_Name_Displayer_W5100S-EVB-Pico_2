# -----------------------------------------------------------------------------
# CircuitPython Library for the HD44780 with Serial Interface (PCF8574T) on W5100SEVBPICO2
#

# Original Project:
# This code is from https://github.com/bablokb/circuitpython-hd44780
# released under the GPL3 license.

# Modifications:
# Adapted to CircuitPython by Arnold Ho

# Minor modifications include:
# - Assigned pins for the i2c explicitly from the main program to ensure i2c in the class exist
# Major changes include:
# - Display write function is changed to display all words in two lines

# Version Information:
# Version: 1.0
# Last Modified: 07/04/2025

# Contributors:
# - Arnold Ho

# Contact Information:
# For questions or feedback, contact: arnoldho@wiznet.hk

# License:
# This project is licensed under the GPL3 License. Please refer to the COPYING file
# for the full license text or visit https://www.gnu.org/licenses/gpl-3.0.en.html.

# Additional Resources:
# - Documentation: 
# 1. https://www.hackster.io/arnoldho/spotify-name-displayer-with-circuitpython-and-w5100sevbpico2-2d9861
# 2. https://github.com/arnold-wiznet/Spotify_Name_Displayer
# - Video Link: 
# 1. https://youtu.be/8WM6HPghsPQ
# 2. https://youtu.be/O-IQCqR1cf4
# 3. https://youtu.be/mQugCvCIfOQ
# -----------------------------------------------------------------------------

# Disclaimer:
# This code is provided as-is, without any warranty or guarantee. Use at your own risk.
# The contributors and copyright holders are not liable for any damages or issues arising from the use of this code.

import board
import busio
import time
import math


class HD44780(object):
  # LCD Address
  ADDRESS = 0x27
  
  # commands
  CLEARDISPLAY = 0x01
  RETURNHOME = 0x02
  ENTRYMODESET = 0x04
  DISPLAYCONTROL = 0x08
  CURSORSHIFT = 0x10
  FUNCTIONSET = 0x20
  SETCGRAMADDR = 0x40
  SETDDRAMADDR = 0x80

  # flags for display entry mode
  ENTRYRIGHT = 0x00
  ENTRYLEFT = 0x02
  ENTRYSHIFTINCREMENT = 0x01
  ENTRYSHIFTDECREMENT = 0x00

  # flags for display on/off control
  DISPLAYON = 0x04
  DISPLAYOFF = 0x00
  CURSORON = 0x02
  CURSOROFF = 0x00
  BLINKON = 0x01
  BLINKOFF = 0x00

  # flags for display/cursor shift
  DISPLAYMOVE = 0x08
  CURSORMOVE = 0x00
  MOVERIGHT = 0x04
  MOVELEFT = 0x00

  # flags for function set
  F_4BITMODE = 0x00
  F_2LINE = 0x08
  F_5x8DOTS = 0x00

  # flags for backlight control
  BACKLIGHT = 0x08
  NOBACKLIGHT = 0x00

  EN = 0b00000100 # Enable bit
  RS = 0b00000001 # Register select bit

  # line address
  LINE = [0x80,0xC0,0x94,0xD4]

  # --- constructor   --------------------------------------------------------
  
  def __init__(self,i2c=None,address=ADDRESS,trans_map={}):
    if i2c is None:
        i2c = busio.I2C(board.SCL,board.SDA)
    else:
        self.i2c= i2c
    
    self.address = address
    self.trans_map = trans_map

    self._write(0x03)
    self._write(0x03)
    self._write(0x03)
    self._write(0x02)

    self._write(HD44780.FUNCTIONSET |
                HD44780.F_2LINE | HD44780.F_5x8DOTS | HD44780.F_4BITMODE)
    self._write(HD44780.DISPLAYCONTROL | HD44780.DISPLAYON)
    self._write(HD44780.CLEARDISPLAY)
    self._write(HD44780.ENTRYMODESET | HD44780.ENTRYLEFT)
    

  # --- set backlight status   -----------------------------------------------
  
  def backlight(self,on):
    if on:
      self._write_to_i2c(HD44780.BACKLIGHT)
    else:
      self._write_to_i2c(HD44780.NOBACKLIGHT)

  # --- display a string on the given line   ---------------------------------

  def write(self,string,line):
    
    string_list = string.split(" ")
    if len(string) >= 16:
        
        # Check for Multiple Lines
        total_line_for_too_long= math.ceil(len(string) /16)
        filled_line = 0

        # Indicate the Start Position and Ending position of the String we need to print
        start = 0
        end = 16
        for i in range(total_line_for_too_long):
            filled_line = filled_line + 1

            # If both line on the screen is occupied, clear the screen with spaces and start printing from start again
            if filled_line >= 3:
                filled_line = 1

                # Printing Spaces onto line 1 and 2
                self._write(HD44780.LINE[0])
                for y in range(16):
                    self._write(32,HD44780.RS)
                self._write(HD44780.LINE[1])
                for y in range(16):
                    self._write(32,HD44780.RS)       
                 
            line = (i % 2) + 1
            self._write(HD44780.LINE[line-1])
            print(string[start:end], ",  Length =  ", len(string[start:end]))
            # Print the string from the start position to the end positione 
            for char in string[start:end]:
              if char in self.trans_map:
                self._write(self.trans_map[char],HD44780.RS)
              else:
                self._write(ord(char),HD44780.RS)

            # Update the new start and end positon as we reached the lmit of the line
            start = start + 16
            if end + 16 <= len(string):
                end = end + 16
            else:
                end = len(string)
                
            
    else:
        
        # Single Line
        self._write(HD44780.LINE[line-1])
        for char in string:
          if char in self.trans_map:
            self._write(self.trans_map[char],HD44780.RS)
          else:
            self._write(ord(char),HD44780.RS)
        
    

  # --- clear the LCD and move cursor to home   -------------------------------

  def clear(self):
    self._write(HD44780.CLEARDISPLAY)
    self._write(HD44780.RETURNHOME)

  # --- write a command to lcd   --------------------------------------------
  
  def _write(self, cmd, mode=0):
    self._write_four_bits(mode | (cmd & 0xF0))
    self._write_four_bits(mode | ((cmd << 4) & 0xF0))

  # --- write four bits   ---------------------------------------------------
  
  def _write_four_bits(self, data):
    self._write_to_i2c(data | HD44780.BACKLIGHT)
    self._strobe(data)

  # --- clocks EN to latch command   -----------------------------------------
  
  def _strobe(self, data):
    self._write_to_i2c(data | HD44780.EN | HD44780.BACKLIGHT)
    time.sleep(.01)
    self._write_to_i2c(((data & ~HD44780.EN) | HD44780.BACKLIGHT))
    time.sleep(.01)

  # --- write data to the bus   ----------------------------------------------

  def _write_to_i2c(self,data):
    data_array = bytearray(1)
    data_array[0] = data
    self.i2c.writeto(0x27,data_array)
    time.sleep(0.001)


