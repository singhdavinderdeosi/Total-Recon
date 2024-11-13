import requests
import tkinter as tk
from tkinter import messagebox, simpledialog
import pyfiglet
import webbrowser
from googlesearch import search
import jwt
from termcolor import colored

# Function to display the ASCII art for "Total Recon"
def show_banner():
    figlet = pyfiglet.figlet_format("Total Recon", font="slant")
    print(figlet)
    print("instagram - @davinder_singh_deosi                                                                   @VIEH GROUP\n")
    print("WELCOME TO TOTAL RECON")

# Function to check HTTP status code
def check_http_status():
    url = simpledialog.askstring("HTTP Status Checker", "Enter the URL:")
    try:
        response = requests.get("http://" + url)
        messagebox.showinfo("HTTP Status Code", f"URL: {url}\nHTTP Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function for subdomain bruteforcing
def bruteforce_subdomains():
    path2 = simpledialog.askstring("Subdomain Bruteforcer", "Enter your domain:")
    open2 = open("2m-subdomains.txt").read().splitlines()
    results = []
    for line1 in open2:
        newurl = line1 + "." + path2
        try:
            response1 = requests.get("http://" + newurl, timeout=5)
            results.append((response1.status_code, newurl))
        except requests.exceptions.ConnectionError:
            continue
    result_message = "\n".join(f"{status} - {url}" for status, url in results)
    messagebox.showinfo("Results", f"Here are your results:\n{result_message}")

# Function for directory bruteforcing
def bruteforce_directories():
    path3 = simpledialog.askstring("Directory Bruteforcer", "Enter your domain:")
    open3 = open("dirbig.txt").read().splitlines()
    results = []
    for line2 in open3:
        newurl1 = "http://" + path3 + "/" + line2
        try:
            response2 = requests.get(newurl1, timeout=5)
            if response2.status_code in [200, 403, 302]:
                results.append((response2.status_code, newurl1))
        except requests.exceptions.ConnectionError:
            continue
    result_message = "\n".join(f"{status} - {url}" for status, url in results)
    messagebox.showinfo("Results", f"Here are your results:\n{result_message}")

# Function for Google dorking
def automated_google_dorking():
    path4 = simpledialog.askstring("Google Dorker", "Enter the Target Domain:")
    open4 = open("gdorks.txt").read().splitlines()
    for line3 in open4:
        newurl2 = f"site:{path4} {line3}"
        webbrowser.open("https://google.com/search?q=" + newurl2)

# Function for JWT bruteforcing
def bruteforce_jwt():
    file2 = simpledialog.askstring("JWT Bruteforcer", "Enter file path:")
    token1 = simpledialog.askstring("JWT Bruteforcer", "Enter your token:")
    algo = simpledialog.askstring("JWT Bruteforcer", "Enter algorithm:")

    with open(file2) as secrets:
        for secret in secrets:
            try:
                payload = jwt.decode(token1, secret.rstrip(), algorithms=[algo])
                messagebox.showinfo("Success", f"Token decoded successfully with secret: {secret.rstrip()}")
                break
            except jwt.InvalidTokenError:
                print(colored(f"Invalid Token: {secret.rstrip()}", 'red'))
            except jwt.ExpiredSignatureError:
                print(colored(f"Token Expired: {secret.rstrip()}", 'red'))

# Setting up Tkinter window
app = tk.Tk()
app.title("Total Recon")
app.geometry("400x300")

show_banner()

# Creating buttons for each option
tk.Label(app, text="Select an option to use:", font=("Helvetica", 12)).pack(pady=10)
tk.Button(app, text="1. Check HTTP Status Code", command=check_http_status).pack(pady=5)
tk.Button(app, text="2. Bruteforce Subdomains", command=bruteforce_subdomains).pack(pady=5)
tk.Button(app, text="3. Bruteforce Hidden Directories", command=bruteforce_directories).pack(pady=5)
tk.Button(app, text="4. Perform Automated Google Dorking", command=automated_google_dorking).pack(pady=5)
tk.Button(app, text="5. Bruteforce JWT Signature", command=bruteforce_jwt).pack(pady=5)

# Running the application
app.mainloop()
