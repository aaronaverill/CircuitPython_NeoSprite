import board
import digitalio
import gc
import neopixel
import os
import time

import neosprite

gc.collect()

# Helper function to recursively search a folder for all files and return the full path
def getFilesRecursive(folder):
  files = []
  folderFiles = os.listdir(folder)
  for file in folderFiles:
    filePath = folder + os.sep + file
    fileStat = os.stat(filePath)
    if fileStat[0] & 0o170000 == 0o040000:
      files.extend(getFilesRecursive(filePath))
    else:
      files.append(filePath)
  return files

# Helper function to calculate the total brightness percentage of the entire sprite
def calcTotalBrightness(sprite, channels = neosprite.PixelLayout_NeoPixel_GRB):
  # Save the current size and offset
  size = sprite.size
  offset = sprite.offset
  # Set the size to the entire bitmap and offset to the top, left
  sprite.size = [sprite.bitmapWidth, sprite.bitmapHeight]
  sprite.offset = [0,0]
  # Get the pixel bytes
  bytesPerPixel = 4 if channels[3] != 0xFF or channels[4] != 0XFF else 3
  pixelBytes = bytearray(bytesPerPixel * sprite.size[0] * sprite.size[1])
  sprite.fillBuffer(pixelBytes, channels)
  # Restore the size
  sprite.size = size
  sprite.offset = offset
  
  percent = 0
  for i in range(len(pixelBytes)):
      percent += pixelBytes[i]
      
  return percent / len(pixelBytes) / 0xFF

# Main Program

# Create a button on D10
button = digitalio.DigitalInOut(board.D10)
button.pull = digitalio.Pull.UP

# Turn off internal NeoPixel
dot = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0)
dot.fill(0)
dot = None

# Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
matrixSize = [8,4]
numPixels = matrixSize[0] * matrixSize[1]
neopixels = neopixel.NeoPixel(board.D6, numPixels, auto_write=False)
neopixels.fill(0)
neopixels.show()

# The sprite brightness
brightness = 0.10 # 10%
# Get all the images in the sprites folder
spriteFolder = 'sprites'
spriteFiles = getFilesRecursive(spriteFolder)

# Whether to loop that animation continuously until a button is clicked
loopAnimation = True
# Number of seconds to delay between animation frames
#frameDelay = 0.1
frameDelay = 0

totalCurrent = 0
clicked = False

while True:
  # Loop through all the sprite files
  for spriteFile in spriteFiles:
    # Garbage collect memory from previously loaded sprite
    sprite = None
    gc.collect()
    
    # Load a new sprite
    print('\nShowing',spriteFile)
    try:
      sprite = neosprite.BmpSprite.open(spriteFile)
      sprite.size = matrixSize
    except Exception as e:
      print('Bitmap load error.', str(e))
    
    if sprite is None:
      continue

    # Adjust the brightness
    if brightness <= 0.99:
      setBrightness = lambda rgb: (int(rgb[0] * brightness), int(rgb[1] * brightness), int(rgb[2] * brightness))
      sprite.transformRgb(setBrightness)

    # Calculate and display the current necessary while this sprite is animating
    mAPerPixel = 60
    percent = calcTotalBrightness(sprite, channels=neosprite.PixelLayout.NeoPixel_GRB)
    current = mAPerPixel * numPixels * percent
    print('brightness:',percent,' current:',round(current),'mA')
    
    #gc.collect()
    print('mem usage:',gc.mem_alloc(),', mem free:',gc.mem_free())
    
    # Loop through the sprite animation frames vertically
    start = time.monotonic()
    frames = 0
    play = True
    while True:
      for yPos in range(0, sprite.bitmapHeight, sprite.size[1]):
        # Set the animation frame
        sprite.offset = [0, yPos]
        
        # Display the RGB data on the NeoPixels
        sprite.fillBuffer(neopixels.buf)
        neopixels.show()
      
        frames += 1
        
        # Check if the button was pressed and move to the next file
        if not button.value:
          if not clicked:
            clicked = True
            play = False
            break
        else:
          clicked = False
        
        # Pause for the animation frame delay
        if frameDelay:
          time.sleep(frameDelay)
      
      if not loopAnimation or not play:
          break
          
    end = time.monotonic()
    duration = end - start
    fps = frames / duration
    pixelsPerSecond = len(neopixels) * fps
    totalCurrent += current * duration / 3600
    print('fps:',fps,', pps:',pixelsPerSecond,', total current:',totalCurrent,'mAh')