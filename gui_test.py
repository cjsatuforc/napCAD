"""
OpenCV portions copied from http://kieleth.blogspot.com/2014/05/webcam-with-opencv-and-tkinter.html
"""

import Tkinter as tk
import tkFileDialog, Tkconstants, tkMessageBox
import cv2
import numpy as np
from PIL import Image, ImageTk  # sudo pip install Pillow, sudo apt-get install python-imaging-tk
import stl_test
from basic_cube import MVP_image_to_3D as mvp
import folding_v2 as fold
import matplotlib, sys
matplotlib.use('TkAgg')
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure


def processImg():
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    curFrame = frame
    cv2.imwrite("napSketch.jpg",curFrame)

    d= VertexDialog(root)
    root.wait_window(d.top)
    vertNum = d.getNum()

    sides = mvp.find_rectangles("napSketch.jpg")#, vertNum)
    side_lists = mvp.normalize_sides(sides)
    front_2D = side_lists[0]
    left_side_2D = side_lists[1]
    back_2D = side_lists[2]
    right_side_2D = side_lists[3]
    top_2D = side_lists[4]
    bottom_2D = side_lists[5]

    side_coordinates = (([0,0],[0,6],[6,6],[6,0]),([0,0],[0,6],[6,6],[6,0]),([0,0],[0,6],[6,6],[6,0]),([0,0],[0,6],[6,6],[6,0]))
    actual_coordinates = (([6,6],[0,6],[0,12],[6,12]),([6,12],[6,18],[12,18],[12,12]),([12,12],[18,12],[18,6],[12,6]),([12,6],[12,0],[6,0],[6,6]))
    x, y, z= fold.make_dictionaries(side_coordinates,actual_coordinates)

    #x,y,z = mvp.output_xyz(front_2D,left_side_2D,back_2D,right_side_2D,top_2D,bottom_2D)
   
    #triangulate
    stl, fig = stl_test.triangulation(x,y,z)
    #fig_base = figure()

    #based off of http://matplotlib.org/examples/user_interfaces/embedding_in_tk.html
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas._tkcanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    toolbar = NavigationToolbar2TkAgg( canvas, root )
    toolbar.update()
    canvas.mpl_connect('key_press_event', key_press_handler)
    canvas.show()
    
    saveButton = tk.Button(master=root, text='Save As', command=lambda:save_as(stl)).pack(side=tk.BOTTOM, expand=1)
    
def show_frame():
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)

    # Convert the image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Convert the grayscale image to binary
    binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]

    # Detect edges with Canny
    edged = cv2.Canny(binary, 30, 200)

    # Find the 10 contours within the edged image
    (cnts,_) = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)#[:10]
    rectCnt = None
    count = 0
    vertices = []
    drawn = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # if contour has four points, draw on the contour
        if len(approx) == 4:
            rectCnt = approx
            vertices.append(rectCnt)
            cv2.drawContours(frame, [rectCnt], -1, (0, 255, 0), 1)
            count += 1
    #get new Image, now with contours drawn on
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after(10, show_frame)

def save_as(content):
    f = tkFileDialog.asksaveasfilename(   #this will make the file path a string
        parent= root,
        defaultextension=".stl",                
        filetypes = (("napCAD STL", "*.stl"),("testText", ".txt")), 
        title="Save STL as...")    #in the save function
    stl_test.stl_write(f,content)

def _quit():
    cap.release()
    cv2.destroyAllWindows()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
def handler():
    if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
        root.quit()


class VertexDialog:
    def __init__(self, parent):
        self.inputVertNum = 0
        top = self.top = tk.Toplevel(parent)
        tk.Label(top, text="Photo Taken! \n Please enter the number of vertices in the geometry.").pack()
        self.e = tk.Entry(top)
        self.e.pack(padx=5)

        b = tk.Button(top, text="OK", command=self.ok)
        b.pack(pady=5)

    def ok(self):
        self.inputVertNum= self.e.get()
        self.top.destroy()

    def getNum(self):
        return self.inputVertNum

width, height = 800, 600
cap = cv2.VideoCapture(0)

if not cap.isOpened(): 
    cap.open()

root = tk.Tk()
root.title('napCAD')

root.protocol("WM_DELETE_WINDOW", handler)
root.bind('<Escape>', lambda e: root.quit())

lmain = tk.Label(root)
lmain.pack()

curFrame = None

b = tk.Button(root, text ="Preview 3D Model", command = processImg).pack()
q = tk.Button(master=root, text='Quit', command=_quit).pack(side=tk.BOTTOM)

show_frame()
root.mainloop()


