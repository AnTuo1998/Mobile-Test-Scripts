import os
import re
import time
import requests
import hashlib
import subprocess as sub
import threading
import instruments
import datetime
import timeout_decorator
from settings import is_open_source
from settings import apk_dir
from Application import App

class Method_handler():
    collecting = False
    @staticmethod
    def start(subject):
        package = subject.package
        Method_handler.collecting = True
        os.system('adb -s ' + subject.serial + ' shell am profile start ' + package + ' sdcard/' + 'tmp' + subject.serial + '.trace')
        print('start collecting')



    @staticmethod
    def stop(subject):
        if Method_handler.collecting:
            #os.system('adb shell am profile ' + pid + ' stop')
            pkg = subject.package
            launch = subject.launch
            os.system('adb -s ' + subject.serial + ' shell am profile stop')
            print('stop collecting')
            Method_handler.collecting = False
            time.sleep(1)
            t = pkg.split('.')
            if len(t) > 2:
                search_text1 = t[0] + '/' + t[1]
            else:
                search_text1 = pkg
            
            if launch != None:
                b = launch.split('.')
                if len(b) > 2:
                    search_text2 = b[0] + '/' + b[1]
                else:
                    search_text2 = launch
            else:
                search_text2 = " "

            os.system('adb -s ' + subject.serial + ' pull sdcard/tmp' + subject.serial + '.trace '  + './')
            cmd = "dmtracedump -o tmp" + subject.serial + ".trace " + " | grep '" + search_text1 + "\|" + search_text2 + "' |grep [^a-zA-Z]ent[^a-zA-Z] > " + "tmp" + subject.serial + ".txt"
            print('dmtrace command ' + cmd)
            os.system(cmd)
            os.system('adb -s ' + subject.serial +  ' shell rm sdcard/' + 'tmp' + subject.serial + '.trace')

    @staticmethod
    def handle_method(subject):
        if not os.path.isfile('tmp' + subject.serial + '.txt'):
            print('No available method collection file!')
            return

        f = open('tmp' + subject.serial + '.txt', 'r')
        text = ""
        method_collec = {}
        method_tot = 0

        for line in f:
            if not line.strip():
                continue
            aft = line.strip().split('/')
            prev_string = aft[0]
            if '.' in prev_string:
                prev = prev_string.split('.')[-1]
            elif '-' in prev_string:
                prev = prev_string.split('-')[-1]
            elif ' ' in prev_string:
                prev = prev_string.split(' ')[-1]
            else:
                print("waited to be check: " + line)
                continue
            aft[0] = prev
            method = '/'.join(aft) + '\n'
            m = hashlib.md5()
            m.update(method.encode())
            #if m.hexdigest() not in method_collec:
            if method_collec.get(m.hexdigest()) == None:
                method_tot += 1
                text = text + method
                method_collec[m.hexdigest()] = 1
            else:
                continue
        f.close()
        print(text, method_tot)
        return method_tot


def matchForeground(package):
    content = os.popen('adb shell dumpsys activity activities').read()
    match = re.findall("(ProcessRecord\{)(.*:)(.*)(/.*)", content)
    # 安卓自带模拟器里匹配的是最后一个出现的record

    if (match != None):
        #print('package: ' + package)
        for m in match:
            #print('compared: ', m)
            if (m[2] == package):
                return True
        return False
    else:
        return False

def handle_activity(package_name):
    activity = []
    lines = os.popen('adb shell logcat -d ActivityManager:I ' + package_name + '| grep "Displayed ' + package_name + '"').readlines()
    
    for line in lines:
        # line:  I/ActivityManager(  425): Displayed com.fitbit.FitbitMobile/com.fitbit.home.ui.HomeActivity_: +1s144ms
        act = line.split('/')[2].split(':')[0]
        #print(activity)
        activity.append(act)
    
    return activity
                

class Check_app():
    @staticmethod
    def calculate_coverage(subject, ins_name):
        #
        print('***testing ' + subject.package + '***')
        os.system('adb -s ' + subject.serial + ' shell logcat -c')
        current_instrument = instruments.instruments[ins_name](subject)
        current_instrument.run()
        time.sleep(current_instrument.wait)
        count = 0
        try:
            while(True):
                count += 1
                if not is_open_source:
                    time.sleep(current_instrument.span)
                    subject.handle_activity()
                else:
                    subject.get_coverage()
                    time.sleep(15)

                if count == 12:
                    if not is_open_source:
                        fk = open(subject.dir + '/' + subject.package + '_' + subject.suit + '_time_coverage.txt', 'a+')
                        record_time = datetime.datetime.now().strftime('%m/%d-%H:%M:%S')
                        fk.write(record_time + ' ' + str(subject.activity_tot) + '\n')
                        fk.close()
                    if not current_instrument.is_alive():
                        print('instrument stop')
                        raise timeout_decorator.timeout_decorator.TimeoutError('timeout')
                    count = 0
        except timeout_decorator.timeout_decorator.TimeoutError as e:
            current_instrument.stop()
            raise timeout_decorator.timeout_decorator.TimeoutError('timeout')


        

if __name__ == '__main__':
    subject = App('com.evancharlton.mileage.apk', 'ZX1G223KRJ', 'monkey')
    os.system('adb install ' + apk_dir + '/com.evancharlton.mileage.apk')
    #Check_app.check_app_running('akai.floatView.op.luffy.apk', 'monkey')
    #Check_app.check_app_running(subject, 'droidbot')
    #Check_app.check_app_running(subject, 'stoat')
    #Check_app.check_app_running(subject, 'sapienz')
    #App.getLaunchActivity('akai.floatView.op.luffy.apk')
    Check_app.calculate_coverage(subject, 'monkey')
    pass
