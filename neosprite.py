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

# Minimize with:
# https://liftoff.github.io/pyminifier/pyminifier.html
# Compile with:
# mpy-cross -O3 -s neosprite.py neosprite.py

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

PixelLayout_NeoPixel_RGB = b'\x00\x01\x02\xFF\xFF'
PixelLayout_NeoPixel_GRB = b'\x01\x00\x02\xFF\xFF'
PixelLayout_NeoPixel_RGBW = b'\x00\x01\x02\x03\xFF'
PixelLayout_NeoPixel_GRBW = b'\x01\x00\x02\x03\xFF'

PixelLayout_DotStar_RGBA = b'\x01\x02\x03\xFF\x00'
PixelLayout_DotStar_RBGA = b'\x01\x03\x02\xFF\x00'
PixelLayout_DotStar_GRBA = b'\x02\x01\x03\xFF\x00'
PixelLayout_DotStar_GBRA = b'\x02\x03\x01\xFF\x00'
PixelLayout_DotStar_BRGA = b'\x03\x01\x02\xFF\x00'
PixelLayout_DotStar_BGRA = b'\x03\x02\x01\xFF\x00'

# Declare a python function to convert an array of bytes into a 2 byte integer
# This code avoids the use of the struct module which is quite large
# Replaces struct.unpack("<i"). Silly!
def toInt(bytes):
  value = bytes[0] + (bytes[1] << 8)
  if len(bytes) == 4 and (bytes[3] & 0x80):
    if __debug__:
      raise ValueError('Cannot read top to bottom bitmap.')
    else:
      raise ValueError(4)
  return value
  
class BmpSprite(object):
  """A sprite sourced from a BMP file"""
  
  def open(filename):
    fp = open(filename, 'rb')
    im = BmpSprite(fp)
    fp.close()
    fp = None
    gc.collect()
    return im

  def __init__(self, fp):
    fp.seek(0x00)
    fileType = fp.read(2)
    if fileType != b'BM':
      if __debug__:
        raise ValueError('Not a bitmap file.')
      else:
        raise ValueError(0)
    
    self._read(fp)
    self.size = [self.bitmapWidth, self.bitmapHeight]
    self.offset = [0, 0]
      
  def _read(self, fp):
    fp.seek(0x0A)
    pixelArrayOffset = toInt(fp.read(4))
    dibHeaderSize = toInt(fp.read(4))
    self.bitmapWidth = toInt(fp.read(4))
    self.bitmapHeight = toInt(fp.read(4))
    self._topToBottom = self.bitmapHeight < 0
    self.bitmapHeight = abs(self.bitmapHeight)
    fp.seek(0x1C)
    self._bitsPerPixel = toInt(fp.read(2))
    bitmapCompression = toInt(fp.read(4))
    
    if self._bitsPerPixel >= 24:
      self.palette = None
      self.byteFillStrategy = self._f24
      self.transformRgb = self._t24
    else:
      fp.seek(0x2E)
      paletteSize = toInt(fp.read(4))
      if paletteSize == 0:
        paletteSize = 1 << self._bitsPerPixel
      fp.seek(14 + dibHeaderSize)
      # We only need the blue, green, red bytes from the palette, toss every 4th byte.
      self.palette = bytearray(paletteSize * 3)
      for i in range(0, paletteSize*3, 3):
        self.palette[i : (i + 3)] = fp.read(3)
        fp.seek(1, 1)
    
      self.byteFillStrategy = self._fP
      self.transformRgb = self._tP

    if self._bitsPerPixel < 8:
      self._bitmapBytesPerCol = self._bitsPerPixel / 8
    else:
      self._bitmapBytesPerCol = int(self._bitsPerPixel / 8)
    
    self._bitmapRowBytes = int((self._bitsPerPixel * self.bitmapWidth + 31)/32) << 2
    pixelArraySize = self._bitmapRowBytes * self.bitmapHeight
    fp.seek(pixelArrayOffset)
    self.pixelArrayData = bytearray(fp.read(pixelArraySize))
    
    if dibHeaderSize != 40:
      if __debug__:
        raise ValueError('Cannot read bitmap header type = ' + str(dibHeaderSize))
      else:
        raise ValueError(1)
    if bitmapCompression != 0:
      if __debug__:
        raise ValueError('Cannot read compression type = ' + str(bitmapCompression))
      else:
        raise ValueError(2)
    if self._bitsPerPixel not in [32, 24, 8, 4, 1]:
      if __debug__:
        raise ValueError('Cannot read ' + str(self._bitsPerPixel) + ' bits per pixel')
      else:
        raise ValueError(3)
        
  
  def fillBuffer(self, buffer, channels = PixelLayout_NeoPixel_GRB, blend = None, pixelRange = None, bufferByteStart = 0):
    if blend is not None:
      blend = max(0, min(1, blend))
    
    if pixelRange is None:
      bufferLen = len(buffer)
      bufferBytesPerPixel = 4 if channels[3] != 0xFF or channels[4] != 0XFF else 3
      pixelRange = (0, int(bufferLen / bufferBytesPerPixel) - 1)

    if self._topToBottom:
      rows = range(self.offset[1], self.offset[1] + self.size[1])
    else:
      rows = range(self.bitmapHeight - self.offset[1] - 1, self.bitmapHeight - self.offset[1] - self.size[1] - 1, -1)
    cols = range(self.offset[0], self.offset[0] + self.size[0])
    
    self.byteFillStrategy(rows, cols, buffer, channels, blend, pixelRange, bufferByteStart)
      
    return buffer

  def _f24(self, rows, cols, buffer, channels, blend, pixelRange, bufferByteStart):
    bufferBytesPerPixel = 4 if channels[3] != 0xFF or channels[4] != 0XFF else 3
    hasWhite = channels[3] != 0xFF
    hasAlpha = channels[4] != 0XFF
    bufferPos = bufferByteStart + pixelRange[0] * bufferBytesPerPixel
    bufferEndPos = bufferByteStart + pixelRange[1] * bufferBytesPerPixel
    bufferLen = len(buffer)
    
    while True:
      for row in rows:
        pixelPos = row * self._bitmapRowBytes + cols[0] * self._bitmapBytesPerCol
        for col in cols:
          # Extract the r, g, b data directly from the pixel array data
          r = self.pixelArrayData[pixelPos+2]
          g = self.pixelArrayData[pixelPos+1]
          b = self.pixelArrayData[pixelPos]
          
          # Copy the r,g,b data into the buffer
          if hasWhite:
            w = 0
            if r == g and g == b:
              w = r
              r = g = b = 0
            if blend is not None:
              w = int(w * blend + (buffer[bufferPos+channels[3]] * (1 - blend)))
            buffer[bufferPos+channels[3]] = w
          elif hasAlpha:
            buffer[bufferPos+channels[3]] = 0xFF
            
          if blend is not None:
            r = int(r * blend + (buffer[bufferPos+channels[0]] * (1 - blend)))
            g = int(g * blend + (buffer[bufferPos+channels[1]] * (1 - blend)))
            b = int(b * blend + (buffer[bufferPos+channels[2]] * (1 - blend)))
              
          buffer[bufferPos+channels[0]] = r
          buffer[bufferPos+channels[1]] = g
          buffer[bufferPos+channels[2]] = b
          
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
          pixelPos += self._bitmapBytesPerCol
    
  def _t24(self, transform):
    data = self.pixelArrayData
    rgbBytes = self._bitmapBytesPerCol
    for row in range(0,self.bitmapHeight):
      for col in range(0,self.bitmapWidth):
        i = row * self._bitmapRowBytes + col * rgbBytes
        rgb = transform((data[i+2], data[i+1], data[i]))
        for p in range(len(rgb)):
          data[i+2-p] = rgb[p]
            
  def _fP(self, rows, cols, buffer, channels, blend, pixelRange, bufferByteStart):
    bufferBytesPerPixel = 4 if channels[3] != 0xFF or channels[4] != 0XFF else 3
    hasWhite = channels[3] != 0xFF
    hasAlpha = channels[4] != 0XFF
    bufferPos = bufferByteStart + pixelRange[0] * bufferBytesPerPixel
    bufferEndPos = bufferByteStart + pixelRange[1] * bufferBytesPerPixel
    bufferLen = len(buffer)
    
    bpp = self._bitsPerPixel
    leftShift = int((8 / bpp) - 1)
    modulo = int(8 / bpp)
    bitMask = 2**bpp - 1
    colOffset = cols[0] % modulo
    colByteStart = int(cols[0] * self._bitmapBytesPerCol)
    
    while True:
      for row in rows:
        colByte = colOffset
        pixelPos = row * self._bitmapRowBytes + colByteStart
        for col in cols:
          if bpp == 8:
            iPalette = self.pixelArrayData[pixelPos]
            pixelPos += 1
          else:  
            # Extract the palette position from the pixel array data
            # Sub-byte pixel data needs to be bit shifted and masked to get the position
            # There's probably a more efficient way to do this but I'm bad at math and this confuses me
            bitshift = bpp * (leftShift - colByte)
            iPalette = (self.pixelArrayData[pixelPos] & (bitMask << bitshift)) >> bitshift
            colByte += 1
            if colByte >= modulo:
              colByte = 0
              pixelPos += 1
          
          iPalette *= 3
          # Extract the r, g, b data from the palette byte offset
          r = self.palette[iPalette+2]
          g = self.palette[iPalette+1]
          b = self.palette[iPalette]
          
          # Copy the r,g,b data into the buffer
          if hasWhite:
            w = 0
            if r == g and g == b:
              w = r
              r = g = b = 0
            if blend is not None:
              w = int(w * blend + (buffer[bufferPos+channels[3]] * (1 - blend)))
            buffer[bufferPos+channels[3]] = w
          elif hasAlpha:
            buffer[bufferPos+channels[3]] = 0xFF

          if blend is not None:
            r = int(r * blend + (buffer[bufferPos+channels[0]] * (1 - blend)))
            g = int(g * blend + (buffer[bufferPos+channels[1]] * (1 - blend)))
            b = int(b * blend + (buffer[bufferPos+channels[2]] * (1 - blend)))

          buffer[bufferPos+channels[0]] = r
          buffer[bufferPos+channels[1]] = g
          buffer[bufferPos+channels[2]] = b
          
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
    
  def _tP(self, transform):
    data = self.palette
    rgbBytes = 3
    for i in range(0, len(data), rgbBytes):
      rgb = transform((data[i+2], data[i+1], data[i]))
      for p in range(len(rgb)):
        data[i+2-p] = rgb[p]