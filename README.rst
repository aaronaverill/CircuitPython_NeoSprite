Introduction
============

.. image:: https://readthedocs.org/projects/circuitpython-neosprite/badge/?version=latest
    :target: https://circuitpython-neosprite.readthedocs.io/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://travis-ci.org/aaronaverill/CircuitPython_neosprite.svg?branch=master
    :target: https://travis-ci.org/aaronaverill/CircuitPython_neosprite
    :alt: Build Status

Library for updating NeoPixel arrays from sprite files such as .BMP

Using this library you can show simple animations on a pixel matrix or pixel strip. Looping 
marquee (chase) animations can be easily implemented. Or you can modify the palette
or pixel data of a sprite bitmap in memory to achieve animations. 

Sprite files can be stored on the flash memory and loaded when activated by user interaction 
(a button press for example). There is sample code to search for all sprites in a folder
and show each one.

The library accesses the pixel buffer directly to write data, allowing you to achieve 2500 
pixel updates per second for example with a ATSAMD21G18 @ 48MHz such as the Adafruit Express M0.

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Adafruit CircuitPython NeoPixel <https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Usage Example
=============

This example demonstrates how to load and animate a sprite from a BMP file that contains animation frames arranged vertically. The example assumes you are using a NeoPixel 4x8 matrix array such as the FeatherWing. Copy the 8 pixel wide 'sprite.bmp' file from 'examples/sprites/matrix-4x8' folder to your flash storage root folder.

If you don't have a 4x8 NeoPixel matrix don't worry you can still see the animation on a LED strip it will just look a bit wonky.

.. code-block::

    import board
    import neopixel
    import neosprite

    brightness = 0.1 # 10%

    # We are using the NeoPixel Featherwing 4x8 https://www.adafruit.com/product/2945
    # Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
    matrixSize = [8,4]
    numPixels = matrixSize[0] * matrixSize[1]
    neopixels = neopixel.NeoPixel(board.D6, numPixels, brightness=brightness, auto_write=False)

    # Load the sprite from a BMP file.
    sprite = neosprite.Sprite.open('sprite.bmp')

    # Set the size of the sprite to 8 pixels wide by 4 pixels tall.
    sprite.size = matrixSize

    while True:
      # Loop through the sprite animation frames vertically
      for yPos in range(0, sprite.bitmapHeight, sprite.size[1]):
        # Set the animation frame
        sprite.offset = [0, yPos]
        
        # Display the RGB data on the NeoPixels
        sprite.fillPixelBytes(neopixels.buf)
        neopixels.show()

This example demonstrates how to set the brightness of a sprite by modifying the bitmap RGB data once at the start of the program and using the default full brightness (1.0) in the NeoPixel. 

When the brightness of the NeoPixel object is set to 100% it avoids a bytearray allocation, memory read, floating point multiplication and memory assignment for every pixel on every animation frame. You should see a significant animation speed improvement with this code change.

Copy the 8 pixel wide 'sprite.bmp' file from 'examples/sprites/matrix-4x8' folder to your flash storage root folder.

.. code-block::

    import board
    import neopixel
    import neosprite

    brightness = 0.1 # 10%
    
    # We are using the NeoPixel Featherwing 4x8 https://www.adafruit.com/product/2945
    # Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
    matrixSize = [8,4]
    numPixels = matrixSize[0] * matrixSize[1]
    neopixels = neopixel.NeoPixel(board.D6, numPixels, auto_write=False)

    # Load the sprite from a BMP file.
    sprite = neosprite.Sprite.open('sprite.bmp')

    # Set the size of the sprite to 8 pixels wide by 4 pixels tall.
    sprite.size = matrixSize

    # Adjust the brightness of the bitmap RGB data in memory
    setBrightness = lambda rgb: (int(rgb[0] * brightness), int(rgb[1] * brightness), int(rgb[2] * brightness))
    sprite.transformRgb(setBrightness)

    while True:
      # Loop through the sprite animation frames vertically
      for yPos in range(0, sprite.bitmapHeight, sprite.size[1]):
        # Set the animation frame
        sprite.offset = [0, yPos]
        
        # Display the RGB data on the NeoPixels
        sprite.fillPixelBytes(neopixels.buf)
        neopixels.show()
        
This example demonstrates a simple chase animation for a pixel strip. Instead of animating through the sprite data we are incrementing the (start,end) range at each loop. The fillPixelBytes() method will tile the 10 pixel sprite across the entire 50 pixel strip and wrap the tiled bitmap around from the end of the strip to the start. 

Copy the 10 pixel wide 'red-comet.bmp' file from 'examples/sprites/strip-10' to your flash storage.

.. code-block::

    import board
    import neopixel
    import neosprite

    # Create a NeoPixel object to control a 50 pixel strip
    numPixels = 50
    neopixels = neopixel.NeoPixel(board.D6, numPixels, auto_write=False)

    # Load the sprite from a BMP file.
    sprite = neosprite.Sprite.open('red-comet.bmp')

    # Set the size of the sprite to 1 pixel tall.
    sprite.size = [sprite.size[0], 1]
    
    range = (0, numPixels - 1)
    while True:
      # Display the RGB data on the NeoPixels
      sprite.fillPixelBytes(neopixels.buf, pixelRange = range)
      neopixels.show()
      
      # Advance the output buffer range one position
      range = ((range[0] + 1) % numPixels, (range[1] + 1) % numPixels)

Performance considerations
================

Memory usage
----------
There are two areas where memory can be optimized:

1. **Code**
Always use a pre-compiled python library with mpy-cross.

If all your bitmaps are the same bits per pixel, include the specific library (eg neosprite_24bpp). These versions only include pixel fill code for the specific bpp, so you can save some memory with these optimized classes. Mind you check the error codes if you try to use a file with different bits per pixel.

Replace the NeoPixel python library with lower level calls (see "Advanced optimization" below). This could save you about 3K.

When you load a new bitmap file, set the previous sprite to None and execute gc.collect() before creating the new sprite object.

2. **Images**
If you can get away with 16 colors consider saving your bitmap file with 4bpp. This will be the smallest file possible with bitmaps that have more than 19 pixels. For larger bitmaps memory use quickly approaches pixels / 2.

If you need more than 16 colors and your image has less than 384 pixels the 24bpp format will consume the smallest memory since there is no palette. As a side benefit it will also animate the fastest.

For images larger than 384 pixels where you need more than 16 colors the 8bpp format will consume the smallest memory (256 * 3 bytes for the palette + 1 byte per pixel).

If you need more than 256 colors provided by the 8bpp palette, well... you'll have to save it as a 24bpp bitmap. Beware large animations as memory use = pixels * 3

If you want to do simple linear chase sequences, consider a wide bitmap 1 pixel high and increment the output range in your loop to achieve the animation.

Finally if you don't mind a chase sequence that tiles across the pixel strip, use a bitmap width that is a smaller subset of your number of pixels. For example if you have a 150 LED pixel strip you can use a 15 pixel wide bitmap that will tile 10 times, animating using the range increment approach and a 24bpp bitmap this will only take 45 bytes of memory for the pixel data.

Pixel Memory Consumption = IF(bpp < 24, (3*2^bpp),0)+CEILING(nPixels*bpp/8))


Animation speed
----------
The fastest animation speed is achieved with 24 bits per pixel bitmap because the bitmap R,G,B bytes map directly to the pixel strip R,G,B bytes. If you have smaller sprite files and can fit them in memory use 24bpp. There's also an optimized library for this scenario (see "Advanced optimization" below).

For larger bitmap files 8, 4 and 1 bit files will take less memory but cost you additional math operations in the pixel fill loop. Animating pixels from bitmaps with these bpp are typically ~20% slower than 24bpp.

If you use the NeoPixel python library (and you don't always have to, see "Advanced optimization" below) always set the brightness to 1.0 and use the transformRgb() method to adjust the brightness of the bitmap data in memory once at the start of the loop. Using a brightness other than 1.0 for the actual NeoPixel object can slow animation down by +30% as it requires floating point math for every R,G,B byte.

RGB pixel strips have a few less operations in the pixel fill loop compared to RGBW pixel strips.

Power consumption
----------
If you're driving a lot of pixels you probably care about power. With complex animations estimating power based on the 20mA / per pixel "rule of thumb" could be wildly inaccurate. If you're doing primarily marquee (chase) animations where most pixels are off most of the time 20mA / per pixel will vastly over estimate your power needs, especially if you're using the primary red, blue, green colors where only one LED is powered.

You can use the following code snippet to estimate the power consumption of a looping sprite animation:

.. code-block::

    # Helper function to calculate the total brightness percentage of the entire sprite
    def calcTotalBrightness(sprite, channels = None):
      # Save the current size and offset
      size = sprite.size
      offset = sprite.offset
      # Set the size to the entire bitmap and offset to the top, left
      sprite.size = [sprite.bitmapWidth, sprite.bitmapHeight]
      sprite.offset = [0,0]
      # Get the pixel bytes
      pixelBytes = sprite.getPixelByteArray(channels)
      # Restore the size
      sprite.size = size
      sprite.offset = offset
      
      percent = 0
      for i in range(len(pixelBytes)):
          percent += pixelBytes[i]
          
      return percent / len(pixelBytes) / 0xFF

Use it after you load a sprite and set the brightness in your main loop:

.. code-block::

    # Calculate and display the current necessary while this sprite is animating
    mAPerPixel = 60
    percent = calcTotalBrightness(sprite)
    current = mAPerPixel * numPixels * percent
    print('brightness:',percent,' current:',round(current),'mA')
    
The "animate_all.py" file in the "examples" folder includes code to estimate the current of each animation after it is loaded, and accumulate the total current used while the animation runs.

Note this estimate only includes the LED current cost, and doesn't include current required by the board (25mA) or by off pixels (1mA) which can add up quickly with lots of pixels.

Advanced optimization
----------
If you really need to push pixel speed or minimize memory there are a few advanced optimizations you can make. If you have R,G,B NeoPixels and smallish bitmap files the following steps will reach near 2500 pixels / per second with a ATSAMD21G18 @ 48MHz and barely sip memory.

1. **Create only 24 bits per pixel bitmaps.** 
Since these map one byte of bitmap data to one byte in the LED output array there is minimal math and no palette color lookup in the pixel fill loop which will speed up animations dramatically.

2. **Compile and use the optimized neosprite_24bpp_rgb library**
This code has been optimized for 24bpp bitmaps on R,G,B NeoPixel strips by removing conditional logic checks inside the pixel fill loop and removing code to handle bitmaps at other bpp (1, 2, 4, 8, 32). So the code is faster and takes less memory.

3. **Replace the NeoPixel python library with lower level calls**
Since we're blasting R,G,B bytes into the NeoPixel buffer, it turns out most of the code isn't used, and you can save almost 3K by not importing the NeoPixel library. This NeoPixel adapter code snippet can be used instead:

.. code-block::

  import digitalio
  from neopixel_write import neopixel_write

  class NeoPixel(object):
    def __init__(self, pin, n):
      self.pin = digitalio.DigitalInOut(pin)
      self.pin.direction = digitalio.Direction.OUTPUT
      self.buf = bytearray(n * 3)
    
Inside your animation loop add the following code:

.. code-block::

  # Display the RGB data on the NeoPixels
  sprite.fillPixelBytes(neopixels.buf)
  neopixel_write(neopixels.pin, neopixels.buf)

  
Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/aaronaverill/CircuitPython_neosprite/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building locally
================

To precompile the python files use the mpy-cross tool.

To build this library locally you'll need to install the
`circuitpython-build-tools <https://github.com/adafruit/circuitpython-build-tools>`_ package.

.. code-block:: shell

    mpy-cross neosprite.py

Once compiled, copy the generated neosprite.mpy file to your board flash storage root folder.
