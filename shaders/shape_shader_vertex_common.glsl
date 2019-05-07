// shape_shader_vertex_common.glsl

#include "shape_shader_common"

uniform int uShapeCount;
uniform sampler2D sColors;

uniform sampler2D sTransforms;
uniform sampler2D sPanelTexParams;
uniform sampler2D sTexParams;

in vec3 centerPos;

int getShapeIndex(float primOffset) {
	return int(primOffset * (uShapeCount-1));
}

TexLayerAttrs loadTexLayerAttrs(int shapeIndex, int row) {
	TexLayerAttrs attrs;

	int vOffset = row * 5;

	vec4 uvmode_texindex_comp_alpha = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 0), 0);
	vec4 scalexyz_uniformscale = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 1), 0);
	vec3 rotatexyz = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 2), 0).rgb;
	vec3 translatexyz = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 3), 0).rgb;
	vec3 pivotxyz = texelFetch(sTexParams, ivec2(shapeIndex, vOffset + 4), 0).rgb;

	attrs.uvMode = int(round(uvmode_texindex_comp_alpha.r));
	attrs.textureIndex = int(round(uvmode_texindex_comp_alpha.g));
	attrs.compositeMode = int(round(uvmode_texindex_comp_alpha.b));
	attrs.level = uvmode_texindex_comp_alpha.a;

	attrs.transform = scaleRotateTranslateMatrix(
		scalexyz_uniformscale.rgb * scalexyz_uniformscale.a,
		rotatexyz,
		translatexyz);
	attrs.pivot = pivotxyz;

	return attrs;
}

VertexAttrs loadVertexAttrs() {
	VertexAttrs attrs;

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		attrs.texCoord0.st = texcoord.st;
	}
	int shapeIndex = getShapeIndex(attrs.texCoord0.y);

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

	vec4 localOffsetAndLevel = texelFetch(sPanelTexParams, ivec2(shapeIndex, 0), 0);
	vec4 globalOffsetAndLevel = texelFetch(sPanelTexParams, ivec2(shapeIndex, 1), 0);

	attrs.faceTexCoord += localOffsetAndLevel.xyz;
	attrs.localTexLevel = localOffsetAndLevel.w;
	attrs.globalTexCoord += globalOffsetAndLevel.xyz;
	attrs.globalTexLevel = globalOffsetAndLevel.w;

	vec3 localScale = texelFetch(sTransforms, ivec2(shapeIndex, 0), 0).xyz;
	vec3 localRotate = texelFetch(sTransforms, ivec2(shapeIndex, 1), 0).xyz;
	vec3 localTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 2), 0).xyz;

	vec3 globalScale = texelFetch(sTransforms, ivec2(shapeIndex, 3), 0).xyz;
	vec3 globalRotate = texelFetch(sTransforms, ivec2(shapeIndex, 4), 0).xyz;
	vec3 globalTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 5), 0).xyz;

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);

	scaleRotateTranslate(
		worldSpacePos,
		globalScale, globalRotate, globalTranslate,
		vec3(0));
	scaleRotateTranslate(
		worldSpacePos,
		localScale, localRotate, localTranslate,
		centerPos);

	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);


	#ifdef PATH_MODE
	attrs.pathTex = loadTexLayerAttrs(shapeIndex, 0);
	#endif
	#ifdef PANEL_MODE
	attrs.texLayer1 = loadTexLayerAttrs(shapeIndex, 0);
	attrs.texLayer2 = loadTexLayerAttrs(shapeIndex, 1);
	attrs.texLayer3 = loadTexLayerAttrs(shapeIndex, 2);
	attrs.texLayer4 = loadTexLayerAttrs(shapeIndex, 3);
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
