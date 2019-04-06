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
		sortvals.sort()
		for sortvalindex, sortval in enumerate(sortvals):
			for shapeindex in range(n):
				if sortchan[shapeindex] == sortval and maskchan[shapeindex] >= 0.5:
					seqindex[shapeindex] = sortvalindex / (len(sortvals) - 1)


