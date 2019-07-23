// shape_shader_vertex_common.glsl

#include "shape_shader_common"

uniform sampler2D sColors;

uniform sampler2D sTransforms;
uniform sampler2D sTexParams;
uniform sampler2D sAttrs;

in vec3 centerPos;
in int shapeIndex;

vec3 getTexCoordForUVMode(in VertexAttrs attrs, int uvMode) {
	switch (uvMode) {
		case UVMODE_GLOBAL: return attrs.globalTexCoord;
		case UVMODE_LOCAL: return attrs.faceTexCoord;
		case UVMODE_PATH: return vec3(attrs.texCoord0, 0.0);
	}
	return vec3(0.0);
}

TexLayerAttrs loadTexLayerAttrs(in int shapeIndex, in VertexAttrs attrs, in int row) {
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
		pivotxyz);
	texAttrs.texCoord = texCoord.xyz;

	return texAttrs;
}

VertexAttrs loadVertexAttrs() {
	VertexAttrs attrs;

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		attrs.texCoord0.st = texcoord.st;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[1]);
		attrs.globalTexCoord = texcoord;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[2]);
		attrs.faceTexCoord = texcoord;
	}

	attrs.shapeIndex = shapeIndex;
	attrs.color = texelFetch(sColors, ivec2(shapeIndex, 0), 0);
	attrs.visible = texelFetch(sAttrs, ivec2(shapeIndex, 0), 0).r > 0.5;

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);


	if (!attrs.visible) {
		worldSpacePos = vec4(-1000.0);
	} else {
		vec4 localScaleXYZUniform = texelFetch(sTransforms, ivec2(shapeIndex, 0), 0);
		vec3 localScale = localScaleXYZUniform.xyz * localScaleXYZUniform.w;
		vec3 localRotate = texelFetch(sTransforms, ivec2(shapeIndex, 1), 0).xyz;
		vec3 localTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 2), 0).xyz;

		vec4 globalScaleXYZUniform = texelFetch(sTransforms, ivec2(shapeIndex, 3), 0);
		vec3 globalScale = globalScaleXYZUniform.xyz * globalScaleXYZUniform.w;
		vec3 globalRotate = texelFetch(sTransforms, ivec2(shapeIndex, 4), 0).xyz;
		vec3 globalTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 5), 0).xyz;

		scaleRotateTranslate(
			worldSpacePos,
			globalScale, globalRotate, globalTranslate,
			vec3(0));
		scaleRotateTranslate(
			worldSpacePos,
			localScale, localRotate, localTranslate,
			centerPos);
	}

	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);

	#ifdef PATH_MODE
	attrs.pathTex = loadTexLayerAttrs(shapeIndex, attrs, 0);
	#endif
	#ifdef PANEL_MODE
	attrs.texLayer1 = loadTexLayerAttrs(shapeIndex, attrs, 0);
	attrs.texLayer2 = loadTexLayerAttrs(shapeIndex, attrs, 1);
	attrs.texLayer3 = loadTexLayerAttrs(shapeIndex, attrs, 2);
	attrs.texLayer4 = loadTexLayerAttrs(shapeIndex, attrs, 3);
	#endif

	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

	attrs.worldSpacePos.xyz = worldSpacePos.xyz;
//	attrs.color *= TDInstanceColor(Cd);

#else // TD_PICKING_ACTIVE

#endif // TD_PICKING_ACTIVE

	return attrs;
}
