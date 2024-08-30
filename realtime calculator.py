import tkinter as tk
import re
from sympy import symbols, Eq, solve, sympify
from PIL import Image, ImageDraw
import cv2
import numpy as np
import easyocr

reader = easyocr.Reader(['en'], gpu=True)

class HandwritingCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Handwriting Calculator")

        # Create a canvas for drawing
        self.canvas = tk.Canvas(self.root, bg='white', width=400, height=300)
        self.canvas.pack(side=tk.TOP)

        # Initialize an image to draw on
        self.image = Image.new("RGB", (400, 300), 'white')
        self.draw = ImageDraw.Draw(self.image)

        # Bind mouse events for drawing
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

        # Add a reset button
        self.reset_button = tk.Button(self.root, text="Reset", font=("Arial", 16), command=self.reset_canvas)
        self.reset_button.pack()

        # Area to display the output
        self.output_label = tk.Label(self.root, text="Output will appear here", font=("Arial", 16), bg='lightgray', width=40, height=4)
        self.output_label.pack(side=tk.BOTTOM)

        self.last_x = None
        self.last_y = None
        self.after_id = None  # To keep track of the debounce callback

    def paint(self, event):
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=5, fill='black', capstyle=tk.ROUND, smooth=tk.TRUE)
            self.draw.line([self.last_x, self.last_y, x, y], fill='black', width=5)

        self.last_x = x
        self.last_y = y

        # Debounce the calculate function to avoid lag
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(700, self.calculate)  # 500ms debounce delay

    def reset(self, event):
        self.last_x = None
        self.last_y = None

    def calculate(self):
        # Convert the PIL image to a format compatible with OpenCV
        image_cv = np.array(self.image)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)

        # Convert to grayscale and apply threshold
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Use easyocr to recognize the equation from the image
        result = reader.readtext(thresh)
        if result:
            text = ''.join([item[1] for item in result])
            text = text.replace(" ", "")  # Remove any spaces for a cleaner result
            print(text)

            try:
                # Check if the text contains an equation
                if '=' in text:
                    # Remove trailing equals sign for evaluation (simple equation)
                    if text.endswith('='):
                        text = text[:-1]

                    # Split into left and right sides of the equation (for quadratic equation)
                    if '=' in text:
                        left_side, right_side = text.split('=')
                    else:
                        left_side, right_side = text, '0'

                    # Detect variables in the equation
                    variables = set(re.findall(r'[a-zA-Z]', left_side + right_side))

                    if variables:
                        # Create sympy symbols for the detected variables
                        symbols_dict = {var: symbols(var) for var in variables}

                        # Convert the equation into a sympy expression
                        equation = Eq(sympify(left_side, locals=symbols_dict), sympify(right_side, locals=symbols_dict))

                        # Solve the equation for the detected variables
                        result = solve(equation, list(symbols_dict.values()))
                        self.output_label.config(text=f"{text} = {result}")
                    else:
                        # Evaluate the arithmetic expression directly
                        result = eval(left_side)
                        self.output_label.config(text=f"{text}={result}")
                else:
                    # If no equals sign, evaluate as a simple arithmetic expression
                    result = eval(text)
                    self.output_label.config(text=f"{text}={result}")
            except Exception as e:
                self.output_label.config(text=f"{text}=error")
        else:
            self.output_label.config(text="No text detected")

    def reset_canvas(self):
        # Clear the canvas and image
        self.canvas.delete("all")
        self.image = Image.new("RGB", (400, 300), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.output_label.config(text="Output will appear here")

if __name__ == "__main__":
    root = tk.Tk()
    app = HandwritingCalculatorApp(root)
    root.mainloop()
