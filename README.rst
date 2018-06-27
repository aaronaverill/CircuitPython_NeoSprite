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

Animation speed
----------


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
