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
# mpy-cross -O3 -s neosprite.py neosprite_24bpp_neopixel_rgb.py

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/aaronaverill/CircuitPython_neosprite.git"

import gc

PixelLayout_NeoPixel_RGB = b'\x00\x01\x02\xFF\xFF'
PixelLayout_NeoPixel_GRB = b'\x01\x00\x02\xFF\xFF'

def toInt(bytes):
  value = 0
  shift = 0
  for byte in bytes:
    value += byte << shift
    shift = shift + 8
    
  if value & 0x80000000 == 0x80000000:
    return -(value & 0x80000000) + (value & ~0x80000000)
  else:
    return value

class BmpSprite_24bpp_NeoPixel_RGB(object):
  def open(filename):
    fp = open(filename, 'rb')
    im = BmpSprite_24bpp_NeoPixel_RGB(fp)
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
    self.offset = [0, 0]
    self.size = [self.bitmapWidth, self.bitmapHeight]
  
  def _read(self, fp):
    fp.seek(0x0A)
    pixelArrayOffset = toInt(fp.read(4))
    fp.seek(0x12)
    self.bitmapWidth = toInt(fp.read(4))
    self.bitmapHeight = toInt(fp.read(4))
    self.topToBottom = self.bitmapHeight < 0
    self.bitmapHeight = abs(self.bitmapHeight)
    self.bitmapRowBytes = int((24 * self.bitmapWidth + 31)/32) <<2
    pixelArraySize = self.bitmapRowBytes * self.bitmapHeight
    fp.seek(pixelArrayOffset)
    self.pixelArrayData = bytearray(fp.read(pixelArraySize))
    
    if __debug__:
      fp.seek(0x0E)
      dibHeaderSize = toInt(fp.read(4))
      fp.seek(0x1C)
      bitsPerPixel = toInt(fp.read(2))
      bitmapCompression = toInt(fp.read(4))
      if dibHeaderSize != 40:
        raise ValueError('Cannot read bitmap header type = ' + str(dibHeaderSize))
      if bitmapCompression != 0:
        raise ValueError('Cannot read compression type = ' + str(bitmapCompression))
      if bitsPerPixel != 24:
        raise ValueError('Cannot read ' + str(bitsPerPixel) + ' bits per pixel')
    
  def transformRgb(self, transform):
    data = self.pixelArrayData
    rows = range(0,self.bitmapHeight)
    cols = range(0,self.bitmapWidth)
    bitmapRowBytes = self.bitmapRowBytes
    
    for row in rows:
      for col in cols:
        i = row * bitmapRowBytes + col * 3
        rgb = transform((data[i+2], data[i+1], data[i]))
        for p in range(len(rgb)):
          data[i+2-p] = rgb[p]
          
  def fillBuffer(self, buffer, channels = b'\x01\x00\x02', pixelRange = None):
    if __debug__:
      if channels not in [b'\x01\x00\x02', b'\x00\x01\x02\xFF\xFF', b'\x01\x00\x02\xFF\xFF']:
        raise ValueError('Invalid channels type.')
        
    bufferLen = len(buffer)
    bufferBytesPerPixel = len(channels)
    if pixelRange is None:
      pixelRange = (0, int(bufferLen / bufferBytesPerPixel) - 1)

    if self.topToBottom:
      rows = range(self.offset[1], self.offset[1] + self.size[1])
    else:
      rows = range(self.bitmapHeight - self.offset[1] - 1, self.bitmapHeight - self.offset[1] - self.size[1] - 1, -1)
    cols = range(self.offset[0], self.offset[0] + self.size[0])
    
    bufferPos = pixelRange[0] * bufferBytesPerPixel
    bufferEndPos = pixelRange[1] * bufferBytesPerPixel
    
    while True:
      for row in rows:
        pixelPos = row * self.bitmapRowBytes + cols[0] * 3
        for col in cols:
          # Extract the r, g, b data directly from the pixel array data
          r = self.pixelArrayData[pixelPos+2]
          g = self.pixelArrayData[pixelPos+1]
          b = self.pixelArrayData[pixelPos]
          
          # Copy the r,g,b data into the buffer
          # This inner loop code is repeated to avoid function call overhead
          buffer[bufferPos+channels[0]] = r
          buffer[bufferPos+channels[1]] = g
          buffer[bufferPos+channels[2]] = b
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
          pixelPos += 3
    
    return buffer
