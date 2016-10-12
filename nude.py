#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from PIL import Image
import os
import sys

dx = [0, 0, 1, -1]
dy = [1, -1, 0, 0]
class Nude(object):
	def __init__(self, path_or_image):
		# 若 path_or_image 为 Image.Image 类型的实例，直接赋值
		if isinstance(path_or_image, Image.Image):
			self.image = path_or_image
		elif isinstance(path_or_image, str):
			self.image = Image.open(path_or_image)

		# 获得图片所有颜色通道
		bands = self.image.getbands()
		# 判断是否为单通道图片（即灰度图），是则将灰度图转换为 RGB 图
		if len(bands) == 1:
			# 新建相同大小的 RGB 图像
			new_img = Image.new('RGB', self.image.size)
			# 拷贝灰度图 self.image 到 RGB 图 new_img.paste （PIL 自动进行颜色通道转换）
			new_img.paste(self.image)
			f = self.image.filename
			# 替换 self.image
			self.image = new_img
			self.image.filename = f

		# 整合后的皮肤区域，元素的索引即为皮肤区域号，元素都是包含一些 Skin 对象的列表
		self.skin_regions = []
		# 色情图像判断结果
		self.result = None
		# 处理得到的信息
		self.message = None
		# 图像宽高
		self.width, self.height = self.image.size
		# 图像总像素
		self.total_pixels = self.width * self.height
		# 像素点是否被访问过
		self.covered = set()

	def resize(self, maxwidth=1000, maxheight=1000):
		"""
		基于最大宽高按比例重设图片大小，
		注意：这可能影响检测算法的结果

		如果没有变化返回 0
		原宽度大于 maxwidth 返回 1
		原高度大于 maxheight 返回 2
		原宽高大于 maxwidth, maxheight 返回 3

		maxwidth - 图片最大宽度
		maxheight - 图片最大高度
		传递参数时都可以设置为 False 来忽略
		------------------------------
		Image.resize(size, resample=0) : 
		size – 包含宽高像素数的元祖 (width, height) resample – 可选的重采样滤波器
		返回 Image 对象
		"""

		# 存储返回值
		ret = 0
		if maxwidth:
			if self.width > maxwidth:
				wpercent = (maxwidth / self.width)
				hsize = int((self.height * wpercent))
				fname = self.image.filename
				# Image.LANCZOS 是重采样滤波器，用于抗锯齿
				self.image = self.image.resize((maxwidth, hsize), Image.LANCZOS)
				self.image.filename = fname
				self.width, self.height = self.image.size
				self.total_pixels = self.width * self.height
				ret += 1
		if maxheight:
			if self.height > maxheight:
				hpercent = (maxheight / float(self.height))
				wsize = int((float(self.width) * float(hpercent)))
				fname = self.image.filename
				self.image = self.image.resize((wsize, maxheight), Image.LANCZOS)
				self.image.filename = fname
				self.width, self.height = self.image.size
				self.total_pixels = self.width * self.height
				ret += 2
		return ret

	def _classify_skin(self, r, g, b):
		print(r,g,b)
		# 根据 RGB 值判定
		# rgb_classifier = r > 95 and \
		# 				g > 40 and g < 100 and \
		# 				b > 20 and \
		# 				max([r, g, b]) - min([r, g, b]) > 15 and \
		# 				abs(r - g) > 15 and \
		# 				r > g and \
		# 				r > b
		# # 根据处理后的 RGB 值判定
		# nr, ng, nb = self._to_normalized(r, g, b)
		# norm_rgb_classifier = nr / ng > 1.185 and \
		# 					float(r * b) / ((r + g + b) ** 2) > 0.107 and \
		# 					float(r * g) / ((r + g + b) ** 2) > 0.112
		# # HSV 颜色模式下的判定
		# h, s, v = self._to_hsv(r, g, b)
		# hsv_classifier = h > 0 and \
		# 				h < 35 and \
		# 				s > 0.23 and \
		# 				s < 0.68

		# YCbCr 颜色模式下的判定
		y, cb, cr = self._to_ycbcr(r, g, b)
		ycbcr_classifier = 97.5 <= cb <= 142.5 and 134 <= cr <= 176

		# 效果不是很好，还需改公式
		#return rgb_classifier or norm_rgb_classifier or hsv_classifier or ycbcr_classifier
		return ycbcr_classifier

	# @profile
	def parse(self):
		# 如果已有结果，返回本对象
		if self.result is not None:
			return self
		# 获得图片所有像素数据
		import ctypes  
		Cfunction = ctypes.CDLL("./_classify_skin.so")  

		self.pixels = self.image.load()
		# 遍历每个像素，对每个未访问过的皮肤像素进行dfs
		for y in range(self.height):
			for x in range(self.width):
				_id = y*self.width+x
				if _id not in self.covered:
					r = self.pixels[x, y][0]	# red
					g = self.pixels[x, y][1] 	# green
					b = self.pixels[x, y][2] 	# blue
					if Cfunction._classify_skin(r, g, b):
						self.covered.add(_id)
						new_region = [(x,y)]
						stack = [(x,y)]
						while stack:
							top = stack[-1]
							flag = 1
							for i in [0,1,2,3]:
								nx = top[0] + dx[i]
								ny = top[1] + dy[i]
								if 0 <= nx < self.width and 0 <= ny < self.height:
									_nid = ny*self.width+nx
									if _nid not in self.covered:
										# 得到像素的 RGB 三个通道的值
										# [x, y] 是 [(x, y)] 的简便写法
										r = self.pixels[nx, ny][0]		# red
										g = self.pixels[nx, ny][1] 		# green
										b = self.pixels[nx, ny][2] 		# blue
										if Cfunction._classify_skin(r, g, b):
											self.covered.add(_nid)
											flag = 0
											new_region.append((nx, ny))
											stack.append((nx, ny))
							if flag:
								stack.pop()
						if len(new_region) > 100:
							self.skin_regions.append(new_region)
		self._analyse_regions()
		return self

	def _to_normalized(self, r, g, b):
		if r == 0:
			r = 0.0001
		if g == 0:
			g = 0.0001
		if b == 0:
			b = 0.0001
		_sum = float(r + g + b)
		return [r / _sum, g / _sum, b / _sum]

	def _to_ycbcr(self, r, g, b):
		# 公式来源：
		# http://stackoverflow.com/questions/19459831/rgb-to-ycbcr-conversion-problems
		y = .299*r + .587*g + .114*b
		cb = 128 - 0.168736*r - 0.331364*g + 0.5*b
		cr = 128 + 0.5*r - 0.418688*g - 0.081312*b
		return y, cb, cr

	def _to_hsv(self, r, g, b):
		h = 0
		_sum = float(r + g + b)
		_max = float(max([r, g, b]))
		_min = float(min([r, g, b]))
		diff = float(_max - _min)
		if _sum == 0:
			_sum = 0.0001

		if _max == r:
			if diff == 0:
				h = sys.maxsize
			else:
				h = (g - b) / diff
		elif _max == g:
			h = 2 + ((g - r) / diff)
		else:
			h = 4 + ((r - g) / diff)

		h *= 60
		if h < 0:
			h += 360

		return [h, 1.0 - (3.0 * (_min / _sum)), (1.0 / 3.0) * _max]

	def _analyse_regions(self):
		# 如果皮肤区域小于 3 个，不是色情
		if len(self.skin_regions) < 3:
			self.message = "Less than 3 skin regions ({_skin_regions_size})".format(_skin_regions_size=len(self.skin_regions))
			self.result = False
			return self.result

		# 为皮肤区域排序
		self.skin_regions = sorted(self.skin_regions, key=lambda s: len(s),
									reverse=True)

		# 计算皮肤总像素数
		total_skin = float(sum([len(skin_region) for skin_region in self.skin_regions]))

		# 如果皮肤区域与整个图像的比值小于 15%，那么不是色情图片
		if total_skin / self.total_pixels * 100 < 15:
			self.message = "Total skin percentage lower than 15 ({:.2f})".format(total_skin / self.total_pixels * 100)
			self.result = False
			return self.result

		# 如果最大皮肤区域小于总皮肤面积的 45%，不是色情图片
		if len(self.skin_regions[0]) / total_skin * 100 < 45:
			self.message = "The biggest region contains less than 45 ({:.2f})".format(len(self.skin_regions[0]) / total_skin * 100)
			self.result = False
			return self.result

		# 皮肤区域数量超过 60 个，不是色情图片
		if len(self.skin_regions) > 60:
			self.message = "More than 60 skin regions ({})".format(len(self.skin_regions))
			self.result = False
			return self.result

		# 其它情况为色情图片
		self.message = "Nude!!"
		self.result = True
		return self.result

	def inspect(self):
		_image = '{} {} {}×{}'.format(self.image.filename, self.image.format, self.width, self.height)
		return "{_image}: result={_result} message='{_message}'".format(_image=_image, _result=self.result, _message=self.message)

	# 将在源文件目录生成图片文件，将皮肤区域可视化
	def showSkinRegions(self):
		# 未得出结果时方法返回
		if self.result is None:
			return
		# 初始化与原图同大小黑色图片
		simage = Image.new('RGBA', self.image.size, (0,0,0))
		# 加载像素数据
		simageData = simage.load()

		for skin_region in self.skin_regions:
			for skin_pixel_coord in skin_region:
				simageData[skin_pixel_coord] = 255, 255, 255

		# 源文件绝对路径
		filePath = os.path.abspath(self.image.filename)
		# 源文件所在目录
		fileDirectory = os.path.dirname(filePath) + '/'
		# 源文件的完整文件名
		fileFullName = os.path.basename(filePath)
		# 分离源文件的完整文件名得到文件名和扩展名
		fileName, fileExtName = os.path.splitext(fileFullName)
		# 保存图片
		simage.save('{}{}_{}{}'.format(fileDirectory, fileName,'Nude' if self.result else 'Normal', fileExtName))

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description='Detect nudity in images.')
	parser.add_argument('files', metavar='image', nargs='+',help='Images you wish to test')
	parser.add_argument('-r', '--resize', action='store_true',help='Reduce image size to increase speed of scanning')
	parser.add_argument('-v', '--visualization', action='store_true',help='Generating areas of skin image')

	args = parser.parse_args()

	for fname in args.files:
		if os.path.isfile(fname):
			n = Nude(fname)
			if args.resize:
				n.resize(maxwidth=800, maxheight=600)
			else:
				n.resize()
			n.parse()
			if args.visualization:
				n.showSkinRegions()
			print(n.result, n.inspect())
		else:
			print(fname, "is not a file")