import math

from PyQt5.QtWidgets import QOpenGLWidget

from pyforms_gui.controls.control_player.AbstractGLWidget import AbstractGLWidget


class VideoQt5GLWidget(AbstractGLWidget, QOpenGLWidget):

	def initializeGL(self):
		self.gl = self.context().versionFunctions()
		self.gl.initializeOpenGLFunctions()

		'''
		 Sets up the OpenGL rendering context, defines display lists, etc. 
		 Gets called once before the first time resizeGL() or paintGL() is called.
		'''
		self.gl.glClearDepth(1.0)
		self.gl.glClearColor(0, 0, 0, 1.0)
		self.gl.glEnable(self.gl.GL_DEPTH_TEST)

	def perspective(self, fovy, aspect, zNear, zFar):
		ymax = zNear * math.tan( fovy * math.pi / 360.0 );
		ymin = -ymax;
		xmin = ymin * aspect;
		xmax = ymax * aspect;

		self.gl.glFrustum( xmin, xmax, ymin, ymax, zNear, zFar )

	def resizeGL(self, width, height):
		self.setupViewport(width, height)

	def setupViewport(self, width, height):
		side = min(width, height)
		self.gl.glViewport((width - side) // 2, (height - side) // 2, side,
				side)

		self.gl.glMatrixMode(self.gl.GL_PROJECTION)
		self.gl.glLoadIdentity()
		self.perspective(40.0, float(width) / float(height), 0.01, 10.0)
		self.gl.glMatrixMode(self.gl.GL_MODELVIEW)

	def draw_helptext(self):
		pass

	def draw_message(self):
		pass