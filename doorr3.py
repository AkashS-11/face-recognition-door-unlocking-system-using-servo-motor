import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import shutil
import os
import cv2
import time
import threading
from simple_facerec import SimpleFacerec
import pyfirmata
import pyttsx3

# --- Arduino and hardware setup ---
ARDUINO_PORT = 'COM3'  # Change to your Arduino port
SERVO_PIN = 8
LED_PIN = 13

servo = None
led = None
board = None

try:
    print(f"[INFO] Connecting to Arduino on {ARDUINO_PORT} ...")
    board = pyfirmata.Arduino(ARDUINO_PORT)
    it = pyfirmata.util.Iterator(board)
    it.start()
    time.sleep(1)
    servo = board.get_pin(f'd:{SERVO_PIN}:s')
    led = board.get_pin(f'd:{LED_PIN}:o')
    time.sleep(1)
    if servo: 
        servo.write(0)
        print("[INFO] Servo initialized at 0 degrees.")
    else:
        print("[ERROR] Servo pin could not be initialized.")
    if led:
        led.write(0)
        print("[INFO] LED initialized and OFF.")
    else:
        print("[ERROR] LED pin could not be initialized.")
except Exception as e:
    print(f"[ERROR] Arduino connection failed: {e}")

def open_servo():
    if servo:
        try:
            servo.write(90)
            print("[SERVO] Servo opened to 90 degrees.")
        except Exception as e:
            print(f"[ERROR] Failed to open servo: {e}")
    else:
        print("[ERROR] Servo not available.")

def close_servo():
    if servo:
        try:
            servo.write(0)
            print("[SERVO] Servo closed to 0 degrees.")
        except Exception as e:
            print(f"[ERROR] Failed to close servo: {e}")
    else:
        print("[ERROR] Servo not available.")

def open_and_auto_close_servo():
    print("[SERVO] Opening servo for 10 seconds...")
    open_servo()
    threading.Timer(10, close_servo).start()

def led_on():
    if led:
        try:
            led.write(1)
            print("[LED] LED ON.")
        except Exception as e:
            print(f"[ERROR] Failed to turn LED on: {e}")
    else:
        print("[ERROR] LED not available.")

def led_off():
    if led:
        try:
            led.write(0)
            print("[LED] LED OFF.")
        except Exception as e:
            print(f"[ERROR] Failed to turn LED off: {e}")
    else:
        print("[ERROR] LED not available.")

def led_on_10s():
    led_on()
    threading.Timer(10, led_off).start()

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[ERROR] Speech error: {e}")

# --- PIN & Face Recognition Setup ---
PIN_FILE = "pin.txt"
MEMBER_DIR = "images"
os.makedirs(MEMBER_DIR, exist_ok=True)

def load_pin():
    if not os.path.exists(PIN_FILE):
        with open(PIN_FILE, "w") as f: f.write("1234")
        return "1234"
    with open(PIN_FILE, "r") as f:
        return f.read().strip()

def save_pin(new_pin):
    with open(PIN_FILE, "w") as f: f.write(new_pin)

def ask_pin(prompt="Enter 4-digit PIN:"):
    while True:
        pin = simpledialog.askstring("PIN Required", prompt, show="*")
        if pin is None: return None
        if pin.isdigit() and len(pin) == 4:
            return pin
        else:
            messagebox.showerror("Invalid PIN", "PIN must be exactly 4 digits.")

sfr = SimpleFacerec()

# --- GUI with background and animation ---
root = tk.Tk()
root.title("Smart Door System")
root.geometry("700x500")
root.resizable(False, False)

# Load background image
try:
    bg_image = Image.open("background.jpg")
    bg_photo = ImageTk.PhotoImage(bg_image.resize((700, 500)))
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except Exception as e:
    root.configure(bg="#e0e0e0")

# Main frame for buttons
main_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="ridge")
main_frame.place(relx=0.5, rely=0.6, anchor="center", width=400, height=400)

# Animation label
anim_label = tk.Label(root, bg="#ffffff")
anim_label.place(relx=0.5, rely=0.25, anchor="center")

def show_animation(anim_file, duration=4):
    try:
        anim_img = Image.open(anim_file)
        frames = []
        delays = []
        try:
            while True:
                frames.append(ImageTk.PhotoImage(anim_img.copy().resize((120, 120))))
                delays.append(anim_img.info.get('duration', 100))
                anim_img.seek(len(frames))
        except EOFError:
            pass

        if frames:
            stop_time = time.time() + duration
            def animate(idx=0):
                if time.time() < stop_time:
                    anim_label.config(image=frames[idx])
                    next_idx = (idx + 1) % len(frames)
                    anim_label.after(delays[idx], animate, next_idx)
                else:
                    anim_label.config(image="")
            animate()
    except Exception as e:
        try:
            img = Image.open(anim_file).resize((120, 120))
            img = ImageTk.PhotoImage(img)
            anim_label.config(image=img)
            anim_label.image = img
            root.after(duration * 1000, lambda: anim_label.config(image=""))
        except:
            pass

def capture_image(member_name):
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Capture Image - Press 'C' to Capture")
    while True:
        ret, frame = cap.read()
        if not ret: break
        cv2.imshow("Capture Image - Press 'C' to Capture", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            _, ext = os.path.splitext("capture.jpg")
            safe_name = "".join(c for c in member_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            filename = f"{safe_name}{ext}"
            dest_path = os.path.join(MEMBER_DIR, filename)
            cv2.imwrite(dest_path, frame)
            messagebox.showinfo("Success", f"Member image '{filename}' added!")
            break
        elif key == 27:
            break
    cap.release()
    cv2.destroyAllWindows()

def add_member():
    valid_extensions = (".jpg", ".jpeg", ".png")
    member_files = [
        f for f in os.listdir(MEMBER_DIR)
        if os.path.isfile(os.path.join(MEMBER_DIR, f)) and f.lower().endswith(valid_extensions)
    ]
    if len(member_files) >= 4:
        messagebox.showwarning("Limit Reached", "Maximum of 4 members allowed. Please delete a member before adding a new one.")
        return

    current_pin = load_pin()
    entered_pin = ask_pin("Enter 4-digit PIN to add a member:")
    if entered_pin is None: return
    if entered_pin != current_pin:
        messagebox.showerror("Access Denied", "Incorrect PIN.")
        return

    member_name = simpledialog.askstring("Member Name", "Enter the name of the new member:")
    if not member_name:
        messagebox.showwarning("No Name", "Member name is required.")
        return

    option_win = tk.Toplevel(root)
    option_win.title("Select Image Source")
    option_win.geometry("300x150")
    option_win.resizable(False, False)
    option_win.grab_set()
    tk.Label(option_win, text="How would you like to add the member image?", font=("Arial", 10)).pack(pady=10)

    btn_capture = tk.Button(option_win, text="Click Picture", width=20,
                            command=lambda: [option_win.destroy(), capture_image(member_name)])
    btn_capture.pack(pady=5)

    def browse_image():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            _, ext = os.path.splitext(file_path)
            safe_name = "".join(c for c in member_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            filename = f"{safe_name}{ext}"
            dest_path = os.path.join(MEMBER_DIR, filename)
            shutil.copy(file_path, dest_path)
            messagebox.showinfo("Success", f"Member image '{filename}' added!")
        option_win.destroy()

    btn_browse = tk.Button(option_win, text="Browse Picture", width=20, command=browse_image)
    btn_browse.pack(pady=5)
    btn_cancel = tk.Button(option_win, text="Cancel", width=20, command=option_win.destroy)
    btn_cancel.pack(pady=5)

def delete_member():
    current_pin = load_pin()
    entered_pin = ask_pin("Enter 4-digit PIN to delete a member:")
    if entered_pin is None: return
    if entered_pin != current_pin:
        messagebox.showerror("Access Denied", "Incorrect PIN.")
        return
    member_name = simpledialog.askstring("Delete Member", "Enter the name of the member to delete:")
    if not member_name:
        messagebox.showwarning("No Name", "Member name is required.")
        return
    found = False
    for filename in os.listdir(MEMBER_DIR):
        name, ext = os.path.splitext(filename)
        if name.lower() == member_name.strip().lower():
            os.remove(os.path.join(MEMBER_DIR, filename))
            messagebox.showinfo("Deleted", f"Member '{name}' deleted.")
            found = True
            break
    if not found:
        messagebox.showwarning("Not Found", f"No member named '{member_name}' found.")

def show_members():
    current_pin = load_pin()
    entered_pin = ask_pin("Enter 4-digit PIN to show members:")
    if entered_pin is None: return
    if entered_pin != current_pin:
        messagebox.showerror("Access Denied", "Incorrect PIN.")
        return
    members = []
    for filename in os.listdir(MEMBER_DIR):
        name, ext = os.path.splitext(filename)
        if ext.lower() in (".jpg", ".jpeg", ".png"):
            members.append(name)
    win = tk.Toplevel(root)
    win.title("Registered Members")
    win.geometry("300x300")
    tk.Label(win, text="Members in System:", font=("Arial", 12, "bold")).pack(pady=10)
    listbox = tk.Listbox(win, width=30, height=12)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    if members:
        for member in sorted(members): listbox.insert(tk.END, member)
    else:
        listbox.insert(tk.END, "No members found.")

def change_pin():
    current_pin = load_pin()
    entered_pin = ask_pin("Enter current 4-digit PIN to change it:")
    if entered_pin is None: return
    if entered_pin != current_pin:
        messagebox.showerror("Access Denied", "Incorrect current PIN.")
        return
    while True:
        new_pin = ask_pin("Enter new 4-digit PIN:")
        if new_pin is None: return
        confirm_pin = ask_pin("Re-enter new 4-digit PIN:")
        if confirm_pin is None: return
        if new_pin != confirm_pin:
            messagebox.showerror("PIN Mismatch", "PINs do not match. Try again.")
        else:
            save_pin(new_pin)
            messagebox.showinfo("Success", "PIN changed successfully!")
            break

def unlock_door():
    valid_extensions = ('.png', '.jpg', '.jpeg')
    member_images = [
        f for f in os.listdir(MEMBER_DIR)
        if os.path.isfile(os.path.join(MEMBER_DIR, f)) and f.lower().endswith(valid_extensions)
    ]
    if not member_images:
        messagebox.showwarning("No Members", "No registered member images found.")
        return
    sfr.load_encoding_images(MEMBER_DIR)
    if not sfr.known_face_encodings:
        messagebox.showwarning("Invalid Data", "No recognizable faces found in registered images.")
        return
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)
    recognized = False
    name = "Unknown"
    unknown_start_time = None
    unknown_timeout = 5  # seconds
    frame_count = 0
    resize_fx = 0.5
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_count += 1
        if frame_count % 2 != 0:
            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == 27: break
            continue
        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
        small_frame = cv2.resize(frame, (0, 0), fx=resize_fx, fy=resize_fx)
        face_locations, face_names = sfr.detect_known_faces(small_frame, threshold=0.4)
        recognized = False
        name = "Unknown"
        for face_loc, detected_name in zip(face_locations, face_names):
            y1, x2, y2, x1 = [int(v / resize_fx) for v in face_loc]
            color = (0, 255, 0) if detected_name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, detected_name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
            if detected_name != "Unknown":
                recognized = True
                name = detected_name
                unknown_start_time = None
                break
        if face_names and all(n == "Unknown" for n in face_names):
            if unknown_start_time is None:
                unknown_start_time = time.time()
            elif time.time() - unknown_start_time >= unknown_timeout:
                break
        else:
            unknown_start_time = None
        cv2.imshow("Face Recognition", frame)
        if recognized or cv2.waitKey(1) & 0xFF == 27: break
    cap.release()
    cv2.destroyAllWindows()
    if recognized and name != "Unknown":
        messagebox.showinfo("Access Granted", f"Welcome, {name}!")
        print("[ACCESS] Access granted. Opening servo and turning on LED.")
        open_and_auto_close_servo()
        led_on_10s()
        speak("Access Granted")
        show_animation("lock_open.gif", duration=4)
    else:
        messagebox.showerror("Access Denied", "Face not recognized.")
        print("[ACCESS] Access denied.")
        speak("Access Denied")
        show_animation("cross.gif", duration=4)

# --- Button styling and layout ---
button_font = ("Helvetica", 14, "bold")
button_style = {
    'width': 18,
    'height': 2,
    'font': button_font,
    'bg': "#1976d2",
    'fg': "white",
    'bd': 0,
    'activebackground': "#1565c0",
    'activeforeground': "white"
}

btn_add = tk.Button(main_frame, text="Add Member", command=add_member, **button_style)
btn_unlock = tk.Button(main_frame, text="Unlock Door", command=unlock_door, **button_style)
btn_change_pin = tk.Button(main_frame, text="Change PIN", command=change_pin, **button_style)
btn_delete = tk.Button(main_frame, text="Delete Member", command=delete_member, **button_style)
btn_show = tk.Button(main_frame, text="Show Members", command=show_members, **button_style)

btn_add.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
btn_unlock.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
btn_change_pin.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
btn_delete.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
btn_show.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

main_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
main_frame.grid_columnconfigure(0, weight=1)

root.mainloop()
