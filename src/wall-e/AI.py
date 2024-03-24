#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import torch
import numpy as np
import cv2

##LOAD MODEL
path='src/wall-e/modelV4.pt'
model = torch.hub.load("ultralytics/yolov5", "custom", path=path, force_reload=True)

##REAL TIME DETECTION
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    
    results = model(frame)
    
    cv2.imshow("YOLO", np.squeeze(results.render()))
    
    if cv2.waitKey(10) & 0xff == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()

