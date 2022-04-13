import socket
from . import RequestUtils
import ssl
import sys
import gzip

line_separator = "\r\n"

class Options():
    timeout = 7

def exception(message, function):
    message = str(function) + " => " + str(message)
    print(message)

def check_ssl(scheme):
    try:
        if scheme == "https://":
            return True
        else:
            return False
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def send(url, method, headers, body, timeout):
    try:
        host = RequestUtils.get_host_from_url(url)
        port = RequestUtils.get_url_port(url)
        raw_request = build_request(url, method, headers, body, host)

        use_ssl = check_ssl(RequestUtils.get_scheme_from_url(url))

        response = send_raw(raw_request, port, host, timeout, use_ssl)

        if response is not None:
            return response
            res = make_object(response)
            if res.status_code == 0:
                res = response
        else:
            res = None

        return res
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)


def gzip_decode(data):
    try:
        body = str(data[data.find('\r\n\r\n')+4:])
        try:
            decoded_body = str(gzip.decompress(bytes(body.encode())), "latin1")

            return decoded_body
        except Exception as error:
            pass

        return body
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def send_raw_with_exceptions(raw_request, port, host, connection_timeout, use_ssl):
    if use_ssl:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_default_certs()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        w_socket = context.wrap_socket(s, server_hostname=host)
        w_socket.settimeout(connection_timeout)
        w_socket.connect((host, int(port)))
    else:
        w_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        w_socket.settimeout(connection_timeout)
        w_socket.connect((host, int(port)))

    w_socket.send(bytes(raw_request, encoding="latin1"))
    data = w_socket.recv(4096).decode("latin1")
        
    if "transfer-encoding: chunked" in data.lower():
        while True:
            data += w_socket.recv(4096).decode("latin1")
            if "0\r\n\r\n" in data:
                break
    elif "content-length: " in data.lower():
        try:
            data_length = int(data.lower().split("content-length: ")[1].split("\r\n")[0])
            if data_length > 0:
                response_body = ""
                while True:
                    response_body += w_socket.recv(4096).decode("latin1")
                    if len(response_body) == data_length:
                        data += response_body
                        break
        except Exception as error:
            if "timed out" not in str(error):
                print('send_raw - body  =>  ' + str(error))

    w_socket.close()

    return data

def send_raw(raw_request, port, host, connection_timeout, use_ssl):
    try:
        data = send_raw_with_exceptions(raw_request, port, host, connection_timeout, use_ssl)

        return data
    except Exception as error:
        str_error = str(error)
#        print(str_error)
        if "Name or service not known" in str_error or 'Task Timeout' in str_error or "UnicodeError" in str_error:
            return None
        #exception(host + " " + str(error), sys._getframe().f_code.co_name)
        return None

def make_object(raw_response):
    try:
        class response():
            status_code = 0
            text = ""
            header = ""
            raw = ""

        splited_response = raw_response.split(line_separator + line_separator)

        headers = splited_response[0]
        if len(splited_response) > 1:
            text = splited_response[1]
        else:
            text = ""
        splited_headers = headers.split(" ")

        status_code = 0
        if len(splited_headers) > 1:
            status_code = int(splited_headers[1])

        response.status_code = status_code
        response.raw = raw_response
        response.text = text
        response.header = headers

        return response
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)


def build_request(url, method, headers, body, host):
    try:
        has_host = False
        has_connection = False
        has_content_length = False
        has_useragent = False

        path = RequestUtils.get_path_from_url(url)

        raw_request = method.upper() + " " + path + " HTTP/1.1" + line_separator

        for key, value in headers.items():
            if key.lower() == "host":
                has_host = True
            if "content-length" in key.lower():
                has_content_length = True
            if key.lower() == "connection":
                has_connection = True
            if key.lower() == "user-agent":
                has_useragent = True

            raw_request += key + ": " + value + line_separator

        if not has_host:
            raw_request += "Host: " + host + line_separator

        if not has_connection:
            raw_request += "Connection: close\r\n"

        if not has_useragent:
            raw_request += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36\r\n"     

        if len(body) > 0:
            if not has_content_length:
                raw_request += "Content-Length: " + str(RequestUtils.calculate_content_lentgh(body)) + line_separator
            raw_request += line_separator
            raw_request += body
        else:
            raw_request += line_separator

        return raw_request
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)
