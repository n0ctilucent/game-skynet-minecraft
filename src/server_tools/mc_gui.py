import tkinter as tk
from mcstatus import JavaServer
import threading
import time
import matplotlib.pyplot as plt

SERVER = "10.10.8.60:25565"
REFRESH = 30 

# Initialize the plot
x_values = []
y_values = []

def update_status():
    try:
        server = JavaServer.lookup(SERVER)
        status = server.status()
        txt = (f"Server: {SERVER}\n"
               f"Version: {status.version.name}\n"
               f"Players: {status.players.online}/{status.players.max}\n"
               f"Latency: {status.latency} ms")
    except Exception as e:
        txt = f"Server offline\n{e}"
    
    # Update the plot
    y_values.append(status.players.online)
    x_values.append(time.time())
    plt.cla()  # Clear the previous plot
    plt.plot(x_values, y_values)  # Plot the new data
    plt.xlabel('Time (s)')
    plt.ylabel('Players')
    plt.title('Minecraft Server Load')
    label.config(text=txt)
    
    root.after(REFRESH*1000, lambda: threading.Thread(target=update_status).start())

root = tk.Tk()
root.title("Minecraft Server Status")
root.geometry("300x250")  # Make room for the plot
label = tk.Label(root, font=("Helvetica", 12), justify="left")
label.pack(expand=True, fill="both", padx=10, pady=10)

# Create a canvas for the plot
fig = plt.Figure()
ax = fig.add_subplot(111)
canvas = tk.Canvas(root, width=200, height=150)
canvas.pack(side=tk.LEFT)
plot_widget = fig.canvas.get_tk_widget()
plot_widget.pack()

threading.Thread(target=update_status).start()
root.mainloop()
