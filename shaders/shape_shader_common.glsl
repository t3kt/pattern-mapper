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
	vec2 pathTexCoord;
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
	m *= translateMatrix(translate);
	return m;
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

	pos *= scaleMatrix(scale);
	pos *= rotationXYZ(rotate);
	pos.xyz += translate;

	pos *= rotationXYZ(radians(rotateAxis));
	pos.xyz += pivot;
}

vec3 getTexCoordForUVMode(in VertexAttrs attrs, int uvMode) {
	switch (uvMode) {
		case UVMODE_GLOBAL: return attrs.globalTexCoord;
		case UVMODE_LOCAL: return attrs.faceTexCoord;
		case UVMODE_PATH: return vec3(attrs.pathTexCoord, 0.0);
	}
	return vec3(0.0);
}

TexLayerAttrs loadTexLayerAttrs(
	in sampler2D sTexParams,
	in int shapeIndex, in VertexAttrs attrs, in int row) {
	TexLayerAttrs texAttrs;

	int vOffset = row * 5;

	vec4 uvmode_texindex_comp_alpha = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 0), 0);
	vec4 scalexyz_uniformscale = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 1), 0);
	vec3 rotatexyz = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 2), 0).rgb;
	vec3 translatexyz = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 3), 0).rgb;
	vec3 pivotxyz = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 4), 0).rgb;

	int uvMode = int(round(uvmode_texindex_comp_alpha.r));
	texAttrs.textureIndex = int(round(uvmode_texindex_comp_alpha.g));
	texAttrs.compositeMode = int(round(uvmode_texindex_comp_alpha.b));
	texAttrs.level = uvmode_texindex_comp_alpha.a;

	vec4 texCoord = vec4(getTexCoordForUVMode(attrs, uvMode), 0.0);
	scaleRotateTranslate(
		texCoord,
		scalexyz_uniformscale.xyz * scalexyz_uniformscale.w,
		rotatexyz,
		translatexyz,
		pivotxyz,
		vec3(0));
	texAttrs.texCoord = texCoord.xyz;

	return texAttrs;
}

void loadBasicVertexAttrs(
	inout VertexAttrs attrs,
	in int shapeIndex,
	in sampler2D sTexParams,
	in sampler2D sColors,
	in sampler2D sAttrs) {
	
	attrs.shapeIndex = shapeIndex;
	attrs.color = texelFetch(sColors, ivec2(shapeIndex, 0), 0);
	attrs.visible = texelFetch(sAttrs, ivec2(shapeIndex, 0), 0).r > 0.5;

	#ifdef PATH_MODE
	attrs.pathTex = loadTexLayerAttrs(sTexParams, shapeIndex, attrs, 0);
	#endif
	#ifdef PANEL_MODE
	attrs.texLayer1 = loadTexLayerAttrs(sTexParams, shapeIndex, attrs, 0);
	attrs.texLayer2 = loadTexLayerAttrs(sTexParams, shapeIndex, attrs, 1);
	attrs.texLayer3 = loadTexLayerAttrs(sTexParams, shapeIndex, attrs, 2);
	attrs.texLayer4 = loadTexLayerAttrs(sTexParams, shapeIndex, attrs, 3);
	#endif
}
