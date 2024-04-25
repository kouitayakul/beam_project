# Beam Downloader

## Descritption

A Python application designed to download files from HTTP/HTTPS, FTP, and SFTP protocols. It supports single and parallel downloads, handles retries, manages partial downloads, and resolves name clashes.

## Features

- **Multiple Protocols**: Supports downloading files via HTTP/HTTPS, FTP, and SFTP
- **Configurable**: Users can specify the download location, number of retries, and whether to handle files in parallel
- **Error Handling**: Automatically retries downloads and cleans up partial files if downloads fail
- **Name Clash Handling**: Manages files with the same name to ensure correct, conflict-free downloads
- **Extensibility**: Designed to easily add support for additional protocols

## Installation

1. Clone the repository

```
git clone https://yourrepositorylink.com/path/to/repo
cd beam_project
```

2. Set up a virtual environment

```
python -m venv venv
source venv/bin/activate
```

3. Install required packages

```
pip install -r requirements.txt
```

## Usage

### Basic Usage

```
python main.py <URI> --dest <path/to/download/folder> --retries <number_of_retries>
```

- Default `--dest` is `./downloads`
- Default `--retries` is `3`

### Download Multiple Files

Pass a list of URIs separated by spaces:

```
python main.py <URI_1> <URI_2> <URI_3>... --dest <path/to/download/folder> --retries <number_of_retries>
```

### Testing HTTP/HTTPS Download(s)

Here are example commands you can run to download files using the HTTP/HTTPS protocol:

Single URI:

```
python main.py http://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf --retries 2
```

Multiple URIs:

```
python main.py http://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf https://freetestdata.com/wp-content/uploads/2022/02/Free_Test_Data_1MB_MP4.mp4 https://freetestdata.com/wp-content/uploads/2021/10/Free_Test_Data_1MB_MOV.mov --retries 2
```

### Testing FTP Download(s)

We're relying on a free public FTP server called `test.rebex.net`

Here are example commands you can run to download files using the FTP protocol:

Single URI:

```
python main.py ftp://test.rebex.net/pub/example/KeyGenerator.png --retries 2
```

Mutiple URIs:

```
python main.py ftp://test.rebex.net/pub/example/KeyGenerator.png ftp://test.rebex.net/pub/example/ResumableTransfer.png ftp://test.rebex.net/pub/example/pocketftp.png --retries 2
```

### Testing SFTP Download(s)

We need to first create a temporary SFTP server using this tool: https://sftpcloud.io/tools/free-sftp-server. Next use any FTP/SFTP client such as FileZilla or Cyberduck to upload testing files on to the remote server.

Make sure that we have the "username:password" within the URI string:

```
python main.py sftp://<username>:<password>@eu-central-1.sftpcloud.io/dummy.pdf
```

### Testing Multiple Protocols Downloads

Please follow the _Testing SFTP Download(s)_ step to set up a temporary SFTP server.

Example command:

```
python main.py http://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf https://freetestdata.com/wp-content/uploads/2022/02/Free_Test_Data_1MB_MP4.mp4 https://freetestdata.com/wp-content/uploads/2021/10/Free_Test_Data_1MB_MOV.mov ftp://test.rebex.net/pub/example/KeyGenerator.png ftp://test.rebex.net/pub/example/ResumableTransfer.png ftp://test.rebex.net/pub/example/pocketftp.png --retries 2
```

### Name Crashes from Different Resources

In an event where a different source has the same filename, we want to download the file under another name, for instance "filename_1.pdf". However, if the same resouce gets downloaded twice, we want to overwrite the existing downloaded file.

## Extensibility

To add support for a new protocol, simply implement a new handler class derived from `BaseHandler`

Example:

```
class NewProtocolHandler(BaseHandler):
    def download_file(self, uri, dest_dir):
        # Implement download logic here
        pass
```

Register the new handler in the main program logic `download_manager.py`

```
self.protocol_handlers = {
    "http": HTTPHandler(...),
    "https": HTTPHandler(...),
    "ftp": FTPHandler(...),
    "sftp": SFTPHandler(...),
    # Add your new handler class here
}
```

### Testing

Run tests using:

```
python -m unittest
```

## Logging

In order to avoid cluttering the command line, debug logs for each rety attempt will get appended to the `debug_logs.log` file. This file will also contain other `DEBUG` level and higher logs.
