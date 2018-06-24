import board
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

# Turn off internal NeoPixel
dot = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0)
dot.fill(0)

# Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
matrixSize = [8,4]
neopixels = neopixel.NeoPixel(board.D6, matrixSize[0] * matrixSize[1], brightness=.1, auto_write=False)
neopixels.fill(0)
neopixels.show()

# Create a pixel strip object to manage the NeoPixel display
pixelStrip = neosprite.PixelStrip(neopixels)

# Get all the images in the sprites folder
spriteFolder = 'sprites'
spriteFiles = getFilesRecursive(spriteFolder)

# Number of seconds to delay between animation frames
frameDelay = 0.1

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
    
    # Loop through the sprite animation frames vertically
    for yPos in range(0, sprite.bitmapHeight, sprite.size[1]):
        # Set the animation frame
        sprite.offset = [0, yPos]
        
        # Get the RGB matrix from the sprite
        rgb = sprite.getRgbMatrix()
        
        # Display the RGB data on the NeoPixels
        pixelStrip.show(rgb)
        
        # Pause for the animation frame delay
        if frameDelay:
            time.sleep(frameDelay)