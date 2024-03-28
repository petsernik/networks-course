from ftplib import FTP
import os

HOSTNAME = "127.0.0.1"
USERNAME = "TestUser"
PASSWORD = ""
PATH_SERVER = "server/"
PATH_STORE = "store/"

# port is 21 by default, it's my case
ftp = FTP(HOSTNAME, USERNAME, PASSWORD)


def list_files(ftp_server, path):
    for item in ftp_server.mlsd():
        name = item[0]
        if item[1]['type'] == 'dir':
            print(f"{path}/{name}/")
            ftp_server.cwd(name)
            list_files(ftp_server, f"{path}/{name}")
            ftp_server.cwd("..")
        else:
            print(f"{path}/{name}")


# print all paths of dirs/files on ftp server
print(f"[MESSAGE] Trying print all paths of dirs or files on ftp server")
list_files(ftp, ".")
print(f"[MESSAGE] Successfully printed all paths of dirs or files on ftp server")

if not os.path.exists(PATH_STORE):
    os.makedirs(PATH_STORE)

# example of downloading
filename_to_download = "Test.txt"
with open(PATH_STORE + filename_to_download, "wb") as file:
    ftp.retrbinary(f"RETR {PATH_SERVER + filename_to_download}", file.write)
    print(f"[MESSAGE] Successfully downloaded: "
          f"{PATH_SERVER + filename_to_download} -> {PATH_STORE + filename_to_download}")

EXAMPLE_FILENAME = "Example.txt"
with open(PATH_STORE + EXAMPLE_FILENAME, "w") as file:
    print("Example", file=file)
print(f"[MESSAGE] Created Example.txt in {PATH_STORE}")

# example of uploading
filename_to_upload = "Example.txt"
with open(PATH_STORE + filename_to_upload, "rb") as file:
    ftp.storbinary(f"STOR {PATH_SERVER + filename_to_upload}", file)
    print(f"[MESSAGE] Successfully uploaded: "
          f"{PATH_STORE + filename_to_upload} -> {PATH_SERVER + filename_to_upload}")

print(f"[MESSAGE] Let's check that uploading was successfully: ")
print(f"[MESSAGE] Trying print all paths of dirs or files on ftp server")
list_files(ftp, ".")
print(f"[MESSAGE] Successfully printed all paths of dirs or files on ftp server")

ftp.quit()
