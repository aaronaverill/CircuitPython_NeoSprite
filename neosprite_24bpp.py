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

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/aaronaverill/CircuitPython_neosprite.git"

import gc
import ustruct

class PixelLayout(object):
  NeoPixel_RGB = 1
  NeoPixel_GRB = 2
  
  channelInfo = {
    NeoPixel_RGB: (0, 1, 2),
    NeoPixel_GRB: (1, 0, 2),
  }
  
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
  def __init__(self, fp):
    self._readFile(fp)
    self.size = [self.bitmapWidth, self.bitmapHeight]
    self.offset = [0, 0]
      
  def _readFile(self, fp):
    err = 'Invalid bitmap.'
    fp.seek(0x00)
    fileType = fp.read(2)
    if fileType != b'BM':
      raise ValueError(err)
      
    ui = '<i'
    fp.seek(0x0A)
    pixelArrayOffset = ustruct.unpack(ui, fp.read(4))[0]
    dibHeaderSize = ustruct.unpack(ui, fp.read(4))[0]
    self.bitmapWidth = ustruct.unpack(ui, fp.read(4))[0]
    self.bitmapHeight = ustruct.unpack(ui, fp.read(4))[0]
    self.topToBottom = self.bitmapHeight < 0
    self.bitmapHeight = abs(self.bitmapHeight)
    fp.seek(0x1C)
    bitsPerPixel = ustruct.unpack(ui, fp.read(2))[0]
    bitmapCompression = ustruct.unpack(ui, fp.read(4))[0]
    self.bitmapRowBytes = int((bitsPerPixel * self.bitmapWidth + 31)/32) << 2
    pixelArraySize = self.bitmapRowBytes * self.bitmapHeight
    fp.seek(pixelArrayOffset)
    self.pixelArrayData = bytearray(fp.read(pixelArraySize))
    
    if dibHeaderSize != 40 or bitmapCompression != 0 or bitsPerPixel not in [24]:
      raise ValueError(err)
  
  def transformRgb(self, transform):
    for row in range(0,self.bitmapHeight):
      i = row * self.bitmapRowBytes
      for col in range(0,self.bitmapWidth):
        rgb = transform((self.pixelArrayData[i+2], self.pixelArrayData[i+1], self.pixelArrayData[i]))
        for p in range(len(rgb)):
          self.pixelArrayData[i+2-p] = rgb[p]
        i += 3

  def fillPixelBytes(self, buffer, channels = None, pixelRange = None):
    if channels is None:
      channels = PixelLayout.NeoPixel_GRB

    bufferLen = len(buffer)
    if pixelRange is None:
      bufferBytesPerPixel = len(PixelLayout.channelInfo[channels])
      pixelRange = (0, int(bufferLen / bufferBytesPerPixel) - 1)

    if self.topToBottom:
      rows = range(self.offset[1], self.offset[1] + self.size[1])
    else:
      rows = range(self.bitmapHeight - self.offset[1] - 1, self.bitmapHeight - self.offset[1] - self.size[1] - 1, -1)
    cols = range(self.offset[0], self.offset[0] + self.size[0])
    
    channelOffsets = PixelLayout.channelInfo[channels]
    bufferBytesPerPixel = len(channelOffsets)
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
          buffer[bufferPos+channelOffsets[0]] = r
          buffer[bufferPos+channelOffsets[1]] = g
          buffer[bufferPos+channelOffsets[2]] = b
          if bufferPos == bufferEndPos:
            return
          bufferPos += bufferBytesPerPixel
          if (bufferPos >= bufferLen):
            bufferPos = 0
          pixelPos += 3
    
    return buffer
