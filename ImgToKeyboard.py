import numpy as np
import cv2
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_pro', default="dummy.pro")
    parser.add_argument('--input_img', default="test.jpg")
    parser.add_argument('--output_pro', default="result.pro")
    parser.add_argument('--amp_LED', default=1.6) # 밝기 127기준으로 더 멀리 퍼지도록 곱하는 값 (진해야 키보드에 잘보임)

    # TODO: 현재 단순 resize, crop 옵션 받도록 변경 필요
    return parser.parse_args()

# 한 키 객체
# 여러개의 컬러값을 insert 받아서 weighted sum을 수행하고 string으로 return함
class OneKey():
    def __init__(self, idx):
        self.idx = idx
        self.Rs = []
        self.Gs = []
        self.Bs = []
        self.Ws = []
    
    # 새로운 컬러 정보 넣기
    def insert(self, R,G,B,W):
        self.Rs.append(R)
        self.Gs.append(G)
        self.Bs.append(B)
        self.Ws.append(W)
    
    # 가진 모든 컬러들 weighted-sum해서 string 리턴하기
    def __str__(self):
        if len(self.Rs) == 0 or len(self.Gs) == 0 or len(self.Bs) == 0 or len(self.Ws) == 0:
            return  f'<AREA ID="{self.idx}" Red="{0}" Green="{0}" Blue="{0}"/>\n'
        
        arr_W = np.array(self.Ws)
        arr_R = np.array(self.Rs)
        arr_G = np.array(self.Gs)
        arr_B = np.array(self.Bs)
        
        R = np.round(np.average(arr_R, weights=arr_W)).astype(int)
        G = np.round(np.average(arr_G, weights=arr_W)).astype(int)
        B = np.round(np.average(arr_B, weights=arr_W)).astype(int)
        
        return  f'<AREA ID="{self.idx}" Red="{R}" Green="{G}" Blue="{B}"/>\n'

if __name__ == '__main__':
        
    args = parse_args()

    lines = None
    with open(args.input_pro, "r") as f:
        lines = f.readlines()

    start_line = -1
    end_line = -1
    for i, line in enumerate(lines):
        if "<AREA" in line:
            if start_line == -1:
                start_line = i
            if end_line < i:
                end_line = i

    end_line = end_line + 1

    img = cv2.imread(args.input_img)
    small = cv2.resize(img, (15,4))

    small = small / 255.0
    small = (small - 0.5) * args.amp_LED + 0.5
    small = small * 255
    small = np.clip(small,0,255)
    small = np.uint8(small)

    # 일반화
    num_keys = 87
    start_idx = 14
    end_idx = 67 # 14~66까지 존재

    keys = [OneKey(i) for i in range(num_keys)]
    pixels = small.reshape(-1,3)
    key_widths = np.ones(end_idx - start_idx)

    key_widths[27-start_idx] = 2.0 # backspace
    key_widths[28-start_idx] = 1. # tab 1.5
    key_widths[41-start_idx] = 2. # \ 1.5
    key_widths[42-start_idx] = 2. # Caps Lock 1.7
    key_widths[54-start_idx] = 2. # Enter 2.3
    key_widths[55-start_idx] = 2. # L-Shift 2.3
    key_widths[66-start_idx] = 3. # R-Shift 2.7

    acc = 0
    
    for i, width in enumerate(key_widths):
        i = i+start_idx
        r = width % 1
        q = int(width - r)
        
        for j in range(q):
            ratio = acc%1
            if ratio == 0:
                B,G,R = pixels[int(acc)]
                W = 1
                keys[i].insert(R,G,B,W)
            else:
                B,G,R = pixels[int(acc)]
                W = ratio
                keys[i].insert(R,G,B,W)
                B,G,R = pixels[int(acc)+1]
                W = 1-ratio
                keys[i].insert(R,G,B,W)
            acc += 1
        acc += r

    with open(args.output_pro, "w+") as f:
        for i, line in enumerate(lines):
            if i >=start_line and i < end_line:
                f.write(str(keys[i-start_line]))
            else:
                f.write(line)

    print("Output:", args.output_pro)