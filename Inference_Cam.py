import torch
import cv2
from PIL import Image
import torchvision.transforms as transforms
import numpy as np
from .Model_Class_From_the_Scratch import MODEL_From_Scratch
from .Model_Class_Transfer_Learning_MobileNet import MobileNet

#gstreamer_string = ("nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)60/1 ! nvvidconv flip-method=0 ! video/x-raw, width=(int)1280, height=(int)720, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")
gstreamer_string = ("v4l2src device=/dev/video0! video/x-raw, width=640, height=480, format=(string)YUY2,framerate=30/1 ! videoconvert ! video/x-raw,width=640,height=480,format=BGR ! appsink")

class Inference_Class(videoSource = 0):
    def __init__(self):
        USE_CUDA = torch.cuda.is_available()
        self.DEVICE = torch.device("cuda" if USE_CUDA else "cpu")
        self.model = None
        self.label_map = None
        self.transform_info = transforms.Compose([
                transforms.Resize(size=(224, 224)),
                transforms.ToTensor()
                ])

    def load_model(self, is_train_from_scratch, label_map_file = "label_map.txt"):
        self.label_map = np.loadtxt(label_map_file, str, delimiter='\t')
        num_classes = len(self.label_map)
        model_str = None
        if is_train_from_scratch:
            self.model = MODEL_From_Scratch(num_classes).to(self.DEVICE)
            model_str = "PyTorch_Training_From_Scratch"
        else:
            self.model = MobileNet(num_classes).to(self.DEVICE)
            model_str = "PyTorch_Transfer_Learning_MobileNet"
        model_str += ".pt" 
        self.model.load_state_dict(torch.load(model_str), map_location=self.DEVICE)
        self.model.eval()

    def inference_video(self, video_source="test_video.mp4"):
        cap = cv2.VideoCapture(video_source)
        if cap.isOpened():
            print("Video Opened")
        else:
            print("Video Not Opened")
            print("Program Abort")
            exit()
        cv2.namedWindow("Input", cv2.WINDOW_GUI_EXPANDED)
        cv2.namedWindow("Output", cv2.WINDOW_GUI_EXPANDED)
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                output = self.inference_frame(frame)
                cv2.imshow("Input", frame)
                cv2.imshow("Output", output)
            else:
                break
            if cv2.waitKey(33) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        return

    def inference_frame(self, opencv_frame):
        image_tensor = self.proprocess_frame(opencv_frame)
        image_tensor = image_tensor.to(self.DEVICE)
        inference_result = self.model(image_tensor)
        result_frame = self.postprocess_frame(opencv_frame, inference_result)
        return result_frame

    def preprocess_frame(self, opencv_frame):
        opencv_rgb = cv2.cvtColor(opencv_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(opencv_rgb)
        image_tensor = self.transform_info(image)
        return image_tensor.unsqueeze(0)

    def postprocess_frame(self, opencv_frame, inference_result):
        result_frame = np.copy(opencv_frame)
        label_text = self.label_map[np.argmax(inference_result.cpu().detach().numpy())]
        return cv2.putText(result_frame, label_text, point=(10, 50), font=cv2.FONT_HERSHEY_PLAIN, fontScale=2.0, color=(0,0,255), thickness=3)

if __name__ == "__main__":
    inferenceClass = Inference_Class()
    inferenceClass.load_model(False)
    inferenceClass.inference_video(gstreamer_string)