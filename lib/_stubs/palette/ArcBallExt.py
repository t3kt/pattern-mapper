from ..TDStoreTools import StorageManager
from .. import op, tdu

class ArcBallExt():

	def __init__(self, ownerComp):
		'''
		Basic extension class for enhancing TouchDesigner component networks
		with python functionality
		'''
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.arcInst = tdu.ArcBall(forCamera=True)
		self.matrix = tdu.Matrix()

		# The name for the dependency storage object is
		# this class name appended with 'Stored' ie. "ArcBallExtStored"
		storedItems = [
			{'name': 'Empty', 'default': 0},
		]

		# The stored attribute allows for easy access to the stored dependency dictionary
		self.stored = StorageManager(self, ownerComp, storedItems)

	def StartTransform(self, btn=None, u=0, v=0):
		if btn == 'lselect':
			# if lselect ==> rotate
			self.arcInst.beginRotate(u, v)
		elif btn == 'rselect':
			# if rselect ==> pan
			self.arcInst.beginPan(u, v)
		elif btn == 'mselect':
			# if mselect ==> zoom
			self.arcInst.beginDolly(u, v)

		return

	def Transform(self, btn=None, u=0, v=0, scaler=1):
		if btn == 'lselect':
			# if lselect ==> rotate
			self.arcInst.rotateTo(u, v, scale=scaler)
		elif btn == 'rselect':
			# if rselect ==> pan
			self.arcInst.panTo(u, v, scale=scaler)
		elif btn == 'mselect':
			# if mselect ==> zoom
			self.arcInst.dollyTo(u, v, scale=scaler)

		self.fillMat()
		return

	def Reset(self):
		op('autoRotate/hold1').par.pulse.pulse()
		op('autoRotate/hold2').par.pulse.pulse()
		op('autoRotate/hold3').par.pulse.pulse()
		self.arcInst.identity()
		self.fillMat()
		return

	def fillMat(self):
		newMat = self.arcInst.transform()
		self.matrix = newMat
		self.ownerComp.cook(force=True)
		for i in range(4):
			for j in range(4):
				op('newMat')[i, j] = newMat[i, j]

		return
