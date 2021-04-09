import time

# Copied in command interpreter, Should be in a utils file.
def send(client, cmd, params):
    message = cmd_to_filename(cmd, params)
    sent = client.send(message)
    # the lostconnection message will get resent anyway, no need to clog up lanes by retrying here.
    while not sent and message != "lostconnection":
        print("Failed to send message, retrying.")
        if len(message) < 200:
            print(message)
        else:
            print(message[0:100])
        time.sleep(2)
        sent = client.send(message)
    if len(message) < 200 and "lostconnection" not in message:
        print(f"Sent {message}")
    elif "lostconnection" not in message:
        print(f"Sent {message[0:100]}")


# Copied in command interpreter, Should be in a utils file.
def filename_to_cmd(filename):
    cmd = filename.split("&")[0]
    params = filename.split("&")[1:]
    i = 0
    for param in params:
        params[i] = param
        i = i + 1
    return cmd, params


# Copied in command interpreter, Should be in a utils file.
def cmd_to_filename(cmd, params):
    filename = cmd
    i = 0
    for param in params:
        filename = filename + "&" + param
        i = i + 1
    return filename