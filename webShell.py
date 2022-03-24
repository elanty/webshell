#!/usr/bin/env python
#coding=utf-8
# desc: 支持文件上传下载，支持远程执行shell命令(需要提前创建一个config.ini文件才行)

__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "bones7456"
__home_page__ = ""
 
import os, sys, platform
import posixpath
import BaseHTTPServer
from SocketServer import ThreadingMixIn
import threading
import urllib
import cgi
import shutil
import mimetypes
import re
import time
import ConfigParser 
import subprocess
import hashlib
import json

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
print ""
print '----------------------------------------------------------------------->> '
try:
   port = int(sys.argv[1])
except Exception, e:
   print '-------->> Warning: Port is not given, will use deafult port: 8902 '
   print '-------->> if you want to use other port, please execute: '
   print '-------->> python SimpleHTTPServerWithUpload.py port '
   print "-------->> port is a integer and it's range: 1024 < port < 65535 "
   port = 8902
   
if not 1024 < port < 65535:  port = 8902
serveraddr = ('', port)
print '-------->> Now, listening at port ' + str(port) + ' ...'
print '-------->> You can visit the URL:   http://localhost:' + str(port)
print '----------------------------------------------------------------------->> '
print "" 
username = "admin"
password = "admin@123"
enableAuth = True

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')
def md5_hash(s):
    m = hashlib.md5()
    m.update(s.encode(encoding='utf-8'))
    return m.hexdigest()
def modification_date(filename):
    # t = os.path.getmtime(filename)
    # return datetime.datetime.fromtimestamp(t)
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getmtime(filename)))

class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "SimpleHTTPWithUpload/" + __version__
    def do_GET(self):
        if self.path == '/login':
            if self.checkToken():
                self.send_response(301)
                self.send_header("Location", "/")
                self.end_headers()
                return
            return self.login()
        if not self.checkToken():
            self.send_response(301)
            self.send_header("Location", "/login")
            self.end_headers()
            return
        self.getOut()
    def do_POST(self):
        if not self.checkToken():
            self.send_response(301)
            self.send_header("Location", "/login")
            self.end_headers()
            return
        if self.path == '/api/user/check':  
            return self.userCheck()
        if self.path == '/api/start':
            return self.start()
        if self.path == '/api/startShell':
            return self.startShell()
        if self.path.startswith("/api/upload"):
            r, info = self.deal_post_data()
            f = StringIO()
            f.write(info)
            length = f.tell()
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", "text/palin")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            self.copyfile(f, self.wfile)
            f.close()
            return   
    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path[11:])
        osType = platform.system()
        try:
            if osType == "Linux":
                fn = os.path.join(path, fn[0].decode('gbk').encode('utf-8'))
            else:
                fn = os.path.join(path, fn[0])
        except Exception, e:
            return (False, "文件名请不要用中文，或者使用IE上传中文名的文件。")
        while os.path.exists(fn):
            fn += "_"
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                 
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "上传成功")
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")
    def start(self):
        length = int(self.headers.getheader('content-length'))
        qs = self.rfile.read(length)
        current = os.getcwd()
        conf = ConfigParser.SafeConfigParser()
        conf.read(current + '/config.ini')
        shell  = conf.get(json.loads(qs)['shell'],"shell")
        status = os.popen(shell)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        self.protocol_version="HTTP/1.1"
        while 1:
            buf = status.readline()
            if not buf:
                break
            self.wfile.writelines(buf)
            self.wfile.flush()
            print buf
    def startShell(self):
        length = int(self.headers.getheader('content-length'))
        qs = self.rfile.read(length)
        current = os.getcwd()
        shell  = current + json.loads(qs)['shell']
        status = os.popen(shell)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        while 1:
            buf = status.readline()
            if not buf:
                break
            self.wfile.writelines(buf)
            self.wfile.flush()
    def getOut(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return
        else:
            f = None   
            ctype = self.guess_type(path)
            try:
                f = open(path, 'rb')
                self.send_response(200)
                self.send_header("Content-type", ctype)
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                self.copyfile(f, self.wfile)
                f.close()
                return
            except IOError:
                self.send_error(404, "File not found")
            
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n')
        f.write('<html><head><title>webShell</title> <meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> </head>\n')
        f.write('<body> <h3>welcome to <span onclick="location=\'/\'">webShell</span></h3>\n')
        current = os.getcwd()
        conf = ConfigParser.SafeConfigParser()
        conf.read(current + '/config.ini')
        sections = conf.sections()
        if len(sections):
            f.write('<hr /> <h4>快捷方式</h4> \n')
            for s in sections:
                name = conf.get(s,"name")
                f.write("<input type=\"button\" value=\"%s\" onClick=\"start('%s')\">&nbsp&nbsp\n" % (name,s))
        f.write('<hr /> <h4>文件管理</h4>\n')
        f.write('<input type="file" id="file-uploader" name="file" /> &nbsp;&nbsp;\n')
        f.write('<input type="button" value="点击上传" onclick="uploadClick()" /> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; \n')
        f.write('<progress id="progress" value="50" max="100"></progress>')
        f.write('<label id="progress-label" for="progress">50%</label><br/><br/>\n')
        f.write(self.list_directory(path))
        f.write('<div id="shell_result_div" style="position: absolute;top:50;left:200;background-color: darkgrey;">\n')
        f.write('<label style="float:right" onclick="hideShellRes()">x&nbsp;&nbsp;</label><br/>\n')
        f.write('<textarea id="shell_result" style="min-height:300;max-height: 800;width:800;overflow:visible"></textarea></div>\n')
        f.write('<script type="text/javascript">\n')
        f.write('var showShellResult = false;\n')
        f.write('document.getElementById("shell_result_div").hidden = true;\n')
        f.write('document.getElementById("progress").hidden = true;\n')
        f.write('document.getElementById("progress-label").hidden = true;\n')
        f.write('function start(s){\n')
        f.write('showShellResult = true;\n')
        f.write('let screenHeight = document.body.clientHeight;\n')
        f.write('let screenWidth = document.body.clientWidth;\n')
        f.write('let height = document.body.clientHeight - 200;\n')
        f.write('height = height < 400 ? 400 : height;\n')
        f.write('let width = document.body.clientWidth - 400;\n')
        f.write('width = width < 600 ? 600 : width;\n')
        f.write('document.getElementById("shell_result").style.height=height;\n')
        f.write('document.getElementById("shell_result").style.width=width;\n')
        f.write('document.getElementById("shell_result_div").style.left=(document.body.clientWidth - width)/2 ;\n')
        f.write('document.getElementById(\'shell_result_div\').hidden = false;\n')
        f.write('document.getElementById("shell_result").value = "运行中...请稍后"\n')
        f.write('var obj = {shell:s};\n')
        f.write('var httpRequest = new XMLHttpRequest();\n')
        f.write('httpRequest.open("POST", "/api/start", true);\n')
        f.write('httpRequest.setRequestHeader("Content-type","application/json");\n')
        f.write('var s=JSON.stringify(obj);\n')
        f.write('httpRequest.send(JSON.stringify(obj));\n')
        f.write('httpRequest.onreadystatechange = function () {\n')
        f.write('if (httpRequest.readyState == 4 && httpRequest.status == 200) {if (!showShellResult){return;}\n')
        f.write('document.getElementById("shell_result_div").hidden = false;\n')
        f.write('document.getElementById("shell_result").value = httpRequest.responseText + "运行结束";}};\n')
        f.write('httpRequest.onprogress = function(){\n')
        f.write('if (!showShellResult){return;}\n')
        f.write('document.getElementById("shell_result_div").hidden = false;\n')
        f.write('document.getElementById("shell_result").value = httpRequest.responseText;}}\n')

        f.write('function startShell(s){\n')
        f.write('showShellResult = true;\n')
        f.write('let screenHeight = document.body.clientHeight;\n')
        f.write('let screenWidth = document.body.clientWidth;\n')
        f.write('let height = document.body.clientHeight - 200;\n')
        f.write('height = height < 400 ? 400 : height;\n')
        f.write('let width = document.body.clientWidth - 400;\n')
        f.write('width = width < 600 ? 600 : width;\n')
        f.write('document.getElementById("shell_result").style.height=height;\n')
        f.write('document.getElementById("shell_result").style.width=width;\n')
        f.write('document.getElementById("shell_result_div").style.left=(document.body.clientWidth - width)/2 ;\n')
        f.write('document.getElementById(\'shell_result_div\').hidden = false;\n')
        f.write('document.getElementById("shell_result").value = "运行中...请稍后"\n')
        f.write('var obj = {shell:s};\n')
        f.write('var httpRequest = new XMLHttpRequest();\n')
        f.write('httpRequest.open("POST", "/api/startShell", true);\n')
        f.write('httpRequest.setRequestHeader("Content-type","application/json");\n')
        f.write('var s=JSON.stringify(obj);\n')
        f.write('httpRequest.send(JSON.stringify(obj));\n')
        f.write('httpRequest.onreadystatechange = function () {\n')
        f.write('if (httpRequest.readyState == 4 && httpRequest.status == 200) {if (!showShellResult){return;}\n')
        f.write('document.getElementById("shell_result_div").hidden = false;\n')
        f.write('document.getElementById("shell_result").value = httpRequest.responseText + "运行结束";}};\n')

        f.write('httpRequest.onprogress = function(){\n')
        f.write('if (!showShellResult){return;}\n')
        f.write('document.getElementById("shell_result_div").hidden = false;\n')
        f.write('document.getElementById("shell_result").value = httpRequest.responseText;}}\n')
        f.write('function hideShellRes(){\n')
        f.write('document.getElementById("shell_result_div").hidden = true;\n')
        f.write('showShellResult = false;}\n')
        f.write('function uploadClick(){\n')
        f.write('var fileObj = document.getElementById("file-uploader").files[0];\n')
        f.write('if(fileObj == null){alert("请先选择要上传的文件");return;}\n')
        f.write('var url = "/api/upload" + this.location.pathname;\n')
        f.write('var form = new FormData();\n')
        f.write('form.append("file", fileObj);\n')
        f.write('var xhr = new XMLHttpRequest();\n')
        f.write('xhr.open("post", url, true);\n')
        f.write('xhr.upload.onprogress = progressFunction;\n')
        f.write('xhr.upload.onloadstart = function(){\n')
        f.write('document.getElementById("progress").hidden = false;\n')
        f.write('document.getElementById("progress-label").hidden = false;};\n')
        f.write('xhr.send(form);\n')
        f.write('xhr.onreadystatechange = function () {\n')
        f.write('if (xhr.readyState == 4 && xhr.status == 200) {\n')
        f.write('progress.value = 100;\n')
        f.write('document.getElementById("progress-label").innerHTML = "100%";\n')
        f.write('document.getElementById("progress").hidden = true;\n')
        f.write('document.getElementById("progress-label").hidden = true;\n')
        f.write('var obj = document.getElementById(\'file-uploader\');\n')
        f.write('alert(xhr.responseText);\n')
        f.write('obj.outerHTML = obj.outerHTML;}};}\n')
        f.write('progress.value = 0;\n')
        f.write('document.getElementById("progress-label").innerHTML = "0%";\n')
        f.write('function progressFunction(evt) {\n')
        f.write('var progress = document.getElementById("progress");\n')
        f.write('if (evt.lengthComputable) {\n')
        f.write('let percent = (evt.loaded / evt.total) * 100;\n')
        f.write('progress.value = percent;\n')
        f.write('document.getElementById("progress-label").innerHTML = Math.round(percent) + "%";\n')
        f.write('}}</script> </body></html>\n')

        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
    def login(self):
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n')
        f.write('<html><head><title>webShell</title> <meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> </head>\n')
        f.write('<body> <h3>welcome to webShell</h3> <hr/>\n')
        f.write('<div style="top:100;text-align: center;">\n')
        f.write('<label>用户</label>&nbsp;&nbsp; <input id="user" type="text"/><br/>\n')
        f.write('<label>密码</label>&nbsp;&nbsp; <input id="pass" type="password" onkeydown="KeyDown()"/><br/><br/>\n')
        f.write('<input type="button" onclick="login()" value="登录"/> \n')
        f.write('</div></div>\n')
        f.write('<script type="text/javascript">\n')
        f.write('function KeyDown(){if(event.keyCode == 13){event.returnValue=false;event.cancel = true;login();}}\n')
        f.write('function login(){\n')
        f.write('var httpRequest = new XMLHttpRequest();\n')
        f.write('httpRequest.open("POST", "/api/user/check", true);\n')
        f.write('httpRequest.setRequestHeader("Content-type","application/json");\n')
        f.write('obj = {user:document.getElementById("user").value,pass:document.getElementById("pass").value};\n')
        f.write('var s=JSON.stringify(obj);\n')
        f.write('httpRequest.send(JSON.stringify(obj));\n')
        f.write('httpRequest.onreadystatechange = function () {\n')
        f.write('if (httpRequest.readyState == 4 && httpRequest.status == 200) {\n')
        f.write('var data = JSON.parse(httpRequest.responseText);\n')
        f.write('if (data.code === 0){\n')
        f.write('var exp = new Date();\n')
        f.write('exp.setTime(exp.getTime() + 30 * 24 * 60 * 60 * 1000);\n')
        f.write('document.cookie = "token" + "=" + escape(data.token) + ";expires=" + exp.toGMTString() + ";path=/";\n')
        #f.write('document.write("<form action=\'/\' method=post name=form style=\'display:none\'>");\n')
        #f.write('document.write("<input type=hidden/>");\n')
        #f.write('document.write("</form>");\n')
        #f.write('document.form.submit(); \n')
        f.write('window.location.href=\'/\'\n')
        f.write('}else{alert("用户名或密码不正确");}}};}\n')
        f.write('</script> </body></html>\n')
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
    def checkToken(self):
        if not enableAuth:
            return True
        if self.path in ["/api/user/check"]:
            return True
        oldmd5 = md5_hash(username + password)
        cookie = self.headers.getheader('Cookie')
        if cookie is None:
            return False
        for k in cookie.split(';'):
            k = k.strip()
            if k.split('=')[0] == 'token':
                if oldmd5 == k.split('=')[1]:
                    return True
        return False
    def userCheck(self):
        length = int(self.headers.getheader('content-length'))
        qs = self.rfile.read(length)
        oldmd5 = md5_hash(username + password)
        md5 = md5_hash(json.loads(qs)['user'] + json.loads(qs)['pass'])
        f = StringIO()
        if md5 == oldmd5:
            f.write('{"code":0,"token":"' + md5 + '"}')
        else:
            f.write('{"code":500}')
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
    def list_directory(self,path):  
        out = ""
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        if not self.path == "/":
            out = out + '<table><tr><td width="50%%"><a href="../">..</a></td><td width="10%%"></td><td width="20%%"></td><td width="20%%"></td></tr></table>\n'
        for name in list:
            fullname = os.path.join(path, name)
            colorName = displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                colorName = '<span style="background-color: #CEFFCE;">' + name + '/</span>'
                displayname = name
                linkname = name + "/"
            if os.path.islink(fullname):
                colorName = '<span style="background-color: #FFBFFF;">' + name + '@</span>'
                displayname = name
                # Note: a link to a directory displays with @ and links with /
            filename = path  + "/" + displayname
            if os.path.isfile(fullname):
                ret = os.access(fullname, os.X_OK)
                if ret and fullname.rsplit('.',1)[1] in ["sh",'py']:
                    out = out + '<table><tr><td width="50%%"><a href="{}">{}</a></td><td width="10%%"><input type=\"button\" value=\"执行\" onClick=\"startShell(\'{}\')\"></td><td width="20%%">{}</td><td width="20%%">{}</td></tr></table>\n'.format(
                    urllib.quote(linkname), colorName,self.path + name,
                        sizeof_fmt(os.path.getsize(filename)), modification_date(filename))
                    continue
            out = out + '<table><tr><td width="50%%"><a href="{}">{}</a></td><td width="10%%"></td><td width="20%%">{}</td><td width="20%%">{}</td></tr></table>\n'.format(
                    urllib.quote(linkname), colorName,
                        sizeof_fmt(os.path.getsize(filename)), modification_date(filename))
        return out
    def translate_path(self, path):
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)
    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
        extensions_map = mimetypes.types_map.copy()
        extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
class ThreadingServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass
def start(HandlerClass = SimpleHTTPRequestHandler,
       ServerClass = BaseHTTPServer.HTTPServer):
    BaseHTTPServer.start(HandlerClass, ServerClass)
 
if __name__ == '__main__':
    srvr = ThreadingServer(serveraddr, SimpleHTTPRequestHandler)
    srvr.serve_forever() 
