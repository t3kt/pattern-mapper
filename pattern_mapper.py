remap = mod.tdu.remap

def getGroupChanNames(groupspec):
	if not groupspec:
		return []
	if ' ' not in groupspec:
		return ['group_' + groupspec]
	return ['group_' + part for part in groupspec.split(' ')]

def generateSequenceIndex(chop, shapeattrs, mask, sortby):
	chop.clear()
	seqindex = chop.appendChan('seqindex')
	n = chop.numSamples = shapeattrs.numSamples
	sortby = sortby or 'index'
	sortchan = shapeattrs.chan(sortby)
	maskchan = mask['mask']
	if sortchan is None:
		for i in range(n):
			seqindex[i] = i / (n - 1)
	else:
		sortvals = []
		for i in range(n):
			if maskchan[i] < 0.5:
				seqindex[i] = 0
				continue
			s = sortchan[i]
			if s not in sortvals:
				sortvals.append(s)
		if len(sortvals) < 2:
			return
		sortvals.sort()
		for sortvalindex, sortval in enumerate(sortvals):
			for shapeindex in range(n):
				if sortchan[shapeindex] == sortval and maskchan[shapeindex] >= 0.5:
					seqindex[shapeindex] = sortvalindex / (len(sortvals) - 1)

class PatternParser:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

	@property
	def _shapeAttrs(self):
		return self.ownerComp.op('shape_attrs')

	@property
	def _shapes(self):
		return self.ownerComp.op('shapes')

	def BuildGroupTable(self, dat):
		dat.clear()
		dat.appendRow(['groupname', 'groupindex', 'shapes'])
		attrs = self._shapeAttrs
		n = attrs.numSamples
		for groupindex, groupchan in enumerate(attrs.chans('group_*')):
			dat.appendRow([
				groupchan.name.replace('group_', ''),
				groupindex,
				' '.join([
					str(i)
					for i in range(n)
					if groupchan[i]
				])
			])

	def BuildPathLookupTable(self, chop, tablelength):
		chop.clear()
		shapes = self._shapes
		shapecount = shapes.numPrims
		chop.numSamples = tablelength
		for shapeindex in range(shapecount):
			xchan = chop.appendChan('shape{}:tx'.format(shapeindex))
			ychan = chop.appendChan('shape{}:ty'.format(shapeindex))
			zchan = chop.appendChan('shape{}:tz'.format(shapeindex))
			prim = shapes.prims[shapeindex]
			for i in range(tablelength):
				pos = prim.eval(i / (tablelength - 1), 0)
				xchan[i] = pos.x
				ychan[i] = pos.y
				zchan[i] = pos.z


class PatternDebugger:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

	@property
	def _shapeAttrs(self):
		return self.ownerComp.op('shape_attrs')

	@property
	def _shapeCount(self):
		return self._shapeAttrs.numSamples

	def SelectShape(self, i, toggle=False):
		n = self._shapeCount
		if i < 0 or i >= n or (toggle and i == self.ownerComp.par.Selectedshape):
			self.ownerComp.par.Selectedshape = -1
		else:
			self.ownerComp.par.Selectedshape = i

	def PrevShape(self):
		i = self.ownerComp.par.Selectedshape
		if i > 0:
			i -= 1
		else:
			i = self._shapeCount - 1
		self.SelectShape(i)

	def NextShape(self):
		i = self.ownerComp.par.Selectedshape
		n = self._shapeCount
		if i < (n - 1):
			i += 1
		else:
			i = 0
		self.SelectShape(i)

	def BuildShapeInfo(self, dat):
		dat.clear()
		i = self.ownerComp.par.Selectedshape.eval()
		attrs = self._shapeAttrs
		if i == -1 or i >= attrs.numSamples:
			i = None
			dat.appendRow(['index', ''])
		else:
			dat.appendRow(['index', i])
		groups = {}
		vals = {}
		for chan in attrs.chans():
			if chan.name == 'index':
				continue
			if i is None:
				val = ''
			else:
				val = chan[i]
			if chan.name.startswith('group_'):
				groupname = chan.name.replace('group_','')
				groups[groupname] = int(val) if isinstance(val, (float,int)) else val
			elif isinstance(val, str):
				vals[chan.name] = val
			else:
				vals[chan.name] = round(val, 4)
		for name in sorted(vals.keys()):
			dat.appendRow([name, vals[name]])
		for name in sorted(groups.keys()):
			dat.appendRow(['group[{}]'.format(name), groups[name]])
