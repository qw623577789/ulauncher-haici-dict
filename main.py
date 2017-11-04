import sys
import json
import urllib
import urllib2
import hashlib
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.event import KeywordQueryEvent

reload(sys)
sys.setdefaultencoding("utf-8")


class HaiciDictExtension(Extension):

    def __init__(self):
        super(HaiciDictExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def getMd5(self, value):
        md5 = hashlib.md5()   
        md5.update(value)
        return  md5.hexdigest()

    def getToken(self, word):
        url = 'http://apii.dict.cn/mini.php?q=' + word
        headers = {
            'Cookie' :  'dictsid=1201.373420645.1071507.128476'
        }
        request = urllib2.Request(url = url, headers=headers)
        response = None
        try:
            response = urllib2.urlopen(request, timeout=2)
            responseData = response.read()
            tokenStringStart = responseData.find('dict_pagetoken="')
            if tokenStringStart == -1:
                return False
            return responseData[tokenStringStart +16 : tokenStringStart +16 + 32]   
        except urllib2.URLError as e:
            return False
        except:
            pass
        finally:
            if response:
                response.close()

    def getExplain(self, word, token):
        t = word + 'dictcn' + token
        query = { 'q' : word, 's' : 2,  't' : self.getMd5(t)}
        serializeData = urllib.urlencode(query)
        url = "http://apii.dict.cn/ajax/dictcontent.php"
        headers = {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Cookie' :  'dictsid=1201.373420645.1071507.128476'
        }
        request = urllib2.Request(url = url,data =serializeData, headers=headers)
        response = None
        try:
            response = urllib2.urlopen(request, timeout=2)
            if response.getcode() != 200:
                return False
            responseData = response.read()
            return responseData
        except urllib2.URLError as e:
            return False
        except:
            pass
        finally:
            if response:
                response.close()

    def on_event(self, event, extension):
        word = event.get_argument()
        icon = 'images/icon.png'
        showList = []
        if word:
            #step1. get token3
            token = self.getToken(word)
            print token
            if token == False:
                showList.append(ExtensionResultItem(icon=icon, name='network error in getting token,please try again', on_enter=HideWindowAction()))

            #step2. get explain by token
            explain = self.getExplain(word, token)
            print explain
            if explain == False:
                showList.append(ExtensionResultItem(icon=icon, name='network error in getting explain,please try again', on_enter=HideWindowAction()))

            #step3. analazy
            jsonResult = json.loads(explain)
            if 'e' not in  jsonResult:
                showList.append(ExtensionResultItem(icon=icon, name='no result', on_enter=HideWindowAction()))
            else:
                for item in jsonResult['e'].split('<br />'):
                    showList.append(ExtensionResultItem(icon=icon, name=item, on_enter=CopyToClipboardAction(item)))
                
                # if has speech
                if 't' in  jsonResult:
                    showList.append(ExtensionResultItem(icon=icon, name='**inflections below**', on_enter=HideWindowAction()))
                    for item in jsonResult['t'].replace('<i>', '').replace('</i>', '').replace('&nbsp;', '').split('\r\n'):
                        if item != '':
                            showList.append(ExtensionResultItem(icon=icon, name=item, on_enter=CopyToClipboardAction(item)))

        else:
            showList.append(ExtensionResultItem(icon=icon, name='please type in some words', on_enter=HideWindowAction()))

        #to render result
        return RenderResultListAction(showList)

if __name__ == '__main__':
    HaiciDictExtension().run()