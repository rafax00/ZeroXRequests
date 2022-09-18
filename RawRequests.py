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
        context = ssl._create_unverified_context()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        w_socket = context.wrap_socket(s, server_hostname=host)
        w_socket.settimeout(connection_timeout)
        w_socket.connect((host, int(port)))
    else:
        w_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        w_socket.settimeout(connection_timeout)
        w_socket.connect((host, int(port)))
    
    w_socket.sendall(bytes(raw_request, encoding="latin1"))
    
    data = w_socket.recv(4096).decode("latin1")
    
    data_received = False
    
    try:
        headers_data = data.split('\r\n\r\n')[0]
        expected_data_length = None
        
        try:
            if '\r\ncontent-length:' in headers_data.lower():
                expected_data_length = int(headers_data.lower().split('\r\ncontent-length:')[1].split('\r')[0].split('\n')[0].replace(' ', ''))
            elif '\r\ntransfer-encoding: chunked' in headers_data.lower():
                expected_data_length = "chunked"
        except:
            pass
            
        if expected_data_length != None and expected_data_length != "chunked":
            if len(data.replace(headers_data+'\r\n\r\n', '')) + 2 >= expected_data_length:
                data_received = True
                
        elif expected_data_length == "chunked" and "0\r\n\r\n" in data.replace(headers_data+'\r\n\r\n', ''):
            data_received = True
        
        if not data_received:    
            while True:
                if expected_data_length != None and expected_data_length != "chunked":
                    if len(data.replace(headers_data+'\r\n\r\n', '')) + 2 >= expected_data_length:
                        break
            
                chunk = w_socket.recv(4096).decode("latin1")
                
                if expected_data_length == "chunked" and "0\r\n\r\n" in chunk:
                    data = data + chunk;
                    break
                    
                elif len(chunk) == 0:
                    break
                    
                data = data + chunk;
    except:
        pass
        
    w_socket.close()

    return data

def send_raw(raw_request, port, host, connection_timeout, use_ssl):
    try:
        data = send_raw_with_exceptions(raw_request, port, host, connection_timeout, use_ssl)

        return data
    except Exception as error:
        str_error = str(error)
        if "Name or service not known" in str_error or 'Task Timeout' in str_error or "UnicodeError" in str_error:
            return None
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
