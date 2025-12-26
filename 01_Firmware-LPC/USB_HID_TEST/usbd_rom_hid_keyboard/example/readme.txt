LPC15XX Keyboard example

Example description:
--------------------
The example shows how to us USBD ROM stack to creates a HID keyboard.

Special connection requirements:
--------------------------------
The tiny joystick that is surface mounted on the eval board has 4 positions
and a button press. They act as number keys '2', '4', '6', '8', and NUMLOCK.
The joystick press toggles NUMLOCK. When NUMLOCK is ON the joystick positions
are mapped to the arrow keys. For most OSs, no drivers are needed.

Build procedures:
-----------------
Visit the LPCOpen quickstart guides to get started building LPCOpen projects.
[Link: http://www.lpcware.com/content/project/lpcopen-platform-nxp-lpc-microcontrollers/lpcopen-v200-quickstart-guides]

