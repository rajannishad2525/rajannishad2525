#!/usr/bin/env python3
"""
assets/photo.jpg -> assets/prepped.png  (head+shoulders, background hata ke, contrast boost)

Article rembg use karta hai, par wo ~180MB ka model kheenchta hai. OpenCV ka
GrabCut isi kaam ke liye kaafi hai jab subject center mein ho aur hum use pehle
face detect karke tight crop kar chuke hon — jo yahan sach hai.
"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "photo.jpg")
OUT = os.path.join(ROOT, "assets", "prepped.png")

# face box ke charon taraf kitna aur lena hai (face height/width ke hisaab se).
# LEFT alag hai: is photo mein background ke log chehre ke BAAYIN taraf hain,
# aur GrabCut unhe bhi foreground maanta hai. Left se kam crop karke wo sawaal
# hi khatam kar dete hain — helmet ka baayan kinara phir bhi bach jata hai.
# Tight face crop. Wide crop pe ASCII mush ban jaata hai: chehra oval ka sirf
# ~40% hota hai aur helmet/jacket/background ka tone usi jaisa, to 78 columns
# pe sab ghul jaata hai. Chehra frame bhare to har feature padha jaata hai.
UP, DOWN, LEFT, RIGHT = 0.50, 0.26, 0.16, 0.22
USE_GRABCUT = False   # neeche wajah likhi hai
TARGET_W = 900


def find_face(gray):
    cc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cc.detectMultiScale(gray, 1.1, 6, minSize=(160, 160))
    if len(faces) == 0:
        return None
    return max(faces, key=lambda r: r[2] * r[3])


def main():
    img = cv2.imread(SRC)
    if img is None:
        sys.exit(f"photo nahi mili: {SRC}")
    H, W = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face = find_face(gray)
    if face is None:
        print("  face nahi mila — beech ka hissa le raha hoon")
        s = min(W, H) // 2
        x, y, w, h = (W - s) // 2, (H - s) // 3, s, s
    else:
        x, y, w, h = face
        print(f"  face: x={x} y={y} w={w} h={h}")

    x0 = max(0, int(x - LEFT * w))
    x1 = min(W, int(x + w + RIGHT * w))
    y0 = max(0, int(y - UP * h))
    y1 = min(H, int(y + h + DOWN * h))
    crop = img[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    print(f"  crop: {cw}x{ch}")

    # GrabCut jaan-boojh ke band hai.
    #
    # Is photo pe usne do tarah se dhokha diya: khule crop pe wo background ke
    # logon ko bhi "foreground" maan leta tha, aur tight crop pe uske paas
    # background seekhne ko itna kam bacha ki usne helmet aur gaal ke tukde hi
    # kaat diye. ASCII portrait ke liye ek saaf oval vignette isse behtar aur
    # bharosemand hai — chehra kabhi nahi katega.
    if USE_GRABCUT:
        mask = np.zeros((ch, cw), np.uint8)
        rect = (int(cw * 0.06), int(ch * 0.04), int(cw * 0.88), int(ch * 0.94))
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(crop, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
        fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    else:
        fg = np.ones((ch, cw), np.uint8)

    # GrabCut akela kaafi nahi: rafting selfie mein baayin taraf ke log/nadi bhi
    # "foreground" ban jaate hain aur ASCII mein sirf shor dete hain. Face ka
    # position hume pata hai, to uske around ek ellipse se kaat do — sirf sar,
    # helmet aur kandhe bachte hain.
    if face is not None:
        fx, fy = x - x0, y - y0
        # helmet chehre se daayin aur upar zyada failta hai, isliye ellipse
        # ka center face box se thoda shift karo
        cx, cy = fx + w // 2, fy + h // 2 - int(0.04 * h)
        # ax crop ki chaudai se chhota rehna chahiye, warna ellipse poora frame dhak
# leti hai aur background kabhi whiten hota hi nahi — deewar ki halki chhaya
# ASCII mein ek ghana bar ban ke baayin taraf khadi ho jaati thi.
        ax, by = int(0.58 * w), int(0.80 * h)
    else:
        cx, cy, ax, by = cw // 2, ch // 2, int(cw * 0.42), int(ch * 0.46)

    # Hard oval cut kaam nahi karta: background (nadi, log, pahad) ka tone
    # chehre jaisa hi hai, to 78 columns pe sab ghul-mil ke shor ban jata hai.
    # Iski jagah graded vignette — andar wale ellipse mein poori detail, bahar
    # ki taraf safed. Safed = ASCII mein space, yaani background apne aap gayab.
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    d = np.sqrt(((xx - cx) / ax) ** 2 + ((yy - cy) / by) ** 2)
    INNER, OUTER = 0.84, 1.00            # d<INNER poori detail, d>OUTER poora safed
    wgt = np.clip((OUTER - d) / (OUTER - INNER), 0.0, 1.0)
    wgt = wgt * wgt * (3 - 2 * wgt)      # smoothstep
    print(f"  vignette: {(wgt > 0.5).mean()*100:.0f}% full-detail area")

    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # CLAHE: chehre ki detail kholta hai, jo ASCII mein sabse zyada dikhti hai
    g = cv2.createCLAHE(clipLimit=3.4, tileGridSize=(8, 8)).apply(g)
    g = cv2.bilateralFilter(g, 7, 60, 60)          # skin smooth, kinare tez

    # Dhoop mein li gayi selfie flat hoti hai — chehre ka tone lagbhag ek jaisa,
    # aur sabse gehri cheez helmet. Aise mein ASCII sirf helmet dikhata hai.
    # Unsharp mask se local contrast badhta hai, to aankh/naak/hont apna alag
    # tone paate hain chahe overall brightness ek jaisi ho.
    blur = cv2.GaussianBlur(g, (0, 0), 9)
    g = cv2.addWeighted(g, 1.45, blur, -0.45, 0)
    g = np.clip(g, 0, 255).astype(np.uint8)

    # vignette se background safed ki taraf le jao
    g = (g.astype(np.float32) * wgt + 255.0 * (1.0 - wgt))
    g = np.clip(g, 0, 255).astype(np.uint8)

    scale = TARGET_W / cw
    g = cv2.resize(g, (TARGET_W, int(ch * scale)), interpolation=cv2.INTER_AREA)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cv2.imwrite(OUT, g)
    print(f"{OUT}  ({g.shape[1]}x{g.shape[0]})")


if __name__ == "__main__":
    main()
