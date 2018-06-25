import board
import digitalio
import gc
import neopixel
import os
import time

import neosprite

gc.collect()

# Create a button on D10
button = digitalio.DigitalInOut(board.D10)
button.pull = digitalio.Pull.UP

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

# Turn off internal NeoPixel
dot = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0)
dot.fill(0)
dot = None

# Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
matrixSize = [8,4]
neopixels = neopixel.NeoPixel(board.D6, matrixSize[0] * matrixSize[1], auto_write=False)
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

clicked = False

while True:
  # Loop through all the sprite files
  for spriteFile in spriteFiles:
    # Garbage collect memory from previously loaded sprite
    sprite = None
    gc.collect()
    
    # Load a new sprite
    print('Showing',spriteFile)
    sprite = neosprite.Sprite.open(spriteFile)
    sprite.size = matrixSize
    
    # Adjust the brightness
    if brightness <= 0.99:
      setBrightness = lambda rgb: (int(rgb[0] * brightness), int(rgb[1] * brightness), int(rgb[2] * brightness))
      sprite.transformRgb(setBrightness)

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
        sprite.fillPixelBytes(neopixels.buf, channels=neosprite.Sprite.GRB)
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
    fps = frames / (end - start)
    pixelsPerSecond = len(neopixels) * fps
    print('fps:',fps,', pps:',pixelsPerSecond)