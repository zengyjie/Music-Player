import win32com.client

def verify_music_folder(device_name):
    shell = win32com.client.Dispatch("Shell.Application")
    devices = shell.NameSpace(17)  # "This PC"

    phone = None
    for item in devices.Items():
        if device_name.lower() in item.Name.lower():
            phone = item
            break

    if not phone:
        print(f"[ERROR] Device '{device_name}' not found!")
        return

    for folder in phone.GetFolder.Items():
        if folder.Name.lower() == "internal storage":
            print(f"[INFO] Found Internal Storage on '{device_name}'")
            for subfolder in folder.GetFolder.Items():
                if subfolder.Name.lower() == "music":
                    print(f"[SUCCESS] Found Music folder: {subfolder.Path}")
                    return
            print("[ERROR] 'Music' folder not found in Internal Storage!")
            return

    print("[ERROR] 'Internal Storage' not found on the device!")

verify_music_folder("Galaxy S24")
