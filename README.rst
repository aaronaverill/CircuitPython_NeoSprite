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

The library accesses the pixel buffer directly to write data, allowing you to achieve 1800+ 
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

This example demonstrates how to load a sprite and animate through the frames. Copy the 8 pixel wide sprite.bmp
file from examples/sprites/matrix-4x8 to your SPI flash storage.

.. code-block::

    import board
    import neopixel

    import neosprite

    # We are using the NeoPixel Featherwing 4x8 https://www.adafruit.com/product/2945
    # Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
    matrixSize = [8,4]
    neopixels = neopixel.NeoPixel(board.D6, matrixSize[0] * matrixSize[1], auto_write=False)
    neopixels.fill(0)
    neopixels.show()

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

This example demonstrates how to set the brightness of a sprite. Modifying the pixel data once at the start instead
of every time the pixels are refreshed allows much faster animations. Copy the 8 pixel wide sprite.bmp
file from examples/sprites/matrix-4x8 to your SPI flash storage.

.. code-block::

    import board
    import neopixel

    import neosprite

    # We are using the NeoPixel Featherwing 4x8 https://www.adafruit.com/product/2945
    # Create a NeoPixel object to control the Adafruit NeoPixel 4x8 RGB FeatherWing
    matrixSize = [8,4]
    neopixels = neopixel.NeoPixel(board.D6, matrixSize[0] * matrixSize[1], auto_write=False)
    neopixels.fill(0)
    neopixels.show()

    # Load the sprite from a BMP file.
    sprite = neosprite.Sprite.open('sprite.bmp')

    # Set the size of the sprite to 8 pixels wide by 4 pixels tall.
    sprite.size = matrixSize

    # Adjust the brightness
    brightness = 0.1 # 10%
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
        
This example demostrates a simple chase animation for a pixel strip. Copy the 8 pixel wide sprite.bmp
file from examples/sprites/matrix-4x8 to your SPI flash storage.

.. code-block::

    import board
    import neopixel

    import neosprite

    # Create a NeoPixel object to control a 50 pixel strip
    numPixels = 50
    neopixels = neopixel.NeoPixel(board.D6, numPixels, auto_write=False)
    neopixels.fill(0)
    neopixels.show()

    # Load the sprite from a BMP file.
    sprite = neosprite.Sprite.open('sprite.bmp')

    # Set the size of the sprite to 8 pixels wide by 1 pixels tall.
    sprite.size = [8, 1]
    
    range = (0, numPixels - 1)
    while True:
      # Display the RGB data on the NeoPixels
      sprite.fillPixelBytes(neopixels.buf, pixelRange = range)
      neopixels.show()
      
      # Advance one position
      range = ((range[0] + 1) % numPixels, (range[1] + 1) % numPixels)
            
Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/aaronaverill/CircuitPython_neosprite/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building locally
================

Zip release files
-----------------

To build this library locally you'll need to install the
`circuitpython-build-tools <https://github.com/adafruit/circuitpython-build-tools>`_ package.

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install circuitpython-build-tools

Once installed, make sure you are in the virtual environment:

.. code-block:: shell

    source .env/bin/activate

Then run the build:

.. code-block:: shell

    circuitpython-build-bundles --filename_prefix circuitpython-neosprite --library_location .

Sphinx documentation
-----------------------

Sphinx is used to build the documentation based on rST files and comments in the code. First,
install dependencies (feel free to reuse the virtual environment from above):

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install Sphinx sphinx-rtd-theme

Now, once you have the virtual environment activated:

.. code-block:: shell

    cd docs
    sphinx-build -E -W -b html . _build/html

This will output the documentation to ``docs/_build/html``. Open the index.html in your browser to
view them. It will also (due to -W) error out on any warning like Travis will. This is a good way to
locally verify it will pass.
