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

import array
import gc
import math
import ustruct

class PixelLayout(object):
  NeoPixel_RGB = 1
  NeoPixel_GRB = 2
  NeoPixel_RGBW = 3
  NeoPixel_GRBW = 4
  
  DotStar_RGBA = 5
  DotStar_RBGA = 6
  DotStar_GRBA = 7
  DotStar_GBRA = 8
  DotStar_BRGA = 9
  DotStar_BGRA = 10
  
  channelInfo = {
    NeoPixel_RGB: (0, 1, 2),
    NeoPixel_GRB: (1, 0, 2),
    NeoPixel_RGBW: (0, 1, 2, 3),
    NeoPixel_GRBW: (1, 0, 2, 3),
    DotStar_RGBA: (1, 2, 3, 0),
    DotStar_RBGA: (1, 3, 2, 0),
    DotStar_GRBA: (2, 1, 3, 0),
    DotStar_GBRA: (2, 3, 1, 0),
    DotStar_BRGA: (3, 1, 2, 0),
    DotStar_BGRA: (3, 2, 1, 0),
  }
  
  whiteLayouts = [NeoPixel_RGBW, NeoPixel_GRBW]
  alphaLayouts = [DotStar_RGBA, DotStar_RBGA, DotStar_GRBA, DotStar_GBRA, DotStar_BRGA, DotStar_BGRA]
  
class Sprite(object):
  def open(filename):
    fp = open(filename, 'rb')
    
    # Only BMP sprites are supported for now
    im = BmpSprite(fp)
    fp.close()
    fp = None
    gc.collect()
    return im

class BmpSprite(object):
  """A sprite sourced from a BMP file"""
  
  def __init__(self, fp):
    fp.seek(0x00)
    fileType = fp.read(2)
    if fileType != b'BM':
      raise ValueError('Not a bitmap file.')
    
    self._readFile(fp)
          
    self.size = [self.bitmapWidth, self.bitmapHeight]
    self.offset = [0, 0]
    
    self.byteFillStrategy = getattr(self, '_fillBytes_' + str(self.bitsPerPixel))
      
  def _readFile(self, fp):
    fp.seek(0x0A)
    pixelArrayOffset = ustruct.unpack('<i', fp.read(4))[0]
    dibHeaderSize = ustruct.unpack('<i', fp.read(4))[0]
    self.bitmapWidth = ustruct.unpack('<i', fp.read(4))[0]
    self.bitmapHeight = ustruct.unpack('<i', fp.read(4))[0]
    self.topToBottom = self.bitmapHeight < 0
    self.bitmapHeight = abs(self.bitmapHeight)
    fp.seek(0x1C)
    self.bitsPerPixel = ustruct.unpack('<i', fp.read(2))[0]
    bitmapCompression = ustruct.unpack('<i', fp.read(4))[0]
    if self.bitsPerPixel < 24:
      fp.seek(0x2E)
      paletteSize = ustruct.unpack('<i', fp.read(4))[0]
      if paletteSize == 0:
        paletteSize = 2 ** self.bitsPerPixel
      fp.seek(14 + dibHeaderSize)
      self.palette = bytearray(fp.read(paletteSize*4))
    else:
      self.palette = None
    self.bitmapRowBytes = math.floor((self.bitsPerPixel * self.bitmapWidth + 31)/32) * 4
    self.bitmapBytesPerCol = self.bitsPerPixel / 8
    if self.bitsPerPixel % 8 == 0:
      self.bitmapBytesPerCol = int(self.bitmapBytesPerCol)
    pixelArraySize = self.bitmapRowBytes * self.bitmapHeight
    fp.seek(pixelArrayOffset)
    self.pixelArrayData = bytearray(fp.read(pixelArraySize))
    
    if dibHeaderSize != 40:
      raise ValueError('Cannot read bitmap header type = ' + str(dibHeaderSize))
    if bitmapCompression != 0:
      raise ValueError('Cannot read compression type = ' + str(bitmapCompression))
    if self.bitsPerPixel not in [32, 24, 8, 4, 1]:
      raise ValueError('Cannot read ' + str(self.bitsPerPixel) + ' bits per pixel')
  
  def transformRgb(self, transform):
    if self.palette is None:
      data = self.pixelArrayData
      rgbBytes = int(self.bitsPerPixel / 8)
    else:
      data = self.palette
      rgbBytes = 4
      
    # Check if the pixel array data is aligned 
    if self.palette is None and self.bitmapRowBytes % rgbBytes != 0:
      for row in range(0,self.bitmapHeight):
        for col in range(0,self.bitmapWidth):
          i = row * self.bitmapRowBytes + col * self.bitmapBytesPerCol
          rgb = transform((data[i+2], data[i+1], data[i]))
          for p in range(len(rgb)):
            data[i+2-p] = rgb[p]
    else:
      for i in range(0, len(data), rgbBytes):
        rgb = transform((data[i+2], data[i+1], data[i]))
        for p in range(len(rgb)):
          data[i+2-p] = rgb[p]

  def getPixelByteArray(self, channels = None, pixelRange = None, bufferByteStart = 0):
    if channels is None:
      channels = PixelLayout.NeoPixel_GRB
    
    bufferBytesPerPixel = len(PixelLayout.channelInfo[channels])
    buffer = bytearray(bufferBytesPerPixel * self.size[0] * self.size[1])
    self.fillPixelBytes(buffer, channels, pixelRange, bufferByteStart)
    return buffer
  
  def fillPixelBytes(self, buffer, channels = None, pixelRange = None, bufferByteStart = 0):
    if channels is None:
      channels = PixelLayout.NeoPixel_GRB

    if pixelRange is None:
      bufferLen = len(buffer)
      bufferBytesPerPixel = len(PixelLayout.channelInfo[channels])
      pixelRange = (0, int(bufferLen / bufferBytesPerPixel) - 1)

    if self.topToBottom:
      rows = range(self.offset[1], self.offset[1] + self.size[1])
    else:
      rows = range(self.bitmapHeight - self.offset[1] - 1, self.bitmapHeight - self.offset[1] - self.size[1] - 1, -1)
    cols = range(self.offset[0], self.offset[0] + self.size[0])
    
    self.byteFillStrategy(rows, cols, buffer, channels, pixelRange, bufferByteStart)
      
    return buffer

  def _fillBytes_32(self, rows, cols, buffer, channels, pixelRange, bufferByteStart):
    self._fillBytes_24(rows, cols, buffer, channels, pixelRange, bufferByteStart)
    
  def _fillBytes_24(self, rows, cols, buffer, channels, pixelRange, bufferByteStart):
    channelOffsets, bufferBytesPerPixel, hasWhite, hasAlpha = self._getChannelInfo(channels)
    bufferPos, bufferEndPos, bufferLen = self._getByteRangeInfo(buffer, bufferByteStart, bufferBytesPerPixel, pixelRange)
    
    while True:
      for row in rows:
        pixelPos = row * self.bitmapRowBytes + cols[0] * self.bitmapBytesPerCol
        for col in cols:
          # Extract the r, g, b data directly from the pixel array data
          r = self.pixelArrayData[pixelPos+2]
          g = self.pixelArrayData[pixelPos+1]
          b = self.pixelArrayData[pixelPos]
          
          # Copy the r,g,b data into the buffer
          # This inner loop code is repeated to avoid function call overhead
          if hasWhite:
            w = 0
            if r == g and g == b:
              w = r
              r = g = b = 0
            buffer[bufferPos+channelOffsets[3]] = w
          elif hasAlpha:
            buffer[bufferPos+channelOffsets[3]] = 0xFF
          buffer[bufferPos+channelOffsets[0]] = r
          buffer[bufferPos+channelOffsets[1]] = g
          buffer[bufferPos+channelOffsets[2]] = b
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
          pixelPos += self.bitmapBytesPerCol
  
  def _fillBytes_8(self, rows, cols, buffer, channels, pixelRange, bufferByteStart):
    channelOffsets, bufferBytesPerPixel, hasWhite, hasAlpha = self._getChannelInfo(channels)
    bufferPos, bufferEndPos, bufferLen = self._getByteRangeInfo(buffer, bufferByteStart, bufferBytesPerPixel, pixelRange)
    
    while True:
      for row in rows:
        pixelPos = row * self.bitmapRowBytes + cols[0]
        for col in cols:
          # Extract the palette position from the pixel array data
          # Palette entries are always 4 bytes so the position is left shifted twice to get the byte offset
          iPalette = self.pixelArrayData[pixelPos] << 2
          # Extract the r, g, b data from the palette byte offset
          r = self.palette[iPalette+2]
          g = self.palette[iPalette+1]
          b = self.palette[iPalette]
          
          # Copy the r,g,b data into the buffer
          # This inner loop code is repeated to avoid function call overhead
          if hasWhite:
            w = 0
            if r == g and g == b:
              w = r
              r = g = b = 0
            buffer[bufferPos+channelOffsets[3]] = w
          elif hasAlpha:
            buffer[bufferPos+channelOffsets[3]] = 0xFF
          buffer[bufferPos+channelOffsets[0]] = r
          buffer[bufferPos+channelOffsets[1]] = g
          buffer[bufferPos+channelOffsets[2]] = b
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
          pixelPos += self.bitmapBytesPerCol
    
  def _fillBytes_4(self, rows, cols, buffer, channels, pixelRange, bufferByteStart):
    self._fillBytes_Palette(4, rows, cols, buffer, channels, pixelRange, bufferByteStart)
  
  def _fillBytes_1(self, rows, cols, buffer, channels, pixelRange, bufferByteStart):
    self._fillBytes_Palette(1, rows, cols, buffer, channels, pixelRange, bufferByteStart)
  
  def _fillBytes_Palette(self, bpp, rows, cols, buffer, channels, pixelRange, bufferByteStart):
    channelOffsets, bufferBytesPerPixel, hasWhite, hasAlpha = self._getChannelInfo(channels)
    bufferPos, bufferEndPos, bufferLen = self._getByteRangeInfo(buffer, bufferByteStart, bufferBytesPerPixel, pixelRange)
    
    leftShift = int((8 / bpp) - 1)
    modulo = int(8 / bpp)
    bitMask = 2**bpp - 1
    
    while True:
      for row in rows:
        for col in cols:
          # Extract the palette position from the pixel array data
          # Sub-byte pixel data needs to be bit shifted and masked to get the position
          # There's probably a more efficient way to do this but I'm bad at math and this confuses me
          bitshift = bpp * (leftShift - (col % modulo))
          pixelPos = int(row * self.bitmapRowBytes + col * self.bitmapBytesPerCol)
          iPalette = ((self.pixelArrayData[pixelPos] & (bitMask << bitshift)) >> bitshift) << 2
          # Extract the r, g, b data from the palette byte offset
          r = self.palette[iPalette+2]
          g = self.palette[iPalette+1]
          b = self.palette[iPalette]
          
          # Copy the r,g,b data into the buffer
          # This inner loop code is repeated to avoid function call overhead
          if hasWhite:
            w = 0
            if r == g and g == b:
              w = r
              r = g = b = 0
            buffer[bufferPos+channelOffsets[3]] = w
          elif hasAlpha:
            buffer[bufferPos+channelOffsets[3]] = 0xFF
          buffer[bufferPos+channelOffsets[0]] = r
          buffer[bufferPos+channelOffsets[1]] = g
          buffer[bufferPos+channelOffsets[2]] = b
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
    
  def _getChannelInfo(self, channels):
    offsets = PixelLayout.channelInfo[channels]
    bpp = len(offsets)
    hasWhite = False
    hasAlpha = False
    if channels in PixelLayout.whiteLayouts:
      hasWhite = True
    elif channels in PixelLayout.alphaLayouts:
      hasAlpha = True
    return (offsets, bpp, hasWhite, hasAlpha)
    
  def _getByteRangeInfo(self, buffer, bufferByteStart, bufferBytesPerPixel, pixelRange):
    return (bufferByteStart + pixelRange[0] * bufferBytesPerPixel, bufferByteStart + pixelRange[1] * bufferBytesPerPixel, len(buffer)) 
