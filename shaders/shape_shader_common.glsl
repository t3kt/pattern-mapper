// shape_shader_common.glsl

struct VertexAttrs {
	vec4 color;
	vec3 worldSpacePos;
	vec2 texCoord0;
	vec2 texCoord1;
	vec2 faceTexCoord;
	flat int shapeIndex;
};


// https://gist.github.com/onedayitwillmake/3288507
mat4 rotationX( in float angle ) {
	return mat4(	1.0,		0,			0,			0,
			 		0, 	cos(angle),	-sin(angle),		0,
					0, 	sin(angle),	 cos(angle),		0,
					0, 			0,			  0, 		1);
}
mat4 rotationY( in float angle ) {
	return mat4(	cos(angle),		0,		sin(angle),	0,
			 				0,		1.0,			 0,	0,
					-sin(angle),	0,		cos(angle),	0,
							0, 		0,				0,	1);
}
mat4 rotationZ( in float angle ) {
	return mat4(	cos(angle),		-sin(angle),	0,	0,
			 		sin(angle),		cos(angle),		0,	0,
							0,				0,		1,	0,
							0,				0,		0,	1);
}

mat4 rotationXYZ(in vec3 r) {
	return rotationX(r.x) * rotationY(r.y) * rotationZ(r.z);
}

void scaleRotateTranslate(
		inout vec4 pos,
		in vec3 scale,
		in vec3 rotate,
		in vec3 translate,
		in vec3 pivot) {
	pos.xyz -= pivot;
	pos.xyz *= scale;
	pos *= rotationXYZ(radians(rotate));
	pos.xyz += translate + pivot;
}
