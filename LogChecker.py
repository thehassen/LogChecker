# -*- coding: utf-8 -*-
u"LogChecker"
import re
Dependencies = ['time']

def macro_LogChecker(macro, noreply=True):
    
    output = """
	<style type="text/css"> 
	.styled-button-10 {
		background:#5CCD00;
		background:-moz-linear-gradient(top,#5CCD00 0%,#4AA400 100%);
		background:-webkit-gradient(linear,left top,left bottom,color-stop(0%,#5CCD00),color-stop(100%,#4AA400));
		background:-webkit-linear-gradient(top,#5CCD00 0%,#4AA400 100%);
		background:-o-linear-gradient(top,#5CCD00 0%,#4AA400 100%);
		background:-ms-linear-gradient(top,#5CCD00 0%,#4AA400 100%);
		background:linear-gradient(top,#5CCD00 0%,#4AA400 100%);
		filter: progid: DXImageTransform.Microsoft.gradient( startColorstr='#5CCD00', endColorstr='#4AA400',GradientType=0);
		padding:10px 15px;
		color:#fff;
		font-family:'Helvetica Neue',sans-serif;
		font-size:16px;
		border-radius:5px;
		-moz-border-radius:5px;
		-webkit-border-radius:5px;
		border:1px solid #459A00
	}
	</style>
    <script src='http://microajax.googlecode.com/files/microajax.minified.js'></script>
    <script language="javascript">
        function getLog(){
            var log = document.getElementById("log");
            var result = document.getElementById("result");
            
            var source = log.value;
            var postdata = "log=" + encodeURIComponent(source);
            
            result.innerHTML = "<img src='moin_static198/common/loading.gif' />";
            
            microAjax("/LogChecker?action=process", function (res) {
              result.innerHTML = res;
            }, postdata
            );
        }
    </script>
    <p><textarea id="log" style="width: 600px; height: 200px;"></textarea></p>
    <p><input type="button" class="styled-button-10" onclick="javascript:getLog();" value="Comprobar" /></p>
    <div id="result"></div>
    """
    
    return output
    
class LogChecker(object):
    def check(self, item, regex, match, scoredelta = 0, msg = "", reverse = False):
        answer = re.findall("((" + item + ")\s*:\s*" + regex + ")", self.source, flags = re.I + re.U)
        
        if len(answer) and answer[0][2] in match.split("|"):
            passed = True
        else:
            passed = False
        
        if reverse:
            passed = not passed
        
        if len(answer):
            item = answer[0][0]
        else:
            item = item.split("|")[0]
        
        if passed:
            self.result.append(item + " : <font color=green>Pass</font>")
        else:
            self.result.append(item + " : <font color=red>Fail")
            if msg:
                self.result[-1] += ", " + msg
            if scoredelta:
                self.result[-1] += " (-" + str(scoredelta) + " points)"
            self.result[-1] += "</font>"
                
            self.score -= scoredelta
    
    def checktrack(self, item, regex, scoredelta = 0, msg = "", reverse = True):
        answer = re.findall("(" + item + "\s*" + regex + ")", self.currenttrack, flags = re.I + re.U)
        if len(answer):
            passed = True
        else:
            passed = False
        
        if reverse:
            passed = not passed
        
        if len(answer):
            item = answer[0][0]
            if "CRC" in item:
                if answer[0][2] != answer[0][4]:
                    passed = False
                    msg = "CRC check does not match"
        else:
            item = item.split("|")[0]
        
        if passed:
            self.result.append(item + " : <font color=green>Pass</font>")
        else:
            self.result.append(item + " : <font color=red>Fail")
            if msg:
                self.result[-1] += ", " + msg
            if scoredelta:
                self.result[-1] += " (-" + str(scoredelta) + " points)"
            self.result[-1] += "</font>"
                
            self.score -= scoredelta
    
    def checkdrive(self):
        drive = re.findall(ur"(Used drive|光驱型号|使用光碟機|使用驱动器)\s*:?\s*(.+)", self.source, flags = re.I + re.U)
        
        if not len(drive):
            self.score = 0
            self.result.append("<font color=red>No drive detected, is it a valid log?</font>")
            return False
        
        drive = drive[0][1]
        drive = re.sub(r"\s+\-\s*", " ", drive)
        drive = re.sub(r"\s+", " ", drive)
        drive = re.sub(r"[^ ]+\:.*?$", " ", drive)
        drive = drive.strip()
        
        if u"光驱型号" in self.source or u"使用驱动器" in self.source:
            self.language = "chs"
        elif u"使用光碟機" in self.source:
            self.language = "cht"
        else:
            self.language = "eng"
        
        fake = ['Generic DVD-ROM SCSI CdRom Device']
        if drive in fake:
            self.score -= 20
            self.result.append("Read offset correction : <font color=red>Fail, Virtual drive used: " + drive + " (-20 points)</font>")
        else:
            logoffset = re.findall(ur"(Read offset correction|读取偏移校正)\s*:\s*([+-]?[0-9]+)", self.source, flags = re.I)
            
            if not len(logoffset):
                self.score -= 5
                self.result.append("Read offset correction : <font color=red>Fail, Cannot determine read offset for drive (-5 points)</font>")
            
            else:
                logoffset = logoffset[0][1]
                
                from pymongo import Connection
                mongo = Connection('127.0.0.1', 27017, safe = True)
                db = mongo.logchecker
                offset = db.offset
                
                results = list(offset.find({"keywords": {"$all": drive.split()}}))
                
                if len(results):
					for result in results:
						if result['offset'] == logoffset or result['offset'] == "+" + logoffset:
							self.result.append("Read offset correction : <font color=green>" + logoffset + "</font> For drive : <font color=blue>" + result['name'] + "</font> : <font color=green>Pass</font>")
							return True
							
						else:
							self.score -= 5
							self.result.append("Read offset correction : <font color=red>Incorrect read offset for drive. (-5 points)</font>")
							self.result.append("Checked against the following drive(s): <table>")
							self.result[-1] += "<tr><td><font color=blue>" + result['name'] + "</font></td><td>" + result['offset'] + "</td></tr>"
							self.result[-1] += "</table>"
                
                if not len(results) and logoffset == "0":
                    self.score -= 5
                    self.result.append("Read offset correction : <font color=red>Fail, The drive was not found in the database, so we cannot determine the correct read offset. However, the read offset in this case was 0, which is almost never correct. As such, we are assuming that the offset is incorrect (-5 points)</font>")
        
        return True
    
    def __init__(self, source):
        self.result = ["", ""]
        self.score = 100
        self.source = source
        
        if not self.checkdrive():
            return
        
        self.result.append("")
        self.check(u"Read mode|抓轨模式|读取模式", r"([^\s]+)", u"Secure|精确模式|可靠Secure|可靠", 40)
        self.check(u"Utilize accurate stream|使用精确流", u"(Yes|No|是|否)", u"Yes|是")
        self.check(u"Defeat audio cache|屏蔽数据缓存|清空音频缓存", u"(Yes|No|是|否)", u"Yes|是", 5, '"Defeat audio cache" should be yes')
        self.check(u"Make use of C2 pointers|使用Ｃ２纠错|使用\s*C2\s*指示器|使用\s*C2\s*指针", u"(Yes|No|是|否)", u"Yes|是", 10, '"C2 pointers were used', reverse = True)
        self.check(u"Fill up missing offset samples with silence|用静音填充丢失的偏移采样|用靜音填充抓取中遺失偏移的取樣|用静音填充抓取中丢失偏移的采样", u"(Yes|No|是|否)", u"Yes|是", 5, 'Does not fill up missing offset samples with silence')
        self.check(u"Delete leading and trailing silent blocks|删除开始与结尾的静音部分|去除首尾靜音區塊|去除首尾静音块", u"(Yes|No|是|否)", u"Yes|是", 5, '"Deletes leading and trailing silent blocks', reverse = True)
        self.check(u"Null samples used in CRC calculations|校验和计算中使用空白采样|在CRC\s*计算中使用了空样本", u"(Yes|No|是|否)", u"Yes|是", 1, '"Null samples should be used in CRC calculations, but they don\'t affect audio data')
        self.check(u"Gap handling|间隙处理", r"([^\s])+", "Not detected", 20, 'Gap handling was not detected', reverse = True)
        self.check(u"Add ID3 tag|添加ＩＤ３标签|添加\s*ID3\s*标签", u"(Yes|No|是|否)", u"Yes|是", 5, 'ID3 tags should not be added to FLAC rips - they are mainly for MP3 files. FLACs should have vorbis comments for tags instead', reverse = True)
        
        self.result.append("")
        
        tracks = re.split(r"(Track\s*\d{1,3})", self.source)
        if len(tracks) < 3 and self.language == "chs":
            tracks = re.split(ur"(音轨\s*\d{1,3})", self.source)
        
        if len(tracks) >= 3:
            for i in range(len(tracks))[1::2]:
                self.result.append("Checking " + tracks[i])
                self.currenttrack = tracks[i + 1]
                
                self.checktrack("Suspicious position", r"(\d:\d{2}:\d{2})", 20, "Suspicious position(s) found")
                self.checktrack("Timing problem", r"(\d:\d{2}:\d{2})", 20, "Suspicious position(s) found")
                self.checktrack("Missing samples", r"", 20, "Missing sample(s) found")
                self.checktrack("Timing problem", r"(\d:\d{2}:\d{2})", 20, "Suspicious position(s) found")
                self.checktrack(u"(Test|测试)\s*CRC", ur"([0-9A-F]{8})\n\s*(Copy|复制)\s*CRC\s*([0-9A-F]{8})", 10, "Test and copy was not used", reverse = False)

def action_LogChecker(request):
    source = request.form['log']
    source = source.replace("\r", "\n").replace("\n\n", "\n").replace(u"　", " ").replace(u"：", ":")
    source = re.sub(r":\s+:", " : ", source)
    
    logchecker = LogChecker(source)
    
    return "Total Score: " + str(logchecker.score) + "<br>".join(logchecker.result)
