export class PatternListEntry {
  name: string;
}

export class PatternData {}

export class PatternSettings {}

export class PointData {
  pos: number[];
  absdist: number;
  reldist: number;
}

export class ShapeInfo {
  shapeindex: number;
  shapename: string;
  shapepath: string;
  parentpath: string;
  color: any;
  center: number[];
  shapelength: number;
  depthlayer: number;
  points: PointData[];
  dupcount: number;
  radius: number;
  rotateaxis: number;
}

export class SequenceStep {
  sequenceindex: number;
  shapeindices: number[];
  isdefault: boolean;
  inferredfromvalue: any;
}

export class GroupInfo {
  groupname: string;
  grouppath: string;
  inferencetype: string;
  inferredfromvalue: any;
  depthlayer: any;
  depth: number;
  shapeindices: number[];
  sequencesteps: SequenceStep[];
  temporary: boolean;
  rotateaxis: number;
}
