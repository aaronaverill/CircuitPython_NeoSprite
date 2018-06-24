# The MIT License (MIT)
#
# Copyright (c) 2018 Aaron Averill
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`neosprite`
====================================================

.. todo:: Describe what the module does

* Author(s): Aaron Averill

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s). Use unordered list & hyperlink rST
   inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
  
.. todo:: Uncomment or remove the Bus Device and/or the Register library dependencies based on the library's use of either.

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/aaronaverill/CircuitPython_neosprite.git"

import math
import ustruct

class BmpSprite(object):
  """A sprite sourced from a BMP file"""
  
  def __init__(self, fp):
    self.data = fp.read()
    
    if self.data[0x00:0x02] != b'BM':
      raise ValueError('Not a bitmap file.')
      
    self.pixelArrayOffset = ustruct.unpack('<i', self.data[0x0A:0x0E])[0]
    self.dibHeaderSize = ustruct.unpack('<i', self.data[0x0E:0x12])[0]
    self.bitmapWidth = ustruct.unpack('<i', self.data[0x12:0x16])[0]
    self.bitmapHeight = ustruct.unpack('<i', self.data[0x16:0x1A])[0]
    self.topToBottom = self.bitmapHeight < 0
    self.bitmapHeight = abs(self.bitmapHeight)
    self.bitsPerPixel = ustruct.unpack('<i', self.data[0x1C:0x1E])[0]
    self.bitmapCompression = ustruct.unpack('<i', self.data[0x1E:0x22])[0]
    if self.bitsPerPixel < 24:
      self.paletteSize = ustruct.unpack('<i', self.data[0x2E:0x32])[0]
      if self.paletteSize == 0:
        self.paletteSize = 2 ** self.bitsPerPixel
      self.paletteOffset = 14 + self.dibHeaderSize
    self.bitmapRowBytes = math.floor((self.bitsPerPixel * self.bitmapWidth + 31)/32) * 4
    self.bitmapBytesPerCol = self.bitsPerPixel / 8
    if self.bitsPerPixel % 8 == 0:
      self.bitmapBytesPerCol = int(self.bitmapBytesPerCol)
    self.size = [self.bitmapWidth, self.bitmapHeight]
    self.offset = [0, 0]
    self.fillRgbFunc = getattr(self, '__fillRgbMatrix_' + str(self.bitsPerPixel))
        
    if self.dibHeaderSize != 40:
      raise ValueError('Cannot read bitmap header type = ' + str(self.dibHeaderSize))
    if self.bitmapCompression != 0:
      raise ValueError('Cannot read compression type = ' + str(self.bitmapCompression))
    if self.bitsPerPixel not in [32, 24, 8, 4, 1]:
      raise ValueError('Cannot read ' + str(self.bitsPerPixel) + ' bits per pixel')

  def getRgbMatrix(self):
    """Return a two dimensional array of RGB tuples from the sprite region"""
    matrix = [[[0,0,0] for c in range(self.size[0])] for r in range(self.size[1])]
      
    if self.topToBottom:
      rows = range(self.offset[1], self.offset[1] + self.size[1])
    else:
      rows = range(self.bitmapHeight - self.offset[1] - 1, self.bitmapHeight - self.offset[1] - self.size[1] - 1, -1)
    cols = range(self.offset[0], self.offset[0] + self.size[0])
    
    # Delegate to the speific bits per pixel function to fill the RGB matrix
    self.fillRgbFunc(matrix, rows, cols)

    return matrix
  
  def __fillRgbMatrix_32(self, matrix, rows, cols):
    self.__fillRgbMatrix_24(matrix, rows, cols)
  
  def __fillRgbMatrix_24(self, matrix, rows, cols):
    y = 0
    for row in rows:
      x = 0
      for col in cols:
        i = self.pixelArrayOffset + row * self.bitmapRowBytes + col * self.bitmapBytesPerCol
        matrix[y][x] = [self.data[i+2], self.data[i+1], self.data[i]]
        x += 1
      y += 1
  
  def __fillRgbMatrix_8(self, matrix, rows, cols):
    y = 0
    for row in rows:
      x = 0
      for col in cols:
        i = self.pixelArrayOffset + row * self.bitmapRowBytes + col * self.bitmapBytesPerCol
        i = self.paletteOffset + self.data[i] * 4
        matrix[y][x] = [self.data[i+2], self.data[i+1], self.data[i]]
        x += 1
      y += 1

  def __fillRgbMatrix_4(self, matrix, rows, cols):
    self.__fillRgbMatrix_palette(matrix, rows, cols, 4)

  def __fillRgbMatrix_1(self, matrix, rows, cols):
    self.__fillRgbMatrix_palette(matrix, rows, cols, 1)

  def __fillRgbMatrix_palette(self, matrix, rows, cols, bpp):
    leftShift = int((8 / bpp) - 1)
    modulo = int(8 / bpp)
    bitMask = 2**bpp - 1
    y = 0
    for row in rows:
      x = 0
      for col in cols:
        bitshift = bpp * (leftShift - (col % modulo))
        i = int(self.pixelArrayOffset + row * self.bitmapRowBytes + col * self.bitmapBytesPerCol)
        i = (self.data[i] & (bitMask << bitshift)) >> bitshift
        i = self.paletteOffset + i * 4
        matrix[y][x] = [self.data[i+2], self.data[i+1], self.data[i]]
        x += 1
      y += 1
  
class Sprite(object):
  def open(filename):
    fp = open(filename, 'rb')
    
    # Only BMP sprites are supported for now
    im = BmpSprite(fp)
    fp.close()
    return im

class PixelStrip(object):
  """A NeoPixel strip segment"""
  
  def __init__(self, neopixels):
    self.neopixels = neopixels
    self.range = [0, len(neopixels) - 1]
  
  def show(self, rgb):
    self.__setPixels(rgb)
    self.neopixels.show()

  def __setPixels(self, rgb):
    iFrom = abs(self.range[0])
    iTo = abs(self.range[1])
    if iFrom == iTo:
      return
    pixelLen = len(self.neopixels)
    rows = range(0, len(rgb))
    cols = range(0, len(rgb[0]))
    i = iFrom
    while True:
      for row in rows:
        for col in cols: 
          self.neopixels[i] = rgb[row][col]
          if i == iTo:
            return
          i += 1
          if i >= pixelLen:
            i = 0
