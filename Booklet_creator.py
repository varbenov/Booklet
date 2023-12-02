import PyPDF2
import os
from PyPDF2 import PdfFileReader, PdfFileWriter, PageObject, Transformation

current_directory = os.path.dirname(__file__)
os.chdir(current_directory)

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
  #Copy amended file back over the original
  shutil.copyfile('Amended.pdf',input)


# Input PDF used for compilation
input_pdf_name = '16.pdf'

# Output compiled PDF name
output_pdf_name = 'compiled.pdf'

# Open input PDF file
input_pdf_file = open(input_pdf_name, 'rb')
pdf_reader = PyPDF2.PdfFileReader(input_pdf_file)
pdf_writer = PyPDF2.PdfFileWriter()

# Ensure the number of pages is a multiple of four
num_pages = pdf_reader.numPages
if num_pages % 4 != 0:
    for _ in range(num_pages % 4):
        add_empty_page(input_pdf_name)

## Optional: add empty sheet
#for _ in range(4):
#    add_empty_page(input_pdf_name)

# Reopen input PDF file
input_pdf_file = open(input_pdf_name, 'rb')
pdf_reader = PyPDF2.PdfFileReader(input_pdf_file)
num_pages = pdf_reader.numPages

# Compute signatures
sheets = num_pages // 4
section_size = 4
odd_sheets = sheets % section_size
even_sheets = sheets // section_size - odd_sheets
offset = 0

# Generate first half
for _ in range(even_sheets // 2):
    page_counter = 1
    for _ in range(section_size):
        output_page = pdf_writer.addBlankPage(595.3, 841.9)
        output_page.mergePage(
          compile_page(input_pdf_name, section_size * 4 - page_counter + 1 + offset, page_counter + offset))
        output_page = pdf_writer.addBlankPage(595.3, 841.9)
        output_page.mergePage(
          compile_page(input_pdf_name, page_counter + 1 + offset, section_size * 4 - page_counter + offset))
        page_counter += 2
    offset += section_size * 4
    print(offset)

# Generate odd signatures
for _ in range(odd_sheets):
    page_counter = 1
    for _ in range(section_size + 1):
        output_page = pdf_writer.addBlankPage(595.3, 841.9)
        output_page.mergePage(
          compile_page(input_pdf_name, (section_size + 1) * 4 - page_counter + 1 + offset, page_counter + offset))
        output_page = pdf_writer.addBlankPage(595.3, 841.9)
        output_page.mergePage(
          compile_page(input_pdf_name, page_counter + 1 + offset, (section_size + 1) * 4 - page_counter + offset))
        page_counter += 2
    offset += (section_size + 1) * 4
    print(offset)

# Generate second half
for _ in range(even_sheets - even_sheets // 2):
    page_counter = 1
    for _ in range(section_size):
        output_page = pdf_writer.addBlankPage(595.3, 841.9)
        output_page.mergePage(
          compile_page(input_pdf_name, section_size * 4 - page_counter + 1 + offset, page_counter + offset))
        output_page = pdf_writer.addBlankPage(595.3, 841.9)
        output_page.mergePage(
          compile_page(input_pdf_name, page_counter + 1 + offset, section_size * 4 - page_counter + offset))
        page_counter += 2
    offset += section_size * 4
    print(offset)

# Write the compiled PDF
with open(output_pdf_name, 'wb') as output_file:
    pdf_writer.write(output_file)
