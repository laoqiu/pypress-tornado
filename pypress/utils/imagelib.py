#! /usr/bin/env python
#coding=utf-8
"""
    imageProcess.py
    ~~~~~~~~~~~~~
    Recaptcha and Thumbnail

    :copyright: (c) 2010 by Laoqiu.
    :license: BSD, see LICENSE for more details.
"""

import os
import random
import Image, ImageFont, ImageDraw, ImageEnhance
import StringIO

def Recaptcha(text):
    img = Image.new('RGB',size=(110,26),color=(255,255,255))
    
    # set font
    font = ImageFont.truetype(os.path.join(os.path.dirname(__file__),'FacesAndCaps.ttf'),25)
    draw = ImageDraw.Draw(img)
    colors = [(250,125,30),(15,65,150),(210,30,90),(64,25,90),(10,120,40),(95,0,16)]
    
    # write text
    for i,s in enumerate(text):
        position = (i*25+4,0)
        draw.text(position, s, fill=random.choice(colors),font=font)
    
    # set border
    #draw.line([(0,0),(99,0),(99,29),(0,29),(0,0)], fill=(180,180,180))
    del draw
    
    # push data
    strIO = StringIO.StringIO()
    img.save(strIO,'PNG')
    strIO.seek(0)
    return strIO

def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

class Thumbnail(object):
    """
        t = Thumbnail(path)
        t.thumb(size=(100,100),outfile='file/to/name.xx',bg=False,watermark=None)
    """
    def __init__(self, path):
        self.path = path
        try:
            self.img = Image.open(self.path)
        except IOError:
            self.img = None
            raise "%s not images" % path

    def thumb(self, size=(100,100), outfile=None, filler=False, watermark=None):
        """
            outfile: 'file/to/outfile.xxx'  
            filler: True|False
            watermark: 'file/to/watermark.xxx'
        """
        if not self.img:
            print 'must be have a image to process'
            return

        if not outfile:
            outfile = self.path

        #原图复制
        part = self.img
        part.thumbnail(size, Image.ANTIALIAS) # 按比例缩略
        
        size = size if filler else part.size # 不补白则正常缩放
        w,h = size
        
        layer = Image.new('RGBA',size,(255,255,255)) # 白色底图

        # 计算粘贴的位置
        pw,ph = part.size
        left = (h-ph)/2
        upper = (w-pw)/2
        layer.paste(part,(upper,left)) # 粘贴原图

        # 如果有watermark参数则加水印
        if watermark:
            part = Image.open(watermark)
            part = reduce_opacity(part, 0.3)
            # 粘贴到右下角
            lw,lh = part.size
            position = (w-lw,h-lh)
            if layer.mode != 'RGBA':
                layer.convert('RGBA')
            mark = Image.new('RGBA', layer.size, (0,0,0,0))
            mark.paste(part, position)
            layer = Image.composite(mark, layer, mark)

        layer.save(outfile, quality=100) # 保存
        return outfile
    

if __name__=='__main__':
    t = Thumbnail('pic.jpg')
    t.thumb()
