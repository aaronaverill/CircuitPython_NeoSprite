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

import gc
import math
import ustruct

class BmpSprite(object):
  """A sprite sourced from a BMP file"""
  
  def __init__(self, fp):
    fp.seek(0x00)
    fileType = fp.read(2)
    if fileType != b'BM':
      raise ValueError('Not a bitmap file.')
    
    fp.seek(0x0A)
    pixelArrayOffset = ustruct.unpack('<i', fp.read(4))[0]
    dibHeaderSize = ustruct.unpack('<i', fp.read(4))[0]
    self.bitmapWidth = ustruct.unpack('<i', fp.read(4))[0]
    self.bitmapHeight = ustruct.unpack('<i', fp.read(4))[0]
    self.topToBottom = self.bitmapHeight < 0
    self.bitmapHeight = abs(self.bitmapHeight)
    fp.seek(0x1C)
    bitsPerPixel = ustruct.unpack('<i', fp.read(2))[0]
    bitmapCompression = ustruct.unpack('<i', fp.read(4))[0]
    fp.seek(pixelArrayOffset)
    self.pixelArrayData = fp.read()
    if bitsPerPixel < 24:
      fp.seek(0x2E)
      paletteSize = ustruct.unpack('<i', fp.read(4))[0]
      if paletteSize == 0:
        paletteSize = 2 ** bitsPerPixel
      fp.seek(14 + dibHeaderSize)
      self.palette = bytearray(fp.read(paletteSize*4))
    self.bitmapRowBytes = math.floor((bitsPerPixel * self.bitmapWidth + 31)/32) * 4
    self.bitmapBytesPerCol = bitsPerPixel / 8
    if bitsPerPixel % 8 == 0:
      self.bitmapBytesPerCol = int(self.bitmapBytesPerCol)
    self.size = [self.bitmapWidth, self.bitmapHeight]
    self.offset = [0, 0]
    self.fillRgbFunc = getattr(self, '__fillRgbMatrix_' + str(bitsPerPixel))
        
    if dibHeaderSize != 40:
      raise ValueError('Cannot read bitmap header type = ' + str(dibHeaderSize))
    if bitmapCompression != 0:
      raise ValueError('Cannot read compression type = ' + str(bitmapCompression))
    if bitsPerPixel not in [32, 24, 8, 4, 1]:
      raise ValueError('Cannot read ' + str(bitsPerPixel) + ' bits per pixel')

  def getRgbMatrix(self):
    """Return a two dimensional array of RGB tuples from the sprite region"""
    matrix = [[0 for c in range(self.size[0])] for r in range(self.size[1])]
      
    if self.topToBottom:
      rows = range(self.offset[1], self.offset[1] + self.size[1])
    else:
      rows = range(self.bitmapHeight - self.offset[1] - 1, self.bitmapHeight - self.offset[1] - self.size[1] - 1, -1)
    cols = range(self.offset[0], self.offset[0] + self.size[0])
    
    # Delegate to the specific bits per pixel function to fill the RGB matrix
    self.fillRgbFunc(matrix, rows, cols)

    return matrix
  
  def __fillRgbMatrix_32(self, matrix, rows, cols):
    self.__fillRgbMatrix_24(matrix, rows, cols)
  
  def __fillRgbMatrix_24(self, matrix, rows, cols):
    y = 0
    for row in rows:
      x = 0
      for col in cols:
        i = row * self.bitmapRowBytes + col * self.bitmapBytesPerCol
        #matrix[y][x] = self.pixelArrayData[i+2]
        #matrix[y][x] = matrix[y][x] * 256 + self.pixelArrayData[i+1]
        #matrix[y][x] = matrix[y][x] * 256 + self.pixelArrayData[i]
        matrix[y][x] = (((int(self.pixelArrayData[i+2]) << 8) | int(self.pixelArrayData[i+1])) << 8) | int(self.pixelArrayData[i])
        x += 1
      y += 1
  
  def __fillRgbMatrix_8(self, matrix, rows, cols):
    y = 0
    for row in rows:
      x = 0
      for col in cols:
        i = row * self.bitmapRowBytes + col * self.bitmapBytesPerCol
        i = self.pixelArrayData[i] * 4
        matrix[y][x] = (((int(self.palette[i+2]) << 8) | int(self.palette[i+1])) << 8) | int(self.palette[i])
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
        i = int(row * self.bitmapRowBytes + col * self.bitmapBytesPerCol)
        i = (self.pixelArrayData[i] & (bitMask << bitshift)) >> bitshift
        i *= 4
        matrix[y][x] = (((int(self.palette[i+2]) << 8) | int(self.palette[i+1])) << 8) | int(self.palette[i])
        x += 1
      y += 1
  
class Sprite(object):
  def open(filename):
    fp = open(filename, 'rb')
    
    # Only BMP sprites are supported for now
    im = BmpSprite(fp)
    fp.close()
    fp = None
    gc.collect()
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
