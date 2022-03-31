#!/usr/bin/env python
#coding=utf-8
# desc: 支持文件上传下载，支持远程执行shell命令(需要提前创建一个webShellConfig.ini文件才行)

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
import codecs
import urlparse

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
reload(sys) 
sys.setdefaultencoding('utf8')   
print ""
print '----------------------------------------------------------------------->> '
try:
   port = int(sys.argv[1])
except Exception, e:
   print '-------->> Warning: Port is not given, will use deafult port: 8903 '
   print '-------->> if you want to use other port, please execute: '
   print '-------->> python SimpleHTTPServerWithUpload.py port '
   print "-------->> port is a integer and it's range: 1024 < port < 65535 "
   port = 8903
   
if not 1024 < port < 65535:  port = 8903
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
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getmtime(filename)))
def getScript():
    s = '\tvar operateStatus = "";\n\tvar operateFile = "";\n\tvar showShellResult = false;\n\tvar showUnzipResult = false;\n\tvar showZipResult = false;\n\tvar selectPath = "";\n\n' 
    s = s + '\tfunction jquery(id) {\n\t\treturn document.getElementById(id);\n\t}\n\n\tfunction fileSearchTextDown() {\n\t\tif (event.keyCode == 13) {\n\t\t\tevent.returnValue = false;\n\t\t\tevent.cancel = true;\n\t\t\tsearchFile();\n\t\t}\n\t}\n\n'  
    s = s + '\tfunction editFile(file) {\n\t\toperateStatus = "edit";\n\t\toperateFile = file;\n\t\tajax("/api/download", {fileName: file}, function (data) {\n\t\t\tsetEditDiv(true, true, "edit");\n\t\t\tjquery("edit_text").value = data;\n\t\t});\n\t}\n\n'
    s = s + '\tfunction deleteFile(file) {\n\t\tif(confirm(`确认删除${file}吗`)){\n\t\t\tajax("/api/delete", {fileName: file}, function (data) {\n\t\t\t\twindow.location.reload();\n\t\t\t});\n\t\t}\n\t}\n\n'
    s = s + '\tfunction renameFile(id, file, fileName, color) {\n\t\tdocument.getElementById("fileTableTd_" + id).innerHTML = `<input id="fileTableTdText_${id}" type="text" value="${fileName}">&nbsp;` +\n\t\t\t`<input style="background-color: green;" '
    s = s + 'type="button" value="√" onClick="renameSaveClick(\'${id}\',\'${file}\')">&nbsp;` +\n\t\t\t`<input style="background-color: red;" type="button" value="X" onClick="renameCancelClick(\'${id}\',\'${fileName}\',\'${color}\')">`;\n\n\t}\n\n'
    s = s + '\tfunction unzipFile(file) {\n\t\tshowUnzipResult = true;\n\t\toperateStatus = "unzip";\n\t\tsetEditDiv(true, false, "unzip");\n\t\tjquery("edit_text").value = "解压中...请稍后"\n\t\tlet httpRequest = ajax("/api/unzip", {fileName: file}, '
    s = s + 'function (data) {\n\t\t\tif (!showUnzipResult) {\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tjquery("edit_text").value = data + "运行结束";\n\t\t\tjquery("edit_text").scrollTop=jquery("edit_text").scrollHeight;\n\t\t});\n\t\thttpRequest.onprogress = '
    s = s + 'function () {\n\t\t\tif (!showUnzipResult) {\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tjquery("edit_text").value = httpRequest.responseText;\n\t\t\tjquery("edit_text").scrollTop=jquery("edit_text").scrollHeight;\n\t\t};\n\t}\n\n'
    s = s + '\tfunction zipFile(file) {\n\t\tshowZipResult = true;\n\t\toperateStatus = "zip";\n\t\tsetEditDiv(true, false, "zip");\n\t\tjquery("edit_text").value = "解压中...请稍后";\n\t\tlet httpRequest = ajax("/api/zip", {fileName: file}, '
    s = s + 'function (data) {\n\t\t\tif (!showZipResult) {\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tjquery("edit_text").value = data + "运行结束";\n\t\t\tjquery("edit_text").scrollTop=jquery("edit_text").scrollHeight;\n\t\t});\n\t\thttpRequest.onprogress = '
    s = s + 'function () {\n\t\t\tif (!showZipResult) {\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tjquery("edit_text").value = httpRequest.responseText;\n\t\t\tjquery("edit_text").scrollTop=jquery("edit_text").scrollHeight;\n\t\t};\n\t}\n\n'
    s = s + '\tfunction mvFile(file) {\n\t\toperateStatus = "mv";\n\t\toperateFile = file;\n\t\tsetEditDiv(true, true, "mv");\n\t\tpathSelectClick(getPath())\n\t}\n\n\t'
    s = s + 'function cpFile(file) {\n\t\toperateStatus = "cp";\n\t\toperateFile = file;\n\t\tsetEditDiv(true, true, "cp");\n\t\tpathSelectClick(getPath())\n\t}\n\n\t'
    s = s + 'function playVideo(file) {\n\t\tsetEditDiv(true, false, "video");\n\t\tjquery("videoPlay").src = "/file" + file;;\n\t}\n\n\tfunction playAudio(file) {\n'
    s = s + '\t\tsetEditDiv(true, false, "audio");\n\t\tjquery("audioPlay").src = "/file" + file;\n\t}\n\n\tfunction execute(s) {\n\t\tshowShellResult = true;\n'
    s = s + '\t\tsetEditDiv(true, false, "edit");\n\t\tjquery("edit_text").value = "运行中...请稍后"\n\t\tlet httpRequest = ajax("/api/start", {shell: s}, '
    s = s + 'function (data) {\n\t\t\tif (!showShellResult) {\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tjquery("edit_text").value = data + "运行结束";\n\t\t\tjquery("edit_text").scrollTop=jquery("edit_text").scrollHeight;\n\t\t});\n\t\thttpRequest.onprogress = '
    s = s + 'function () {\n\t\t\tif (!showShellResult) {\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tjquery("edit_text").value = httpRequest.responseText;\n\t\t\tjquery("edit_text").scrollTop=jquery("edit_text").scrollHeight;\n\t\t};\n\t}\n\n\t'
    s = s + 'function hideEditDev() {\n\t\tjquery("modal_div").hidden = true;\n\t\tshowShellResult = false;\n\t\tshowUnzipResult = false;\n\t\tshowZipResult = false;\n\t\tselectPath = "";\n\t\tjquery("videoPlay").src = "";\n\t\tjquery("audioPlay").src = "";\n\t\tif(operateStatus === "unzip" || operateStatus === "zip"){\n\t\t\twindow.location.reload();\n\t\t}\n\t}\n'
    s = s + '\n\tfunction uploadClick() {\n\t\tvar fileObj = jquery("file-uploader").files[0];\n\t\tif (fileObj == null) {\n\t\t\talert("请先选择要上传的文件");\n\t\t\treturn;\n\t\t}\n\t\tvar url = "/api/upload" + this.location.pathname;\n\t\tvar form = new FormData();\n'
    s = s + '\t\tform.append("file", fileObj);\n\t\tvar xhr = new XMLHttpRequest();\n\t\txhr.open("post", url, true);\n\t\txhr.upload.onprogress = progressFunction;\n\t\txhr.upload.onloadstart = function () {\n\t\t\tjquery("progress").hidden = false;\n'
    s = s + '\t\t\tjquery("progress-label").hidden = false;\n\t\t};\n\t\txhr.send(form);\n\t\txhr.onreadystatechange = function () {\n\t\t\tif (xhr.readyState == 4 && xhr.status == 200) {\n\t\t\t\tjquery("progress").value = 100;\n\t\t\t\tjquery("progress-label").innerHTML = "100%";\n'
    s = s + '\t\t\t\tjquery("progress").hidden = true;\n\t\t\t\tjquery("progress-label").hidden = true;\n\t\t\t\twindow.location.reload();\n\t\t\t\talert(xhr.responseText);\n\t\t\t\tjquery("file-uploader").outerHTML = jquery("file-uploader").outerHTML;\n\t\t\t\tjquery("progress").value = 0;\n\t\t\t\tjquery("progress-label").innerHTML = "0%";\n\t\t\t}\n\t\t};\n\t}\n\n'
    s = s + '\tfunction progressFunction(evt) {\n\t\tif (evt.lengthComputable) {\n\t\t\tlet percent = (evt.loaded / evt.total) * 100;\n\t\t\tjquery("progress").value = percent;\n\t\t\tjquery("progress-label").innerHTML = Math.round(percent) + "%";\n\n\t\t}\n\t}\n\n'
    s = s + '\tfunction setEditDiv(isShow, isShowSaveButton, type) {\n\t\tjquery("edit_text").hidden = true;\n\t\tjquery("videoPlay").hidden = true;\n\t\tjquery("audioPlay").hidden = true;\n\t\tjquery("fileDirSelect").hidden = true;\n'
    s = s + '\t\tswitch (type) {\n\t\t\tcase "edit":\n\t\t\tcase "unzip":\n\t\t\tcase "zip":\n\t\t\t\tjquery("edit_text").style.height = `${document.body.clientHeight < 600 ? 400 : document.body.clientHeight - 200}px`;\n\t\t\t\tjquery("edit_text").style.width = `${document.body.clientWidth < 1000 ? 600 : document.body.clientWidth - 400}px`;\n'
    s = s + '\t\t\t\tjquery("modal_div").style.left = `${document.body.clientWidth < 600 ? 0 : 200}px`;\n\t\t\t\tjquery("edit_text").hidden = false;\n\t\t\t\tbreak;\n\t\t\tcase "video":\n\t\t\t\tjquery("videoPlay").style.height = `${document.body.clientHeight < 600 ? 400 : document.body.clientHeight - 200}px`;\n'
    s = s + '\t\t\t\tjquery("videoPlay").style.width = `${document.body.clientWidth < 1000 ? 600 : document.body.clientWidth - 400}px`;\n\t\t\t\tjquery("modal_div").style.left = `${document.body.clientWidth < 600 ? 0 : 200}px`;\n\t\t\t\tjquery("videoPlay").hidden = false;\n\t\t\t\tbreak;\n\t\t\tcase "audio":\n'
    s = s + '\t\t\t\tjquery("audioPlay").style.height = "100px";\n\t\t\t\tjquery("audioPlay").style.width = `${document.body.clientWidth < 1000 ? 600 : document.body.clientWidth - 400}px`;\n\t\t\t\tjquery("modal_div").style.left = `${document.body.clientWidth < 600 ? 0 : 200}px`;\n'
    s = s + '\t\t\t\tjquery("audioPlay").hidden = false;\n\t\t\t\tbreak;\n\t\t\tcase "mv":\n\t\t\tcase "cp":\n\t\t\t\tjquery("fileDirSelect").style.height = `${document.body.clientHeight < 600 ? 400 : document.body.clientHeight - 200}px`;\n'
    s = s + '\t\t\t\tjquery("fileDirSelect").style.width = `${document.body.clientWidth < 1000 ? 600 : document.body.clientWidth - 400}px`;\n\t\t\t\tjquery("modal_div").style.left = `${document.body.clientWidth < 600 ? 0 : 200}px`;\n\t\t\t\tjquery("fileDirSelect").hidden = false;\n\t\t\t\tbreak;\n\t\t}\n\t\tif (isShow) {\n\t\t\tjquery("modal_div").hidden = false;\n'
    s = s + '\t\t\tif (isShowSaveButton) {\n\t\t\t\tjquery("editSaveButton").hidden = false;\n\t\t\t} else {\n\t\t\t\tjquery("editSaveButton").hidden = true;\n\t\t\t}\n\t\t} else {\n\t\t\tjquery("modal_div").hidden = true;\n\t\t}\n\t}\n\n\tfunction ajax(url, obj, func) {\n\t\tlet httpRequest = new XMLHttpRequest();\n\t\thttpRequest.open("POST", url, true);\n\t\thttpRequest.setRequestHeader("Content-type", "application/json");\n\t\thttpRequest.send(JSON.stringify(obj));\n\t\thttpRequest.onreadystatechange = function () {\n\t\t\tif (httpRequest.readyState === 4 && httpRequest.status === 200) {\n\t\t\t\tlet obj = httpRequest.responseText;\n\t\t\t\ttry {\n\t\t\t\t\tobj = JSON.parse(obj);\n\t\t\t\t} catch (e) {\n\t\t\t\t}\n\t\t\t\tfunc(obj);\n\t\t\t}\n\t\t};\n\t\treturn httpRequest;\n\t}\n\n'
    s = s + '\tfunction renameSaveClick(id, oldName) {\n\t\tlet newName = jquery("fileTableTdText_" + id).value;\n\t\tajax("/api/rename", {oldName: oldName, newName: getPath() + newName}, function (data) {\n\t\t\twindow.location.reload();\n\t\t});\n\t}\n\n\tfunction renameCancelClick(id, oldName,color) {\n\t\tjquery("fileTableTd_" + id).innerHTML = `<a style="background:{color}" id="fileTable_a_${id}" href="${oldName}">${oldName}</a>`;\n\t}\n\n\tfunction pathSelectClick(fileDir) {\n\t\tfileDir = fileDir.endsWith("/") ? fileDir : fileDir + "/";\n\t\tselectPath = fileDir;\n\t\tajax("/api/dirList", {dir: fileDir}, function (data) {\n\t\t\tlet str = `<h4>${fileDir}</h4><br/>`;\n\t\t\tif (fileDir !== "/") {\n\t\t\tlet f = fileDir.substr(0, fileDir.length - 1);'
    s = s + '\t\t\t\tstr = str + `&nbsp;&nbsp;&nbsp;&nbsp;<label onclick="pathSelectClick(\'${f.substring(0, f.lastIndexOf("\\/"))}\')">..</label><br/>`\n\t\t\t}\n\t\t\telse{\n\t\t\t\tfileDir="";\n\t\t\t}\n\t\t\tfor (let i = 0; i < data.data.length; i++) {\n\t\t\t\tstr = str + `&nbsp;&nbsp;&nbsp;&nbsp;<label onclick="pathSelectClick(\'${fileDir + data.data[i]}\')">${data.data[i]}</label><br/>`\n\t\t\t}\n\t\t\tjquery("fileDirSelect").innerHTML = str;\n\t\t});\n\t}\n\n\tfunction selectChange(id) {\n\t\tlet fileName = getPath() + jquery("fileTable_a_" + id).innerHTML;\n\t\tswitch (jquery("fileTableSelect_" + id).value) {\n\t\t\tcase "delete":\n\t\t\t\tdeleteFile(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "rename":\n'
    s = s + '\t\t\t\trenameFile(id, fileName, jquery("fileTable_a_" + id).innerHTML, jquery("fileTable_a_" + id).style.background);\n\t\t\tbreak;\n\t\t\tcase "video":\n\t\t\t\tplayVideo(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "audio":\n\t\t\t\tplayAudio(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "edit":\n\t\t\t\teditFile(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "cp":\n\t\t\t\tcpFile(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "mv":\n\t\t\t\tmvFile(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "unzip":\n\t\t\t\tunzipFile(fileName);\n\t\t\t\tbreak;\n\t\t\tcase "zip":\n\t\t\t\tzipFile(fileName);\n\t\t\t\tbreak;\n\t\t}\n\t\tjquery("fileTableSelect_" + id).value = "";\n\t}\n\n\tfunction searchFile() {\n\t\tlet text = jquery("fileSearchText").value;\n\t\tif (text !== "") {\n'
    s = s + '\t\t\twindow.location.href = document.location.pathname + "?search=" + text;\n\t\t} else {\n\t\t\twindow.location.href = document.location.pathname;\n\t\t}\n\n\t}\n\n\tfunction addNewDir() {\n\t\tlet newFileName = prompt("请输入文件名", "");\n\t\tif (newFileName != null && newFileName != "") {\n\t\t\tajax("/api/addNewDir", {fileName: getPath() + newFileName}, function (data) {\n\t\t\t\talert(data.message);\n\t\t\t\twindow.location.reload();\n\t\t\t});\n\t\t}\n\n\t}\n\n\tfunction getPath() {\n\t\tlet path = document.location.pathname.split("/file")[1];\n\t\tif (!path.endsWith("/")) {\n\t\t\tpath = path + "/"\n\t\t}\n\t\treturn decodeURIComponent(path);\n\t}\n\n\tfunction editSaveClick() {\n\t\tif (operateStatus === "mv") {\n'
    s = s + '\t\t\tajax("/api/mv", {fileName: operateFile, newPath: selectPath}, function (data) {\n\t\t\t\talert(data.message);\n\t\t\t\twindow.location.reload();\n\t\t\t});\n\t\t} else if (operateStatus === "cp") {\n\t\t\tajax("/api/cp", {fileName: operateFile, newPath: selectPath}, function (data) {\n\t\t\t\talert(data.message);\n\t\t\t\twindow.location.reload();\n\t\t\t});\n\t\t} else if (operateStatus === "edit") {\n\t\t\tajax("/api/edit", {fileName: operateFile, content: jquery("edit_text").value}, function (data) {\n\t\t\t\talert(data.message);\n\t\t\t\tsetEditDiv(false, false, "edit");\n\t\t\t});\n\t\t}\n\t}\n\n\tjquery("modal_div").hidden = true;\n\tjquery("progress").hidden = true;\n\tjquery("progress-label").hidden = true;\n\tlet fileSearchText = window.location.search.substr(1).match(new RegExp("(^|&)search=([^&]*)(&|$)", "i"));\n\tjquery("fileSearchText").value = fileSearchText != null && fileSearchText[2] != null ? decodeURI(fileSearchText[2]) : "";\n'
    return s
class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "SimpleHTTPWithUpload/" + __version__
    def do_GET(self):
        if self.path == '/web/login':
            if self.checkToken():
                self.send_response(301)
                self.send_header("Location", "/")
                self.end_headers()
                return
            return self.login()
        if not self.checkToken():
            self.send_response(301)
            self.send_header("Location", "/web/login")
            self.end_headers()
            return
        if not self.path.startswith("/file/"):
            self.send_response(301)
            self.send_header("Location", "/file/")
            self.end_headers()
            return
        self.getOut()
    def do_POST(self):
        if not self.checkToken():
            self.send_response(301)
            self.send_header("Location", "/web/login")
            self.end_headers()
            return
        if self.path == '/api/user/check':  
            return self.userCheck()
        if self.path == '/api/start':
            return self.start()
        if self.path == '/api/startShell':
            return self.startShell()
        if self.path == '/api/download':
            return self.downloadFile()
        if self.path == '/api/delete':
            return self.deleteFile()
        if self.path == '/api/unzip':
            return self.unzipFile()
        if self.path == '/api/zip':
            return self.zipFile()
        if self.path == '/api/addNewDir':
            return self.addNewDir()
        if self.path == '/api/mv':
            return self.mvFile()
        if self.path == '/api/cp':
            return self.cpFile()
        if self.path == '/api/edit':
            return self.saveEditedFile()
        if self.path == '/api/rename':
            return self.renameFile()
        if self.path == '/api/dirList':
            return self.getDirList()
        if self.path.startswith("/api/upload"):
            r, info = self.upload()
            self.sendMessage(info)
            return   
    def upload(self):
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
        path = self.translate_path(self.path[16:])
        osType = platform.system()
        try:
            if osType == "Linux":
                fn = os.path.join(path, fn[0].decode('utf-8').encode('utf-8'))
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
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        conf = ConfigParser.SafeConfigParser()
        conf.read(os.getcwd() + '/webShellConfig.ini')
        shell  = conf.get(json.loads(qs)['shell'],"shell")
        status = os.popen(shell)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        self.protocol_version="HTTP/1.1"
        self.wfile.writelines("运行中...请稍后" + " " * 1024)
        while 1:
            buf = status.readline()
            if not buf:
                break
            self.wfile.writelines(buf)
            self.wfile.flush()
        status.close()
    def getOut(self):
        path = self.translate_path(self.path[5:])
        if os.path.isdir(path):
            p = self.path.split('?',1)[0]
            if not p.endswith('/'):
                if len(self.path.split('?',1)) > 1:
                    self.send_response(301)
                    self.send_header("Location", p + "/?" + self.path.split('?',1)[1])
                    self.end_headers()
                    return
                else:
                    self.send_response(301)
                    self.send_header("Location", self.path + "/")
                    self.end_headers()
                    return
        else:
            if path.endswith('.mp4') or path.endswith('.mp3'):
                rangeString = self.headers.getheader("Range")
                if rangeString:
                    range1 = int(rangeString[int(rangeString.index('=') + 1):rangeString.index('-')])  
                    ctype = self.guess_type(path)
                    try:
                        f = open(path, 'rb')
                        fs = os.fstat(f.fileno())
                        self.send_response(206)
                        self.send_header("Content-type", ctype)
                        self.send_header("Content-Range", "bytes %s-%s/%s" % (range1,fs[6] -1,fs[6]))
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("content-disposition", "attachment;filename=" + os.path.basename(f.name))
                        self.send_header("Content-Length", str(fs[6] - range1))
                        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                        self.end_headers()
                        f.seek(range1)
                        self.copyfile(f, self.wfile)
                        f.close()
                        return
                    except IOError:
                        self.send_error(404, "File not found")
                        return
            f = None   
            ctype = self.guess_type(path)
            try:
                f = open(path, 'rb')
                self.send_response(200)
                self.send_header("Content-type", ctype)
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.send_header("content-disposition", "attachment;filename=" + os.path.basename(f.name))
                self.end_headers()
                self.copyfile(f, self.wfile)
                f.close()
                return
            except IOError:
                self.send_error(404, "File not found")
                return
            
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n')
        f.write('<html>\n<head>\n\t<title>webShell</title>\n\t<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n</head>\n')
        f.write('<body>\n\t<h3>welcome to <span onclick="location=\'/\'">webShell</span></h3>\n')
        conf = ConfigParser.SafeConfigParser()
        conf.read(os.getcwd() + '/webShellConfig.ini')
        sections = conf.sections()
        if len(sections):
            f.write('\t<hr /> <h4>快捷方式</h4> \n')
            for s in sections:
                name = conf.get(s,"name")
                f.write("\t<input type=\"button\" value=\"%s\" onClick=\"execute('%s')\">&nbsp&nbsp\n" % (name,s))
        f.write('\t<hr /> <h4>文件管理</h4>\n')
        f.write('\t<input type="file" id="file-uploader" name="file" /> &nbsp;&nbsp;\n')
        f.write('\t<input type="button" value="点击上传" onclick="uploadClick()" /> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; \n')
        f.write('\t<progress id="progress" value="0" max="100"></progress>\n')
        f.write('\t<label id="progress-label" for="progress">0%</label>\n')
        f.write('\t<input type="text" value="" id="fileSearchText" onkeydown="fileSearchTextDown()">\n')
        f.write('\t<input type="button" value="搜索" onClick="searchFile()">&nbsp;&nbsp;\n')
        f.write('\t<input type="button" value="新建文件夹" onClick="addNewDir()">&nbsp;&nbsp;\n<br/><br/>\n')
        if "search=" in self.path:
            f.write(self.getFileHtml(self.searchFile(),True))
        else:
            f.write(self.getFileHtml(self.list_directory(path),False))
        
        f.write('<div id="modal_div" draggable="true" style="position: absolute;top:50px;left:200px;background-color: #e0e0e0;">\n')
        f.write('\t<div style="float:right">\n\t\t<input type="button" id="editSaveButton" value="确定" onClick="editSaveClick()">&nbsp;&nbsp;&nbsp;&nbsp;')
        f.write('\n\t\t<label onclick="hideEditDev()">x&nbsp;&nbsp;</label>\n\t\t</div>\n\t\t<br/>\n')
        f.write('\t<textarea id="edit_text" style="min-height:300px;max-height: 800px;width:800px;overflow:visible"></textarea>\n')
        f.write('\t<video id="videoPlay" src="" controls autoplay width="100%" disablePictureInPicture>您的浏览器暂不支持视频播放</video>\n')
        f.write('\t<audio id="audioPlay" src="" controls autoplay loop disablePictureInPicture><p>您的浏览器暂不支持音频播放 </p></audio>\n')
        f.write('\t<div id="fileDirSelect" style="left:30px;background-color: #ffffff;border:1px solid #F00;overflow:scroll;">\n\t\t</div>\n</div>\n')
        f.write('<script type="text/javascript">\n')
        f.write(getScript())
        f.write('\n</script> \n</body>\n</html>\n')
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
        f.write('<html>\n<head>\n\t<title>webShell</title>\n\t<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n</head>\n')
        f.write('<body>\n\t<h3>welcome to webShell</h3>\n\t<hr/>\n')
        f.write('\t<div style="top:100;text-align: center;">\n')
        f.write('\t\t<label>用户</label>&nbsp;&nbsp; <input id="user" type="text"/><br/>\n')
        f.write('\t\t<label>密码</label>&nbsp;&nbsp; <input id="pass" type="password" onkeydown="KeyDown()"/><br/><br/>\n')
        f.write('\t\t<input type="button" onclick="login()" value="登录"/> \n')
        f.write('\t</div>\n')
        f.write('<script type="text/javascript">\n')
        f.write('function KeyDown(){\n\tif(event.keyCode == 13){\n\t\tevent.returnValue=false;\n\t\tevent.cancel = true;\n\t\tlogin();\n\t}\n}\n')
        f.write('function login(){\n')
        f.write('\tvar httpRequest = new XMLHttpRequest();\n')
        f.write('\thttpRequest.open("POST", "/api/user/check", true);\n')
        f.write('\thttpRequest.setRequestHeader("Content-type","application/json");\n')
        f.write('\tobj = {user:document.getElementById("user").value,pass:document.getElementById("pass").value};\n')
        f.write('\tvar s=JSON.stringify(obj);\n')
        f.write('\thttpRequest.send(JSON.stringify(obj));\n')
        f.write('\thttpRequest.onreadystatechange = function () {\n')
        f.write('\t\tif (httpRequest.readyState == 4 && httpRequest.status == 200) {\n')
        f.write('\t\t\tvar data = JSON.parse(httpRequest.responseText);\n')
        f.write('\t\t\tif (data.code === 0){\n')
        f.write('\t\t\t\tvar exp = new Date();\n')
        f.write('\t\t\t\texp.setTime(exp.getTime() + 30 * 24 * 60 * 60 * 1000);\n')
        f.write('\t\t\t\tdocument.cookie = "token" + "=" + escape(data.data) + ";expires=" + exp.toGMTString() + ";path=/";\n')
        f.write('\t\t\t\twindow.location.href=\'/file/\'\n')
        f.write('\t\t\t}else{\n\t\t\t\talert("用户名或密码不正确");\n\t\t\t}\n\t\t}\n\t}\n}\n')
        f.write('</script>\n</body>\n</html>\n')
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
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        oldmd5 = md5_hash(username + password)
        md5 = md5_hash(json.loads(qs)['user'] + json.loads(qs)['pass'])
        if md5 == oldmd5:
            self.sendMessage('{"code":0,"data":"' + md5 + '"}')
        else:
            self.sendMessage('{"code":500}')
    def downloadFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        path = json.loads(qs)['fileName']
        f = open(self.translate_path(path), 'r')
        fs = os.fstat(f.fileno())
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(fs[6]))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
    def getDirList(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        path = self.translate_path(json.loads(qs)['dir'])
        list = os.listdir(path)
        list.sort(key=lambda a: a.lower())
        a = []
        for name in list:
            if os.path.isdir(os.path.join(path, name)): 
                a.append(name)      
        res={'data':a}
        self.sendMessage(json.dumps(res))
    def addNewDir(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        name = json.loads(qs)['name']
        os.mkdir(name)
        res={'message':'添加成功'}
        self.sendMessage(json.dumps(res))
    def renameFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        oldName = self.translate_path(json.loads(qs)['oldName'])
        newName = self.translate_path(json.loads(qs)['newName'])
        os.rename(oldName,newName)
        res={'message':'修改成功'}
        self.sendMessage(json.dumps(res))
    def deleteFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        fileName = self.translate_path(json.loads(qs)['fileName'])
        if os.path.isdir(fileName):
            shutil.rmtree(fileName)
        else:
            os.remove(fileName)
        res={'message':'删除成功'}
        self.sendMessage(json.dumps(res))
    def zipFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        path=self.translate_path(json.loads(qs)['fileName']).rsplit('/',1)[0]
        fileName = json.loads(qs)['fileName'].rsplit('/',1)[1]
        status = os.popen("cd %s;tar -zcvf %s.tar.gz %s;cd %s" % (path, fileName, fileName,os.getcwd()))
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        self.protocol_version="HTTP/1.1"
        self.wfile.writelines("运行中...请稍后" + " " * 1024)
        while 1:
            buf = status.readline()
            if not buf:
                break
            self.wfile.writelines(buf)
            self.wfile.flush()
        status.close()
    def unzipFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        path=self.translate_path(json.loads(qs)['fileName']).rsplit('/',1)[0]
        fileName = json.loads(qs)['fileName'].rsplit('/',1)[1]
        status = None
        if fileName.endswith(".tar"):
            status = os.popen("cd %s;tar -xvf %s;cd %s" % (path, fileName, os.getcwd()))
        if fileName.endswith(".tar.gz"):
            status = os.popen("cd %s;tar -xzvf %s;cd %s" % (path, fileName, os.getcwd()))
        if fileName.endswith(".zip"):
            status = os.popen("cd %s;unzip %s;cd %s" % (path, fileName,os.getcwd()))
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        self.protocol_version="HTTP/1.1"
        self.wfile.writelines("运行中...请稍后" + " " * 1024)
        while 1:
            buf = status.readline()
            if not buf:
                break
            self.wfile.writelines(buf)
            self.wfile.flush()
        status.close()
    def mvFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        fileName = self.translate_path(json.loads(qs)['fileName'])
        newPath = self.translate_path(json.loads(qs)['newPath']) + "/" + fileName.rsplit('/',1)[1]
        shutil.move(fileName,newPath)
        res={'message':'移动成功'}
        self.sendMessage(json.dumps(res))
    def cpFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        fileName = self.translate_path(json.loads(qs)['fileName'])
        newPath = self.translate_path(json.loads(qs)['newPath']) + "/" + fileName.rsplit('/',1)[1]
        if os.path.isdir(fileName):
            shutil.copytree(fileName,newPath)
        else:
            shutil.copyfile(fileName,newPath)
        res={'message':'复制成功'}
        self.sendMessage(json.dumps(res))
    def addNewDir(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        fileName = self.translate_path(json.loads(qs)['fileName'])
        os.makedirs(fileName)
        res={'message':'创建成功'}
        self.sendMessage(json.dumps(res))
    def saveEditedFile(self):
        qs = self.rfile.read(int(self.headers.getheader('content-length')))
        fileName = self.translate_path(json.loads(qs)['fileName'])
        content = json.loads(qs)['content']
        f = codecs.open(fileName,"w",encoding='utf-8')
        f.write(content)
        f.close()
        res={'message':'保存成功'}
        self.sendMessage(json.dumps(res))
    def searchFile(self):
        search = urlparse.parse_qs(urlparse.urlparse(self.path).query)["search"][0]
        path = self.translate_path(self.path[5:])
        res = self.search(path, [], search)
        return res
    def search(self,path,res,search):
        for dirpath,dirnames,files in os.walk(path):
            for name in files:
                if search in name:
                    res.append(dirpath + "/" + name)
                    if len(res) > 200:
                        return res
            for dir in dirnames:
                if search in dir:
                    res.append(dirpath + "/" + dir)
                    if len(res) > 200:
                        return res
                res = self.search(dirpath + "/" + dir, res, search)
                if len(res) > 200:
                    return res
        return res
    def sendMessage(self,msg):
        f = StringIO()
        f.write(msg)
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
    def getFileHtml(self,fileList,isSearch):
        out = ""
        if isSearch and len(fileList) >= 200:
            out = out + "<h3>只展示200条搜索结果</h3>"
        currentLength = len(os.getcwd())
        if not (self.translate_path(self.path[5:]) == os.getcwd()):
            out = out + '\t<table><tr><td width="50%"><a href="../">..</a></td><td width="10%"></td><td width="20%"></td><td width="20%"></td></tr></table>\n'
        num = 0
        for fullName in fileList:
            fileName =  fullName.rsplit('/',1)[1]
            if fileName == __file__ or fullName == self.translate_path("/webShellConfig.ini"):
                num = num + 1
                continue
            colorName = "0xFFF"
            
            if os.path.isdir(fullName):
                colorName = "#CEFFCE"
            if os.path.islink(fullName):
                colorName = "#FFBFFF"
            if isSearch:
                fileName = fullName[len(self.translate_path(self.path[5:])) + 1:]      
            out = out + '\t<table><tr><td width="50%" id="fileTableTd_{}"><a href="{}" id="fileTable_a_{}" style="background:{}">{}</a></td><td width="10%">{}</td><td width="20%">{}</td><td width="20%">{}</td></tr></table>\n'.format(
                    num,urllib.quote(fileName), num,colorName,fileName,self.getSelectHtml(num,fullName),
                        sizeof_fmt(os.path.getsize(fullName)), modification_date(fullName))
            num = num + 1
        return out
    def getSelectHtml(self,num,fullName):
        out = '<select id="fileTableSelect_%s" onchange="selectChange(\'%s\')">' % (num, num)
        out = out + '<option value="">操作</option>'
        out = out + '<option value="delete">删除</option>'
        out = out + '<option value="rename">重命名</option>'
        out = out + '<option value="mv">移动到</option>'
        out = out + '<option value="cp">复制到</option>'
        out = out + '<option value="zip">压缩</option>'
        if fullName.endswith(".tar") or fullName.endswith(".tar.gz") or fullName.endswith(".zip"):
            out = out + '<option value="unzip">解压</option>'
        if fullName.endswith(".mp3"):
            out = out + '<option value="audio">播放</option>'
        if fullName.endswith(".mp4"):
            out = out + '<option value="video">播放</option>'
        if (not os.path.isdir(fullName)) and (os.path.getsize(fullName) < 1024 * 1024) and (fullName.endswith(".txt") or fullName.endswith(".ini") or fullName.endswith(".log") or fullName.endswith(".js") 
        or fullName.endswith(".html") or fullName.endswith(".java") or fullName.endswith(".csv") or fullName.endswith(".ftl")):
            out = out + '<option value="edit">编辑</option>'
        out = out + '</select>'
        return out
    def list_directory(self,path):  
        res = []
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        for name in list:
            fullname = os.path.join(path, name)  
            res.append(fullname)        
        return res
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

