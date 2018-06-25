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

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Usage Example
=============

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

    y = 0
    while True:
      # Loop through the sprite animation frames vertically
      for yPos in range(0, sprite.bitmapHeight, sprite.size[1]):
        # Set the animation frame
        sprite.offset = [0, yPos]
        
        # Display the RGB data on the NeoPixels
        sprite.fillPixelBytes(neopixels.buf, channels=neosprite.Sprite.GRB)
        neopixels.show()


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
