#!/usr/bin/env python3

#         Python Stream Deck & Icom IC-705 Control
#
#
#           Written By: Jason Boucher
#
#


import os
import threading
import icom
import time
from os.path import exists

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
page = 1

icomTrx = icom.icom('COM6','115200',164)

keycommand = {1: {'name' : 'LSB', 'com' : 'icomTrx.setMode("LSB")', 'subcom': 20, 'text' : False},
              2: {'name' : 'USB', 'com' : 'icomTrx.setMode("USB")', 'subcom': 30, 'text' : False},
              7: {'name' : 'PTT', 'com' : 'icomTrx.setMode("USB")', 'subcom': 30, 'text' : True},
              30: {'name' : 'Memory', 'com' : 'icomTrx.setMode("USB")', 'subcom': 30, 'text' : True},
              31: {'name' : 'Exit', 'com' : 'icomTrx.setMode("USB")', 'subcom': 30, 'text' : True}}

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")



# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, icon_filename, font_filename, label_text,key, page):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    icon = Image.open(icon_filename)
    if page == 2:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])
    elif keycommand[key]['text']:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20, 0])
    else:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    if page == 2:
        font = ImageFont.truetype(font_filename, 48)
        draw.text((image.width / 2, image.height - 35), text=label_text, font=font, anchor="ms", fill="black")
    else:
        draw.text((image.width / 2, image.height - 5), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state, page):
    # Last button in the example application is the exit button.
    exit_key_index = deck.key_count() - 1

    if key == exit_key_index and page != 2:
        name = "exit"
        icon = "{}.png".format("Exit")
        font = "Roboto-Regular.ttf"
        label = "Bye" if state else "Exit"
    elif page == 2:
        print("Page 2 Icons")
        name = "mem"
        icon = "{}.png".format("MemoryNumber")
        font = "Roboto-Regular.ttf"
        label = str(key)
    else:
        name = "emoji"
        keyname = keycommand[key]['name']
        if exists(os.path.join(ASSETS_PATH, keyname + "_Pressed.png")) and exists(os.path.join(ASSETS_PATH, keyname + "_Released.png")):
            icon = "{}.png".format(keyname + "_Pressed" if state else keyname + "_Released")
        else:
            icon = "{}.png".format("nokey" if state else "nokey")

        if keycommand[key]['text']:
            label = "Pressed!" if state else keycommand[key]['name']
        else:
            label = "Pressed!" if state else ''
        font = "Roboto-Regular.ttf"
        #label = "Pressed!" if state else "Key {}".format(key)

    return {
        "name": name,
        "icon": os.path.join(ASSETS_PATH, icon),
        "font": os.path.join(ASSETS_PATH, font),
        "label": label
    }


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, key, state, page):
    # Determine what icon and label to use on the generated key.
    print("The Page Is: " + str(page))
    key_style = get_key_style(deck, key, state, page)

    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"], key, page)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)


# Prints key state change information, updates rhe key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):
    global page
    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    # Update the key image based on the new key state.
    print("The Page Is: " + str(page))
    if page == 2 and state:
        print(key)
        icomTrx.setMemory(str(key))
        page = 1
        deck.reset()
        for key in range(deck.key_count()):
            if key in keycommand.keys():
                update_key_image(deck, key, False, page)

    elif key in keycommand.keys() and keycommand[key]['name'] == 'Memory':
        print("Memory Key Pressed")
        page = 2
        for key in range(32):
            update_key_image(deck, key, False, page)


    elif key in keycommand.keys():
        page = 1
        update_key_image(deck, key, state, page)

    # Check if the key is changing to the pressed state.
    if key in keycommand.keys():
        keypressed = keycommand[key]
        #print("Key: " + str(key))
        #print(keycommand[key]['com'])
        #print(keycommand[key]['subcom'])
        #print(keycommand[key])









    if state and key in keycommand.keys():
        key_style = get_key_style(deck, key, state, page)

        # When an exit button is pressed, close the application.
        if key_style["name"] == "exit":
            # Use a scoped-with on the deck to ensure we're the only thread
            # using it right now.
            with deck:
                # Reset deck, clearing all button images.
                deck.reset()

                # Close deck handle, terminating internal worker threads.
                deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        # This example only works with devices that have screens.
        if not deck.is_visual():
            continue

        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))

        # Set initial screen brightness to 30%.
        deck.set_brightness(50)

        # Set initial key images.
        for key in range(deck.key_count()):
            if key in keycommand.keys():
                update_key_image(deck, key, False, page)

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass