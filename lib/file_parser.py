#!/usr/bin/env python3

import re
from requests.exceptions import SSLError
import base64
import warnings
from . import config
from .ansi_colors import *
from .alerts import error
import xml.etree.ElementTree as ET
from lib.debug import save_stack_trace
import traceback
import sys
import json

warnings.filterwarnings("ignore")


def make_request(data, headers, options, url, data_type):
    response = None
    try:
        if options.put_method:
            try:
                if data_type == "raw":  # Check if data is anything but json
                    response = options.session.put(url, data=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects,
                                                   verify=options.verify_tls, timeout=options.request_timeout)
                else:  # Send a JSON request
                    response = options.session.put(url, json=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects,
                                                   verify=options.verify_tls, timeout=options.request_timeout)
                options.protocol = 'https'

            # Fall back to HTTP
            except SSLError:
                url_http = url.replace('https://', 'http://')  # Change protocol to http
                if data_type == "raw":  # Check if data is anything but json
                    response = options.session.put(url_http, data=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects, verify=False, timeout=options.request_timeout)
                else:  # Send a JSON request
                    response = options.session.put(url_http, json=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects,
                                                   verify=options.verify_tls, timeout=options.request_timeout)

                options.protocol = 'http'

        elif options.patch_method:        
            try:
                if data_type == "raw":  # Check if data is anything but json
                    response = options.session.patch(url, data=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects,
                                                   verify=options.verify_tls, timeout=options.request_timeout)
                else:  # Send a JSON request
                    response = options.session.patch(url, json=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects,
                                                   verify=options.verify_tls, timeout=options.request_timeout)
                options.protocol = 'https'

            # Fall back to HTTP
            except SSLError:
                url_http = url.replace('https://', 'http://')  # Change protocol to http
                if data_type == "raw":  # Check if data is anything but json
                    response = options.session.patch(url_http, data=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects, verify=False, timeout=options.request_timeout)
                else:  # Send a JSON request
                    response = options.session.patch(url_http, json=data, headers=headers, proxies=options.proxies,
                                                   allow_redirects=options.allow_redirects,
                                                   verify=options.verify_tls, timeout=options.request_timeout)

                options.protocol = 'http'
        else:

            try:
                if data_type == "raw":  # Check if data is anything but json
                    response = options.session.post(url, data=data, headers=headers, proxies=options.proxies,
                                                    allow_redirects=options.allow_redirects,
                                                    verify=options.verify_tls, timeout=options.request_timeout)
                else:  # Send a JSON request
                    response = options.session.post(url, json=data, headers=headers, proxies=options.proxies,
                                                    allow_redirects=options.allow_redirects,
                                                    verify=options.verify_tls, timeout=options.request_timeout)
                options.protocol = 'https'

                    # Fall back to HTTP
            except SSLError:
                url_http = url.replace('https://', 'http://')  # Change protocol to http
                if data_type == "raw":  # Check if data is anything but json
                    response = options.session.post(url_http, data=data, headers=headers, proxies=options.proxies,
                                                    allow_redirects=options.allow_redirects, verify=False, timeout=options.request_timeout)
                else:  # Send a JSON request
                    response = options.session.post(url_http, json=data, headers=headers, proxies=options.proxies,
                                                    allow_redirects=options.allow_redirects,
                                                    verify=options.verify_tls, timeout=options.request_timeout)
                options.protocol = 'http'

    except Exception as e:

        if options.debug:

            # Check if debug mode is activated
            debug_mode = options.debug
            # Print the stack trace to the screen
            traceback.print_exc()

            # Save the stack trace to the 'debug' directory
            save_stack_trace(debug_mode, sys.argv, options.request_file)
        else:
            error(f'{e}\n{red}[-]{reset} For a full stack trace error use the --debug flag')

    return response, headers, url


# Parsing headers from the request
def parse_headers(options, request):
    try:
        # Split the request into headers and body
        headers_end_index = request.find('\n\n')

        # If no double newline is found, try finding '\n\r\n'
        if headers_end_index == -1:
            headers_end_index = request.find('\n\r\n')

        # Extract the header content
        headers_content = request[:headers_end_index]

        # Extract headers using regular expression
        headers_list = re.findall(r'^(?P<name>[^:\r\n]+):\s*(?P<value>[^\r\n]*)', headers_content, flags=re.MULTILINE)

        # Convert the list of tuples to a list of dictionaries for easier manipulation
        headers_list = [{'key': key.strip(), 'value': value.strip()} for key, value in headers_list]

        # Convert the list of dictionaries to a dictionary
        headers = {item['key']: item['value'] for item in headers_list}

        # Split the request string by lines
        lines = request.split('\n')

        # Extract the host value from the 'Host' header
        host = [line.split(': ')[1] for line in lines if line.startswith('Host')][0].split()[0]

        # Just in case the user choose -A / --allowed flag
        options.host = host

        # Extract the path from the first line of the request
        path = lines[0].split(' ')[1]

        # Extract protocol from a predefined configuration
        protocol = config.protocol

        # Construct the URL from the extracted components
        url = f'{protocol}://{host}{path}'

        # Just in case the user choose -A / --allowed flag
        options.url = url

        keys_to_delete = []
        for key, value in headers.items():
            # Deleting unnecessary headers except cookies and authorization header
            if "Accept" in key:
                keys_to_delete.append(key)

        # Delete unnecessary headers
        for key in keys_to_delete:
            del headers[key]

        return headers, url

    except IndexError:
        error("A malformed request file was supplied, please check your request file.")

    except Exception as e:

        if options.debug:

            # Check if debug mode is activated
            debug_mode = options.debug
            # Print the stack trace to the screen
            traceback.print_exc()

            # Save the stack trace to the 'debug' directory
            save_stack_trace(debug_mode, sys.argv, options.request_file)
        else:
            error(f'{e}\n{red}[-]{reset} For a full stack trace error use the --debug flag')


def parse_request_file(request_file, options, file_name, original_extension, mimetype, magic_bytes=None,
                       file_data=None, module=None):
    try:
        try:
            request = ""  # Initialize an empty string to store the decoded request

            # Declaring an XML object and parsing the XML file
            tree = ET.parse(request_file)
            root = tree.getroot()

            for i in root:
                # Search for the 'request' element in the XML and extracting its text content
                request = i.find('request').text

                # Decode the base64 encoded content
                content = base64.b64decode(request)

                # Decode the content from latin-1 encoding
                request = content.decode('latin-1')

        except:
            # Open the request file as text
            with open(request_file, "r") as f:
                request = f.read()

        headers, url = parse_headers(options, request)

        # Check for a detection mode
        if options.detect:
            try:
                if module == 'polyglot':
                    with open(f"assets/samples/polyglot_sample.php", 'rb') as file:
                        file_data = file.read()
                elif not file_data:
                    with open(f"assets/samples/sample.{original_extension}", 'rb') as file:
                        file_data = file.read()
            except FileNotFoundError:
                error(f"File not found: assets/samples/sample.{original_extension}")

        # Check for exploitation mode
        elif options.exploitation:
            if module == 'polyglot':
                with open(f"assets/samples/polyglot_shell.php", 'rb') as file:
                    file_data = file.read()
            elif not file_data:
                file_data_b64 = config.webshells[original_extension]
                file_data = base64.b64decode(file_data_b64)

                # Checks for anti_malware detection mode
        elif options.anti_malware:
            if not file_data:
                file_data = config.eicar

                # Check if the binary data is bytes and decodes it
        if isinstance(file_data, bytes):
            file_data = file_data.decode('latin-1')

        # Check if mimetype and anti_malware is true and set the data without magic_bytes (Eicar string must be exact 68 chars)
        if magic_bytes and options.anti_malware:
            file_data = file_data

            # Add magic bytes to the binary data
        elif magic_bytes:
            file_data = f"{magic_bytes.decode('latin-1')}\n{file_data}"

        request = request.replace("\r\n", "\n").replace("\n", "\r\n")
        # Replace marker with a filename
        content = request.replace(config.filename_marker, file_name)

        xml_mimetypes = config.xml_mimetypes
        xml = False

        # Auto-detect xml and base64 the data binary
        for xml_mime in xml_mimetypes:
            if xml_mime in str(headers):
                xml = True
                break

        # Auto-detect JSON and base64 the data binary
        if "application/json" in str(headers):
            if isinstance(file_data, bytes):
                file_data = base64.b64encode(file_data)
            else:
                file_data = base64.b64encode(file_data.encode('latin-1'))

        if options.base64:
            if isinstance(file_data, bytes):
                file_data = base64.b64encode(file_data)
            else:
                file_data = base64.b64encode(file_data.encode('latin-1'))
        else:
            if not xml:
                if isinstance(file_data, bytes):
                    file_data = file_data.decode('latin-1')
                    # Replace marker with binary data
                    content = content.replace(config.data_marker, file_data)
                else:
                    content = content.replace(config.data_marker, file_data)
            else:
                if isinstance(file_data, bytes):
                    file_data = base64.b64encode(file_data)
                else:
                    file_data = base64.b64encode(file_data.encode('latin-1'))

        if isinstance(file_data, bytes):
            content = content.replace(config.data_marker, file_data.decode('latin-1'))
        else:
            content = content.replace(config.data_marker, file_data)

        # Handle various newlines and carriage returns
        try:
            content = content.split('\r\n\r\n', 1)
            body = content[1]
        except IndexError:
            try:
                content = content.split('\n\n', 1)
                body = content[1]
            except AttributeError:
                content = content[0]
                content = content.split('\n\n', 1)
                body = content[1]

        # Replace the mimetype marker with the file's mimetype
        data = body.replace(config.mimetype_marker, mimetype)

        try:
            data = data.encode("latin-1")
        except UnicodeDecodeError:
            data = data.encode("utf-8")

        if "application/json" not in str(headers):
            data_type = "raw"

        else:
            data_type = "json"
            try:
                data = json.loads(data)
            except json.decoder.JSONDecodeError:
                error(
                    "Null_byte_cutoff module is not supported with JSON data, please exclude null_byte_cutoff with -x null_byte_cutoff or uncomment the module in config.py.")

        # Sends the request
        response, headers, url = make_request(data, headers, options, url, data_type)

        return response, headers, url, mimetype

    except Exception as e:

        if options.debug:

            # Check if debug mode is activated
            debug_mode = options.debug
            # Print the stack trace to the screen
            traceback.print_exc()

            # Save the stack trace to the 'debug' directory
            save_stack_trace(debug_mode, sys.argv, options.request_file)
        else:
            error(f'{e}\n{red}[-]{reset} For a full stack trace error use the --debug flag')
