import tkinter as tk
import hid

VENDOR_ID = 0x1FC9
PRODUCT_ID = 0x0081

# vypis vsech zarizeni HID

# for d in hid.enumerate():
#     print(hex(d['vendor_id']), hex(d['product_id']), d['product_string'])

# devices = hid.enumerate()
# for d in devices:
#     print(d)

# ---------- HID zařízení ----------
device = None

def connect_hid():
    global device
    try:
        device = hid.device(VENDOR_ID, PRODUCT_ID)
        device.open(VENDOR_ID, PRODUCT_ID)
        print("HID device connected.")
    except Exception as e:
        print("Error when connecting HID device:", e)
        device = None


def send_report(r, g, b):
    if device is None:
        print("Device disconnected.")
        return

    # spodni 4 bity – R,G,B,USER
    value = (r << 0) | (g << 1) | (b << 2)


    report = [0] * 64
    report[0] = value

    message = message = b"\xAA" + bytes(report)

    print(message)

    try:
        device.write(message)
        print("Transmitted:", r, g, b)
    except Exception as e:
        print("Error while transmitting:", e)


# ---------- GUI ----------

def on_change():
    r = r_var.get()
    g = g_var.get()
    b = b_var.get()
    send_report(r, g, b)

    # print(r, g, b)

root = tk.Tk()
root.title("RGB HID Controller – Procedural")

# připojit HID při startu
connect_hid()

r_var = tk.IntVar()
g_var = tk.IntVar()
b_var = tk.IntVar()

tk.Checkbutton(root, text="R", variable=r_var, command=on_change).pack()
tk.Checkbutton(root, text="G", variable=g_var, command=on_change).pack()
tk.Checkbutton(root, text="B", variable=b_var, command=on_change).pack()

root.mainloop()

# -----------------------------------------------

# import hid

# if __name__ == "main":

# dev = hid.device(0x1FC9, 0x0081)
# dev.open(0x1FC9, 0x0081)
# message = (b"\x00\xff\x00" + b"\x00"*61)
# dev.write(message)
# print(message)
