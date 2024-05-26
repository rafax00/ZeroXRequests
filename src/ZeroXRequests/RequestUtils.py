
import requests
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
public_session = requests.Session()

def exception(message, function):
    message = str(function) + " => " + str(message)
    print(message)

def calculate_content_lentgh(body):
    try:
        return len(body)
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def add_path_to_url(url, pathname):
    try:
        port = get_string_port_from_url(url)
        host_value = get_host_from_url(url)
        scheme = get_scheme_from_url(url)
        old_path = get_path_from_url(url).split("?")[0].split("#")[0]
        
        if old_path.endswith("/"):
            new_path = old_path + pathname
        else:
            new_path = old_path + "/" + pathname
            
        query_parameters = url.split("?")
        string_query_parameters = ""
        if len(query_parameters) > 1:
            string_query_parameters = "?"
            for i in range(1, len(query_parameters)):
                string_query_parameters += query_parameters[i]
                
        new_url = scheme + host_value + port + new_path + string_query_parameters
        
        return new_url
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def get_url_port(url):
    try:
        scheme = get_scheme_from_url(url)
        splited_host = url.split(scheme)[1].split("/")[0].split("?")[0].split("#")[0].split(":")
        port = ""

        if "https://" == scheme:
            port = "443"
        elif "http://" == scheme:
            port = "80"

        if len(splited_host) > 1:
            port = splited_host[1]
        
        return port
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def remove_last_path_from_url(url):
    try:
        scheme = get_scheme_from_url(url)
        splited_scheme_url = url[len(scheme):]
        splited_parameters_url = url.split("?")[0].split("#")[0]
        splited_paths = splited_scheme_url.split("/")
        
        new_url = scheme
        if len(splited_paths) > 1:
            for i in range(0, len(splited_paths)-1):
                new_url += splited_paths[i] + "/"
        else:
            new_url += splited_paths[0] + "/"
                
        splited_query_parameters = url.split("#")[0].split("?")
        if len(splited_query_parameters) > 1:
            new_url += "?"
            for i in range(1, len(splited_query_parameters)):
                if i == len(splited_query_parameters)-1:
                    new_url += splited_query_parameters[i]
                else:
                    new_url += splited_query_parameters[i] + "?"
        
        splited_hash = url.split("#")
        if len(splited_hash) > 1:
            new_url += "#"
            for i in range(1, len(splited_hash)):
                if i == len(splited_hash)-1:
                    new_url += splited_hash[i]
                else:
                    new_url += splited_hash[i] + "#"
        
        return new_url
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)


def get_path_folder_from_url(url):
    try:
        folder = url.rsplit('/',1)
        
        return folder[0] + "/"
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def get_string_port_from_url(url):
    try:
        base = url.replace(get_scheme_from_url(url), "").split("?")[0].split("/")[0].split("#")[0]
        if ":" in base:
            return ":" + base.split(":")[1]
        else:
            return ""
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def get_path_from_url(url):
    try:
        host = get_host_from_url(url)
        scheme = get_scheme_from_url(url)
        string_port = get_string_port_from_url(url)

        url_base = scheme + host + string_port
        path = "/"
        splited_url = url.split(url_base)
        if len(splited_url) > 1:
            path = splited_url[1]
            
        if not path.startswith('/'):
            path = "/" + path
         
        return path
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def get_host_from_url(url):
    try:
        host = url.split("://")[1].split("/")[0].split("?")[0].split("#")[0].split(":")[0]

        return host
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)
        return "www.google.com"

def calculate_encoded_data(data):
    data = data.replace("\r\n", "rc")
    return str(hex(len(data)))[2:]

def make_request_public_session(url, method, headers, body):
    try:
        if len(body) > 0:
            prepped = requests.Request(method, url, data=body, headers=headers).prepare()
        else:
            prepped = requests.Request(method, url, headers=headers).prepare()

        req = public_session.send(prepped, verify=False, timeout=5, allow_redirects=False)

        return req
    except Exception as error:
        pass

def get_scheme_from_url(url):
    try:
        return url.split("://")[0] + "://"
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)

def make_request_unique_session(url, method, headers, body):
    try:
        private_session = requests.Session()
        if len(body) > 0:
            prepped = requests.Request(method, url, data=body, headers=headers).prepare()
        else:
            prepped = requests.Request(method, url, headers=headers).prepare()

        prepped.headers["Content-length"] = headers["Content-Length"]
        req = private_session.send(prepped, verify=False, timeout=10, allow_redirects=False)

        return req
    except Exception as error:
        pass

def create_raw_request(url, method, headers, body):
    try:
        has_host = False
        raw_request = method + " " + get_path_from_url(url) + " HTTP/1.1\r\n"
        for key, value in headers.items():
            if key.lower() == "host":
                has_host = True
            raw_request += key + ": " + value + "\r\n"

        if not has_host:
            raw_request += "Host: " + get_host_from_url(url) + "\r\n"

        raw_request += "\r\n"

        raw_request += body

        return raw_request
    except Exception as error:
        exception(error, sys._getframe().f_code.co_name)
