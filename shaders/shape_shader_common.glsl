// shape_shader_common.glsl

struct TexLayerAttrs {
	flat int textureIndex;
	flat int compositeMode;
	flat float level;
	vec3 texCoord;
};

struct VertexAttrs {
	flat bool visible;
	flat vec4 color;
	vec3 worldSpacePos;
	vec2 texCoord0;
	vec3 faceTexCoord;
	vec3 globalTexCoord;
	flat int shapeIndex;

	#ifdef PATH_MODE
	TexLayerAttrs pathTex;
	#endif
	#ifdef PANEL_MODE
	TexLayerAttrs texLayer1;
	TexLayerAttrs texLayer2;
	TexLayerAttrs texLayer3;
	TexLayerAttrs texLayer4;
	#endif
};

#define UVMODE_LOCAL 0
#define UVMODE_GLOBAL 1
#define UVMODE_PATH 2

#define COMP_ADD 0
#define COMP_ATOP 1
#define COMP_AVERAGE 2
#define COMP_DIFFERENCE 3
#define COMP_INSIDE 4
#define COMP_MAXIMUM 5
#define COMP_MINIMUM 6
#define COMP_MULTIPLY 7
#define COMP_OUTSIDE 8
#define COMP_OVER 9
#define COMP_SCREEN 10
#define COMP_SUBTRACT 11
#define COMP_UNDER 12

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

mat4 translateMatrix(in vec3 t) {
	return mat4(
		1.0, 0.0, 0.0, t.x,
		0.0, 1.0, 0.0, t.y,
		0.0, 0.0, 1.0, t.z,
		0.0, 0.0, 0.0, 1.0);
}

mat4 scaleMatrix(in vec3 s) {
	return mat4(
		s.x, 0.0, 0.0, 0.0,
		0.0, s.y, 0.0, 0.0,
		0.0, 0.0, s.z, 0.0,
		0.0, 0.0, 0.0, 1.0);
}

mat4 scaleRotateTranslateMatrix(in vec3 scale, in vec3 rotate, in vec3 translate) {
	mat4 m = scaleMatrix(scale);
	m *= rotationXYZ(radians(rotate));
	return m * translateMatrix(translate);
}

void scaleRotateTranslate(
		inout vec4 pos,
		in vec3 scale,
		in vec3 rotate,
		in vec3 translate,
		in vec3 pivot,
		in vec3 rotateAxis) {
	pos.xyz -= pivot;
	pos *= rotationXYZ(-radians(rotateAxis));
	pos *= scaleRotateTranslateMatrix(scale, rotate, translate);
	pos *= rotationXYZ(radians(rotateAxis));
	pos.xyz += pivot;
}

void scaleRotateTranslate(
		inout mat4 m,
		in vec3 scale,
		in vec3 rotate,
		in vec3 translate,
		in vec3 pivot,
		in vec3 rotateAxis) {
	m *= translateMatrix(-pivot);
	m *= rotationXYZ(-radians(rotateAxis));
	m *= scaleRotateTranslateMatrix(scale, rotate, translate);
	m *= rotationXYZ(radians(rotateAxis));
	m *= translateMatrix(pivot);
}
