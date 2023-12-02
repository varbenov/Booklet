import tkinter as tk
from tkinter import filedialog
import os
import PyPDF2
import os
from PyPDF2 import PdfFileReader, PdfFileWriter

class AfMatrix:
    """ A matrix of a 2D affine transform. """
    __slots__ = ('__a', '__b', '__c', '__d', '__e', '__f')

    def __init__(self, a, b, c, d, e, f):
        self.__a = float(a)
        self.__b = float(b)
        self.__c = float(c)
        self.__d = float(d)
        self.__e = float(e)
        self.__f = float(f)

    def __iter__(self):
        yield self.__a
        yield self.__b
        yield self.__c
        yield self.__d
        yield self.__e
        yield self.__f

    @classmethod
    def compose(cls, *what):
        a, b, c, d, e, f = (
            1, 0,
            0, 1,
            0, 0,
        )
        for rhs in what:
            A, B, C, D, E, F = rhs
            a, b, c, d, e, f = (
                a * A + b * C,
                a * B + b * D,
                c * A + d * C,
                c * B + d * D,
                e * A + f * C + E,
                e * B + f * D + F,
            )
        return cls(
            a, b,
            c, d,
            e, f
        )

    @classmethod
    def translate(cls, x=0, y=0):
        return cls(
            1, 0,
            0, 1,
            x, y
        )

    def __takes_origin(func):
        def translated_func(cls, *args, origin=(0, 0), **kwargs):
            if origin == (0, 0):
                return func(cls, *args, **kwargs)
            return cls.compose(
                cls.translate(-origin[0], -origin[1]),
                func(cls, *args, **kwargs),
                cls.translate(origin[0], origin[1])
            )
        return translated_func

    @classmethod
    @__takes_origin
    def rotate(cls, angle):
        from math import cos, sin, radians
        angle = radians(angle)
        C = cos(angle)
        S = sin(angle)
        return cls(
             C,  S,
            -S,  C,
             0,  0
        )

def compile_page (input, page1_num, page2_num):

    reader = PdfFileReader(open(input,'rb'))
    writer = PdfFileWriter()

    page1 = reader.pages[page1_num-1]
    page2 = reader.pages[page2_num-1]

    opg1 = writer.addBlankPage(0, 0)

    opg1.mergeTransformedPage(page1, AfMatrix.compose(
        AfMatrix.rotate(90),
        AfMatrix.translate(x=page1.mediaBox.getHeight(), y=0)
    ), expand=True)

    opg1.mergeTransformedPage(page2, AfMatrix.compose(
        AfMatrix.rotate(90),
        AfMatrix.translate(x=page2.mediaBox.getHeight(), y=422.3)
    ), expand=True)

    return opg1

def add_empty_page(input):
  import shutil
  a = open(input, 'rb')
  pdf=PyPDF2.PdfFileReader(a)
  outPdf=PyPDF2.PdfFileWriter()
  outPdf.appendPagesFromReader(pdf)
  outPdf.addBlankPage()
  outStream=open('Amended.pdf','wb')
  outPdf.write(outStream)
  outStream.close()
  a.close()

def browse_input_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        input_pdf_var.set(file_path)
    pdf_directory = os.path.dirname(file_path)
    os.chdir(pdf_directory)

def compile_pdf():
    # Extract input parameters
    input_pdf = input_pdf_var.get()
    output_pdf_name = output_name_var.get() + '.pdf'
    section_size = section_size_var.get()
    empty_sheet = empty_sheet_var.get()

    # Open input PDF file
    input_pdf_file = open(input_pdf, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(input_pdf_file)
    pdf_writer = PyPDF2.PdfFileWriter()

    # Ensure the number of pages is a multiple of four
    num_pages = pdf_reader.numPages
    if num_pages % 4 != 0:
        for _ in range(num_pages % 4):
            add_empty_page(input_pdf)

    ## Optional: add empty sheet
    if empty_sheet:
      for _ in range(4):
          add_empty_page(input_pdf)
      input_pdf_file = open('Amended.pdf', 'rb')

    # Reopen input PDF file
    if not empty_sheet:
      input_pdf_file = open(input_pdf, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(input_pdf_file)
    num_pages = pdf_reader.numPages

    # Compute signatures
    sheets = num_pages // 4
    odd_sheets = sheets % section_size
    even_sheets = sheets // section_size - odd_sheets
    offset = 0
    signatures_to_print = []

    # Generate first half
    for _ in range(even_sheets // 2):
        page_counter = 1
        for _ in range(section_size):
            output_page = pdf_writer.addBlankPage(595.3, 841.9)
            output_page.mergePage(
              compile_page(input_pdf, section_size * 4 - page_counter + 1 + offset, page_counter + offset))
            output_page = pdf_writer.addBlankPage(595.3, 841.9)
            output_page.mergePage(
              compile_page(input_pdf, page_counter + 1 + offset, section_size * 4 - page_counter + offset))
            page_counter += 2
        offset += section_size * 4
        signatures_to_print.append(offset)

    # Generate odd signatures
    for _ in range(odd_sheets):
        page_counter = 1
        for _ in range(section_size + 1):
            output_page = pdf_writer.addBlankPage(595.3, 841.9)
            output_page.mergePage(
              compile_page(input_pdf, (section_size + 1) * 4 - page_counter + 1 + offset, page_counter + offset))
            output_page = pdf_writer.addBlankPage(595.3, 841.9)
            output_page.mergePage(
              compile_page(input_pdf, page_counter + 1 + offset, (section_size + 1) * 4 - page_counter + offset))
            page_counter += 2
        offset += (section_size + 1) * 4
        signatures_to_print.append(offset)

    # Generate second half
    for _ in range(even_sheets - even_sheets // 2):
        page_counter = 1
        for _ in range(section_size):
            output_page = pdf_writer.addBlankPage(595.3, 841.9)
            output_page.mergePage(
              compile_page(input_pdf, section_size * 4 - page_counter + 1 + offset, page_counter + offset))
            output_page = pdf_writer.addBlankPage(595.3, 841.9)
            output_page.mergePage(
              compile_page(input_pdf, page_counter + 1 + offset, section_size * 4 - page_counter + offset))
            page_counter += 2
        offset += section_size * 4
        signatures_to_print.append(offset)

    # Write the compiled PDF
    with open(output_pdf_name, 'wb') as output_file:
        pdf_writer.write(output_file)

    update_signatures_text("The signatures are "+ " ".join(map(str, signatures_to_print)) + ".")

###############################################################################
# GUI
###############################################################################

# Create the main window
window = tk.Tk()
window.title("PDF Compilation Tool")

def update_signatures_text(new_text):
    signatures_text.config(state=tk.NORMAL)  # Enable the widget temporarily
    signatures_text.delete(1.0, tk.END)  # Clear existing text
    signatures_text.insert(tk.END, new_text)  # Insert the new text
    signatures_text.config(state=tk.DISABLED)  # Disable the widget again

# Variables to store file paths and options
input_pdf_var = tk.StringVar()
output_name_var = tk.StringVar(value="compiled")
section_size_var = tk.IntVar(value=4)
empty_sheet_var = tk.BooleanVar(value=False)

# Input PDF Label and Browse Button
input_label = tk.Label(window, text="Input PDF:")
input_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

input_entry = tk.Entry(window, textvariable=input_pdf_var, width=40)
input_entry.grid(row=0, column=1, padx=5, pady=10, sticky="w")

input_browse_button = tk.Button(window, text="Browse", command=lambda: browse_input_pdf())
input_browse_button.grid(row=0, column=2, padx=10, pady=10)

# Output Name Label and Entry Box
output_name_label = tk.Label(window, text="Output Name:")
output_name_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

output_name_entry = tk.Entry(window, textvariable=output_name_var)
output_name_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")

# Section Size Dropdown
section_size_label = tk.Label(window, text="Section Size:")
section_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")

section_size_dropdown = tk.OptionMenu(window, section_size_var, 3, 4, 5, 6, 7, 8)
section_size_dropdown.grid(row=2, column=1, padx=5, pady=10, sticky="w")

# Empty Sheet Checkbox
empty_sheet_checkbox = tk.Checkbutton(window, text="Empty Sheet", variable=empty_sheet_var)
empty_sheet_checkbox.grid(row=2, column=2, padx=10, pady=10, sticky="w")

# Compile PDF Button
compile_button = tk.Button(window, text="Compile", command=compile_pdf)
compile_button.grid(row=2, column=3, padx=10, pady=10, sticky="w")

# Signatures Label and Text Output
signatures_label = tk.Label(window, text="Signatures:")
signatures_label.grid(row=3, column=0, padx=10, pady=10, sticky="e")

signatures_text = tk.Text(window, height=5, width=50, state="disabled")
signatures_text.grid(row=3, column=1, columnspan=3, padx=5, pady=10, sticky="w")

# Run the Tkinter event loop
window.mainloop()
