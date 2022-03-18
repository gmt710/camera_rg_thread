# -*- coding: utf-8 -*-
"""
refer : https://blog.csdn.net/weixin_41576121/article/details/96128253
Created on 2022/3/17 15:20
@author  : GMT
"""
import cv2
import threading
from collections import deque
import time


class RealReadThread(threading.Thread):
    def __init__(self, input):
        super(RealReadThread).__init__()
        self._jobq = input
        self.maxsizeq = input.maxlen
        # ip_camera_url = 'rtsp://admin:admin@192.168.1.64/'   # rtsp数据流
        # 创建一个窗口
        self.cap = cv2.VideoCapture(0)
        self.lockr = threading.Lock()
        threading.Thread.__init__(self)

    def run(self):
        # cv2.namedWindow('ip_camera', flags=cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
        if not self.cap.isOpened():
            print('请检查IP地址还有端口号，或者查看IP摄像头是否开启，另外记得使用sudo权限运行脚本')
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue
            self.lockr.acquire()
            if len(self._jobq) == self.maxsizeq:
                self._jobq.popleft()
            else:
                self._jobq.append(frame)
            self.lockr.release()
            # cv2.imshow('ip_camera', frame)
            #             # if cv2.waitKey(10) == ord('q'):
            #             #     # 退出程序
            #             #     break
            time.sleep(0.001)
        print("实时读取线程退出！！！！")
        # cv2.destroyWindow('ip_camera')
        self._jobq.clear()  # 读取进程结束时清空队列
        self.cap.release()


class GetThread(threading.Thread):
    def __init__(self, input, result):
        super(GetThread).__init__()
        self._jobq = input
        self.maxsizeq = input.maxlen
        self.frame_idx = 0
        self.callbacks = []
        self.result = result
        self.lockg = threading.Lock()
        threading.Thread.__init__(self)

    def addcallback(self, callback):
        print(callback)
        self.callbacks.append(callback)

    def run(self):
        # cv2.namedWindow('get', flags=cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
        flag = False
        while (True):
            try:
                if len(self._jobq) != 0:
                    self.lockg.acquire()
                    im_new = self._jobq.popleft()
                    if im_new is not None:
                        self.frame_idx += 1

                    if len(self.result) == self.maxsizeq:
                        self.result.popleft()
                    else:
                        self.result.append((self.frame_idx, im_new))

                    for cb in self.callbacks:
                        cb(self.result)
                    self.lockg.release()
                    flag = True

                elif flag == True and len(self._jobq) == 0:
                    time.sleep(0.001)
                    # break
            except Exception as e:
                print(e)
        print("间隔1s获取图像线程退出！！！！")

    def get_result(self, result):
        return result


if __name__ == "__main__":
    maxsizeq = 10
    q = deque([], maxsizeq)
    result = deque([], 10)
    th1 = RealReadThread(q)
    th2 = GetThread(q, result)
    ths = [th1, th2]
    print("--------------begin---------------")
    for i, th in enumerate(ths):
        th.daemon = True
        th.start()  # 开启两个线程
        if i == 1:
            th.addcallback(th.get_result)

    cv2.namedWindow('img_show', flags=cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
    cv2.startWindowThread()
    frame_idx = last_frame_idx = 0

    while True:
        try:
            # result = th2.result
            if len(result) != 0:
                frame_idx, your_img = result.popleft()
                if frame_idx == last_frame_idx:
                    continue
                print("now you can process your img index : {}".format(frame_idx))
                last_frame_idx = frame_idx
                cv2.imshow("img_show", your_img)
                cv2.waitKey(1)
        except Exception as e:
            print("-------------------------", e)
            continue
